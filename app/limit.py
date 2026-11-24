import hmac
import os
from contextlib import closing, contextmanager

from fastapi import HTTPException

from db import get_db_connection


@contextmanager
def compter_message(session_id: str, adresse_ip: str):
    """Réserve les quotas et fournit la transaction où enregistrer la réponse."""

    if not session_id.strip() or len(session_id) > 255:
        raise HTTPException(
            status_code=422,
            detail="Identifiant de session invalide.",
        )

    # La clé reste sur le backend. Neon reçoit seulement l'empreinte de l'IP.
    cle_secrete = os.environ["RATE_LIMIT_SECRET"].encode()
    empreinte_ip = hmac.digest(cle_secrete, adresse_ip.encode(), "sha256").hex()

    quotas = [
        ("session", session_id, 35), #limit session
        ("ip", empreinte_ip, 70), #limit ip
    ]

    with closing(get_db_connection()) as connexion:
        # 1. Supprimer les empreintes IP des jours précédents.
        # Les compteurs de session et l'historique des conversations sont conservés.
        with connexion:
            with connexion.cursor() as curseur:
                curseur.execute(
                    """
                    DELETE FROM rate_limits
                    WHERE identifier_type = 'ip'
                      AND date < (CURRENT_TIMESTAMP AT TIME ZONE 'Europe/Paris')::date
                    """
                )

        # 2. Réserver une place dans chacun des deux quotas.
        with connexion:
            with connexion.cursor() as curseur:
                for type_id, identifiant, limite in quotas:
                    curseur.execute(
                        """
                        INSERT INTO rate_limits
                            (identifier, identifier_type, date, message_count)
                        VALUES (
                            %s, %s,
                            (CURRENT_TIMESTAMP AT TIME ZONE 'Europe/Paris')::date,
                            1
                        )
                        ON CONFLICT (identifier, identifier_type, date)
                        DO UPDATE SET message_count = rate_limits.message_count + 1
                        WHERE rate_limits.message_count < %s
                        RETURNING message_count
                        """,
                        (identifiant, type_id, limite),
                    )

                    # Une fois la limite atteinte, le SQL ne renvoie aucune ligne.
                    if curseur.fetchone() is None:
                        raise HTTPException(
                            status_code=429,
                            detail=(
                                "Limite quotidienne atteinte. "
                                "Réessaie après minuit, heure de Paris."
                            ),
                        )

            # L'historique et les deux compteurs sont validés ensemble.
            yield connexion
