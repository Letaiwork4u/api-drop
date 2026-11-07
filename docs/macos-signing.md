# macOS: Signieren & Notarisieren einrichten

## Einfachster Weg: lokal auf dem eigenen Mac

Voraussetzungen: „Developer ID Application“-Zertifikat im Schlüsselbund
(`security find-identity -v -p codesigning` zeigt es) und einmalig gespeicherte Notarisierungs-Daten:

```bash
xcrun notarytool store-credentials "apidrop-notary"   # fragt Apple-ID, App-Passwort, Team-ID
```

Danach signiert, notarisiert und staplet ein einziger Befehl die gebaute App:

```bash
SIGN_IDENTITY=auto NOTARY_PROFILE=apidrop-notary tools/macos_sign.sh dist/ApiDrop.app dist/ApiDrop.dmg
```

Der Weg über GitHub-Secrets (unten) ist nur nötig, wenn GitHub Actions selbst signieren soll.

Der Build-Workflow ist vorbereitet. **Solange keine Secrets hinterlegt sind, baut er wie bisher**
(ad-hoc-signiert, Nutzer müssen einmal „Dennoch öffnen“). Sobald die sechs Secrets unten
gesetzt sind, wird die App automatisch mit deiner Developer ID signiert, notarisiert und
„gestapelt“ – Nutzer können sie dann ohne Warnung per Doppelklick öffnen.

Bereits lokal getestet: Signieren mit Hardened Runtime (alle 76 Programmdateien im Bundle),
Entitlements, Start der Oberfläche, `apidrop run` und `apidrop list` aus der gehärteten App.
Nicht testbar ohne dein Zertifikat: der echte Notarisierungs-Lauf bei Apple.

## 1. Apple Developer Program

- Anmeldung: <https://developer.apple.com/programs/enroll/> (Jahresgebühr, aktuell auf der Seite prüfen).
- **Als Einzelperson:** schnell, aber in macOS erscheint dein **Personenname** als Entwickler.
- **Als Organisation (LetAIwork4u):** erscheint als Firmenname, braucht aber eine **D-U-N-S-Nummer**
  und eine eingetragene Rechtsform; dauert länger.

## 2. Zertifikat „Developer ID Application“ erstellen

Am einfachsten mit Xcode: *Xcode → Settings → Accounts → (Apple ID) → Manage Certificates → „+“ →
Developer ID Application*.

Ohne Xcode: Schlüsselbundverwaltung → *Zertifikatsassistent → Zertifikat einer Zertifizierungsinstanz
anfordern* (auf Festplatte sichern), dann auf <https://developer.apple.com/account/resources/certificates>
ein „Developer ID Application“-Zertifikat mit dieser Anfrage erstellen und per Doppelklick installieren.

## 3. Zertifikat exportieren

Schlüsselbundverwaltung → *Meine Zertifikate* → „Developer ID Application: …“ → Rechtsklick →
**Exportieren** → Format `.p12` → ein starkes Export-Passwort vergeben → z. B. `~/Desktop/devid.p12`.

Den genauen Namen der Identität brauchst du gleich:

```bash
security find-identity -v -p codesigning
```

Ausgabe z. B. `"Developer ID Application: Max Muster (AB12CD34EF)"` – die Zeichen in Klammern
sind deine **Team-ID**.

## 4. App-spezifisches Passwort

<https://account.apple.com> → *Anmeldung und Sicherheit* → **App-spezifische Passwörter** → neues
Passwort „API Drop notarization“ erzeugen.

## 5. GitHub-Secrets setzen

Im Terminal im Ordner `api-drop-app` (angemeldet als Letaiwork4u). Jeder Befehl fragt den Wert
**verdeckt** ab – so landet nichts im Shell-Verlauf:

```bash
base64 -i ~/Desktop/devid.p12 | gh secret set MACOS_CERT_P12_BASE64
gh secret set MACOS_CERT_PASSWORD        # Export-Passwort der .p12
gh secret set MACOS_SIGN_IDENTITY        # z. B. Developer ID Application: Max Muster (AB12CD34EF)
gh secret set APPLE_ID                   # Apple-ID-E-Mail
gh secret set APPLE_TEAM_ID              # z. B. AB12CD34EF
gh secret set APPLE_APP_PASSWORD         # app-spezifisches Passwort aus Schritt 4
```

Danach `~/Desktop/devid.p12` löschen.

## 6. Testlauf, dann Release

```bash
gh workflow run build.yml --ref main
gh run watch
```

Im Log von „Signieren, DMG, Notarisieren“ muss `The staple and validate action worked!` und
`source=Notarized Developer ID` stehen. Dann `__version__` in `app.py` erhöhen (z. B. 1.1.1),
committen, Tag `v1.1.1` pushen – das Release ist dann signiert und notarisiert.

Lokal geht dasselbe mit:

```bash
SIGN_IDENTITY="Developer ID Application: …" APPLE_ID=… APPLE_TEAM_ID=… APPLE_APP_PASSWORD=… \
  tools/macos_sign.sh dist/ApiDrop.app dist/ApiDrop.dmg
```

## Danach anpassen

- Webseite & README: den Hinweis „macOS warnt beim ersten Start einmal …“ für macOS entfernen.
- Falls die Notarisierung abgelehnt wird: `xcrun notarytool log <submission-id> --apple-id … --team-id … --password …`
  zeigt die betroffene Datei.
