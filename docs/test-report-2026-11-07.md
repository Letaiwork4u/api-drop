# API Drop v1.0.0 – Testbericht (7. Nov. 2026)

Getestet wurde der Code auf `main` (Commit `20cba7b`) und die veröffentlichte `ApiDrop.dmg` (v1.0.0).
Die automatischen Tests liegen in `tests/` (`pip install pytest PyQt6 cryptography`, dann `python -m pytest tests`).
Jeder unten genannte Fehler hat einen Test, der aktuell **fehlschlägt** – nach dem Fix wird er grün.

**Ergebnis:** 39 Tests, 26 bestanden, 13 fehlgeschlagen. Die veröffentlichte macOS-App startet und läuft stabil.

Was funktioniert: Anbieter-Erkennung (OpenAI, Anthropic, Gemini, GitHub, Stripe, AWS, HF, Slack),
Namensvorschlag, doppelte Namen werden abgelehnt, Verschlüsselung (Key steht nie im Klartext auf der Platte),
falsches Passwort wird erkannt, `apidrop run` setzt den Key, gibt den Exit-Code weiter und zeigt den Key nie an,
`apidrop list` zeigt nur Referenzen.

---

## Kritisch – vor dem Signieren beheben

### 1. Datenverlust: gespeicherte Keys werden überschrieben
Ablauf: Keys speichern → App neu starten → „Gespeicherte Keys laden?“ mit **Nein** beantworten → neuen Key
hinzufügen → „Store keys encrypted locally“ anhaken. Der Vault enthält danach **nur noch den neuen Key**,
alle alten Keys sind weg. Mit einem anderen Passwort passiert dasselbe ohne Warnung.
Tests: `test_declining_load_then_enabling_persist_keeps_old_keys`, `test_enabling_persist_with_different_password_does_not_overwrite`
Fix: Wenn ein Vault existiert, beim Anhaken erst laden (Passwort abfragen) und zusammenführen; ein neues Passwort nur nach expliziter Bestätigung „Vault ersetzen?“.

### 2. `apidrop run` gibt es im Download nicht
Die DMG/EXE/Linux-Datei enthält nur die Desktop-App. Das Kommando `apidrop`, das Webseite, README und Video
zeigen, existiert für Download-Nutzer nicht – es läuft nur mit Python aus dem Quellcode (`python apidrop_cli.py run -- …`).
Fix-Vorschlag: Die App erkennt Kommandozeilen-Argumente (`ApiDrop run -- …` / `ApiDrop list`) und startet dann
ohne Fenster; dazu ein Menüpunkt „Kommandozeilen-Tool installieren“, der `/usr/local/bin/apidrop` als Link anlegt
(Windows: `apidrop.exe` als zweites PyInstaller-Ziel).

### 3. Umbenennen zerstört bestehende `.env`-Referenzen
Die Referenz wird aus dem Namen abgeleitet. Wer „OpenAI API 1“ in „Chatbot prod“ umbenennt, bricht jede `.env`
mit `apidrop://openai-api-1` – `apidrop run` bricht dann ab.
Test: `test_rename_breaks_existing_env_reference`
Fix: Beim Anlegen ein festes `ref`-Feld speichern (der Resolver unterstützt `ref` bereits) und beim Umbenennen behalten.

### Stand nach den Fixes (gleicher Tag, Branch `test/app-review-and-icon`)

1–3 sind behoben – 44 Tests, 34 bestanden; die 10 restlichen Fehlschläge sind die Punkte 4–11 unten.

- **Fix 1:** Beim Anhaken von „Store keys encrypted locally“ wird ein vorhandener Vault zuerst mit seinem
  Passwort entsperrt und zusammengeführt. Gleichnamige neue Keys heißen dann z. B. „OpenAI API 1 (2)“.
  Bei falschem Passwort: erneut versuchen oder – nur nach ausdrücklicher Bestätigung – einen neuen Vault anlegen.
- **Fix 2:** Die App ist zugleich das `apidrop`-Kommando (`ApiDrop run -- …`, `ApiDrop list`, oder über einen
  Link namens `apidrop`). Neuer Button „Terminal setup“ kopiert den Link-Befehl. Windows bekommt zusätzlich
  `apidrop.exe` (Konsole) im Release. Lokal mit dem gebauten macOS-Bundle getestet.
- **Fix 3:** Jeder Eintrag hat eine feste Referenz (`ref`), die beim Umbenennen erhalten bleibt; „Copy reference“
  nutzt sie. Umbenennen/Anlegen auf eine bereits vergebene Referenz wird abgelehnt (behebt Punkt 5 in der App).
  Ältere Vaults ohne `ref` bekommen sie beim Laden automatisch.

### Stand nach der zweiten Runde: Punkte 4–11 behoben – 53 Tests, alle grün

- **4** `.env`-Parser entfernt Inline-Kommentare wie python-dotenv (`KEY=wert  # x`; `#` in Anführungszeichen bleibt).
- **5** Mehrdeutige Referenzen brechen `apidrop run` mit klarer Meldung ab, statt still einen Key zu nehmen;
  feste `ref`-Felder haben Vorrang vor Namen. `apidrop list` zeigt die feste Referenz.
