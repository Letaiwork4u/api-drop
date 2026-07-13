# App-Repo anlegen und die Downloads bauen

## Warum GitHub das für dich baut

Eine `.exe` entsteht nur auf Windows, eine `.dmg` nur auf macOS, das
Linux-Binary nur auf Linux. Du hast nur einen Mac – deshalb baut GitHub
die drei Versionen kostenlos für dich (GitHub Actions stellt dafür
Windows-, Mac- und Linux-Rechner bereit).

---

## Schritt 1 — Das öffentliche Repo anlegen

1. Auf github.com (als **Letaiwork4u** angemeldet) → **+** → **New repository**
2. Name: **`api-drop`**
3. Sichtbarkeit: **Public** ← wichtig! Nur öffentliche Repos können Sterne bekommen.
4. **Kein** README/gitignore/License hinzufügen (haben wir schon)
5. **Create repository**

## Schritt 2 — Dateien hochladen

Auf der leeren Repo-Seite: **"uploading an existing file"** → alle Dateien
aus diesem Paket per Drag & Drop hochladen.

Achtung bei den Ordnern: `.github/workflows/build.yml` und `assets/logo.svg`
müssen ihre Ordnerstruktur behalten. Beim Drag & Drop im Browser einfach
die Ordner `.github` und `assets` mit hineinziehen – GitHub übernimmt die
Struktur.

Falls das nicht klappt: Über **Add file → Create new file** den Pfad
`.github/workflows/build.yml` von Hand eintippen (GitHub erzeugt die Ordner
automatisch, sobald du Schrägstriche tippst) und den Inhalt hineinkopieren.

Dann **Commit changes**.

## Schritt 3 — README-Platzhalter ersetzen

In `README.md` und `README.de.md` steht an drei Stellen `DEIN-NAME`.
Ersetze das durch **Letaiwork4u**:

- Der Stern-Badge oben
- Der Link im Badge
- Der `git clone`-Befehl

Auf GitHub: Datei öffnen → Stift-Symbol → ändern → Commit.

## Schritt 4 — Den Build starten

1. Im Repo auf den Reiter **Actions**
2. Falls gefragt: Workflows aktivieren bestätigen
3. Links **"Build API Drop (Windows, macOS, Linux)"** anklicken
4. Rechts **"Run workflow"** → **Run workflow**

Jetzt bauen drei Rechner parallel. Das dauert ca. 5–10 Minuten.
Grüne Haken = fertig.

## Schritt 5 — Die fertigen Apps holen

Nach dem Build: In den Workflow-Lauf klicken → ganz unten unter
**Artifacts** liegen:

- `ApiDrop-windows` → die `.exe`
- `ApiDrop-macos` → die `.dmg`
- `ApiDrop-linux` → das Linux-Binary

**Lade die macOS-Version herunter und teste sie auf deinem Mac**, bevor du
sie öffentlich anbietest.

## Schritt 6 — Ein Release erstellen (die Download-Seite)

Damit Nutzer die Apps bequem finden:

1. Im Repo rechts auf **Releases** → **Create a new release**
2. **Choose a tag** → neuen Tag eintippen: `v1.0.0` → "Create new tag"
3. Titel: `API Drop v1.0.0`
4. **Publish release**

Der Workflow läuft dann automatisch nochmal und hängt die drei Dateien
direkt ans Release. Ab dann sind sie unter
`github.com/Letaiwork4u/api-drop/releases/latest` herunterladbar – und
genau dorthin zeigen später die Download-Buttons auf der Website.

---

## Wichtige Warnung: Nicht-signierte Apps

Deine Apps sind nicht mit einem kostenpflichtigen Entwickler-Zertifikat
signiert. Das bedeutet:

- **macOS** zeigt beim ersten Start: *"ApiDrop kann nicht geöffnet werden,
  da es von einem nicht verifizierten Entwickler stammt"*.
  Workaround für Nutzer: Rechtsklick auf die App → **Öffnen** → **Öffnen**.
- **Windows** zeigt einen SmartScreen-Hinweis: *"Windows hat den Start
  geschützt"* → **Weitere Informationen** → **Trotzdem ausführen**.

Das ist normal für Open-Source-Projekte ohne Zertifikat. Erkläre es in der
README, damit Nutzer nicht abgeschreckt werden. Zertifikate kosten Geld
(Apple ca. 99 $/Jahr, Windows-Signatur je nach Anbieter) – das lohnt sich
erst, wenn das Projekt läuft.
