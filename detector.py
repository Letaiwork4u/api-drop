"""
detector.py
-----------
Erkennt anhand des Präfix-Musters eines API Keys, von welchem Anbieter
er stammt. Die Liste kann jederzeit um neue Muster erweitert werden.

Wichtig: Es wird NUR das Präfix analysiert, niemals der komplette Key
irgendwohin gesendet. Alles läuft lokal.
"""

import re

# Reihenfolge ist relevant: spezifischere Muster zuerst prüfen.
PROVIDER_PATTERNS = [
    ("Anthropic (Claude)", re.compile(r"^sk-ant-")),
    ("OpenAI", re.compile(r"^sk-proj-")),
    ("OpenAI", re.compile(r"^sk-")),
    ("Google (Gemini)", re.compile(r"^AIza")),
    ("Mistral", re.compile(r"^[a-zA-Z0-9]{32}$")),
    ("Cohere", re.compile(r"^co-")),
    ("HuggingFace", re.compile(r"^hf_")),
    ("GitHub", re.compile(r"^gh[pousr]_")),
    ("Stripe", re.compile(r"^(sk|pk)_(live|test)_")),
    ("AWS", re.compile(r"^AKIA")),
    ("Slack", re.compile(r"^xox[baprs]-")),
]


def detect_provider(api_key: str) -> str:
    """
    Gibt den erkannten Anbieternamen zurück, oder "Unbekannt",
    falls kein Muster passt.
    """
    key = api_key.strip()
    for name, pattern in PROVIDER_PATTERNS:
        if pattern.match(key):
            return name
    return "Unbekannt"


def suggest_label(api_key: str, existing_labels: list[str]) -> str:
    """
    Schlägt einen fortlaufenden Namen vor, z.B. "OpenAI API 1",
    "OpenAI API 2", basierend auf bereits vergebenen Namen.
    """
    provider = detect_provider(api_key)
    base = f"{provider} API "
    counter = 1
    while f"{base}{counter}" in existing_labels:
        counter += 1
    return f"{base}{counter}"
