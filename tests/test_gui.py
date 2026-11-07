"""GUI flows of app.py, driven offscreen with dialogs stubbed out."""
import pytest

pytest.importorskip("PyQt6")
from PyQt6.QtWidgets import QApplication, QInputDialog, QMessageBox  # noqa: E402

import storage  # noqa: E402
from conftest import FAKE_ANTHROPIC, FAKE_OPENAI  # noqa: E402

YES = QMessageBox.StandardButton.Yes
NO = QMessageBox.StandardButton.No


@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def ui(qapp, vault_dir, monkeypatch):
    """Returns (make_window, log). Dialogs are recorded and answered from queues."""
    import app

    log = {"info": [], "warn": [], "pw": [], "question": []}
    answers = {"pw": [], "question": [], "text": []}

    monkeypatch.setattr(QMessageBox, "information", staticmethod(lambda p, t, m, *a, **k: log["info"].append(m)))
    monkeypatch.setattr(QMessageBox, "warning", staticmethod(lambda p, t, m, *a, **k: log["warn"].append(m)))

    def question(p, t, m, *a, **k):
        log["question"].append(m)
        return answers["question"].pop(0) if answers["question"] else NO
    monkeypatch.setattr(QMessageBox, "question", staticmethod(question))

    def get_text(parent, title, prompt, *a, **k):
        if "echo" in k:  # password dialog
            log["pw"].append(title)
            return (answers["pw"].pop(0), True) if answers["pw"] else ("", False)
        return (answers["text"].pop(0), True) if answers["text"] else ("", False)
    monkeypatch.setattr(QInputDialog, "getText", staticmethod(get_text))

    def make():
        w = app.ApiDropWindow()
        w._offer_load_existing()  # normally fired by a timer
        return w
    return make, log, answers


def add_key(w, key):
    w.key_input.setText(key)
    w._on_detect()
    w._on_add()


def test_add_detect_and_reference(ui, qapp):
    make, log, _ = ui
    w = make()
    add_key(w, FAKE_OPENAI)
    assert w.table.item(0, 0).text() == "OpenAI API 1"
    assert w.key_input.text() == ""
    w.table.selectRow(0)
    w._on_copy_reference()
    assert qapp.clipboard().text() == "apidrop://openai-api-1"
    assert "OPENAI_API_KEY=apidrop://openai-api-1" in log["info"][-1]


def test_duplicate_name_rejected(ui):
    make, log, _ = ui
    w = make()
    add_key(w, FAKE_OPENAI)
    w.key_input.setText(FAKE_OPENAI)
    w.name_input.setText("OpenAI API 1")
    w._on_add()
    assert w.table.rowCount() == 1 and log["warn"]


def test_persist_then_reload(ui):
    make, log, answers = ui
    w = make()
    add_key(w, FAKE_OPENAI)
    answers["pw"] += ["pw-1", "pw-1"]
    w.persist_check.setChecked(True)
    assert storage.vault_exists()
    w2 = None
    answers["question"].append(YES)
    answers["pw"].append("pw-1")
    w2 = make()
    assert w2.table.rowCount() == 1 and w2.persist_check.isChecked()


def test_declining_load_then_enabling_persist_keeps_old_keys(ui):
    """Session 1 stores key A. Session 2 says 'No' to loading, adds key B,
    ticks 'Store keys encrypted locally' -> key A must not be wiped."""
    make, log, answers = ui
    w = make()
    add_key(w, FAKE_OPENAI)
    answers["pw"] += ["pw-1", "pw-1"]
    w.persist_check.setChecked(True)

    answers["question"].append(NO)          # "Load stored keys?" -> No
    w2 = make()
    add_key(w2, FAKE_ANTHROPIC)
    answers["pw"] += ["pw-1", "pw-1"]
    w2.persist_check.setChecked(True)
    labels = [e["label"] for e in storage.load_entries("pw-1")]
    assert "OpenAI API 1" in labels, f"vault now only contains {labels}"


def test_enabling_persist_with_different_password_does_not_overwrite(ui):
    """Same as above but the user types a NEW password: the old vault is silently replaced."""
    make, log, answers = ui
    w = make()
    add_key(w, FAKE_OPENAI)
    answers["pw"] += ["old", "old"]
    w.persist_check.setChecked(True)
    answers["question"].append(NO)
    w2 = make()
    add_key(w2, FAKE_ANTHROPIC)
    answers["pw"] += ["new", "new"]
    w2.persist_check.setChecked(True)
    try:
        storage.load_entries("old")
    except ValueError:
        pytest.fail("old vault (password 'old') was overwritten without warning")


