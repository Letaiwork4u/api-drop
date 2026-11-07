<div align="center">

<img src="assets/logo.svg" alt="API Drop" width="420">

**English** · [Deutsch](README.de.md)

### Your API key doesn't belong in the file.

**API Drop** keeps your real API keys encrypted and local. Your `.env` holds
nothing but a harmless **alias** — the real key is injected only at runtime.
Paste it once, and it's locked away.

**An alias instead of a cost trap.** Nothing on screen, nothing to revoke.

![License](https://img.shields.io/badge/license-MIT-3f8f79)
![Platform](https://img.shields.io/badge/os-Windows%20%7C%20macOS%20%7C%20Linux-38545c)
![Local first](https://img.shields.io/badge/local--first-no%20cloud-38545c)
![GDPR](https://img.shields.io/badge/GDPR-ready-3f8f79)
[![Stars](https://img.shields.io/github/stars/Letaiwork4u/api-drop?style=social)](https://github.com/Letaiwork4u/api-drop)

</div>

---

## The problem

An API key gets dropped into a `.env` "just for now" — and stays there. On a shared
screen, in a screenshot, in a git commit, in a tutorial video. Automated scanners find
public keys within minutes.

- **Over 39 million** secrets were exposed on GitHub in 2024 alone. *(GitHub Blog, 2025)*
- **$4.88M** is the average cost of a breach involving compromised credentials. *(IBM Cost of a Data Breach Report, 2024)*
- **Secret Leakage** ranks #2 in the OWASP Non-Human Identities Top 10. *(OWASP, 2025)*

The safest key is the one that never sits in plaintext in the file.

## The solution

API Drop flips the flow. Your `.env` holds only a reference:

```dotenv
# before – real key, visible to everyone
OPENAI_API_KEY=sk-proj-3f9K2aXn7Qw8Lp0Vt1Rz6Ub4Yc5Dg2Hj

# with API Drop – a harmless reference, not a secret
OPENAI_API_KEY=apidrop://openai-api-1
```

At startup, `apidrop` injects the real key from the encrypted vault:

```bash
apidrop run -- python app.py
```

Your code reads the variable through `os.environ` / `process.env` as usual — it
never sees the reference. The real key is never written to disk in plaintext and
never shown on screen.

> The same `run --` mechanism powers Doppler (`doppler run`) and Infisical
> (`infisical run`). API Drop brings it **local, offline and account-free**.

## Features

- 🔍 **Auto-detection** — recognizes keys from OpenAI, Anthropic, Google, GitHub, Stripe, AWS and more by their prefix
- 🏷️ **Human-readable names** — `sk-proj-…` becomes `OpenAI API 1`, freely renameable
- 🔒 **AES-encrypted vault** — keys are protected with your master password (PBKDF2 + Fernet), never stored in plaintext
- 🖥️ **Desktop app** — a clean GUI for Windows, macOS and Linux
- ⚡ **`apidrop run`** — references resolved at runtime, no code changes
- 🌐 **Offline & account-free** — no cloud, no telemetry, GDPR by design

## Installation

### Download (recommended)

Grab the ready-to-run app for your system from the
**[latest release](https://github.com/Letaiwork4u/api-drop/releases/latest)** —
no Python required.

| System | File |
|---|---|
| Windows | `ApiDrop.exe` (app) + `apidrop.exe` (terminal command) |
| macOS | `ApiDrop.dmg` |
| Linux | `ApiDrop` (binary) |

### The `apidrop` terminal command

The app doubles as the command line tool:

- **macOS:** click **Terminal setup** in the app — it copies a one-time command that links
  `apidrop` into `/usr/local/bin`:
  `sudo mkdir -p /usr/local/bin && sudo ln -sf "/Applications/ApiDrop.app/Contents/MacOS/ApiDrop" /usr/local/bin/apidrop`
- **Linux:** `sudo ln -sf /path/to/ApiDrop /usr/local/bin/apidrop` (or call `./ApiDrop run -- …` directly).
- **Windows:** put `apidrop.exe` into a folder on your `PATH`.
- **From source:** `python apidrop_cli.py run -- …`

> **First launch:** the app isn't signed with a paid developer certificate, so your
> OS warns once. **macOS:** System Settings → Privacy & Security → "Open Anyway".
> **Windows:** "More info" → "Run anyway". The source is open — inspect it any time.

### From source

```bash
git clone https://github.com/Letaiwork4u/api-drop.git
cd api-drop
pip install -r requirements.txt

# launch the desktop app
python app.py
```

## Quickstart

1. **Key into the vault:** open the app, paste your key, hit "Detect & suggest name",
   enable "Store keys encrypted locally".
2. **Reference into your `.env`:** in the key list, click "Copy reference" — it puts
   `apidrop://openai-api-1` on your clipboard. Paste it into `.env`.
3. **Run:**

   ```bash
   apidrop run -- python app.py
   ```

List your references (without ever showing the keys):

```bash
apidrop list
```

## Security & privacy

- **Local & offline** — the vault lives on your machine, nowhere else.
- **AES-encrypted** — no plaintext keys on disk.
- **No system hooks** — `apidrop run` merely spawns a child process with an enriched
  environment. No accessibility permissions, no admin rights.
- **GDPR by design** — no cloud, no cookies, no tracking.

Please report security issues **privately** to the address in the
[imprint](https://api-drop.com/impressum.html), not via public issues.

## How it compares

| | API Drop | Doppler / Infisical |
|---|---|---|
| `run --` injection | ✅ | ✅ |
| Local & offline | ✅ | cloud-first |
| Usable without an account | ✅ | account required |
| Focus | individual developer, GDPR | team SaaS |
| Price | free, open source | freemium |

## Roadmap

- [x] Prebuilt installers (`.exe` / `.dmg` / Linux) via GitHub Releases
- [ ] Auto-detection straight from the clipboard
- [ ] OS keychain integration (macOS Keychain, Windows Credential Manager)
- [ ] A small SDK so `import apidrop` can replace `run --`

## Contributing

Contributions are welcome! Issues and pull requests are appreciated. For larger
changes, please open an issue first so we can align on direction.

## License

MIT — see [LICENSE](LICENSE). You're free to use, modify and distribute API Drop.

---

<div align="center">

A ⭐ helps other developers discover API Drop.

powered by **[LetAIwork4u](https://www.letaiwork4u.com)**

</div>
