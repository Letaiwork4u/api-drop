import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture
def vault_dir(tmp_path, monkeypatch):
    """Point storage at an isolated temp vault (never touches ~/.apidrop)."""
    import storage

    app_dir = tmp_path / ".apidrop"
    monkeypatch.setattr(storage, "APP_DIR", app_dir)
    monkeypatch.setattr(storage, "DATA_FILE", app_dir / "vault.enc")
    monkeypatch.setattr(storage, "SALT_FILE", app_dir / "salt.bin")
    return app_dir


# Obviously fake test keys (correct prefixes, random tails)
FAKE_OPENAI = "sk-proj-" + "A1b2C3d4E5f6G7h8I9j0" * 4
FAKE_ANTHROPIC = "sk-ant-api03-" + "x9Y8z7W6v5U4t3S2r1Q0" * 4
FAKE_STRIPE = "sk_test_" + "51HxYzAbCdEfGhIjKlMnOp" * 2
