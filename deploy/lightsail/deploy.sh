#!/usr/bin/env bash
# Run as the SSH deployment user (Docker access required). Never use set -x.
set -Eeuo pipefail
umask 077

IMAGE=${1:?Image argument required}
[[ "$IMAGE" =~ ^mimi-backend:[a-f0-9]{40}-[0-9]+-[0-9]+$ ]] || exit 2
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
ENV_FILE="$HOME/.config/mimibot/backend.env"
CURRENT=mimi-backend
PREVIOUS=mimi-backend-previous
phase=preflight
cutover=0
old_exists=0
old_saved=0
finished=0

log() { printf '%s\n' "$*"; }
exists() { docker container inspect "$1" > /dev/null 2>&1; }

on_exit() {
  local rc=$?
  trap - EXIT HUP INT TERM
  if (( finished == 0 )); then
    log "ERROR: deployment failed during '$phase'. Application logs and environment are not printed."
    if (( cutover == 1 )); then
      log "Restoring previous container..."
      if (( old_saved == 1 )); then
        docker rm -f "$CURRENT" > /dev/null 2>&1 || true
        if docker rename "$PREVIOUS" "$CURRENT" > /dev/null 2>&1 \
          && docker update --restart unless-stopped "$CURRENT" > /dev/null 2>&1 \
          && docker start "$CURRENT" > /dev/null 2>&1; then
          log "ROLLBACK OK: previous container and its original environment restored."
        else
          log "ROLLBACK FAILED: inspect the VM locally; previous image has not been deleted."
        fi
      elif (( old_exists == 1 )); then
        if docker update --restart unless-stopped "$CURRENT" > /dev/null 2>&1 \
          && docker start "$CURRENT" > /dev/null 2>&1; then
          log "ROLLBACK OK: original container restarted."
        else
          log "ROLLBACK FAILED: inspect the original container locally."
        fi
      else
        docker rm -f "$CURRENT" > /dev/null 2>&1 || true
        log "First deployment: no previous container exists; failed container removed."
      fi
    else
      log "The running backend was not replaced."
    fi
    rc=1
  fi
  exit "$rc"
}

[[ -d "$HOME/.config/mimibot" ]] || { log "ERROR: create the protected ~/.config/mimibot directory first."; exit 1; }
# Serialize deployments on the VM as well as in GitHub Actions.
exec 9> "$HOME/.config/mimibot/deploy.lock"
flock -n 9 || { log "ERROR: another deployment is already running."; exit 1; }
trap on_exit EXIT
trap 'exit 1' HUP INT TERM

[[ -f "$ENV_FILE" && ! -L "$ENV_FILE" ]] || { log "ERROR: backend.env is missing or is a symlink."; exit 1; }
[[ $(stat -c %a "$ENV_FILE") == 600 && $(stat -c %u "$ENV_FILE") == "$(id -u)" ]] \
  || { log "ERROR: backend.env must be owned by the deployment user, mode 600."; exit 1; }
[[ $(uname -m) == x86_64 ]] || { log "ERROR: workflow builds amd64; VM architecture must be x86_64."; exit 1; }
docker info > /dev/null 2>&1
sha256sum --check --status image.sha256 || { log "ERROR: image archive checksum mismatch."; exit 1; }
phase=image-load
docker load -i image.tar.gz > /dev/null 2>&1
docker image inspect "$IMAGE" > /dev/null 2>&1

phase=cutover
if exists "$CURRENT"; then
  old_exists=1
  # Retain the current release; discard only the older rollback container.
  if exists "$PREVIOUS"; then docker rm -f "$PREVIOUS" > /dev/null 2>&1; fi
  cutover=1
  docker stop --time 30 "$CURRENT" > /dev/null 2>&1
  docker update --restart no "$CURRENT" > /dev/null 2>&1
  docker rename "$CURRENT" "$PREVIOUS"
  old_saved=1
else
  cutover=1
fi
docker run -d --name "$CURRENT" --restart unless-stopped \
  --env-file "$ENV_FILE" -p 127.0.0.1:8000:8000 \
  --log-opt max-size=10m --log-opt max-file=3 "$IMAGE" > /dev/null 2>&1
finished=1
log "Backend container started. No application tests were run."
log "Previous container retained stopped; runtime env file untouched."
