"""
resolver.py
-----------
Kern des "apidrop run"-Mechanismus.

Idee (wie 1Password / Doppler / Infisical):
- In der .env-Datei stehen nur harmlose Referenzen, z.B.
      OPENAI_API_KEY=apidrop://openai-api-1
  Das ist sicher auf Kamera/Screenshare – es ist kein Secret.
- Zur Laufzeit ersetzt der Resolver jede Referenz durch den echten
  Key aus dem verschlüsselten Vault und übergibt ihn NUR an das
  gestartete Programm (Prozess-Umgebung). Der echte Key steht nie
  im Klartext auf der Platte und nie auf dem Bildschirm.

Dieser Mechanismus braucht keine System-Hooks, keine Accessibility-
Rechte und keine Admin-Rechte – er startet einfach einen Kindprozess
mit einer angereicherten Umgebung. Läuft identisch auf Windows, macOS
und Linux.
"""

from __future__ import annotations

import re

REFERENCE_PREFIX = "apidrop://"
# Erlaubt optional Anführungszeichen um den Wert in der .env
_ENV_LINE = re.compile(r"""^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$""")


def ref_for_label(label: str) -> str:
    """
    Wandelt einen Anzeige-Namen in eine stabile Referenz-Kennung um.
    "OpenAI API 1" -> "openai-api-1"
    """
    slug = label.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def parse_env_file(text: str) -> list[tuple[str, str]]:
    """
    Liest eine .env-Datei und gibt eine Liste (KEY, WERT) zurück.
    Kommentarzeilen (#) und Leerzeilen werden übersprungen.
    """
    pairs: list[tuple[str, str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        m = _ENV_LINE.match(line)
        if not m:
            continue
        name, raw_value = m.group(1), m.group(2)
        # Inline-Kommentar hinter unquoted Wert entfernen
        pairs.append((name, _unquote(raw_value)))
    return pairs


def is_reference(value: str) -> bool:
    return value.strip().startswith(REFERENCE_PREFIX)


def reference_name(value: str) -> str:
    """apidrop://openai-api-1 -> openai-api-1"""
    return value.strip()[len(REFERENCE_PREFIX):].strip().strip("/")


def build_ref_index(entries: list[dict]) -> dict[str, dict]:
    """
    Baut ein Nachschlage-Register: Referenz-Kennung -> Eintrag.
    Nutzt sowohl den Slug des Labels als auch ein evtl. vorhandenes
    explizites 'ref'-Feld.
    """
    index: dict[str, dict] = {}
    for entry in entries:
        label = entry.get("label", "")
        index[ref_for_label(label)] = entry
        explicit = entry.get("ref")
        if explicit:
            index[ref_for_label(explicit)] = entry
    return index


class UnresolvedReferenceError(Exception):
    """Eine Referenz in der .env konnte im Vault nicht gefunden werden."""


def resolve_pairs(
    pairs: list[tuple[str, str]],
    entries: list[dict],
) -> tuple[dict[str, str], list[str]]:
    """
    Ersetzt alle apidrop://-Referenzen durch echte Keys.

    Rückgabe:
      resolved: dict KEY -> echter Wert (Referenzen aufgelöst)
      touched:  Liste der KEYs, bei denen eine Referenz aufgelöst wurde
    Wirft UnresolvedReferenceError, wenn eine Referenz nicht existiert.
    """
    index = build_ref_index(entries)
    resolved: dict[str, str] = {}
    touched: list[str] = []

    for name, value in pairs:
        if is_reference(value):
            ref = ref_for_label(reference_name(value))
            entry = index.get(ref)
            if entry is None:
                raise UnresolvedReferenceError(
                    f"Referenz '{REFERENCE_PREFIX}{ref}' für {name} "
                    f"wurde im Vault nicht gefunden."
                )
            resolved[name] = entry["key"]
            touched.append(name)
        else:
            resolved[name] = value

    return resolved, touched
