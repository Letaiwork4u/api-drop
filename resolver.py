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
    """Remove surrounding quotes and inline comments, like python-dotenv:
    KEY=value  # comment   -> value
    KEY="a # b"  # comment -> a # b   (inside quotes '#' is kept)
    KEY=abc#def            -> abc#def (needs whitespace before '#')
    """
    value = value.strip()
    if value[:1] in ("'", '"'):
        quote = value[0]
        end = value.find(quote, 1)
        if end != -1:
            return value[1:end]
        return value
    m = re.search(r"\s+#", value)
    if m:
        value = value[: m.start()]
    return value.strip()


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
    Explizite 'ref'-Felder haben Vorrang vor dem Slug des aktuellen Namens.
    Zeigt eine Kennung auf zwei verschiedene Keys, wird sie als mehrdeutig
    markiert (AMBIGUOUS) statt still einen der beiden zu nehmen.
    """
    index: dict[str, dict] = {}
    explicit_refs: set[str] = set()

    def put(ref: str, entry: dict) -> None:
        current = index.get(ref)
        if current is None:
            index[ref] = entry
        elif current is not AMBIGUOUS and current is not entry and current.get("key") != entry.get("key"):
            index[ref] = AMBIGUOUS

    for entry in entries:                       # 1) stable references
        if entry.get("ref"):
            ref = ref_for_label(entry["ref"])
            explicit_refs.add(ref)
            put(ref, entry)
    for entry in entries:                       # 2) slug of the current name
        ref = ref_for_label(entry.get("label", ""))
        if ref and ref not in explicit_refs:
            put(ref, entry)
    return index


AMBIGUOUS: dict = {"__ambiguous__": True}


class UnresolvedReferenceError(Exception):
    """A reference in the .env could not be resolved from the vault."""


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
                    f"reference '{REFERENCE_PREFIX}{ref}' for {name} was not found in the vault."
                )
            if entry is AMBIGUOUS:
                raise UnresolvedReferenceError(
                    f"reference '{REFERENCE_PREFIX}{ref}' for {name} matches more than one key "
                    f"in the vault. Rename one of them in the API Drop app."
                )
            resolved[name] = entry["key"]
            touched.append(name)
        else:
            resolved[name] = value

    return resolved, touched