- **6** Vault-Ordner `0700`, Dateien `0600`, Schreiben atomar (Temp-Datei + `os.replace`).
- **7** Checkbox-Text jetzt „required for apidrop run“; beim Ausschalten fragt die App, ob der Vault gelöscht werden soll.
- **8** Falsches Passwort beim Start: englische Meldung und „Try again?“ statt Neustart.
- **9** Button zeigt „Detect & suggest name“ (EN und DE).
- **10** CLI- und Fehlermeldungen auf Englisch, unbekannte Keys heißen „Unknown API 1“.
- **11** Mistral wird nur noch bei 32 Zeichen mit Groß-, Kleinbuchstaben und Ziffern erkannt (keine Hashes mehr).

Offen bleiben 12 (Versionsnummer, Intel-Build) und 13 (Zahlenformat auf der englischen Webseite).

## Mittel

4. **Inline-Kommentar in `.env` bricht die Referenz** – `KEY=apidrop://openai-api-1  # Haupt-Key` wird zu
   `openai-api-1-haupt-key`. Der Code-Kommentar verspricht das Entfernen, es ist aber nicht umgesetzt.
   Tests: `test_parse_env_strips_inline_comment`, `test_inline_comment_after_reference`
5. **Namens-Kollision** – „OpenAI API 1“ und „openai api-1“ ergeben dieselbe Referenz; ein Key gewinnt still.
   Doppelprüfung sollte auf der Referenz statt auf dem Namen laufen. Test: `test_labels_with_same_slug_collide`
6. **Vault-Dateien sind für alle Benutzer lesbar** (`0644`) und werden nicht atomar geschrieben (Absturz beim
   Speichern kann den Vault zerstören). Fix: Ordner `0700`, Dateien `0600`, in Temp-Datei schreiben + `os.replace`.
   Test: `test_vault_files_are_private`
7. **„Speichern aus“ lässt die Keys auf der Platte liegen**, und der Hinweis „recommended: off when not needed“
   widerspricht dem Kern-Workflow – `apidrop run` funktioniert *nur* mit gespeichertem Vault.
   Vorschlag: Text ändern zu „Required for apidrop run“ und beim Abschalten fragen, ob der Vault gelöscht werden soll.
   Test: `test_unticking_persist_leaves_keys_on_disk`
8. **Falsches Passwort beim Start**: keine zweite Chance (App muss neu gestartet werden) und die Meldung ist
   Deutsch, obwohl die Oberfläche Englisch ist. Test: `test_wrong_password_on_startup_message_is_english`

## Klein

9. Button zeigt „Detect _suggest name“ – Qt liest `&` als Tastenkürzel. Fix: `"Detect && suggest name"` (DE: `"Erkennen && Namen vorschlagen"`).
10. Sprach-Mix: CLI-Ausgaben, Fehlermeldungen aus `storage`/`resolver` und „Unbekannt“ (Anbieter) sind immer Deutsch.
11. Jeder 32-stellige alphanumerische String (z. B. MD5-Hash) wird als „Mistral“ erkannt.
12. App-Bundle: Version `0.0.0`, nur Apple Silicon (arm64) – Intel-Macs können die DMG nicht starten.
13. Webseite (EN): „39 Mio.“ und „4,88 Mio. $“ → „39M“ und „$4.88M“.

## In diesem Branch bereits umgesetzt

- **App-Icon aus dem API-Drop-Logo** (`assets/icons/ApiDrop.icns`, `.ico`, `apidrop_512.png`, erzeugt mit `tools/make_icons.py`),
  im Build-Workflow für macOS und Windows eingebunden, Fenster-Icon für Windows/Linux in `app.py`.
- **Bundle-ID** `com.letaiwork4u.apidrop` (Voraussetzung für die Notarisierung).
- Lokal mit PyInstaller gebaut und gestartet: Icon im Bundle, App läuft.

## Signieren & Notarisieren (macOS)

Voraussetzungen: Apple Developer Program, Zertifikat „Developer ID Application“, ein App-spezifisches Passwort.

```bash
codesign --deep --force --options runtime --timestamp \
  --sign "Developer ID Application: <Name> (<TEAMID>)" dist/ApiDrop.app
# DMG bauen (wie bisher), dann:
codesign --sign "Developer ID Application: <Name> (<TEAMID>)" --timestamp dist/ApiDrop.dmg
xcrun notarytool submit dist/ApiDrop.dmg --apple-id <mail> --team-id <TEAMID> --password <app-pw> --wait
xcrun stapler staple dist/ApiDrop.dmg
```

Im CI-Workflow kommen Zertifikat und Passwort als GitHub-Secrets dazu. Für Windows wäre ein
Authenticode-Zertifikat nötig, sonst bleibt die SmartScreen-Warnung.
Empfehlung: Punkte 1–3 vor dem ersten signierten Release beheben, außerdem eine echte Versionsnummer setzen
und einen Universal- oder zusätzlichen Intel-Build anbieten.
