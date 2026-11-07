"""
API Drop – Desktop app
======================
Long, cryptic API keys get a human-readable name (e.g. "OpenAI API 1").
The real key stays encrypted in a local vault; the .env only holds a
reference like apidrop://openai-api-1.

Runs fully local, no internet connection, no telemetry.
UI: PyQt6. Default language English, switchable to German.
"""

import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QCheckBox, QMessageBox, QInputDialog, QFrame, QHeaderView,
    QAbstractItemView, QSizePolicy, QGraphicsOpacityEffect,
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtSvgWidgets import QSvgWidget

from detector import detect_provider, suggest_label, env_var_for_provider
from resolver import ref_for_label
import storage

def _asset_dir() -> Path:
    """
    Ordner, in dem die Logo-Dateien liegen.
    Beim normalen Start: der Ordner dieser Datei.
    In einer mit PyInstaller verpackten App: das temporäre Bundle-Verzeichnis
    (sys._MEIPASS), in das PyInstaller die mitgelieferten Dateien entpackt.
    """
    bundle = getattr(sys, "_MEIPASS", None)
    if bundle:
        return Path(bundle)
    return Path(__file__).resolve().parent


ASSET_DIR = _asset_dir()

__version__ = "1.1.1"

# ---- Brand colours (mint-blue family) -------------------------------
NAVY = "#38545c"
NAVY_LIGHT = "#45666f"
BG = "#edf3f4"
CARD = "#ffffff"
BORDER = "#d9e5e8"
TEXT_MUTED = "#6b7d8c"
ACCENT = "#45666f"
ACCENT_HOVER = "#38545c"
DANGER = "#c0392b"

