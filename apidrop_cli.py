#!/usr/bin/env python3
"""
apidrop – Kommandozeilen-Resolver für API Drop.

Beispiele:
    apidrop run -- python main.py
    apidrop run --env .env.local -- node server.js
    apidrop list

Prinzip: In der .env stehen nur Referenzen (apidrop://name). Beim Start
setzt apidrop die echten Keys aus dem verschlüsselten Vault in die
Umgebung des gestarteten Programms ein. Der echte Key steht nie im
Klartext in der Datei und nie auf dem Bildschirm.
"""

from __future__ import annotations

import argparse
import getpass
import os
import subprocess
import sys
from pathlib import Path

import storage
import resolver


PASSPHRASE_ENV = "APIDROP_PASSPHRASE"


def _load_vault_entries() -> list[dict]:
    """Vault entschlüsseln. Passwort aus Env-Variable oder Abfrage."""
    if not storage.vault_exists():
        _fail(
            "no vault found. Store your keys in the API Drop app first "
            "(checkbox 'Store keys encrypted locally')."
        )
    passphrase = os.environ.get(PASSPHRASE_ENV)
    if not passphrase:
        # Interaktive, verdeckte Eingabe (kein Echo auf dem Bildschirm)
        passphrase = getpass.getpass("API Drop master password: ")
    try:
        return storage.load_entries(passphrase)
    except ValueError as exc:
        _fail(str(exc))
    return []  # unerreichbar, macht Typprüfer glücklich


def _fail(message: str, code: int = 1):
    print(f"apidrop: {message}", file=sys.stderr)
    sys.exit(code)


def cmd_run(args: argparse.Namespace) -> int:
    if not args.command:
        _fail("no command given. Example: apidrop run -- python main.py")

    env_path = Path(args.env)
    if not env_path.exists():
        _fail(f".env file not found: {env_path}")

    pairs = resolver.parse_env_file(env_path.read_text(encoding="utf-8"))
    entries = _load_vault_entries()

    try:
        resolved, touched = resolver.resolve_pairs(pairs, entries)
    except resolver.UnresolvedReferenceError as exc:
        _fail(str(exc))
        return 1

    # Umgebung des Kindprozesses: bestehende Umgebung + aufgelöste Werte
    child_env = os.environ.copy()
    child_env.update(resolved)

    # Nur Namen der aufgelösten Variablen anzeigen, niemals die Werte
    if touched and not args.quiet:
        joined = ", ".join(touched)
        print(f"apidrop: resolved {len(touched)} reference(s): {joined}",
              file=sys.stderr)

    try:
        completed = subprocess.run(args.command, env=child_env)
        return completed.returncode
    except FileNotFoundError:
        _fail(f"command not found: {args.command[0]}")
        return 127


def cmd_list(args: argparse.Namespace) -> int:
    entries = _load_vault_entries()
    if not entries:
        print("No keys in the vault.")
        return 0
    print("Available references (keys are NOT shown):\n")
    width = max((len(e.get("label", "")) for e in entries), default=0)
    for e in entries:
        label = e.get("label", "")
        ref = e.get("ref") or resolver.ref_for_label(label)  # stable ref survives renames
        provider = e.get("provider", "")
        print(f"  {label.ljust(width)}   apidrop://{ref}   [{provider}]")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="apidrop",
        description="Resolves apidrop:// references from the encrypted API Drop vault.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="run a program with the real keys injected")
    p_run.add_argument("--env", default=".env", help="path to the .env file (default: .env)")
    p_run.add_argument("-q", "--quiet", action="store_true", help="no status line")
    p_run.add_argument(
        "command", nargs=argparse.REMAINDER,
        help="-- followed by the command to run",
    )
    p_run.set_defaults(func=cmd_run)

    p_list = sub.add_parser("list", help="list stored references (never the keys)")
    p_list.set_defaults(func=cmd_list)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    # argparse.REMAINDER nimmt das führende "--" mit; entfernen
    if getattr(args, "command", None) and args.command and args.command[0] == "--":
        args.command = args.command[1:]
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
