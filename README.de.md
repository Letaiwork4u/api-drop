<div align="center">

<img src="assets/logo.svg" alt="API Drop" width="420">

[English](README.md) · **Deutsch**

### Dein API-Key gehört nicht in die Datei.

**API Drop** hält deine echten API-Keys verschlüsselt und lokal.
In deiner `.env` steht nur eine harmlose Referenz – der echte Key wird
erst zur Laufzeit eingesetzt. Nichts auf dem Bildschirm, nichts zu widerrufen.

<!-- TODO: DEIN-NAME durch deinen GitHub-Namen ersetzen -->
![License](https://img.shields.io/badge/license-MIT-3f8f79)
![Platform](https://img.shields.io/badge/os-Windows%20%7C%20macOS%20%7C%20Linux-38545c)
![Local first](https://img.shields.io/badge/local--first-no%20cloud-38545c)
![DSGVO](https://img.shields.io/badge/DSGVO-konform-3f8f79)
[![Stars](https://img.shields.io/github/stars/DEIN-NAME/api-drop?style=social)](https://github.com/DEIN-NAME/api-drop)

</div>

---

## Das Problem

Ein API-Key landet schnell mal „temporär" in der `.env` – und bleibt dort. Auf einem
geteilten Bildschirm, in einem Screenshot, in einem Git-Commit, in einem Tutorial-Video.
Automatisierte Scanner finden öffentliche Keys binnen Minuten.

- **Über 39 Millionen** offengelegte Secrets fand GitHub allein in 2024. *(GitHub Blog, 2025)*
- **Ø 4,88 Mio. $** kostet ein Vorfall durch kompromittierte Zugangsdaten. *(IBM Cost of a Data Breach Report, 2024)*
- **Secret Leakage** steht auf Platz 2 der OWASP Non-Human Identities Top 10. *(OWASP, 2025)*

Der sicherste Key ist der, der nie im Klartext in der Datei steht.

## Die Lösung

API Drop dreht den Ablauf um. In deiner `.env` steht nur eine Referenz:

```dotenv
# vorher – echter Key, sichtbar für jeden
OPENAI_API_KEY=sk-proj-3f9K2aXn7Qw8Lp0Vt1Rz6Ub4Yc5Dg2Hj

# mit API Drop – harmlose Referenz, kein Geheimnis
OPENAI_API_KEY=apidrop://openai-api-1
```

Beim Start setzt `apidrop` den echten Key aus dem verschlüsselten Vault ein:

```bash
apidrop run -- python app.py
```

Dein Code liest die Variable ganz normal über `os.environ` / `process.env` –
er merkt nichts von der Referenz. Der echte Key steht nie im Klartext auf der
Platte und nie auf dem Bildschirm.

> Dieselbe `run --`-Mechanik nutzen auch Doppler (`doppler run`) und Infisical
> (`infisical run`). API Drop bringt sie **lokal, offline und ohne Konto**.

## Features

- 🔍 **Auto-Erkennung** – erkennt Keys von OpenAI, Anthropic, Google, GitHub, Stripe, AWS u. a. am Präfix
- 🏷️ **Sprechende Namen** – aus `sk-proj-…` wird `OpenAI API 1`, frei umbenennbar
- 🔒 **AES-verschlüsselter Vault** – Keys werden mit deinem Master-Passwort geschützt (PBKDF2 + Fernet), nie im Klartext
- 🖥️ **Desktop-App** – aufgeräumte GUI für Windows, macOS und Linux
- ⚡ **`apidrop run`** – Referenzen werden zur Laufzeit aufgelöst, ohne dein Code zu ändern
- 🌐 **Offline & ohne Konto** – keine Cloud, keine Telemetrie, DSGVO by design

## Installation

> TODO vor dem ersten Release: fertige Builds (`.exe` / `.dmg` / Linux) unter *Releases* verlinken.

### Aus dem Quellcode

```bash
git clone https://github.com/DEIN-NAME/api-drop.git
cd api-drop
pip install -r requirements.txt

# Desktop-App starten
python app.py
```

## Schnellstart

1. **Key in den Vault:** App öffnen, Key einfügen, „Erkennen & Namen vorschlagen",
   „Keys verschlüsselt lokal speichern" aktivieren.
2. **Referenz in die `.env`:** In der Key-Liste „Referenz kopieren" – das legt
   `apidrop://openai-api-1` in die Zwischenablage. Ab in die `.env`.
3. **Starten:**

   ```bash
   apidrop run -- python app.py
   ```

Referenzen auflisten (ohne die Keys zu zeigen):

```bash
apidrop list
```

## Sicherheit & Datenschutz

- **Lokal & offline** – der Vault liegt auf deinem Rechner, sonst nirgends.
- **AES-verschlüsselt** – keine Klartext-Keys auf der Platte.
- **Kein System-Hook** – `apidrop run` startet nur einen Kindprozess mit
  angereicherter Umgebung. Keine Accessibility-Rechte, keine Admin-Rechte.
- **DSGVO by design** – keine Cloud, keine Cookies, kein Tracking.

Einen Sicherheitshinweis bitte **nicht** über öffentliche Issues melden, sondern
an die im [Impressum](https://api-drop.com/impressum.html) genannte Adresse.

## Wie es sich einordnet

| | API Drop | Doppler / Infisical |
|---|---|---|
| `run --`-Injektion | ✅ | ✅ |
| Lokal & offline | ✅ | Cloud-first |
| Ohne Konto nutzbar | ✅ | Konto nötig |
| Fokus | einzelne:r Entwickler:in, DSGVO | Team-SaaS |
| Preis | kostenlos, Open Source | Freemium |

## Roadmap

- [ ] Fertige Installer (`.exe` / `.dmg` / Linux) über GitHub Releases
- [ ] Auto-Erkennung direkt aus der Zwischenablage
- [ ] Integration mit OS-Keychains (macOS Keychain, Windows Credential Manager)
- [ ] Kleines SDK, damit `import apidrop` das `run --` ersetzen kann

## Mitmachen

Beiträge sind willkommen! Issues und Pull Requests gern. Bei größeren Änderungen
bitte vorher ein Issue eröffnen, damit wir die Richtung abstimmen.

## Lizenz

MIT – siehe [LICENSE](LICENSE). Du darfst API Drop frei nutzen, anpassen und
weitergeben.

---

<div align="center">

Ein ⭐ hilft anderen Entwickler:innen, API Drop zu finden.

powered by **[LetAIwork4u](https://www.letaiwork4u.com)**

</div>