# ---- Translations ---------------------------------------------------
TR = {
    "en": {
        "subtitle": "Turn a long key into a short name.",
        "lang_button": "Deutsch",
        "add_section": "ADD A NEW KEY",
        "key_placeholder": "Paste API key here \u2026",
        "show": "Show",
        "hide": "Hide",
        "detect": "Detect && suggest name",  # "&&" = literal "&" in Qt buttons
        "name_placeholder": "Name, e.g. OpenAI API 1 (freely editable)",
        "add_to_list": "Add to list",
        "list_section": "MY KEYS \u00b7 ONLY THE NAME IS VISIBLE",
        "col_name": "Name",
        "col_provider": "Provider",
        "copy_reference": "Copy reference",
        "copy_name": "Copy name",
        "rename": "Rename",
        "remove": "Remove",
        "ref_tooltip": "Copies apidrop://name for your .env file",
        "persist_check": "  Store keys encrypted locally  \u00b7  required for apidrop run",
        "delete_saved": "Delete stored keys",
        "local_note": "All data stays on this machine. No transfer to the internet.",
        "dlg_notice_title": "Security notice",
        "dlg_info_title": "API Drop",
        "dlg_hint_title": "Notice",
        "need_key_first": "Please paste an API key first.",
        "need_key_and_name": "API key and name are required.",
        "name_exists": "This name already exists. Please choose another.",
        "select_first": "Please select an entry in the list first.",
        "ref_copied": "{ref}\n\ncopied. Paste it into your .env file, e.g.:\n\n{env_var}={ref}\n\nLater run your program with:  apidrop run -- <your command>\nThe real key is injected only at runtime \u2013 never visible in the file.",
        "name_copied": "\"{label}\" copied.\n\nThe actual API key was NOT copied.",
        "rename_title": "Rename",
        "rename_prompt": "New name:",
        "name_in_use": "This name is already in use.",
        "remove_title": "Remove",
        "remove_confirm": "Really remove \"{label}\"?",
        "pw_title": "Master password",
        "pw_prompt": "Master password:",
        "pw_confirm_title": "Confirm master password",
        "pw_confirm_prompt": "Enter password again:",
        "pw_mismatch": "Passwords do not match.",
        "persist_notice": "Keys will be stored encrypted on this machine (AES with your master password).\n\nDon't forget the password \u2013 there is no recovery.",
        "found_title": "Stored keys found",
        "found_prompt": "Previously stored keys were found. Load them now?",
        "no_saved": "There are no stored keys.",
        "delete_title": "Really delete?",
        "delete_confirm": "All locally stored keys will be permanently deleted. Continue?",
        "deleted_done": "All stored keys have been deleted.",
        "unlock_prompt": "A vault with stored keys already exists.\nEnter its master password to add your keys to it:",
        "wrong_pw_retry": "Wrong master password for the existing vault.\n\nTry again?",
        "wrong_pw_load": "Wrong master password.\n\nTry again?",
        "off_title": "Storage switched off",
        "off_delete": "Also delete the stored keys from this computer now?\n\nYes = delete the vault permanently.\nNo = keep it (apidrop run keeps working, but changes in this session are no longer saved).",
        "replace_title": "Replace existing vault?",
        "replace_confirm": "Start a NEW vault instead?\n\nAll keys stored in the existing vault will be permanently lost.",
        "ref_in_use": "This name would create the reference apidrop://{ref}, which another key already uses. Please choose a different name.",
        "cli_button": "Terminal setup",
        "cli_title": "Use apidrop in the terminal",
        "cli_text": "Run this once in Terminal to install the apidrop command:\n\n{cmd}\n\n(The command has been copied to your clipboard.)\n\nAfterwards:  apidrop run -- <your command>\nThe vault must be stored locally (checkbox below).",
        "cli_text_win": "Download apidrop-cli-windows.zip (same release page), unzip it and put apidrop.exe in a folder on your PATH.\n\nThen:  apidrop run -- <your command>\nThe vault must be stored locally (checkbox below).",
    },
    "de": {
        "subtitle": "Aus einem langen Key wird ein kurzer Name.",
        "lang_button": "English",
        "add_section": "NEUEN KEY HINZUF\u00dcGEN",
        "key_placeholder": "API Key hier einf\u00fcgen \u2026",
        "show": "Anzeigen",
        "hide": "Verbergen",
        "detect": "Erkennen && Namen vorschlagen",
        "name_placeholder": "Name, z.B. OpenAI API 1 (frei \u00e4nderbar)",
        "add_to_list": "Zur Liste",
        "list_section": "MEINE KEYS \u00b7 NUR DER NAME IST SICHTBAR",
        "col_name": "Name",
        "col_provider": "Anbieter",
        "copy_reference": "Referenz kopieren",
        "copy_name": "Namen kopieren",
        "rename": "Umbenennen",
        "remove": "Entfernen",
        "ref_tooltip": "Kopiert apidrop://name f\u00fcr die .env-Datei",
        "persist_check": "  Keys verschl\u00fcsselt lokal speichern  \u00b7  n\u00f6tig f\u00fcr apidrop run",
        "delete_saved": "Gespeicherte Keys l\u00f6schen",
        "local_note": "Alle Daten bleiben auf diesem Rechner. Keine \u00dcbertragung ins Internet.",
        "dlg_notice_title": "Sicherheitshinweis",
        "dlg_info_title": "API Drop",
        "dlg_hint_title": "Hinweis",
        "need_key_first": "Bitte zuerst einen API Key einf\u00fcgen.",
        "need_key_and_name": "API Key und Name werden ben\u00f6tigt.",
        "name_exists": "Dieser Name existiert bereits. Bitte einen anderen w\u00e4hlen.",
        "select_first": "Bitte zuerst einen Eintrag in der Liste ausw\u00e4hlen.",
        "ref_copied": "{ref}\n\nwurde kopiert. F\u00fcge das in deine .env-Datei ein, z.B.:\n\n{env_var}={ref}\n\nStarte dein Programm sp\u00e4ter mit:  apidrop run -- <dein Befehl>\nDer echte Key wird erst zur Laufzeit eingesetzt \u2013 nie sichtbar in der Datei.",
        "name_copied": "\"{label}\" wurde kopiert.\n\nDer eigentliche API Key wurde NICHT kopiert.",
        "rename_title": "Umbenennen",
        "rename_prompt": "Neuer Name:",
        "name_in_use": "Dieser Name wird bereits verwendet.",
        "remove_title": "Entfernen",
        "remove_confirm": "\"{label}\" wirklich entfernen?",
        "pw_title": "Master-Passwort",
        "pw_prompt": "Master-Passwort:",
        "pw_confirm_title": "Master-Passwort best\u00e4tigen",
        "pw_confirm_prompt": "Passwort erneut eingeben:",
        "pw_mismatch": "Passw\u00f6rter stimmen nicht \u00fcberein.",
        "persist_notice": "Keys werden verschl\u00fcsselt auf diesem Rechner gespeichert (AES mit deinem Master-Passwort).\n\nVergiss das Passwort nicht \u2013 es gibt keine Wiederherstellung.",
        "found_title": "Gespeicherte Keys gefunden",
        "found_prompt": "Es wurden zuvor gespeicherte Keys gefunden. Jetzt laden?",
        "no_saved": "Es sind keine gespeicherten Keys vorhanden.",
        "delete_title": "Wirklich l\u00f6schen?",
        "delete_confirm": "Alle lokal gespeicherten Keys werden unwiderruflich gel\u00f6scht. Fortfahren?",
        "deleted_done": "Alle gespeicherten Keys wurden gel\u00f6scht.",
        "unlock_prompt": "Es gibt bereits einen Vault mit gespeicherten Keys.\nGib sein Master-Passwort ein, um deine Keys hinzuzuf\u00fcgen:",
        "wrong_pw_retry": "Falsches Master-Passwort f\u00fcr den vorhandenen Vault.\n\nNochmal versuchen?",
        "wrong_pw_load": "Falsches Master-Passwort.\n\nNochmal versuchen?",
        "off_title": "Speichern ausgeschaltet",
        "off_delete": "Die gespeicherten Keys jetzt auch von diesem Rechner l\u00f6schen?\n\nJa = Vault unwiderruflich l\u00f6schen.\nNein = behalten (apidrop run funktioniert weiter, \u00c4nderungen dieser Sitzung werden aber nicht mehr gespeichert).",
        "replace_title": "Vorhandenen Vault ersetzen?",
        "replace_confirm": "Stattdessen einen NEUEN Vault anlegen?\n\nAlle Keys im vorhandenen Vault gehen unwiderruflich verloren.",
        "ref_in_use": "Dieser Name w\u00fcrde die Referenz apidrop://{ref} erzeugen, die schon ein anderer Key nutzt. Bitte einen anderen Namen w\u00e4hlen.",
        "cli_button": "Terminal einrichten",
        "cli_title": "apidrop im Terminal nutzen",
        "cli_text": "F\u00fchre diesen Befehl einmal im Terminal aus, um den Befehl apidrop zu installieren:\n\n{cmd}\n\n(Der Befehl wurde in die Zwischenablage kopiert.)\n\nDanach:  apidrop run -- <dein Befehl>\nDer Vault muss lokal gespeichert sein (H\u00e4kchen unten).",
        "cli_text_win": "Lade apidrop-cli-windows.zip (gleiche Release-Seite), entpacke sie und lege apidrop.exe in einen Ordner im PATH.\n\nDanach:  apidrop run -- <dein Befehl>\nDer Vault muss lokal gespeichert sein (H\u00e4kchen unten).",
    },
}


class ApiDropWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.entries = []
        self._master_password = None
        self.persist_enabled = False
        self.lang = "en"

        self.setWindowTitle(f"API Drop {__version__}")
        self.setMinimumSize(760, 720)
        self.resize(820, 780)
        self.setStyleSheet(f"background-color: {BG};")

        self._build_ui()
        self._retranslate()
        self._play_intro_animation()
        # Vault-Abfrage erst NACH dem Fenster-Aufbau, damit die Animation
        # nicht von Dialogen überdeckt wird.
        QTimer.singleShot(750, self._offer_load_existing)

    def t(self, key):
        return TR[self.lang][key]

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(18)
        root.addWidget(self._build_header())
        root.addWidget(self._build_input_card())
        root.addWidget(self._build_list_card(), stretch=1)
        root.addWidget(self._build_storage_card())

    def _build_header(self):
        header = QWidget()
        layout = QVBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        self.logo = QSvgWidget()
        self.logo.setMaximumHeight(76)
        self.logo.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self._load_logo()
        top.addWidget(self.logo, alignment=Qt.AlignmentFlag.AlignLeft)
        top.addStretch(1)
        self.cli_btn = QPushButton()
        self.cli_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cli_btn.setStyleSheet(self._ghost_button_style())
        self.cli_btn.setMaximumHeight(30)
        self.cli_btn.clicked.connect(self._on_cli_setup)
        top.addWidget(self.cli_btn, alignment=Qt.AlignmentFlag.AlignTop)
        self.lang_toggle = QPushButton()
        self.lang_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lang_toggle.setStyleSheet(self._ghost_button_style())
        self.lang_toggle.setMaximumHeight(30)
        self.lang_toggle.clicked.connect(self._toggle_language)
        top.addWidget(self.lang_toggle, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(top)
        self.subtitle = QLabel()
        self.subtitle.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px;")
        layout.addWidget(self.subtitle)
        return header

    def _load_logo(self):
        path = ASSET_DIR / "logo_full_mint.svg"
        if path.exists():
            self.logo.load(str(path))
            ratio = 520 / 260
            self.logo.setFixedSize(int(76 * ratio), 76)

    def _card_frame(self):
        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame {{ background-color: {CARD}; border: 1px solid {BORDER};"
            f" border-radius: 12px; }}"
        )
        return frame

    def _section_label(self, attr):
        lbl = QLabel()
        lbl.setStyleSheet(
            f"color: {NAVY}; font-size: 11px; font-weight: bold;"
            f" letter-spacing: 1px; border: none;"
        )
        setattr(self, attr, lbl)
        return lbl

    def _build_input_card(self):
        card = self._card_frame()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        layout.addWidget(self._section_label("lbl_add_section"))
        key_row = QHBoxLayout()
        key_row.setSpacing(8)
        self.key_input = QLineEdit()
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setStyleSheet(self._input_style())
        self.key_input.setMinimumHeight(40)
        self.show_btn = QPushButton()
        self.show_btn.setCheckable(True)
        self.show_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.show_btn.setStyleSheet(self._ghost_button_style())
        self.show_btn.setMinimumHeight(40)
        self.show_btn.clicked.connect(self._toggle_visibility)
        key_row.addWidget(self.key_input, stretch=1)
        key_row.addWidget(self.show_btn)
        layout.addLayout(key_row)
        self.detect_btn = QPushButton()
        self.detect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.detect_btn.setStyleSheet(self._primary_button_style())
        self.detect_btn.setMinimumHeight(42)
        self.detect_btn.clicked.connect(self._on_detect)
        layout.addWidget(self.detect_btn)
        name_row = QHBoxLayout()
        name_row.setSpacing(8)
        self.name_input = QLineEdit()
        self.name_input.setStyleSheet(self._input_style())
        self.name_input.setMinimumHeight(40)
        self.add_btn = QPushButton()
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.setStyleSheet(self._navy_button_style())
        self.add_btn.setMinimumHeight(40)
        self.add_btn.clicked.connect(self._on_add)
        name_row.addWidget(self.name_input, stretch=1)
        name_row.addWidget(self.add_btn)
        layout.addLayout(name_row)
        return card

    def _build_list_card(self):
        card = self._card_frame()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)
        layout.addWidget(self._section_label("lbl_list_section"))
        self.table = QTableWidget(0, 2)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setStyleSheet(self._table_style())
        layout.addWidget(self.table, stretch=1)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self.ref_btn = QPushButton()
        self.ref_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ref_btn.setStyleSheet(self._primary_button_style())
        self.ref_btn.setMinimumHeight(40)
        self.ref_btn.clicked.connect(self._on_copy_reference)
        self.copy_btn = QPushButton()
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.setStyleSheet(self._ghost_button_style())
        self.copy_btn.setMinimumHeight(40)
        self.copy_btn.clicked.connect(self._on_copy)
        self.rename_btn = QPushButton()
        self.rename_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.rename_btn.setStyleSheet(self._ghost_button_style())
        self.rename_btn.setMinimumHeight(40)
        self.rename_btn.clicked.connect(self._on_rename)
        self.remove_btn = QPushButton()
        self.remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.remove_btn.setStyleSheet(self._ghost_button_style())
        self.remove_btn.setMinimumHeight(40)
        self.remove_btn.clicked.connect(self._on_remove)
        btn_row.addWidget(self.ref_btn, stretch=1)
        btn_row.addWidget(self.copy_btn)
        btn_row.addWidget(self.rename_btn)
        btn_row.addWidget(self.remove_btn)
        layout.addLayout(btn_row)
        return card

    def _build_storage_card(self):
        card = self._card_frame()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)
        row = QHBoxLayout()
        self.persist_check = QCheckBox()
        self.persist_check.setCursor(Qt.CursorShape.PointingHandCursor)
        self.persist_check.setStyleSheet(
            f"QCheckBox {{ color: {NAVY}; font-size: 12px; border: none; }}"
            f"QCheckBox::indicator {{ width: 18px; height: 18px; }}"
        )
        self.persist_check.stateChanged.connect(self._on_toggle_persist)
        row.addWidget(self.persist_check, stretch=1)
        self.delete_btn = QPushButton()
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_btn.setStyleSheet(self._danger_button_style())
        self.delete_btn.setMinimumHeight(34)
        self.delete_btn.clicked.connect(self._on_delete_vault)
        row.addWidget(self.delete_btn)
        layout.addLayout(row)
        self.local_note = QLabel()
        self.local_note.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; border: none;")
        layout.addWidget(self.local_note)
        return card

    def _retranslate(self):
        self.lang_toggle.setText(self.t("lang_button"))
        self.cli_btn.setText(self.t("cli_button"))
        self.subtitle.setText(self.t("subtitle"))
        self.lbl_add_section.setText(self.t("add_section"))
        self.key_input.setPlaceholderText(self.t("key_placeholder"))
        self.show_btn.setText(self.t("hide") if self.show_btn.isChecked() else self.t("show"))
        self.detect_btn.setText(self.t("detect"))
        self.name_input.setPlaceholderText(self.t("name_placeholder"))
        self.add_btn.setText(self.t("add_to_list"))
        self.lbl_list_section.setText(self.t("list_section"))
        self.table.setHorizontalHeaderLabels([self.t("col_name"), self.t("col_provider")])
        self.ref_btn.setText(self.t("copy_reference"))
        self.ref_btn.setToolTip(self.t("ref_tooltip"))
        self.copy_btn.setText(self.t("copy_name"))
        self.rename_btn.setText(self.t("rename"))
        self.remove_btn.setText(self.t("remove"))
        self.persist_check.setText(self.t("persist_check"))
        self.delete_btn.setText(self.t("delete_saved"))
        self.local_note.setText(self.t("local_note"))

    def _toggle_language(self):
        self.lang = "de" if self.lang == "en" else "en"
        self._retranslate()

    def _play_intro_animation(self):
        effect = QGraphicsOpacityEffect(self.logo)
        self.logo.setGraphicsEffect(effect)
        effect.setOpacity(0.0)
        self._intro_anim = QPropertyAnimation(effect, b"opacity")
        self._intro_anim.setDuration(650)
        self._intro_anim.setStartValue(0.0)
        self._intro_anim.setEndValue(1.0)
        self._intro_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._intro_anim.finished.connect(lambda: self.logo.setGraphicsEffect(None))
        QTimer.singleShot(60, self._intro_anim.start)

    def _input_style(self):
        return (
            f"QLineEdit {{ background-color: {BG}; border: 1px solid {BORDER};"
            f" border-radius: 8px; padding: 8px 12px; color: {NAVY};"
            f" font-size: 13px; }}"
            f"QLineEdit:focus {{ border: 1px solid {ACCENT}; }}"
        )

    def _primary_button_style(self):
        return (
            f"QPushButton {{ background-color: {ACCENT}; color: white;"
            f" border: none; border-radius: 8px; padding: 8px 16px;"
            f" font-size: 13px; font-weight: bold; }}"
            f"QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}"
            f"QPushButton:pressed {{ background-color: {NAVY}; }}"
        )

    def _navy_button_style(self):
        return (
            f"QPushButton {{ background-color: {NAVY}; color: white;"
            f" border: none; border-radius: 8px; padding: 8px 16px;"
            f" font-size: 13px; font-weight: bold; }}"
            f"QPushButton:hover {{ background-color: {NAVY_LIGHT}; }}"
        )

    def _ghost_button_style(self):
        return (
            f"QPushButton {{ background-color: white; color: {NAVY};"
            f" border: 1px solid {BORDER}; border-radius: 8px;"
            f" padding: 8px 16px; font-size: 13px; }}"
            f"QPushButton:hover {{ border: 1px solid {ACCENT}; color: {ACCENT}; }}"
            f"QPushButton:checked {{ background-color: {NAVY}; color: white; }}"
        )

    def _danger_button_style(self):
        return (
            f"QPushButton {{ background-color: #fbeceb; color: {DANGER};"
            f" border: 1px solid #f0c4c0; border-radius: 8px;"
            f" padding: 6px 14px; font-size: 12px; }}"
            f"QPushButton:hover {{ background-color: {DANGER}; color: white; }}"
        )

    def _table_style(self):
        return (
            f"QTableWidget {{ background-color: white; border: 1px solid {BORDER};"
            f" border-radius: 8px; gridline-color: {BORDER};"
            f" color: {NAVY}; font-size: 13px; }}"
            f"QTableWidget::item {{ padding: 8px; }}"
            f"QTableWidget::item:selected {{ background-color: #dbe3f0; color: {NAVY}; }}"
            f"QHeaderView::section {{ background-color: {BG}; color: {TEXT_MUTED};"
            f" padding: 8px; border: none; border-bottom: 1px solid {BORDER};"
            f" font-size: 11px; font-weight: bold; }}"
        )

    def _toggle_visibility(self):
        if self.show_btn.isChecked():
            self.key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_btn.setText(self.t("hide"))
        else:
            self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_btn.setText(self.t("show"))

    def _on_detect(self):
        key = self.key_input.text().strip()
        if not key:
            self._warn(self.t("need_key_first"))
            return
        existing = [e["label"] for e in self.entries]
        self.name_input.setText(suggest_label(key, existing))

    def _on_add(self):
        key = self.key_input.text().strip()
        label = self.name_input.text().strip()
        if not key or not label:
            self._warn(self.t("need_key_and_name"))
            return
        if any(e["label"] == label for e in self.entries):
            self._warn(self.t("name_exists"))
            return
        ref = ref_for_label(label)
        if not ref or self._ref_taken(ref):
            self._warn(self.t("ref_in_use").format(ref=ref))
            return
        provider = detect_provider(key)
        # "ref" is fixed at creation: renaming must not break existing .env files
        self.entries.append({"label": label, "provider": provider, "key": key, "ref": ref})
        self._append_row(label, provider)
        self.key_input.clear()
        self.name_input.clear()
        if self.persist_enabled:
            self._save_to_disk()

    @staticmethod
    def _ref_of(entry):
        """Stable reference of an entry (older vaults have no 'ref' yet)."""
        return entry.get("ref") or ref_for_label(entry["label"])

    def _ref_taken(self, ref, ignore=None):
        """True if `ref` is already reachable for another entry
        (via its stable ref or the slug of its current label)."""
        for e in self.entries:
            if e is ignore:
                continue
            if ref in (self._ref_of(e), ref_for_label(e["label"])):
                return True
        return False

    def _rebuild_table(self):
        self.table.setRowCount(0)
        for e in self.entries:
            self._append_row(e["label"], e["provider"])

    def _append_row(self, label, provider):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(label))
        self.table.setItem(row, 1, QTableWidgetItem(provider))

    def _selected_row(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            self._info(self.t("select_first"))
            return -1
        return rows[0].row()

    def _on_copy_reference(self):
        row = self._selected_row()
        if row < 0:
            return
        entry = self.entries[row]
        provider = entry["provider"]
        reference = f"apidrop://{self._ref_of(entry)}"
        env_var = env_var_for_provider(provider)
        QApplication.clipboard().setText(reference)
        self._info(self.t("ref_copied").format(ref=reference, env_var=env_var))

    def _on_copy(self):
        row = self._selected_row()
        if row < 0:
            return
        label = self.table.item(row, 0).text()
        QApplication.clipboard().setText(label)
        self._info(self.t("name_copied").format(label=label))

    def _on_rename(self):
        row = self._selected_row()
        if row < 0:
            return
        old = self.table.item(row, 0).text()
        new, ok = QInputDialog.getText(self, self.t("rename_title"), self.t("rename_prompt"), text=old)
        new = new.strip() if ok else ""
        if not new or new == old:
            return
        if any(e["label"] == new for e in self.entries):
            self._warn(self.t("name_in_use"))
            return
        entry = self.entries[row]
        new_ref = ref_for_label(new)
        if not new_ref or self._ref_taken(new_ref, ignore=entry):
            self._warn(self.t("ref_in_use").format(ref=new_ref))
            return
        # Pin the reference before renaming, so apidrop://<old-name> keeps working
        entry["ref"] = self._ref_of(entry)
        entry["label"] = new
        self.table.item(row, 0).setText(new)
        if self.persist_enabled:
            self._save_to_disk()

    def _on_remove(self):
        row = self._selected_row()
        if row < 0:
            return
        label = self.table.item(row, 0).text()
        confirm = QMessageBox.question(self, self.t("remove_title"), self.t("remove_confirm").format(label=label))
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self.entries.pop(row)
        self.table.removeRow(row)
        if self.persist_enabled:
            self._save_to_disk()

    def _ask_password(self, confirm=False):
        pw, ok = QInputDialog.getText(self, self.t("pw_title"), self.t("pw_prompt"), echo=QLineEdit.EchoMode.Password)
        if not ok or not pw:
            return None
        if confirm:
            pw2, ok2 = QInputDialog.getText(self, self.t("pw_confirm_title"), self.t("pw_confirm_prompt"), echo=QLineEdit.EchoMode.Password)
            if not ok2 or pw != pw2:
                self._warn(self.t("pw_mismatch"))
                return None
        return pw

    def _on_toggle_persist(self):
        if self.persist_check.isChecked():
            # Passwort schon aus dieser Sitzung bekannt? Dann nicht erneut fragen.
            if self._master_password:
                self.persist_enabled = True
                self._save_to_disk()
                return
            if storage.vault_exists():
                # Never overwrite a vault we haven't opened: unlock it and merge.
                if not self._unlock_and_merge_existing_vault():
                    self._uncheck_persist()
                    return
            else:
                QMessageBox.information(self, self.t("dlg_notice_title"), self.t("persist_notice"))
                pw = self._ask_password(confirm=True)
                if not pw:
                    self._uncheck_persist()
                    return
                self._master_password = pw
            self.persist_enabled = True
            self._save_to_disk()
        else:
            self.persist_enabled = False
            self._master_password = None
            if storage.vault_exists():
                answer = QMessageBox.question(self, self.t("off_title"), self.t("off_delete"))
                if answer == QMessageBox.StandardButton.Yes:
                    storage.delete_vault()
                    self._info(self.t("deleted_done"))

    def _uncheck_persist(self):
        self.persist_check.blockSignals(True)
        self.persist_check.setChecked(False)
        self.persist_check.blockSignals(False)
        self.persist_enabled = False

    def _unlock_and_merge_existing_vault(self) -> bool:
        """Ask for the existing vault's password, load it and merge the keys
        of this session into it. Returns False if the user cancels.
        Replacing the vault is only possible after an explicit confirmation."""
        while True:
            pw, ok = QInputDialog.getText(self, self.t("pw_title"), self.t("unlock_prompt"),
                                          echo=QLineEdit.EchoMode.Password)
            if not ok or not pw:
                return False
            try:
                stored = storage.load_entries(pw)
            except ValueError:
                again = QMessageBox.question(self, self.t("dlg_hint_title"), self.t("wrong_pw_retry"))
                if again == QMessageBox.StandardButton.Yes:
                    continue
                replace = QMessageBox.question(self, self.t("replace_title"), self.t("replace_confirm"))
                if replace != QMessageBox.StandardButton.Yes:
                    return False
                new_pw = self._ask_password(confirm=True)
                if not new_pw:
                    return False
                self._master_password = new_pw
                return True
            self._merge_stored_entries(stored)
            self._master_password = pw
            return True

    def _merge_stored_entries(self, stored):
        """Stored keys come first and keep their references (they may already be
        used in .env files). Session keys whose name/reference clashes are renamed."""
        merged = []
        for e in stored:
            e.setdefault("ref", ref_for_label(e["label"]))
            merged.append(e)
        current = self.entries
        self.entries = merged
        for e in current:
            if any(s["key"] == e["key"] for s in merged):
                continue  # same key already stored
            label, n = e["label"], 2
            while any(x["label"] == label for x in self.entries) or self._ref_taken(ref_for_label(label)):
                label, n = f"{e['label']} ({n})", n + 1
            e["label"], e["ref"] = label, ref_for_label(label)
            self.entries.append(e)
        self._rebuild_table()

    def _save_to_disk(self):
        if not self._master_password:
            pw = self._ask_password(confirm=True)
            if not pw:
                self.persist_check.blockSignals(True)
                self.persist_check.setChecked(False)
                self.persist_check.blockSignals(False)
                self.persist_enabled = False
                return
            self._master_password = pw
        storage.save_entries(self.entries, self._master_password)

    def _offer_load_existing(self):
        if not storage.vault_exists():
            return
        answer = QMessageBox.question(self, self.t("found_title"), self.t("found_prompt"))
        if answer == QMessageBox.StandardButton.Yes:
            self._load_from_disk()

    def _load_from_disk(self):
        while True:
            pw = self._ask_password()
            if not pw:
                return
            try:
                entries = storage.load_entries(pw)
                break
            except ValueError:
                again = QMessageBox.question(self, self.t("dlg_hint_title"), self.t("wrong_pw_load"))
                if again != QMessageBox.StandardButton.Yes:
                    return
        self._master_password = pw
        for e in entries:
            e.setdefault("ref", ref_for_label(e["label"]))
        self.entries = entries
        self._rebuild_table()
        self.persist_enabled = True
        # Häkchen setzen, ohne _on_toggle_persist erneut auszulösen
        # (sonst würde nochmal nach dem Passwort gefragt).
        self.persist_check.blockSignals(True)
        self.persist_check.setChecked(True)
        self.persist_check.blockSignals(False)

    def _on_delete_vault(self):
        if not storage.vault_exists():
            self._info(self.t("no_saved"))
            return
        confirm = QMessageBox.question(self, self.t("delete_title"), self.t("delete_confirm"))
        if confirm != QMessageBox.StandardButton.Yes:
            return
        storage.delete_vault()
        self._info(self.t("deleted_done"))

    def _on_cli_setup(self):
        if sys.platform.startswith("win"):
            self._info(self.t("cli_text_win"))
            return
        if getattr(sys, "frozen", False):
            target = sys.executable           # .../ApiDrop.app/Contents/MacOS/ApiDrop
        else:
            target = str(Path(__file__).resolve().parent / "apidrop_cli.py")
        # /usr/local/bin does not exist on every fresh Apple-silicon Mac
        cmd = f'sudo mkdir -p /usr/local/bin && sudo ln -sf "{target}" /usr/local/bin/apidrop'
        QApplication.clipboard().setText(cmd)
        QMessageBox.information(self, self.t("cli_title"), self.t("cli_text").format(cmd=cmd))

    def _warn(self, msg):
        QMessageBox.warning(self, self.t("dlg_hint_title"), msg)

    def _info(self, msg):
        QMessageBox.information(self, self.t("dlg_info_title"), msg)


CLI_COMMANDS = {"run", "list", "-h", "--help"}


def wants_cli(argv) -> bool:
    """The packaged app doubles as the `apidrop` command:
    `ApiDrop run -- …`, `ApiDrop list`, or any call through a link named `apidrop`."""
    invoked_as = Path(argv[0]).name
    if invoked_as in ("apidrop", "apidrop.exe"):
        return True
    return len(argv) > 1 and argv[1] in CLI_COMMANDS


def main():
    if wants_cli(sys.argv):
        import apidrop_cli
        raise SystemExit(apidrop_cli.main(sys.argv[1:]))
    app = QApplication(sys.argv)
    app.setApplicationName("API Drop")
    icon_path = ASSET_DIR / "assets" / "icons" / "apidrop_512.png"
    if icon_path.exists():
        # Window / taskbar icon on Windows and Linux (macOS uses the .icns of the bundle)
        app.setWindowIcon(QIcon(str(icon_path)))
    app.setStyleSheet(
        "QMessageBox, QInputDialog { background-color: #ffffff; }"
        "QMessageBox QLabel, QInputDialog QLabel { color: #22343a; }"
        "QMessageBox QPushButton, QInputDialog QPushButton {"
        " color: #22343a; background-color: #edf3f4;"
        " border: 1px solid #d9e5e8; border-radius: 7px; padding: 5px 14px; }"
        "QMessageBox QPushButton:hover, QInputDialog QPushButton:hover {"
        " border-color: #45666f; }"
        "QInputDialog QLineEdit { color: #22343a; background-color: #edf3f4;"
        " border: 1px solid #d9e5e8; border-radius: 6px; padding: 6px 8px; }"
    )
    window = ApiDropWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