def test_rename_keeps_existing_env_reference(ui):
    """.env holds apidrop://openai-api-1; after renaming the entry the reference no longer resolves."""
    import resolver
    make, log, answers = ui
    w = make()
    add_key(w, FAKE_OPENAI)
    w.table.selectRow(0)
    answers["text"].append("Chatbot prod")
    w._on_rename()
    resolved, _ = resolver.resolve_pairs([("K", "apidrop://openai-api-1")], w.entries)
    assert resolved["K"] == FAKE_OPENAI


def test_unticking_persist_asks_and_keeps_on_no(ui):
    """Switching storage off asks whether to delete the vault ("No" keeps it)."""
    make, log, answers = ui
    w = make()
    add_key(w, FAKE_OPENAI)
    answers["pw"] += ["pw", "pw"]
    w.persist_check.setChecked(True)
    log["info"].clear(); log["question"].clear()
    w.persist_check.setChecked(False)
    assert log["question"], "switching storage off must offer to delete the vault"
    assert storage.vault_exists()           # answered "No" -> kept


def test_unticking_persist_can_delete_vault(ui):
    make, log, answers = ui
    w = make()
    add_key(w, FAKE_OPENAI)
    answers["pw"] += ["pw", "pw"]
    w.persist_check.setChecked(True)
    answers["question"].append(YES)
    w.persist_check.setChecked(False)
    assert not storage.vault_exists()


def test_wrong_password_on_startup_allows_retry(ui):
    """Wrong password at startup: English prompt, second try loads the keys."""
    make, log, answers = ui
    storage.save_entries([{"label": "a", "provider": "OpenAI", "key": "k"}], "right")
    answers["question"] += [YES, YES]       # load? yes / try again? yes
    answers["pw"] += ["wrong", "right"]
    w = make()
    assert "Wrong master password" in log["question"][-1]
    assert w.table.rowCount() == 1 and w.entries[0]["ref"] == "a"


def test_detect_button_label_renders_ampersand(ui):
    make, *_ = ui
    w = make()
    # Qt treats a single '&' as mnemonic marker -> shown as "Detect _suggest name"
    assert "&&" in w.detect_btn.text() or "&" not in w.detect_btn.text()


def test_copy_reference_after_rename_keeps_old_reference(ui, qapp):
    make, log, answers = ui
    w = make()
    add_key(w, FAKE_OPENAI)
    w.table.selectRow(0)
    answers["text"].append("Chatbot prod")
    w._on_rename()
    w.table.selectRow(0)
    w._on_copy_reference()
    assert qapp.clipboard().text() == "apidrop://openai-api-1"


def test_rename_to_name_with_taken_reference_is_rejected(ui):
    make, log, answers = ui
    w = make()
    add_key(w, FAKE_OPENAI)                 # OpenAI API 1
    add_key(w, FAKE_OPENAI[::-1])           # Unbekannt/Unknown API 1 (different key)
    w.table.selectRow(1)
    answers["text"].append("openai api-1")  # same slug as row 0
    w._on_rename()
    assert w.entries[1]["label"] != "openai api-1" and log["warn"]


def test_merge_renames_clashing_session_key(ui):
    """Vault has 'OpenAI API 1'; new session adds a different key also named 'OpenAI API 1'."""
    make, log, answers = ui
    storage.save_entries([{"label": "OpenAI API 1", "provider": "OpenAI", "key": "old-key"}], "pw")
    answers["question"].append(NO)
    w = make()
    add_key(w, FAKE_OPENAI)
    answers["pw"].append("pw")
    w.persist_check.setChecked(True)
    stored = {e["label"]: e for e in storage.load_entries("pw")}
    assert stored["OpenAI API 1"]["key"] == "old-key"
    assert stored["OpenAI API 1 (2)"]["key"] == FAKE_OPENAI


def test_wrong_password_then_replace_requires_confirmation(ui):
    make, log, answers = ui
    storage.save_entries([{"label": "a", "provider": "x", "key": "k"}], "right")
    answers["question"].append(NO)                 # don't load at start
    w = make()
    add_key(w, FAKE_OPENAI)
    answers["pw"] += ["wrong", "new", "new"]
    answers["question"] += [NO, YES]               # no retry, yes replace
    w.persist_check.setChecked(True)
    assert storage.load_entries("new")[0]["key"] == FAKE_OPENAI


def test_cli_dispatch():
    import app
    assert app.wants_cli(["/x/ApiDrop", "run", "--", "python", "a.py"])
    assert app.wants_cli(["/x/ApiDrop", "list"])
    assert app.wants_cli(["/usr/local/bin/apidrop"])
    assert not app.wants_cli(["/x/ApiDrop"])
    assert not app.wants_cli(["/x/ApiDrop", "-psn_0_12345"])
