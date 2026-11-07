"""End-to-end tests of apidrop_cli.py in a subprocess with an isolated HOME."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import FAKE_OPENAI, ROOT

CLI = str(ROOT / "apidrop_cli.py")
PW = "test-Passw0rd!"


@pytest.fixture
def home(tmp_path):
    h = tmp_path / "home"
    h.mkdir()
    # create a vault with the real storage module, under this HOME
    code = (
        "import storage; storage.save_entries(["
        f"{{'label':'OpenAI API 1','provider':'OpenAI','key':{FAKE_OPENAI!r}}}], {PW!r})"
    )
    subprocess.run([sys.executable, "-c", code], cwd=ROOT, env={**os.environ, "HOME": str(h)}, check=True)
    return h


@pytest.fixture
def project(tmp_path):
    p = tmp_path / "proj"
    p.mkdir()
    (p / ".env").write_text("OPENAI_API_KEY=apidrop://openai-api-1\nMODEL=gpt-5\n")
    (p / "show.py").write_text(
        "import os\nk=os.environ.get('OPENAI_API_KEY','')\n"
        "print('LEN', len(k)); print('MODEL', os.environ.get('MODEL'))\n")
    return p


def run(args, home, cwd, pw=PW, **kw):
    env = {**os.environ, "HOME": str(home)}
    env.pop("APIDROP_PASSPHRASE", None)
    if pw is not None:
        env["APIDROP_PASSPHRASE"] = pw
    return subprocess.run([sys.executable, CLI, *args], cwd=cwd, env=env,
                          capture_output=True, text=True, **kw)


def test_run_injects_key(home, project):
    r = run(["run", "--", sys.executable, "show.py"], home, project)
    assert r.returncode == 0, r.stderr
    assert f"LEN {len(FAKE_OPENAI)}" in r.stdout
    assert "MODEL gpt-5" in r.stdout
    assert FAKE_OPENAI not in r.stdout + r.stderr   # never printed


def test_exit_code_is_passed_through(home, project):
    r = run(["run", "--", sys.executable, "-c", "raise SystemExit(7)"], home, project)
    assert r.returncode == 7


def test_wrong_password_fails(home, project):
    r = run(["run", "--", sys.executable, "show.py"], home, project, pw="nope")
    assert r.returncode != 0


def test_list_never_shows_keys(home, project):
    r = run(["list"], home, project)
    assert "apidrop://openai-api-1" in r.stdout
    assert FAKE_OPENAI not in r.stdout


def test_missing_env_file(home, tmp_path):
    r = run(["run", "--", "true"], home, tmp_path)
    assert r.returncode != 0 and ".env" in r.stderr


def test_unresolved_reference(home, project):
    (project / ".env").write_text("X=apidrop://does-not-exist\n")
    r = run(["run", "--", "true"], home, project)
    assert r.returncode != 0


def test_inline_comment_after_reference(home, project):
    (project / ".env").write_text("OPENAI_API_KEY=apidrop://openai-api-1   # main key\n")
    r = run(["run", "--", sys.executable, "show.py"], home, project)
    assert r.returncode == 0, r.stderr


def test_cli_messages_are_english(home, project):
    """GUI defaults to English, CLI only speaks German."""
    r = run(["run", "--", sys.executable, "show.py"], home, project)
    assert "resolved" in r.stderr.lower(), r.stderr


def test_no_vault_message(tmp_path, project):
    h = tmp_path / "empty"
    h.mkdir()
    r = run(["run", "--", "true"], h, project)
    assert r.returncode != 0


def test_list_shows_stable_reference_after_rename(tmp_path, project):
    h = tmp_path / "h2"
    h.mkdir()
    code = ("import storage; storage.save_entries([{'label':'Chatbot prod','provider':'OpenAI',"
            f"'key':{FAKE_OPENAI!r},'ref':'openai-api-1'}}], {PW!r})")
    subprocess.run([sys.executable, "-c", code], cwd=ROOT, env={**os.environ, "HOME": str(h)}, check=True)
    r = run(["list"], h, project)
    assert "apidrop://openai-api-1" in r.stdout
    r = run(["run", "--", sys.executable, "show.py"], h, project)
    assert r.returncode == 0 and f"LEN {len(FAKE_OPENAI)}" in r.stdout
