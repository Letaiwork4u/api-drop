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
    # Mistral keys have no prefix: 32 chars mixing upper, lower and digits.
    # Requiring all three avoids matching hex hashes / session ids.
    ("Mistral", re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])[a-zA-Z0-9]{32}$")),
    ("Cohere", re.compile(r"^co-")),
    ("HuggingFace", re.compile(r"^hf_")),
    ("GitHub", re.compile(r"^gh[pousr]_")),
    ("Stripe", re.compile(r"^(sk|pk)_(live|test)_")),
    ("AWS", re.compile(r"^AKIA")),
    ("Slack", re.compile(r"^xox[baprs]-")),
]


def detect_provider(api_key: str) -> str:
    """
    Gibt den erkannten Anbieternamen zurück, oder "Unknown",
    falls kein Muster passt.
    """
    key = api_key.strip()
    for name, pattern in PROVIDER_PATTERNS:
        if pattern.match(key):
            return name
    return "Unknown"


# Übliche Umgebungsvariablen-Namen je Anbieter. Wird nur für das
# Beispiel im Kopier-Dialog genutzt; der Nutzer kann jeden Namen wählen.
PROVIDER_ENV_VARS = {
    "Anthropic (Claude)": "ANTHROPIC_API_KEY",
    "OpenAI": "OPENAI_API_KEY",
    "Google (Gemini)": "GEMINI_API_KEY",
    "Mistral": "MISTRAL_API_KEY",
    "Cohere": "COHERE_API_KEY",
    "HuggingFace": "HUGGINGFACE_API_KEY",
    "GitHub": "GITHUB_TOKEN",
    "Stripe": "STRIPE_API_KEY",
    "AWS": "AWS_ACCESS_KEY_ID",
    "Slack": "SLACK_TOKEN",
}


def env_var_for_provider(provider: str) -> str:
    """
    Liefert den üblichen Umgebungsvariablen-Namen für einen Anbieter,
    z.B. "Anthropic (Claude)" -> "ANTHROPIC_API_KEY". Fällt auf einen
    neutralen Namen zurück, wenn der Anbieter unbekannt ist.
    """
    return PROVIDER_ENV_VARS.get(provider, "YOUR_API_KEY")


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
