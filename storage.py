"""
storage.py
----------
Optionale, verschlüsselte lokale Speicherung von API Keys.

Sicherheitskonzept (DSGVO-relevant):
- Es werden KEINE Daten an externe Server gesendet. Alles bleibt auf
  dem Rechner des Nutzers (Art. 5 DSGVO: Datenminimierung).
- Die Speicherung ist standardmäßig AUSGESCHALTET. Der Nutzer muss sie
  aktiv per Schalter einschalten ("Recommended: off, wenn nicht nötig").
- Wird sie aktiviert, werden die Keys mit einem vom Nutzer gewählten
  Master-Passwort (PBKDF2 + Fernet/AES) verschlüsselt auf der Platte
  abgelegt, nicht im Klartext.
- Der Nutzer kann jederzeit alle gespeicherten Keys löschen
  (Recht auf Löschung, Art. 17 DSGVO).
"""

import json
import base64
import os
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

APP_DIR = Path.home() / ".apidrop"
DATA_FILE = APP_DIR / "vault.enc"
SALT_FILE = APP_DIR / "salt.bin"


def _ensure_app_dir():
    APP_DIR.mkdir(parents=True, exist_ok=True)


def _derive_key(master_password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=390_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(master_password.encode("utf-8")))


def _get_salt() -> bytes:
    _ensure_app_dir()
    if SALT_FILE.exists():
        return SALT_FILE.read_bytes()
    salt = os.urandom(16)
    SALT_FILE.write_bytes(salt)
    return salt


def vault_exists() -> bool:
    return DATA_FILE.exists()


def save_entries(entries: list[dict], master_password: str) -> None:
    """
    entries: Liste von {"label": str, "provider": str, "key": str}
    Wird als verschlüsseltes JSON auf Platte geschrieben.
    """
    _ensure_app_dir()
    salt = _get_salt()
    fernet = Fernet(_derive_key(master_password, salt))
    payload = json.dumps(entries).encode("utf-8")
    token = fernet.encrypt(payload)
    DATA_FILE.write_bytes(token)


def load_entries(master_password: str) -> list[dict]:
    """
    Lädt und entschlüsselt die gespeicherten Einträge.
    Wirft ValueError bei falschem Passwort.
    """
    if not vault_exists():
        return []
    salt = _get_salt()
    fernet = Fernet(_derive_key(master_password, salt))
    token = DATA_FILE.read_bytes()
    try:
        payload = fernet.decrypt(token)
    except Exception as exc:
        raise ValueError("Falsches Master-Passwort oder beschädigte Datei.") from exc
    return json.loads(payload.decode("utf-8"))


def delete_vault() -> None:
    """Löscht alle lokal gespeicherten Keys unwiderruflich (Recht auf Löschung)."""
    if DATA_FILE.exists():
        DATA_FILE.unlink()
    if SALT_FILE.exists():
        SALT_FILE.unlink()
