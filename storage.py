"""
storage.py
----------
Optionale, verschlüsselte lokale Speicherung von API Keys.

Sicherheitskonzept (DSGVO-relevant):
- Es werden KEINE Daten an externe Server gesendet. Alles bleibt auf
  dem Rechner des Nutzers (Art. 5 DSGVO: Datenminimierung).
- Die Speicherung ist standardmäßig AUSGESCHALTET. Der Nutzer muss sie
  aktiv per Schalter einschalten.
- Wird sie aktiviert, werden die Keys mit einem vom Nutzer gewählten
  Master-Passwort (PBKDF2 + Fernet/AES) verschlüsselt auf der Platte
  abgelegt, nicht im Klartext.
- Ordner 0700, Dateien 0600: nur der eigene Benutzer kann sie lesen.
- Schreiben ist atomar (Temp-Datei + os.replace): ein Absturz beim
  Speichern lässt den bisherigen Vault unversehrt.
- Der Nutzer kann jederzeit alle gespeicherten Keys löschen
  (Recht auf Löschung, Art. 17 DSGVO).
"""

import base64
import json
import os
import tempfile
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

APP_DIR = Path.home() / ".apidrop"
DATA_FILE = APP_DIR / "vault.enc"
SALT_FILE = APP_DIR / "salt.bin"

WRONG_PASSWORD = "Wrong master password or damaged vault file."


class WrongPasswordError(ValueError):
    """Raised when the vault cannot be decrypted."""


def _ensure_app_dir():
    APP_DIR.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(APP_DIR, 0o700)
    except OSError:
        pass  # e.g. filesystems without POSIX permissions


def _write_private_atomic(path: Path, data: bytes) -> None:
    """Write `data` to `path` atomically with mode 0600."""
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


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
    _write_private_atomic(SALT_FILE, salt)
    return salt


def vault_exists() -> bool:
    return DATA_FILE.exists()


def save_entries(entries: list[dict], master_password: str) -> None:
    """
    entries: Liste von {"label": str, "provider": str, "key": str, "ref": str}
    Wird als verschlüsseltes JSON auf Platte geschrieben.
    """
    _ensure_app_dir()
    salt = _get_salt()
    fernet = Fernet(_derive_key(master_password, salt))
    payload = json.dumps(entries).encode("utf-8")
    _write_private_atomic(DATA_FILE, fernet.encrypt(payload))


def load_entries(master_password: str) -> list[dict]:
    """
    Lädt und entschlüsselt die gespeicherten Einträge.
    Wirft WrongPasswordError (ein ValueError) bei falschem Passwort.
    """
    if not vault_exists():
        return []
    salt = _get_salt()
    fernet = Fernet(_derive_key(master_password, salt))
    token = DATA_FILE.read_bytes()
    try:
        payload = fernet.decrypt(token)
    except (InvalidToken, ValueError) as exc:
        raise WrongPasswordError(WRONG_PASSWORD) from exc
    return json.loads(payload.decode("utf-8"))


def delete_vault() -> None:
    """Löscht alle lokal gespeicherten Keys unwiderruflich (Recht auf Löschung)."""
    if DATA_FILE.exists():
        DATA_FILE.unlink()
    if SALT_FILE.exists():
        SALT_FILE.unlink()
