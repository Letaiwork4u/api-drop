"""Detector, resolver and storage."""
import os
import stat

import pytest

import detector
import resolver
import storage
from conftest import FAKE_ANTHROPIC, FAKE_OPENAI, FAKE_STRIPE


# ---------------- detector ----------------
@pytest.mark.parametrize("key,provider", [
    (FAKE_OPENAI, "OpenAI"),
    ("sk-" + "a" * 48, "OpenAI"),
    (FAKE_ANTHROPIC, "Anthropic (Claude)"),
    ("AIza" + "b" * 35, "Google (Gemini)"),
    ("ghp_" + "c" * 36, "GitHub"),
    (FAKE_STRIPE, "Stripe"),
    ("AKIA" + "D" * 16, "AWS"),
    ("hf_" + "e" * 34, "HuggingFace"),
    ("xoxb-123-456-abc", "Slack"),
])
def test_detect_known_providers(key, provider):
    assert detector.detect_provider(key) == provider


def test_suggest_label_counts_up():
    assert detector.suggest_label(FAKE_OPENAI, []) == "OpenAI API 1"
    assert detector.suggest_label(FAKE_OPENAI, ["OpenAI API 1"]) == "OpenAI API 2"


def test_unknown_provider_label_is_english():
    """UI is English by default, but unknown keys become 'Unbekannt API 1'."""
    assert detector.suggest_label("zzz-not-a-known-key", []) == "Unknown API 1"


def test_generic_32_char_token_is_not_mistral():
    """Any 32-char alphanumeric string (session ids, hex hashes...) is labelled Mistral."""
    md5_like = "d41d8cd98f00b204e9800998ecf8427e"
    assert detector.detect_provider(md5_like) != "Mistral"


# ---------------- resolver ----------------
def test_ref_slug():
    assert resolver.ref_for_label("OpenAI API 1") == "openai-api-1"


def test_parse_env_basic_quotes_export_comments():
    text = "# c\nexport A=1\nB='two'\nC=\"three\"\n\nD=apidrop://openai-api-1\n"
    assert resolver.parse_env_file(text) == [("A", "1"), ("B", "two"), ("C", "three"),
                                            ("D", "apidrop://openai-api-1")]


def test_parse_env_strips_inline_comment():
    """The code comment promises this, but it isn't implemented."""
    pairs = resolver.parse_env_file("OPENAI_API_KEY=apidrop://openai-api-1  # my key\n")
    assert pairs == [("OPENAI_API_KEY", "apidrop://openai-api-1")]


def test_resolve_pairs_happy_path():
    entries = [{"label": "OpenAI API 1", "provider": "OpenAI", "key": FAKE_OPENAI}]
    resolved, touched = resolver.resolve_pairs([("OPENAI_API_KEY", "apidrop://openai-api-1"),
                                                ("MODEL", "gpt-5")], entries)
    assert resolved == {"OPENAI_API_KEY": FAKE_OPENAI, "MODEL": "gpt-5"}
    assert touched == ["OPENAI_API_KEY"]


def test_resolve_unknown_reference_raises():
    with pytest.raises(resolver.UnresolvedReferenceError):
        resolver.resolve_pairs([("X", "apidrop://nope")], [])


def test_labels_with_same_slug_collide():
    """'OpenAI API 1' and 'openai-api-1' are different labels but the same reference."""
    entries = [{"label": "OpenAI API 1", "provider": "OpenAI", "key": "first"},
               {"label": "openai api-1", "provider": "OpenAI", "key": "second"}]
    with pytest.raises(resolver.UnresolvedReferenceError, match="more than one"):
        resolver.resolve_pairs([("K", "apidrop://openai-api-1")], entries)


def test_stable_ref_wins_over_other_entrys_name():
    """Entry A was renamed (keeps ref openai-api-1); entry B is now *named* 'OpenAI API 1'."""
    entries = [{"label": "Chatbot prod", "ref": "openai-api-1", "provider": "OpenAI", "key": "A"},
               {"label": "OpenAI API 1", "ref": "openai-api-1-b", "provider": "OpenAI", "key": "B"}]
    resolved, _ = resolver.resolve_pairs([("K", "apidrop://openai-api-1")], entries)
    assert resolved["K"] == "A"


@pytest.mark.parametrize("line,value", [
    ('K="a # b"  # c', "a # b"),
    ("K='x'#c", "x"),
    ("K=abc#def", "abc#def"),
    ("K=val\t# tab comment", "val"),
])
def test_parse_env_comment_variants(line, value):
    assert resolver.parse_env_file(line) == [("K", value)]


# ---------------- storage ----------------
def test_roundtrip_and_wrong_password(vault_dir):
    entries = [{"label": "OpenAI API 1", "provider": "OpenAI", "key": FAKE_OPENAI}]
    storage.save_entries(entries, "pw-1234")
    assert storage.load_entries("pw-1234") == entries
    with pytest.raises(ValueError):
        storage.load_entries("wrong")
    raw = (vault_dir / "vault.enc").read_bytes()
    assert FAKE_OPENAI.encode() not in raw


def test_delete_vault(vault_dir):
    storage.save_entries([], "pw")
    storage.delete_vault()
    assert not storage.vault_exists()


def test_vault_files_are_private(vault_dir):
    """vault.enc / salt.bin are created with default umask (world-readable 0644)."""
    storage.save_entries([{"label": "a", "provider": "x", "key": "k"}], "pw")
    for f in ("vault.enc", "salt.bin"):
        mode = stat.S_IMODE(os.stat(vault_dir / f).st_mode)
        assert mode & 0o077 == 0, f"{f} has mode {oct(mode)}"


def test_save_is_atomic(vault_dir, monkeypatch):
    """A crash while replacing the file keeps the old vault and leaves no temp file."""
    storage.save_entries([{"label": "a", "provider": "x", "key": "k"}], "pw")

    def boom(*a, **k):
        raise OSError("simulated crash")
    monkeypatch.setattr(storage.os, "replace", boom)
    with pytest.raises(OSError):
        storage.save_entries([{"label": "b", "provider": "x", "key": "k2"}], "pw")
    monkeypatch.setattr(storage.os, "replace", os.replace)
    assert storage.load_entries("pw")[0]["label"] == "a"
    assert sorted(p.name for p in vault_dir.iterdir()) == ["salt.bin", "vault.enc"]


def test_wrong_password_message_is_english(vault_dir):
    storage.save_entries([], "pw")
    with pytest.raises(storage.WrongPasswordError, match="Wrong master password"):
        storage.load_entries("nope")
