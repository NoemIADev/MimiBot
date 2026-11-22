#!/usr/bin/env bash
# Run as the SSH deployment user (Docker access required). Never use set -x.
set -Eeuo pipefail
umask 077

IMAGE=${1:?Image argument required}
DOMAIN=${2:?HTTPS domain argument required}
[[ "$IMAGE" =~ ^mimi-backend:[a-f0-9]{40}-[0-9]+-[0-9]+$ ]] || exit 2
[[ "$DOMAIN" =~ ^[a-zA-Z0-9][a-zA-Z0-9.-]*\.[a-zA-Z]{2,}$ ]] || exit 2
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
ENV_FILE="$HOME/.config/mimibot/backend.env"
CURRENT=mimi-backend
PREVIOUS=mimi-backend-previous
CANDIDATE=mimi-backend-candidate
phase=preflight
cutover=0
old_exists=0
old_saved=0
candidate_created=0
finished=0

log() { printf '%s\n' "$*"; }
exists() { docker container inspect "$1" > /dev/null 2>&1; }
healthy() {
  local container=$1
  for attempt in {1..30}; do
    if docker exec "$container" python -c '
import json, urllib.request
origin = "https://main.dglkmagjtpwpq.amplifyapp.com"
request = urllib.request.Request("http://127.0.0.1:8000/", headers={"Origin": origin})
with urllib.request.urlopen(request, timeout=2) as response:
    data = json.load(response)
    assert response.headers.get("Access-Control-Allow-Origin") == origin
assert data["message"] == "API Mimi OK"
assert origin in data["allowed_origins"]
' > /dev/null 2>&1; then
      return 0
    fi
    sleep 2
  done
  return 1
}

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
          && docker start "$CURRENT" > /dev/null 2>&1 && healthy "$CURRENT"; then
          log "ROLLBACK OK: previous container and its original environment restored."
        else
          log "ROLLBACK FAILED: inspect the VM locally; previous image has not been deleted."
        fi
      elif (( old_exists == 1 )); then
        if docker update --restart unless-stopped "$CURRENT" > /dev/null 2>&1 \
          && docker start "$CURRENT" > /dev/null 2>&1 && healthy "$CURRENT"; then
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
  if (( candidate_created == 1 )); then
    docker rm -f "$CANDIDATE" > /dev/null 2>&1 || true
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

phase=environment-validation
# Docker parses the env file; it is never sourced as shell code or logged.
docker run --rm --network none --env-file "$ENV_FILE" --entrypoint python "$IMAGE" -c '
import os, sys
required = ("DATABASE_URL", "OPENROUTER_API_KEY", "OPENROUTER_BASE_URL",
            "OPENROUTER_LLM_MODEL", "OPENROUTER_EMBEDDING_MODEL",
            "OPENROUTER_EMBEDDING_DIMENSIONS", "ALLOWED_ORIGINS")
if any(not os.getenv(key) for key in required):
    sys.exit(1)
assert os.environ["OPENROUTER_EMBEDDING_DIMENSIONS"] == "1536"
assert "https://main.dglkmagjtpwpq.amplifyapp.com" in [x.strip() for x in os.environ["ALLOWED_ORIGINS"].split(",")]
' > /dev/null 2>&1 || { log "ERROR: check the seven required env variables, dimensions=1536 and Amplify origin on the VM."; exit 1; }

phase=candidate-health
exists "$CANDIDATE" && { log "ERROR: stale candidate container; inspect it locally before retrying."; exit 1; }
candidate_created=1
docker run -d --name "$CANDIDATE" --env-file "$ENV_FILE" \
  --log-opt max-size=10m --log-opt max-file=3 "$IMAGE" > /dev/null 2>&1
healthy "$CANDIDATE" || { log "ERROR: candidate GET / or CORS configuration failed."; exit 1; }
docker rm -f "$CANDIDATE" > /dev/null 2>&1
candidate_created=0
log "PASS: new image starts and permits the Amplify origin."

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
phase=live-health
healthy "$CURRENT"
phase=https-health
curl --fail --silent --connect-timeout 10 --max-time 20 --retry 3 --retry-delay 3 \
  "https://$DOMAIN/" 2>/dev/null | python3 -c '
import json, sys
data = json.load(sys.stdin)
assert data["message"] == "API Mimi OK"
assert "https://main.dglkmagjtpwpq.amplifyapp.com" in data["allowed_origins"]
' > /dev/null 2>&1
finished=1
log "PASS: deployment, GET / over HTTPS and CORS verified."
log "Previous container retained stopped for rollback; runtime env file untouched."
