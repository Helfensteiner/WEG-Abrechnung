"""
Hausverwaltung – Eigentümergemeinschaft
Desktop-App mit Tkinter · SQLite-Datenbank
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import sqlite3
import json
import os
import glob
import csv
import re
import subprocess
import threading
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, date
from pathlib import Path

# ── Versionierung ──────────────────────────────────────────────────────────────
# Semantic Versioning: 0.MINOR.PATCH (Major=0 solange in Entwicklung)
# Synchron mit GitHub-Tags: git tag v0.4.0
#
# Versionshistorie:
#   0.1.0 — Initiale App: Tkinter-GUI, SQLite, CRUD für alle Entitäten,
#            CAMT.052 XML-Import, CSV-Import, Dashboard, Einstellungen
#   0.2.0 — RBAC (Rollen & Rechte), Buchhaltung-Intelligenz (Lernfähiges
#            Buchungssystem), Erweiterte Stammdaten (Adresse, IBAN, MEA ‰),
#            Benutzerverwaltung, Login, Kontoauszug Auto-Transfer
#   0.3.0 — Scrollbare/resizable Dialoge mit Größenpersistenz,
#            Rollenverwaltung-UI, Eigentümer-Wohnungszuordnung im Dialog,
#            Eigentümer als Bewohner (Eigennutzung), Versionierung
#   0.4.0 — Multi-Datei/Ordner-Import (CAMT.052 + CSV), Dublettenprüfung,
#            Buchungsstatus (Neu/Geprüft/Freigegeben), visuelle Hervorhebung
#   0.4.1 — Bugfix Buchhaltung-Vorschläge (sqlite3.Row.get), Passwort-Management
#            (generieren, ändern, Passwortabfrage abschaltbar pro Benutzer)
#   0.5.0 — WEG-Kostenkategorien (27 Kategorien mit Metadaten), Einstellungen
#            erweitert (Kontobezeichnungen, IBAN-Formatierung, Standard-Importpfad),
#            Kontoauszug-Filter, Fett-Markierung neuer Buchungen, erweiterte Kacheln,
#            Batch-Übernahme Vorschläge, PW-Skip pro Rolle
#   0.6.0 — Bugfixes: DB-Lock Multi-Import, Übernehmen-Button, Einstellungen Kontenfelder;
#            Importfortschritt, Kostenarten-CRUD (neu/bearbeiten/deaktivieren/löschen),
#            „Kategorie offen", verbessertes Buchungsregeln-Matching (Auftraggeber,
#            Keywords, Füllwörter-Filterung, dreistufige Matching-Strategie)
# ───────────────────────────────────────────────────────────────────────────────

#   0.9.0 — KI-Assistent (Claude/Anthropic API): Chat, Auto-Kategorisierung,
#            Anomalie-Check, Monats-Bericht, Offene Forderungen, Modell-Dropdown;
#            parse_float() für deutsche Kommazahlen aus SQLite;
#   0.9.1 — Issues #10-16: KI-Buttons repariert, Fenstertitel aus WEG-Stammdaten,
#            MEA-Doppelfeld entfernt, Mehrfach-Löschen Buchhaltung, Dublettencheck
#            zahlungen beim Import, Aufteilung Typ Wasserkosten nach Punkten,
#            bedingte Navigation Wasserkosten-Seite
#   0.9.2 — Issue #17: WEG-Stammdaten in einzelne Felder aufgeteilt (Straße, PLZ, Ort, E-Mail, Telefon)
#   0.9.3 — SQL-Injection in Buchhaltung behoben, Duplikat-Code entfernt, DB-Indizes + FOREIGN KEY
#   0.9.4 — AufteilungDialog: Widget-Referenzen korrekt gespeichert, Wasserkosten-Nav immer sichtbar
#   0.10.0 — Einheitliches Kategoriensystem (§2 BetrKV): globale WEG_KATEGORIEN für Buchhaltung
#             + Nebenkosten; NebenkostenPage komplett neu: §28 WEG Eigentümer-Abrechnung aus
#             Zahlungen (Anteil nach MEA), §556 BGB Mieter-Abrechnung (Anteil nach Wohnfläche),
#             Wirtschaftsplan (neue Tabelle + Soll/Ist-Vergleich); wirtschaftsplan-Tabelle in DB
#   0.10.1 — 4-Rollen-Review: parse_float() None-sicher (crashte bei NULL-Werten in flaeche_qm
#             + nebenkosten_vorauszahlung); try/finally in _wp_delete; Index wirtschaftsplan(jahr);
#             Soll/Ist-Status "– kein Soll" wenn kein Soll-Wert geplant (statt fälschlicherweise
#             "⚠ Überzogen"); Issues #23-26 angelegt
#   0.11.0 — Issues #21, #26, #27, #28, #29 umgesetzt:
#             #27 Mietende (auszug) in MieterDialog, MieterPage, §556 BGB aktive-Mieter-Filter;
#             #21 Leere Tabellen zeigen Hinweistext "(Keine Einträge vorhanden)";
#             #26 Soll/Ist-Dialog: Fehlermeldung wenn keine Wirtschaftsplan-Daten vorhanden;
#             #29 Rechnungs-Upload: Beleg-Datei-Picker in ZahlungDialog, beleg_dateipfad-Spalte,
#                 📎-Indikator in Buchungstabelle, "Beleg öffnen"-Button;
#             #28 Einstellungen: 4-Tab-Layout (Stammdaten, Bankdaten, Speicherpfade, KI-Administration)
#                 mit Ollama-Integration und Anbieter-Auswahl
APP_VERSION = "0.16.1"
APP_NAME    = "Hausverwaltung"
APP_AUTHOR  = "WEG Welte Rapp Bilgery"
#   0.16.0 — Issues #38–#41:
#             #38 Default Speicherpfade: get_pfad() anlegt Unterordner automatisch,
#                 _get_default_import_dir, DokumentePage, EinstellungenPage.
#             #39 Aufteilungstypen: Benutzerdefiniert kennzeichnen (ist_benutzerdefiniert),
#                 aktiv/inaktiv Status, Typ "Ausgewählte Wohnungen" mit Multi-Select,
#                 Super-Admin kann löschen (mit Verwendungs-Prüfung).
#             #40 Buchungsregeln-Keywords: keywords-Spalte, vorschlag_kategorie nutzt Keywords,
#                 Keyword-Suche mit 0.65 Konfidenz.
#             #41 Wirtschaftsplan-Vorschläge: aus Vorjahres-Istdaten generieren,
#                 WirtschaftsplanVorschlagDialog mit Preisanpassung pro Position + global.
#   0.15.1 — Bugfix Buchhaltung Ordner-Struktur:
#   0.13.1 — Bugfix KI-Assistent Ollama-Integration:
#             _api_call_thread() liest ki_anbieter und routet zu _anthropic_call_thread()
#             oder _ollama_call_thread() (POST /api/chat, stream=false);
#             Modell-Dropdown zeigt Claude-Modelle ODER das konfigurierte Ollama-Modell;
#             _provider_aktualisieren() synct UI mit Einstellungen inkl. Verbindungstest;
#             "🔄 Provider neu laden"-Button; Header- und Warte-Text anbieterabhängig;
#   0.14.0 — Issues #33, #34, #35, #36:
#             #33 KI-Modell-Dropdown: zeigt ALLE konfigurierten Modelle beider Anbieter;
#                 _alle_ki_modelle() + _parse_modell_auswahl(); Config-Key ki_aktives_modell;
#                 Routing per Dropdown-Auswahl statt ki_anbieter-Schlüssel;
#             #34 KI-Zugriffssteuerung in Rollen & Rechte: neuer Bereich "KI-Administration";
#                 "Zugriff nach Rollen"-Feld aus Einstellungen entfernt; KI-Admin-Tab prüft
#                 hat_recht("KI-Administration","lesen"); init_db() vergibt Default-Rechte;
#             #35 KI-Rechnungsanalyse: "🤖 KI-Analyse starten"-Button in ZahlungDialog;
#                 liest PDF/Bild, sendet an KI, parst JSON-Antwort, befüllt Formularfelder;
#                 neues Feld "Rechnungssteller"; DB-Spalte zahlungen.rechnungssteller;
#                 Dateiname-Generierung YYYY-MM-TT_Rechnungssteller_N; Lernfunktion;
#             #36 Custom-Kategorien: BuchhaltungPage._sync_kategorien_from_config() lädt
#                 custom_kategorien aus Config bei Init — Buchung-Dialog und Kostenarten-Tab
#                 zeigen jetzt dieselben Kategorien;
#             SQL-Injection WartungPage._load() behoben (parametrisiertes Query);
#   0.14.1 — Issue #37:
#             NameError KiAssistentPage → KIAssistentPage in _ki_analyse_starten behoben;
#             Modell-Dropdown direkt im ZahlungDialog (Auswahl vor globalem Default);
#             Beschreibungsfeld wird bei KI-Analyse nicht überschrieben wenn bereits gefüllt;
#   0.15.0 — Smart-Workflow Komplettimplementierung (Phase 1-9):
#             Phase 1: DB-Schema (verbrauchsdaten, abrechnungen, abrechnung_positionen, abrechnung_anteile)
#             Phase 2: Konfidenz-Scoring in vorschlag_kategorie (4. Rückgabewert)
#             Phase 3: Status-Pipeline im Kontoauszug (importiert/vorschlag/uebernommen/abgerechnet)
#             Phase 4: Abrechnungsrelevanz in ZahlungDialog (Checkbox + abrechnungsjahr-Feld)
#             Phase 5: Verbrauchsdaten-Tab in NebenkostenPage (HeizKV-Unterstützung)
#             Phase 6: pro_rata_temporis-Funktion für zeitanteilige Mieterabrechnung
#             Phase 7: Abrechnungs-Snapshot (_abrechnung_feststellen, _show_abrechnungen)
#             Phase 8: Dashboard-KPIs für Buchungs-/Abrechnungsstatus
#   0.13.0 — Issues #19, #20, #22, #30, #31, #32:
#             #19 Wohngeld Soll/Ist: neuer Tab "💰 Wohngeld Soll/Ist" in BuchhaltungPage;
#                 KPI-Zeile + Tabelle pro Eigentümer (MEA-Soll vs. gez. Hausgeld, Saldo, Status);
#             #20 MEA-Sync: neue Funktion sync_mea_eigentuemer(); wird nach Wohnungs-Neu/Edit
#                 und bei init_db() aufgerufen — eigentuemer.anteil_prozent immer aus
#                 SUM(wohnungen.mea_tausendstel)/10 berechnet; kein veralteter Wert mehr;
#             #22 Jahresabschluss-PDF: "📄 Jahresabschluss"-Button in BuchhaltungPage-Header;
#                 reportlab-PDF mit Einnahmen/Ausgaben nach Kategorie + monatliche Übersicht;
#                 Jahr per Dialog eingeben; Farben: Einnahmen grün, Ausgaben rot;
#             #30 Backup/Restore: "💾 Backup erstellen" + "♻ Wiederherstellen" in Einstellungen
#                 Tab Speicherpfade; Backup kopiert DB mit Timestamp; Restore legt Auto-Backup
#                 der alten DB an bevor sie ersetzt wird;
#             #31 CSV-Export verbessert: Jahresfilter per Dialog, Typfilter aus aktuellem Filter,
#                 Dateiname enthält Jahres-/Typ-Info; Anzahl exportierter Buchungen im Info-Dialog;
#             #32 Dashboard-Erweiterung: 6 KPI-Karten (vorher 4); neu: Jahressaldo + Rücklagen
#                 (kumuliert); Jahressaldo rot wenn negativ;
#   0.12.0 — Issues #23, #24, #25:
#             #23 §28 WEG: Erhaltungsrücklage und Sonderumlage als "Rücklage-Einlage"
#                 separat ausgewiesen (neues WEG_EINLAGE_KATEGORIEN-Set); KPI zeigt
#                 Bewirtschaftungskosten / Rücklage-Einlage getrennt; Typ-Spalte in
#                 Kategorie-Tabelle; Einlage-Zeilen blau hervorgehoben;
#             #24 §556 BGB: Alle Wohnungen inkl. Leerstand in Flächenberechnung;
#                 LEFT JOIN mit Bedingung im ON-Teil statt WHERE-Filter; Leerstand-
#                 Wohnungen als "⚠ Leerstand (Eigentümer)" markiert (golden); Leerstand-
#                 KPI-Karte zeigt Anzahl freier Wohnungen;
#             #25 PDF-Export: reportlab-basierter PDF-Export für §28 WEG Jahresabrechnung,
#                 §556 BGB Betriebskostenabrechnung und Wirtschaftsplan Soll/Ist-Vergleich;
#                 "📄 PDF Export"-Buttons in allen drei NebenkostenPage-Tabs;


def _git_info() -> dict:
    """Liest Git-Informationen (Commit, Branch, Tag) aus dem Repository."""
    info = {"commit": "–", "commit_short": "–", "branch": "–",
            "tag": "–", "date": "–", "dirty": False}
    try:
        repo_dir = Path(__file__).parent
        def _run(cmd):
            return subprocess.check_output(
                cmd, cwd=repo_dir, stderr=subprocess.DEVNULL
            ).decode().strip()

        info["commit"] = _run(["git", "rev-parse", "HEAD"])
        info["commit_short"] = _run(["git", "rev-parse", "--short", "HEAD"])
        info["branch"] = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        info["date"] = _run(["git", "log", "-1", "--format=%ci"])[:10]
        # Nächster Tag zum aktuellen Commit (oder letzter Tag)
        try:
            info["tag"] = _run(["git", "describe", "--tags", "--abbrev=0"])
        except Exception:
            info["tag"] = "–"
        # Dirty check (uncommitted changes)
        try:
            status = _run(["git", "status", "--porcelain"])
            info["dirty"] = bool(status)
        except Exception:
            pass
    except Exception:
        pass
    return info


DB_PATH = Path.home() / "hausverwaltung.db"

# ── Konfiguration ───────────────────────────────────────────────────────────

CONFIG_PATH = Path(__file__).parent / "einstellungen.json"
APP_DIR = Path(__file__).parent  # Verzeichnis der Programmdatei (#38)

def load_config():
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_config(cfg: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

def get_pfad(schluessel: str, standard_unterordner: str) -> str:
    """Gibt den konfigurierten Pfad zurück oder legt einen Standard-Unterordner an.

    Wenn unter schluessel kein Pfad hinterlegt ist, wird automatisch ein Unterordner
    im Programmverzeichnis angelegt, gespeichert und zurückgegeben (#38).
    """
    cfg = load_config()
    pfad = cfg.get(schluessel, "")
    if pfad and os.path.isdir(pfad):
        return pfad
    # Standard-Unterordner anlegen
    standard = APP_DIR / standard_unterordner
    try:
        standard.mkdir(parents=True, exist_ok=True)
        cfg[schluessel] = str(standard)
        save_config(cfg)
    except Exception:
        pass
    return str(standard)

# ── Berechtigungen ──────────────────────────────────────────────────────────

_CURRENT_USER = None  # Set after login

def hat_recht(bereich: str, aktion: str = "lesen") -> bool:
    """Prüft ob der aktuelle Benutzer ein Recht für bereich/aktion hat."""
    global _CURRENT_USER
    if not _CURRENT_USER:
        return False
    conn = get_db()
    user = conn.execute("SELECT * FROM benutzer WHERE id=?", (_CURRENT_USER["id"],)).fetchone()
    if not user:
        conn.close(); return False
    u = dict(user)
    if not u.get("rolle_id"):
        conn.close(); return False
    rolle = conn.execute("SELECT * FROM rollen WHERE id=? AND aktiv=1", (u["rolle_id"],)).fetchone()
    if not rolle:
        conn.close(); return False
    if rolle["ist_superadmin"]:
        conn.close(); return True
    recht = conn.execute("SELECT * FROM rechte WHERE rolle_id=? AND bereich=?",
                         (rolle["id"], bereich)).fetchone()
    conn.close()
    if not recht: return False
    if aktion in ("lesen", "schreiben", "loeschen"):
        return bool(recht[aktion])
    return False

# ── Farben ──────────────────────────────────────────────────────────────────

BG          = "#F7F5F0"
BG_SIDEBAR  = "#1C2B3A"
BG_CARD     = "#FFFFFF"
BG_INPUT    = "#F0EDE8"
ACCENT      = "#C8A96E"
ACCENT2     = "#2E6DA4"
SUCCESS     = "#3A7D44"
DANGER      = "#C0392B"
WARNING     = "#D4820A"
TEXT        = "#1A1A2E"
TEXT_LIGHT  = "#6B7280"
TEXT_WHITE  = "#F0EDE8"
BORDER      = "#DDD8D0"
SIDEBAR_FG  = "#A8B8C8"
SIDEBAR_ACT = "#C8A96E"

FONT_H1     = ("Georgia", 18, "bold")
FONT_H2     = ("Georgia", 13, "bold")
FONT_H3     = ("Georgia", 11, "bold")
FONT_BODY   = ("Segoe UI", 10)
FONT_SMALL  = ("Segoe UI", 9)
FONT_MONO   = ("Consolas", 9)
FONT_NAV    = ("Segoe UI Semibold", 10)

# ── Einheitliches Kategoriensystem §2 BetrKV / WEG ────────────────────────────
# Zentrale Quelle für Buchhaltung, Nebenkosten und Wirtschaftsplan
# Format: name → (ober_gruppe, umlagefaehig_auf_mieter, empfohlener_schluessel)
WEG_KATEGORIEN = {
    # Laufende Betriebskosten – umlagefähig §2 BetrKV
    "Heizung":                    ("Laufende Betriebskosten", True,  "Verbrauch/Wohnfläche"),
    "Warmwasser":                 ("Laufende Betriebskosten", True,  "Verbrauch"),
    "Wasser/Abwasser":            ("Laufende Betriebskosten", True,  "Verbrauch/Wohnfläche"),
    "Allgemeinstrom":             ("Laufende Betriebskosten", True,  "MEA"),
    "Aufzug":                     ("Laufende Betriebskosten", True,  "MEA/Wohneinheiten"),
    "Straßenreinigung":           ("Laufende Betriebskosten", True,  "MEA/Wohneinheiten"),
    "Müllabfuhr":                 ("Laufende Betriebskosten", True,  "MEA/Wohneinheiten"),
    "Gebäudereinigung":           ("Laufende Betriebskosten", True,  "MEA/Fläche"),
    "Ungezieferbekämpfung":       ("Laufende Betriebskosten", True,  "MEA"),
    "Gartenpflege":               ("Laufende Betriebskosten", True,  "MEA/Fläche"),
    "Beleuchtung":                ("Laufende Betriebskosten", True,  "MEA"),
    "Schornsteinreinigung":       ("Laufende Betriebskosten", True,  "Wohneinheiten"),
    "Hausmeister":                ("Laufende Betriebskosten", True,  "MEA/Fläche"),
    "Winterdienst":               ("Laufende Betriebskosten", True,  "MEA/Fläche"),
    # Versicherungen – umlagefähig §2 Nr. 13 BetrKV
    "Wohngebäudeversicherung":    ("Versicherungen",           True,  "MEA"),
    "Haftpflichtversicherung":    ("Versicherungen",           True,  "MEA"),
    "Elementar-/Glasversicherung":("Versicherungen",           True,  "MEA"),
    # Verwaltungskosten – NICHT umlagefähig auf Mieter (§26 WEG)
    "Verwaltervergütung":         ("Verwaltungskosten",        False, "MEA"),
    "Bankgebühren":               ("Verwaltungskosten",        False, "MEA"),
    "Porto/Telefon":              ("Verwaltungskosten",        False, "MEA"),
    "Rechts-/Prozesskosten":      ("Verwaltungskosten",        False, "MEA"),
    # Instandhaltung – §28 WEG Eigentümer, nicht umlagefähig
    "Reparaturen":                ("Instandhaltung & Wartung", False, "MEA"),
    "Wartungsverträge":           ("Instandhaltung & Wartung", False, "MEA"),
    "Sanierung":                  ("Instandhaltung & Wartung", False, "MEA"),
    # Finanzplanung & Rücklagen – Einlagen (nicht Betriebskosten, §28 WEG separat ausweisen)
    "Erhaltungsrücklage":         ("Finanzplanung & Rücklagen",False, "MEA"),
    "Sonderumlage":               ("Finanzplanung & Rücklagen",False, "MEA"),
    # Einnahmen
    "Hausgeld":                   ("Einnahmen",                False, "–"),
    "Miete":                      ("Einnahmen",                False, "–"),
    "Nebenkosten-Vorauszahlung":  ("Einnahmen",                False, "–"),
    # Sonstiges
    "Sonstiges":                  ("Sonstiges",                False, "–"),
    "Kategorie offen":            ("Offen",                    False, "–"),
}
# Flache Liste für Combo-Dropdowns
WEG_KATEGORIEN_LISTE = list(WEG_KATEGORIEN.keys())
# Nur umlagefähige Kategorien (§556 BGB Mieter-Abrechnung)
WEG_KATEGORIEN_UMLAGE = [k for k, v in WEG_KATEGORIEN.items() if v[1]]
# Rücklage-Einlagen (§28 WEG: separat ausweisen, nicht als Betriebskosten)
WEG_EINLAGE_KATEGORIEN = {"Erhaltungsrücklage", "Sonderumlage"}

# ── Datenbank ────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # Referentielle Integrität erzwingen
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript("""
CREATE TABLE IF NOT EXISTS eigentuemer (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    telefon TEXT,
    anteil_prozent REAL DEFAULT 33.33,
    einheit TEXT,
    notizen TEXT
);
CREATE TABLE IF NOT EXISTS mieter (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    telefon TEXT,
    einheit TEXT,
    einzug DATE,
    auszug DATE,
    kaltmiete REAL,
    nebenkosten_vorauszahlung REAL,
    kaution REAL,
    notizen TEXT
);
CREATE TABLE IF NOT EXISTS zahlungen (
    id INTEGER PRIMARY KEY,
    datum DATE NOT NULL,
    betrag REAL NOT NULL,
    typ TEXT NOT NULL,
    kategorie TEXT,
    mieter_id INTEGER,
    eigentuemer_id INTEGER,
    beschreibung TEXT,
    belegnr TEXT,
    erstellt_am DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS kontoauszug (
    id INTEGER PRIMARY KEY,
    datum DATE,
    buchungstext TEXT,
    betrag REAL,
    saldo REAL,
    zugeordnet INTEGER DEFAULT 0,
    zahlung_id INTEGER,
    importiert_am DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS wartung (
    id INTEGER PRIMARY KEY,
    titel TEXT NOT NULL,
    beschreibung TEXT,
    prioritaet TEXT DEFAULT 'Mittel',
    status TEXT DEFAULT 'Offen',
    gemeldet_von TEXT,
    einheit TEXT,
    erstellt_am DATE,
    erledigt_am DATE,
    kosten REAL,
    notizen TEXT
);
CREATE TABLE IF NOT EXISTS dokumente (
    id INTEGER PRIMARY KEY,
    titel TEXT NOT NULL,
    kategorie TEXT,
    dateiname TEXT,
    dateipfad TEXT,
    beschreibung TEXT,
    erstellt_am DATE,
    bezug_typ TEXT,
    bezug_id INTEGER
);
CREATE TABLE IF NOT EXISTS nachrichten (
    id INTEGER PRIMARY KEY,
    datum DATETIME DEFAULT CURRENT_TIMESTAMP,
    von TEXT,
    an TEXT,
    betreff TEXT NOT NULL,
    inhalt TEXT,
    gelesen INTEGER DEFAULT 0,
    prioritaet TEXT DEFAULT 'Normal'
);
CREATE TABLE IF NOT EXISTS nebenkosten (
    id INTEGER PRIMARY KEY,
    jahr INTEGER NOT NULL,
    monat INTEGER,
    kategorie TEXT NOT NULL,
    betrag REAL NOT NULL,
    umlageschluessel TEXT DEFAULT 'Wohnflaeche',
    notizen TEXT
);
CREATE TABLE IF NOT EXISTS wirtschaftsplan (
    id INTEGER PRIMARY KEY,
    jahr INTEGER NOT NULL,
    kategorie TEXT NOT NULL,
    betrag_soll REAL DEFAULT 0,
    notizen TEXT,
    UNIQUE(jahr, kategorie)
);
CREATE TABLE IF NOT EXISTS wohnungen (
    id INTEGER PRIMARY KEY,
    bezeichnung TEXT NOT NULL,
    etage TEXT,
    flaeche_qm REAL,
    zimmer INTEGER,
    eigentuemer_id INTEGER,
    mieter_id INTEGER,
    miteigentumsanteil REAL,
    baujahr INTEGER,
    notizen TEXT
);
CREATE TABLE IF NOT EXISTS aufteilungen (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    beschreibung TEXT,
    typ TEXT DEFAULT 'Wohnfläche',
    bezug TEXT,
    wert REAL,
    notizen TEXT
);
CREATE TABLE IF NOT EXISTS aufteilung_wohnungen (
    id INTEGER PRIMARY KEY,
    aufteilung_id INTEGER NOT NULL,
    wohnung_id INTEGER NOT NULL,
    UNIQUE(aufteilung_id, wohnung_id),
    FOREIGN KEY (aufteilung_id) REFERENCES aufteilungen(id)
);
CREATE TABLE IF NOT EXISTS buchungsregeln (
    id INTEGER PRIMARY KEY,
    muster TEXT NOT NULL,
    kategorie TEXT,
    typ TEXT DEFAULT 'Einnahme',
    konto_typ TEXT DEFAULT 'Girokonto',
    treffer INTEGER DEFAULT 0,
    ist_korrektur INTEGER DEFAULT 0,
    erstellt_am DATE DEFAULT CURRENT_DATE
);
CREATE TABLE IF NOT EXISTS benutzer (
    id INTEGER PRIMARY KEY,
    benutzername TEXT NOT NULL UNIQUE,
    passwort_hash TEXT NOT NULL,
    rolle TEXT DEFAULT 'Benutzer',
    aktiv INTEGER DEFAULT 1,
    erstellt_am DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS rollen (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    beschreibung TEXT,
    ist_superadmin INTEGER DEFAULT 0,
    aktiv INTEGER DEFAULT 1,
    erstellt_am DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS rechte (
    id INTEGER PRIMARY KEY,
    rolle_id INTEGER NOT NULL,
    bereich TEXT NOT NULL,
    lesen INTEGER DEFAULT 1,
    schreiben INTEGER DEFAULT 1,
    loeschen INTEGER DEFAULT 0,
    FOREIGN KEY (rolle_id) REFERENCES rollen(id)
);
""")
    # Wasserkosten-Tabellen
    c.executescript("""
CREATE TABLE IF NOT EXISTS wasserkosten_positionen (
    id            INTEGER PRIMARY KEY,
    jahr          INTEGER NOT NULL,
    typ           TEXT    NOT NULL,
    verbrauch_m3  REAL    DEFAULT 0,
    kosten_eur    REAL    DEFAULT 0,
    ablesedatum   DATE,
    erstellt_am   DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS wasserkosten_wohnungsdaten (
    id                      INTEGER PRIMARY KEY,
    jahr                    INTEGER NOT NULL,
    wohnung_bezeichnung     TEXT    NOT NULL,
    eigentuemer             TEXT,
    von_datum               DATE,
    bis_datum               DATE,
    personen                INTEGER DEFAULT 0,
    spuelmaschinen          INTEGER DEFAULT 0,
    waschmaschinen          INTEGER DEFAULT 0,
    trockner_wasserkuehlung INTEGER DEFAULT 0,
    monate                  REAL    DEFAULT 12,
    bemerkung               TEXT,
    erstellt_am             DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS wasserkosten_vorjahr (
    id               INTEGER PRIMARY KEY,
    jahr             INTEGER NOT NULL,
    eigentuemer      TEXT    NOT NULL,
    wasserkosten_eur REAL    DEFAULT 0
);
""")
    # Neue Tabellen für Smart Workflow
    c.executescript("""
CREATE TABLE IF NOT EXISTS verbrauchsdaten (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wohnung_id INTEGER NOT NULL,
    kategorie TEXT NOT NULL,
    jahr INTEGER NOT NULL,
    zaehlerstand_anfang REAL DEFAULT 0,
    zaehlerstand_ende REAL DEFAULT 0,
    einheit TEXT DEFAULT 'kWh',
    ablesedatum DATE,
    notizen TEXT,
    UNIQUE(wohnung_id, kategorie, jahr)
);
CREATE TABLE IF NOT EXISTS abrechnungen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    jahr INTEGER NOT NULL,
    typ TEXT NOT NULL,
    status TEXT DEFAULT 'Entwurf',
    erstellt_am DATETIME DEFAULT CURRENT_TIMESTAMP,
    festgestellt_am DATETIME,
    festgestellt_von INTEGER,
    pdf_pfad TEXT,
    notizen TEXT,
    UNIQUE(jahr, typ)
);
CREATE TABLE IF NOT EXISTS abrechnung_positionen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    abrechnung_id INTEGER NOT NULL,
    zahlung_id INTEGER NOT NULL,
    kategorie TEXT NOT NULL,
    betrag REAL NOT NULL,
    umlageschluessel TEXT DEFAULT 'Wohnflaeche',
    FOREIGN KEY (abrechnung_id) REFERENCES abrechnungen(id)
);
CREATE TABLE IF NOT EXISTS abrechnung_anteile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    abrechnung_id INTEGER NOT NULL,
    eigentuemer_id INTEGER,
    mieter_id INTEGER,
    kategorie TEXT NOT NULL,
    anteil_faktor REAL DEFAULT 0,
    betrag_anteil REAL DEFAULT 0,
    vorauszahlung REAL DEFAULT 0,
    FOREIGN KEY (abrechnung_id) REFERENCES abrechnungen(id)
);
CREATE TABLE IF NOT EXISTS ista_abrechnungen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_datum DATETIME DEFAULT CURRENT_TIMESTAMP,
    abrechnungsjahr INTEGER NOT NULL,
    abrechnungszeitraum_von DATE,
    abrechnungszeitraum_bis DATE,
    pdf_pfad TEXT,
    gesamtkosten_heizung REAL DEFAULT 0,
    gesamtkosten_warmwasser REAL DEFAULT 0,
    gesamtkosten_gesamt REAL DEFAULT 0,
    objekt_adresse TEXT,
    ista_auftragsnummer TEXT,
    notizen TEXT,
    erstellt_am DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS ista_positionen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    abrechnung_id INTEGER NOT NULL,
    wohnung_id INTEGER,
    ista_einheit_nr TEXT,
    ista_einheit_bezeichnung TEXT,
    mieter_name TEXT,
    hke REAL DEFAULT 0,
    hke_anteil_pct REAL DEFAULT 0,
    warmwasser_m3 REAL DEFAULT 0,
    warmwasser_anteil_pct REAL DEFAULT 0,
    heizkosten_grundkosten REAL DEFAULT 0,
    heizkosten_verbrauchskosten REAL DEFAULT 0,
    heizkosten_gesamt REAL DEFAULT 0,
    warmwasserkosten_gesamt REAL DEFAULT 0,
    gesamtkosten REAL DEFAULT 0,
    vorauszahlung REAL DEFAULT 0,
    nachzahlung_guthaben REAL DEFAULT 0,
    als_zahlung_uebernommen INTEGER DEFAULT 0,
    FOREIGN KEY (abrechnung_id) REFERENCES ista_abrechnungen(id)
);
CREATE INDEX IF NOT EXISTS idx_ista_positionen_abr ON ista_positionen(abrechnung_id);
CREATE INDEX IF NOT EXISTS idx_ista_positionen_wohnung ON ista_positionen(wohnung_id);
""")
    conn.commit()
    # Indizes für häufig abgefragte Spalten (IF NOT EXISTS = idempotent)
    for idx_sql in [
        "CREATE INDEX IF NOT EXISTS idx_zahlungen_datum   ON zahlungen(datum)",
        "CREATE INDEX IF NOT EXISTS idx_zahlungen_typ     ON zahlungen(typ)",
        "CREATE INDEX IF NOT EXISTS idx_zahlungen_kat     ON zahlungen(kategorie)",
        "CREATE INDEX IF NOT EXISTS idx_kontoauszug_datum ON kontoauszug(datum)",
        "CREATE INDEX IF NOT EXISTS idx_kontoauszug_uebernommen ON kontoauszug(als_buchung_uebernommen)",
        "CREATE INDEX IF NOT EXISTS idx_nachrichten_gelesen ON nachrichten(gelesen)",
        "CREATE INDEX IF NOT EXISTS idx_wohnungen_eigentuemer ON wohnungen(eigentuemer_id)",
        "CREATE INDEX IF NOT EXISTS idx_mieter_wohnung ON mieter(wohnung_id)",
        "CREATE INDEX IF NOT EXISTS idx_wirtschaftsplan_jahr ON wirtschaftsplan(jahr)",
        "CREATE INDEX IF NOT EXISTS idx_zahlungen_abrechnung ON zahlungen(abrechnungsrelevant, abrechnungsjahr)",
        "CREATE INDEX IF NOT EXISTS idx_kontoauszug_status ON kontoauszug(buchung_status)",
        "CREATE INDEX IF NOT EXISTS idx_abrechnung_positionen ON abrechnung_positionen(abrechnung_id)",
        "CREATE INDEX IF NOT EXISTS idx_verbrauchsdaten ON verbrauchsdaten(wohnung_id, kategorie, jahr)",
    ]:
        try:
            c.execute(idx_sql)
        except Exception:
            pass
    conn.commit()
    # Schema-Migration: neue Spalten hinzufügen falls noch nicht vorhanden
    for sql in [
        "ALTER TABLE mieter ADD COLUMN vorname TEXT",
        "ALTER TABLE eigentuemer ADD COLUMN vorname TEXT",
        "ALTER TABLE zahlungen ADD COLUMN konto_typ TEXT DEFAULT 'Girokonto'",
        "ALTER TABLE kontoauszug ADD COLUMN iban TEXT",
        "ALTER TABLE kontoauszug ADD COLUMN kategorie_vorschlag TEXT",
        "ALTER TABLE kontoauszug ADD COLUMN als_buchung_uebernommen INTEGER DEFAULT 0",
        "ALTER TABLE kontoauszug ADD COLUMN falsch_zugeordnet INTEGER DEFAULT 0",
        "ALTER TABLE kontoauszug ADD COLUMN konto_typ TEXT DEFAULT 'Unbekannt'",
        "ALTER TABLE eigentuemer ADD COLUMN strasse TEXT",
        "ALTER TABLE eigentuemer ADD COLUMN plz TEXT",
        "ALTER TABLE eigentuemer ADD COLUMN ort TEXT",
        "ALTER TABLE eigentuemer ADD COLUMN land TEXT DEFAULT 'Deutschland'",
        "ALTER TABLE eigentuemer ADD COLUMN iban TEXT",
        "ALTER TABLE mieter ADD COLUMN strasse TEXT",
        "ALTER TABLE mieter ADD COLUMN plz TEXT",
        "ALTER TABLE mieter ADD COLUMN ort TEXT",
        "ALTER TABLE mieter ADD COLUMN land TEXT DEFAULT 'Deutschland'",
        "ALTER TABLE mieter ADD COLUMN iban TEXT",
        "ALTER TABLE mieter ADD COLUMN wohnung_id INTEGER",
        "ALTER TABLE wohnungen ADD COLUMN typ TEXT DEFAULT 'Wohnung'",
        "ALTER TABLE wohnungen ADD COLUMN lage TEXT",
        "ALTER TABLE wohnungen ADD COLUMN nutzflaeche_qm REAL",
        "ALTER TABLE wohnungen ADD COLUMN balkon INTEGER DEFAULT 0",
        "ALTER TABLE wohnungen ADD COLUMN keller TEXT",
        "ALTER TABLE wohnungen ADD COLUMN stellplatz TEXT",
        "ALTER TABLE wohnungen ADD COLUMN heizungsart TEXT DEFAULT 'Zentralheizung'",
        "ALTER TABLE wohnungen ADD COLUMN mea_tausendstel REAL",
        "ALTER TABLE benutzer ADD COLUMN rolle_id INTEGER",
        "ALTER TABLE zahlungen ADD COLUMN status TEXT DEFAULT 'Geprüft'",
        "ALTER TABLE benutzer ADD COLUMN passwort_skip INTEGER DEFAULT 0",
        "ALTER TABLE kontoauszug ADD COLUMN ist_neu INTEGER DEFAULT 1",
        "ALTER TABLE rollen ADD COLUMN passwort_skip INTEGER DEFAULT 0",
        "ALTER TABLE mieter ADD COLUMN personen INTEGER DEFAULT 1",
        "ALTER TABLE mieter ADD COLUMN spuelmaschinen INTEGER DEFAULT 0",
        "ALTER TABLE mieter ADD COLUMN waschmaschinen INTEGER DEFAULT 1",
        "ALTER TABLE mieter ADD COLUMN trockner_wasserkuehlung INTEGER DEFAULT 0",
        "ALTER TABLE zahlungen ADD COLUMN beleg_dateipfad TEXT",
        "ALTER TABLE zahlungen ADD COLUMN rechnungssteller TEXT",  # #35 KI-Erkennung
        "ALTER TABLE zahlungen ADD COLUMN abrechnungsrelevant INTEGER DEFAULT 1",
        "ALTER TABLE zahlungen ADD COLUMN abrechnungsjahr INTEGER",
        "ALTER TABLE zahlungen ADD COLUMN kommentar_abrechnung TEXT",
        "ALTER TABLE buchungsregeln ADD COLUMN betrag_min REAL",
        "ALTER TABLE buchungsregeln ADD COLUMN betrag_max REAL",
        "ALTER TABLE buchungsregeln ADD COLUMN konfidenz REAL DEFAULT 0.5",
        "ALTER TABLE kontoauszug ADD COLUMN buchung_status TEXT DEFAULT 'importiert'",
        "ALTER TABLE wohnungen ADD COLUMN bewohner_anzahl INTEGER DEFAULT 1",
        "ALTER TABLE ista_positionen ADD COLUMN abrechnungszeitraum_von DATE",
        "ALTER TABLE ista_positionen ADD COLUMN abrechnungszeitraum_bis DATE",
        "ALTER TABLE aufteilungen ADD COLUMN aktiv INTEGER DEFAULT 1",  # #39
        "ALTER TABLE aufteilungen ADD COLUMN ist_benutzerdefiniert INTEGER DEFAULT 0",  # #39
        "ALTER TABLE buchungsregeln ADD COLUMN keywords TEXT",  # #40
    ]:
        try:
            c.execute(sql)
            conn.commit()
        except Exception:
            pass
    # Rechte "KI-Assistent" und "KI-Administration" zu allen vorhandenen Rollen hinzufügen (#34 fix)
    for rolle_row in c.execute("SELECT id, ist_superadmin FROM rollen").fetchall():
        for bereich in ("KI-Assistent", "KI-Administration"):
            existing = c.execute("SELECT 1 FROM rechte WHERE rolle_id=? AND bereich=?",
                                 (rolle_row[0], bereich)).fetchone()
            if not existing:
                ist_super = bool(rolle_row[1])
                # KI-Administration: nur Superadmin/Admin; KI-Assistent: alle
                if bereich == "KI-Administration":
                    lesen = 1 if ist_super else 0
                    schreiben = 1 if ist_super else 0
                else:
                    lesen = 1
                    schreiben = 1
                c.execute("INSERT INTO rechte (rolle_id, bereich, lesen, schreiben, loeschen) VALUES (?,?,?,?,0)",
                          (rolle_row[0], bereich, lesen, schreiben))
    conn.commit()
    # Create default admin user if no users exist
    import hashlib
    if not c.execute("SELECT COUNT(*) FROM benutzer").fetchone()[0]:
        pw_hash = hashlib.sha256("admin".encode()).hexdigest()
        c.execute("INSERT INTO benutzer (benutzername, passwort_hash, rolle) VALUES (?, ?, ?)",
                  ("admin", pw_hash, "Admin"))

    # Default roles
    if not c.execute("SELECT COUNT(*) FROM rollen").fetchone()[0]:
        c.execute("INSERT INTO rollen (name, beschreibung, ist_superadmin) VALUES ('Superadmin', 'Vollzugriff – kann nicht gelöscht werden', 1)")
        c.execute("INSERT INTO rollen (name, beschreibung) VALUES ('Administrator', 'Verwaltung ohne Superadmin-Rechte')")
        c.execute("INSERT INTO rollen (name, beschreibung) VALUES ('Benutzer', 'Standardrechte')")
        admin_id = c.execute("SELECT id FROM rollen WHERE name='Administrator'").fetchone()[0]
        benutzer_id = c.execute("SELECT id FROM rollen WHERE name='Benutzer'").fetchone()[0]
        bereiche = ["Übersicht","Eigentümer","Wohnungen","Mieter","Kontoauszug","Buchhaltung",
                    "Wartung","Nebenkosten","Aufteilungen","Nachrichten","Dokumente",
                    "Benutzer","Rollen & Rechte","Einstellungen","KI-Assistent","KI-Administration","Ista-Wärme"]
        for b in bereiche:
            c.execute("INSERT INTO rechte (rolle_id,bereich,lesen,schreiben,loeschen) VALUES (?,?,1,1,1)", (admin_id, b))
            c.execute("INSERT INTO rechte (rolle_id,bereich,lesen,schreiben,loeschen) VALUES (?,?,1,1,0)", (benutzer_id, b))
        c.execute("UPDATE rechte SET lesen=0,schreiben=0,loeschen=0 WHERE rolle_id=? "
                  "AND bereich IN ('Benutzer','Rollen & Rechte','Einstellungen','KI-Administration')", (benutzer_id,))
        conn.commit()
    # Assign Superadmin role to admin user
    sa_role = c.execute("SELECT id FROM rollen WHERE ist_superadmin=1").fetchone()
    if sa_role:
        c.execute("UPDATE benutzer SET rolle_id=? WHERE benutzername='admin' AND (rolle_id IS NULL OR rolle_id=0)", (sa_role[0],))
        conn.commit()

    # Ista-Spezialist-Rolle anlegen (idempotent)
    if not c.execute("SELECT id FROM rollen WHERE name='Ista-Spezialist'").fetchone():
        c.execute(
            "INSERT INTO rollen (name, beschreibung) VALUES (?,?)",
            ("Ista-Spezialist",
             "Profi für Ista-Wärmeabrechnung: Importiert und verwaltet Heizkostenabrechnungen von Ista. "
             "Vollzugriff auf Ista-Wärme, Nebenkosten und Verbrauchsdaten.")
        )
        ista_id = c.execute("SELECT id FROM rollen WHERE name='Ista-Spezialist'").fetchone()[0]
        ista_bereiche = {
            "Übersicht":         (1, 0, 0),
            "Wohnungen":         (1, 0, 0),
            "Mieter":            (1, 0, 0),
            "Nebenkosten":       (1, 1, 1),
            "Ista-Wärme":        (1, 1, 1),
            "Buchhaltung":       (1, 1, 0),
            "Dokumente":         (1, 1, 0),
        }
        for bereich, (l, s, d) in ista_bereiche.items():
            c.execute(
                "INSERT OR IGNORE INTO rechte (rolle_id,bereich,lesen,schreiben,loeschen) VALUES (?,?,?,?,?)",
                (ista_id, bereich, l, s, d)
            )
        conn.commit()
    # Ista-Wärme-Recht zu allen bestehenden Rollen hinzufügen (idempotent)
    for rolle_row in c.execute("SELECT id, ist_superadmin FROM rollen").fetchall():
        if not c.execute("SELECT 1 FROM rechte WHERE rolle_id=? AND bereich='Ista-Wärme'",
                         (rolle_row[0],)).fetchone():
            ist_super = bool(rolle_row[1])
            c.execute(
                "INSERT INTO rechte (rolle_id,bereich,lesen,schreiben,loeschen) VALUES (?,?,?,?,?)",
                (rolle_row[0], "Ista-Wärme", 1, 1 if ist_super else 0, 0)
            )
    conn.commit()

    if not c.execute("SELECT COUNT(*) FROM eigentuemer").fetchone()[0]:
        _insert_demo(c)
    conn.commit()
    sync_mea_eigentuemer(conn)  # #20 MEA-Sync: Bestandsdaten beim Start angleichen
    conn.commit()
    conn.close()

def _insert_demo(c):
    c.executemany("INSERT INTO eigentuemer (name,email,telefon,anteil_prozent,einheit) VALUES (?,?,?,?,?)", [
        ("Hans Müller",   "h.mueller@mail.de", "0201-111111", 40.0, "EG links"),
        ("Petra Schmidt", "p.schmidt@mail.de", "0201-222222", 35.0, "EG rechts"),
        ("Karl Weber",    "k.weber@mail.de",   "0201-333333", 25.0, "OG"),
    ])
    c.executemany("INSERT INTO mieter (name,email,telefon,einheit,einzug,kaltmiete,nebenkosten_vorauszahlung,kaution) VALUES (?,?,?,?,?,?,?,?)", [
        ("Anna Bauer",    "a.bauer@mail.de",   "0201-444444", "EG links Whg 1",  "2022-03-01", 780, 150, 1560),
        ("Tom Fischer",   "t.fischer@mail.de", "0201-555555", "EG links Whg 2",  "2021-06-15", 650, 130, 1300),
        ("Lisa Hoffmann", "l.hoff@mail.de",    "0201-666666", "EG rechts",       "2023-01-01", 920, 180, 1840),
        ("Erik Schulz",   "e.schulz@mail.de",  "0201-777777", "OG Whg 1",        "2020-09-01", 710, 140, 1420),
        ("Maria Klein",   "m.klein@mail.de",   "0201-888888", "OG Whg 2",        "2022-11-15", 760, 150, 1520),
    ])
    today = date.today().isoformat()
    c.executemany("INSERT INTO zahlungen (datum,betrag,typ,kategorie,beschreibung) VALUES (?,?,?,?,?)", [
        (today, 780,  "Einnahme", "Miete",      "Mietzahlung Anna Bauer März"),
        (today, 650,  "Einnahme", "Miete",      "Mietzahlung Tom Fischer März"),
        (today, -320, "Ausgabe",  "Wartung",    "Heizungswartung"),
        (today, -85,  "Ausgabe",  "Verwaltung", "Büromaterial"),
    ])
    c.executemany("INSERT INTO wartung (titel,prioritaet,status,einheit,erstellt_am,kosten) VALUES (?,?,?,?,?,?)", [
        ("Heizung prüfen",       "Hoch",   "Offen",    "Keller", today, None),
        ("Briefkasten defekt",   "Mittel", "In Arbeit","EG",     today, None),
        ("Dachrinne reinigen",   "Niedrig","Erledigt",  "Dach",  today, 180),
    ])
    c.executemany("INSERT INTO nachrichten (von,an,betreff,inhalt,prioritaet) VALUES (?,?,?,?,?)", [
        ("Hans Müller",   "Alle",          "Eigentümerversammlung",  "Nächste Versammlung am 20. April, 19 Uhr.", "Hoch"),
        ("Anna Bauer",    "Hausverwaltung","Heizung kalt",           "Im Bad kommt keine Wärme.", "Normal"),
        ("Petra Schmidt", "Alle",          "Gartenordnung",          "Bitte Grünschnitt am Wochenende.", "Normal"),
    ])

# ── Hilfsfunktionen ──────────────────────────────────────────────────────────

def parse_float(val) -> float:
    """Konvertiert Zahl-Strings mit deutschem Komma ('334,69') oder Punkt ('334.69') zu float.
    Gibt 0.0 zurück bei None oder leerem String (kein ValueError)."""
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if not s:
        return 0.0
    return float(s.replace(",", "."))

def fmt_euro(val):
    try:
        return f"{float(val):,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "– €"

def fmt_date(val):
    if not val:
        return "–"
    try:
        return datetime.strptime(str(val)[:10], "%Y-%m-%d").strftime("%d.%m.%Y")
    except:
        return str(val)

def parse_datum(s: str) -> str:
    """Normalisiert Datumseingabe auf ISO JJJJ-MM-TT.
    Akzeptiert: JJJJ-MM-TT, TT.MM.JJJJ, TT/MM/JJJJ
    """
    s = (s or "").strip()
    if not s:
        return ""
    if re.match(r'^\d{4}-\d{2}-\d{2}$', s):
        return s
    m = re.match(r'^(\d{1,2})[./](\d{1,2})[./](\d{4})$', s)
    if m:
        return f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"
    return s

def sync_mea_eigentuemer(conn=None):
    """#20 MEA-Sync: Berechnet eigentuemer.anteil_prozent aus SUM(wohnungen.mea_tausendstel) / 10.
    Wird nach jedem Wohnungs-Speichern aufgerufen, um Konsistenz sicherzustellen.
    conn: optionale bestehende Verbindung (wird NICHT geschlossen); None → eigene Verbindung."""
    own_conn = conn is None
    if own_conn:
        conn = get_db()
    try:
        rows = conn.execute(
            "SELECT eigentuemer_id, SUM(mea_tausendstel) as mea_sum "
            "FROM wohnungen WHERE eigentuemer_id IS NOT NULL GROUP BY eigentuemer_id"
        ).fetchall()
        for r in rows:
            if r["eigentuemer_id"] and r["mea_sum"] is not None:
                anteil = r["mea_sum"] / 10.0   # ‰ → %
                conn.execute(
                    "UPDATE eigentuemer SET anteil_prozent=? WHERE id=?",
                    (anteil, r["eigentuemer_id"]))
        if own_conn:
            conn.commit()
    finally:
        if own_conn:
            conn.close()

# ── Basis-Widget-Helfer ───────────────────────────────────────────────────────

def make_btn(parent, text, command, color=ACCENT2, fg=TEXT_WHITE, **kw):
    return tk.Button(parent, text=text, command=command,
                     bg=color, fg=fg, relief="flat", bd=0,
                     font=FONT_BODY, padx=12, pady=6,
                     activebackground=ACCENT, activeforeground=TEXT_WHITE,
                     cursor="hand2", **kw)

def make_entry(parent, **kw):
    return tk.Entry(parent, bg=BG_INPUT, fg=TEXT, relief="flat",
                    insertbackground=ACCENT2, font=FONT_BODY, bd=0, **kw)

def make_label(parent, text, style="body", **kw):
    fonts  = {"h1": FONT_H1, "h2": FONT_H2, "h3": FONT_H3,
              "body": FONT_BODY, "small": FONT_SMALL, "mono": FONT_MONO}
    colors = {"h1": TEXT, "h2": TEXT, "h3": TEXT,
              "body": TEXT, "small": TEXT_LIGHT, "mono": TEXT}
    return tk.Label(parent, text=text, bg=BG_CARD,
                    fg=kw.pop("fg", colors.get(style, TEXT)),
                    font=fonts.get(style, FONT_BODY), **kw)

def section_header(parent, title, btn_text=None, btn_cmd=None):
    row = tk.Frame(parent, bg=BG_CARD)
    row.pack(fill="x", padx=20, pady=(18, 6))
    tk.Label(row, text=title, bg=BG_CARD, fg=TEXT, font=FONT_H2).pack(side="left")
    if btn_text:
        make_btn(row, btn_text, btn_cmd).pack(side="right")
    tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=20)

# ── Tabellen-Widget ───────────────────────────────────────────────────────────

def make_table(parent, columns, height=12):
    style = ttk.Style()
    style.configure("HV.Treeview",
                    background=BG_CARD, fieldbackground=BG_CARD,
                    foreground=TEXT, rowheight=28, font=FONT_BODY, borderwidth=0)
    style.configure("HV.Treeview.Heading",
                    background=BG_INPUT, foreground=TEXT_LIGHT,
                    font=("Segoe UI Semibold", 9), relief="flat", borderwidth=0)
    style.map("HV.Treeview",
              background=[("selected", ACCENT2)],
              foreground=[("selected", TEXT_WHITE)])
    frame = tk.Frame(parent, bg=BG_CARD)
    tree  = ttk.Treeview(frame, columns=columns, show="headings",
                         height=height, style="HV.Treeview")
    vsb   = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")
    return frame, tree

def tree_empty_hint(tree, text="(Keine Einträge vorhanden)"):
    """Zeigt einen Hinweis-Eintrag, wenn die Tabelle leer ist."""
    if not tree.get_children():
        cols = tree["columns"]
        vals = [text] + [""] * (len(cols) - 1)
        tree.insert("", "end", iid="__empty__", values=vals, tags=("empty",))
        tree.tag_configure("empty", foreground=TEXT_LIGHT)

# ── Dialog-Basis ──────────────────────────────────────────────────────────────

# ── Buchhaltung-Intelligenz (Lernfähiges Buchungssystem) ──────────────────────

# Füllwörter die bei der Buchungsregel-Erstellung und -Suche ignoriert werden
FUELLWOERTER = {
    "der", "die", "das", "den", "dem", "des", "ein", "eine", "einen", "einem", "einer",
    "und", "oder", "von", "vom", "zum", "zur", "auf", "aus", "bei", "mit", "nach",
    "über", "unter", "für", "gegen", "durch", "an", "in", "im", "am", "um",
    "ist", "sind", "hat", "haben", "wird", "werden", "wurde", "wurden",
    "gmbh", "ag", "kg", "ohg", "mbh", "ug", "e.v.", "co", "nr", "ggmbh",
    "ref", "datum", "kto", "blz", "bic", "iban", "end-to-end",
}

def _bereinige_text(text: str) -> str:
    """Entfernt Füllwörter und normalisiert Text für besseres Matching."""
    words = text.lower().split()
    return " ".join(w for w in words if w not in FUELLWOERTER and len(w) > 2)

def vorschlag_kategorie(buchungstext: str, betrag: float = None) -> tuple:
    """Gibt (kategorie, typ, konto_typ, konfidenz) zurück basierend auf gelernten Regeln.

    Konfidenz-Stufen:
    - 0.95: Exakter Treffer + Betrag im erlaubten Bereich
    - 0.85: Exakter Text-Treffer, kein Betragsfilter
    - 0.70: Auftraggeber-Treffer (bereinigt)
    - 0.50: Keyword-Treffer im Verwendungszweck
    - 0.00: Kein Treffer
    """
    if not buchungstext:
        return "", "Einnahme", "Wohngeldkonto", 0.0
    conn = get_db()
    try:
        regeln = conn.execute(
            "SELECT * FROM buchungsregeln ORDER BY ist_korrektur DESC, treffer DESC, konfidenz DESC"
        ).fetchall()
    finally:
        conn.close()

    text_lower = buchungstext.lower()
    if "||" in buchungstext:
        auftraggeber, vzweck = buchungstext.split("||", 1)
        auftraggeber = auftraggeber.strip().lower()
        vzweck = vzweck.strip().lower()
    else:
        auftraggeber = ""
        vzweck = text_lower

    def _treffer(regel, basis_konfidenz):
        k = regel["kategorie"] or ""
        t = regel["typ"] or "Einnahme"
        kt = regel["konto_typ"] or "Wohngeldkonto"
        # Betragsfilter erhöht Konfidenz
        if betrag is not None:
            bmin = regel.get("betrag_min")
            bmax = regel.get("betrag_max")
            if bmin is not None and bmax is not None:
                if bmin <= abs(betrag) <= bmax:
                    return k, t, kt, min(basis_konfidenz + 0.10, 1.0)
                else:
                    return k, t, kt, max(basis_konfidenz - 0.15, 0.0)
        return k, t, kt, basis_konfidenz

    # Stufe 1: Exakter Muster-Match im gesamten Text
    for regel in regeln:
        muster = regel["muster"].lower() if regel["muster"] else ""
        if muster and muster in text_lower:
            return _treffer(regel, 0.85)

    # Stufe 1b: Keyword-Suche in Buchungsregeln (#40)
    for regel in regeln:
        kws = [k.strip().lower() for k in (regel.get("keywords") or "").split(",") if k.strip()]
        if any(kw and kw in text_lower for kw in kws):
            return _treffer(regel, 0.65)  # Etwas unter direktem Muster-Match

    # Stufe 2: Auftraggeber-Match (bereinigt)
    if auftraggeber:
        auftr_bereinigt = _bereinige_text(auftraggeber)
        for regel in regeln:
            muster = _bereinige_text(regel["muster"] if regel["muster"] else "")
            if muster and muster in auftr_bereinigt:
                return _treffer(regel, 0.70)

    # Stufe 3: Keyword-Match im Verwendungszweck
    vzweck_bereinigt = _bereinige_text(vzweck)
    for regel in regeln:
        muster = _bereinige_text(regel["muster"] if regel["muster"] else "")
        if muster and muster in vzweck_bereinigt:
            return _treffer(regel, 0.50)

    return "", "Einnahme", "Wohngeldkonto", 0.0

def pro_rata_temporis(einzug, auszug, jahr: int) -> float:
    """Berechnet den zeitanteiligen Anteil eines Mieters im Jahr.
    Gibt einen Faktor 0.0–1.0 zurück (z.B. 0.5 wenn 6 Monate bewohnt).

    Args:
        einzug: str ISO-Datum oder date-Objekt
        auszug: str ISO-Datum, date-Objekt oder None (noch aktiv)
        jahr: Abrechnungsjahr
    """
    from datetime import date as _date
    def _to_date(v):
        if v is None:
            return None
        if isinstance(v, _date):
            return v
        try:
            return _date.fromisoformat(str(v)[:10])
        except Exception:
            return None

    j_start = _date(jahr, 1, 1)
    j_ende  = _date(jahr, 12, 31)
    jahrestage = (j_ende - j_start).days + 1

    einzug_d = _to_date(einzug) or j_start
    auszug_d = _to_date(auszug) or j_ende

    start = max(einzug_d, j_start)
    ende  = min(auszug_d, j_ende)

    if ende < start:
        return 0.0

    tage = (ende - start).days + 1
    return max(0.0, min(1.0, tage / jahrestage))

def lerne_buchung(buchungstext: str, kategorie: str, typ: str, konto_typ: str, ist_korrektur: bool = False):
    """Speichert oder aktualisiert eine Buchungsregel.

    Muster-Extraktion:
    - Bei buchungstext mit || → Auftraggeber/Empfänger (vor ||) als Muster
    - Sonst: gesamten Text (max 40 Zeichen) als Muster
    - Füllwörter werden nicht entfernt (das passiert beim Matching)
    """
    if not buchungstext or not kategorie:
        return
    if "||" in buchungstext:
        auftraggeber = buchungstext.split("||")[0].strip()
        # Auftraggeber als primäres Muster (max 60 Zeichen)
        muster = auftraggeber[:60] if auftraggeber else buchungstext[:40]
    else:
        muster = buchungstext[:40]
    if not muster:
        return
    conn = get_db()
    existing = conn.execute(
        "SELECT * FROM buchungsregeln WHERE muster=?", (muster,)
    ).fetchone()
    if existing:
        conn.execute(
            "UPDATE buchungsregeln SET kategorie=?, typ=?, konto_typ=?, treffer=treffer+1, ist_korrektur=? WHERE id=?",
            (kategorie, typ, konto_typ, 1 if ist_korrektur else 0, existing["id"])
        )
    else:
        conn.execute(
            "INSERT INTO buchungsregeln (muster, kategorie, typ, konto_typ, treffer, ist_korrektur) VALUES (?,?,?,?,1,?)",
            (muster, kategorie, typ, konto_typ, 1 if ist_korrektur else 0)
        )
    conn.commit()
    conn.close()

# ── Dialog-Basis ──────────────────────────────────────────────────────────────

class BaseDialog(tk.Toplevel):
    """Basis-Dialog: scrollbar, größenveränderbar, Größe wird in Config gespeichert."""

    # Class-level cache for window sizes (persisted to config on close)
    _size_cache = None

    @classmethod
    def _load_size_cache(cls):
        if cls._size_cache is None:
            cfg = load_config()
            cls._size_cache = cfg.get("dialog_sizes", {})
        return cls._size_cache

    @classmethod
    def _save_size_cache(cls):
        if cls._size_cache is not None:
            cfg = load_config()
            cfg["dialog_sizes"] = cls._size_cache
            save_config(cfg)

    def __init__(self, parent, title, width=500, height=520):
        super().__init__(parent)
        self._dialog_key = title  # key for size persistence
        self.title(title)
        self.configure(bg=BG_CARD)
        self.resizable(True, True)
        self.minsize(380, 300)
        self.grab_set()
        self.result = None
        self._fields = {}

        # Restore saved size or use defaults
        sizes = self._load_size_cache()
        saved = sizes.get(self._dialog_key)
        if saved:
            self.geometry(f"{saved['w']}x{saved['h']}")
        else:
            self.geometry(f"{width}x{height}")

        # ── Header ────────────────────────────────────────────────────
        header = tk.Frame(self, bg=BG_SIDEBAR, height=48)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=title, bg=BG_SIDEBAR, fg=TEXT_WHITE,
                 font=FONT_H3).pack(side="left", padx=16, pady=12)

        # ── Scrollable body ───────────────────────────────────────────
        self._scroll_container = tk.Frame(self, bg=BG_CARD)
        self._scroll_container.pack(fill="both", expand=True)

        self._canvas = tk.Canvas(self._scroll_container, bg=BG_CARD,
                                 highlightthickness=0, bd=0)
        self._vsb = ttk.Scrollbar(self._scroll_container, orient="vertical",
                                   command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._vsb.set)
        self._vsb.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._body = tk.Frame(self._canvas, bg=BG_CARD)
        self._body_window = self._canvas.create_window(
            (0, 0), window=self._body, anchor="nw")

        self._body.bind("<Configure>", self._on_body_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        # Mousewheel scrolling
        self._body.bind("<Enter>", lambda e: self._bind_mousewheel())
        self._body.bind("<Leave>", lambda e: self._unbind_mousewheel())

        # ── Buttons (fixed at bottom) ─────────────────────────────────
        self._btn_row = tk.Frame(self, bg=BG_CARD)
        self._btn_row.pack(fill="x", padx=20, pady=(8, 12))
        make_btn(self._btn_row, "Abbrechen", self.destroy,
                 color=BG_INPUT, fg=TEXT).pack(side="right", padx=(8, 0))
        make_btn(self._btn_row, "Speichern", self._on_save,
                 color=ACCENT2).pack(side="right")

        # Save size on close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Enter-Taste speichert
        self.bind("<Return>", lambda e: self._on_save())

    def _on_body_configure(self, event=None):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event=None):
        # Make body width match canvas width (minus scrollbar padding)
        self._canvas.itemconfig(self._body_window, width=event.width - 4)

    def _bind_mousewheel(self):
        self._canvas.bind_all("<MouseWheel>",
                              lambda e: self._canvas.yview_scroll(-1 * (e.delta // 120), "units"))
        self._canvas.bind_all("<Button-4>",
                              lambda e: self._canvas.yview_scroll(-1, "units"))
        self._canvas.bind_all("<Button-5>",
                              lambda e: self._canvas.yview_scroll(1, "units"))

    def _unbind_mousewheel(self):
        self._canvas.unbind_all("<MouseWheel>")
        self._canvas.unbind_all("<Button-4>")
        self._canvas.unbind_all("<Button-5>")

    def _on_close(self):
        self._persist_size()
        self.destroy()

    def _persist_size(self):
        """Save current window geometry to cache."""
        try:
            w = self.winfo_width()
            h = self.winfo_height()
            if w > 100 and h > 100:
                sizes = self._load_size_cache()
                sizes[self._dialog_key] = {"w": w, "h": h}
                self._save_size_cache()
        except Exception:
            pass

    def _add_field(self, label, key, default="", widget_type="entry", options=None, row=None):
        frame = self._body if row is None else row
        lbl = tk.Label(frame, text=label, bg=BG_CARD, fg=TEXT_LIGHT,
                 font=FONT_SMALL)
        lbl.pack(anchor="w", padx=20 if frame is self._body else 0, pady=(8, 1))
        if widget_type == "entry":
            var = tk.StringVar(value=str(default) if default else "")
            w   = make_entry(frame, textvariable=var)
            w.pack(fill="x", padx=20 if frame is self._body else 0, ipady=6)
            self._fields[key] = var
        elif widget_type == "text":
            w = tk.Text(frame, height=3, bg=BG_INPUT, fg=TEXT,
                        relief="flat", font=FONT_BODY, bd=0, padx=6, pady=4)
            w.pack(fill="x", padx=20 if frame is self._body else 0)
            if default:
                w.insert("1.0", str(default))
            self._fields[key] = w
        elif widget_type == "combo":
            var = tk.StringVar(value=str(default) if default else "")
            w   = ttk.Combobox(frame, textvariable=var, values=options or [],
                               state="readonly", font=FONT_BODY)
            w.pack(fill="x", padx=20 if frame is self._body else 0, ipady=4)
            self._fields[key] = var
        return w

    def _get_values(self):
        result = {}
        for key, widget in self._fields.items():
            if isinstance(widget, tk.StringVar):
                result[key] = widget.get()
            elif isinstance(widget, tk.Text):
                result[key] = widget.get("1.0", "end-1c")
        return result

    def _on_save(self):
        self._persist_size()
        self.result = self._get_values()
        self.destroy()

# ══════════════════════════════════════════════════════════════════════════════
# SEITEN
# ══════════════════════════════════════════════════════════════════════════════

class DashboardPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self._build()

    def _build(self):
        tk.Label(self, text="Übersicht", bg=BG, fg=TEXT,
                 font=FONT_H1).pack(anchor="w", padx=28, pady=(24, 4))
        tk.Label(self, text=f"Stand: {date.today().strftime('%d. %B %Y')}",
                 bg=BG, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w", padx=28)

        kpi_row = tk.Frame(self, bg=BG)
        kpi_row.pack(fill="x", padx=28, pady=16)
        kpi_row.columnconfigure((0, 1, 2, 3), weight=1, uniform="kpi")

        conn = get_db()
        mieter_count   = conn.execute("SELECT COUNT(*) FROM mieter WHERE auszug IS NULL OR auszug=''").fetchone()[0]
        ej_count       = conn.execute("SELECT COUNT(*) FROM eigentuemer").fetchone()[0]
        offene_wartung = conn.execute("SELECT COUNT(*) FROM wartung WHERE status!='Erledigt'").fetchone()[0]
        einnahmen      = conn.execute("SELECT COALESCE(SUM(betrag),0) FROM zahlungen WHERE typ='Einnahme' AND strftime('%Y-%m',datum)=strftime('%Y-%m','now')").fetchone()[0]
        ausgaben       = conn.execute("SELECT COALESCE(SUM(ABS(betrag)),0) FROM zahlungen WHERE typ='Ausgabe' AND strftime('%Y-%m',datum)=strftime('%Y-%m','now')").fetchone()[0]
        ungelesen      = conn.execute("SELECT COUNT(*) FROM nachrichten WHERE gelesen=0").fetchone()[0]
        # #32 Zusatz-KPIs
        jahres_ein     = conn.execute("SELECT COALESCE(SUM(betrag),0) FROM zahlungen WHERE typ='Einnahme' AND strftime('%Y',datum)=strftime('%Y','now')").fetchone()[0]
        jahres_aus     = conn.execute("SELECT COALESCE(SUM(betrag),0) FROM zahlungen WHERE typ='Ausgabe' AND strftime('%Y',datum)=strftime('%Y','now')").fetchone()[0]
        jahres_saldo   = jahres_ein - jahres_aus
        ruecklage_sum  = conn.execute("SELECT COALESCE(SUM(betrag),0) FROM zahlungen WHERE typ='Ausgabe' AND kategorie='Erhaltungsrücklage'").fetchone()[0]
        conn.close()

        kpi_row.columnconfigure((0, 1, 2, 3, 4, 5), weight=1, uniform="kpi")
        kpis = [
            ("🏠", "Aktive Mieter",    str(mieter_count),           ACCENT2),
            ("💰", "Einnahmen (Monat)", fmt_euro(einnahmen),          SUCCESS),
            ("📊", f"Jahressaldo {date.today().year}", fmt_euro(jahres_saldo),
             SUCCESS if jahres_saldo >= 0 else DANGER),
            ("🏦", "Rücklagen (kum.)",  fmt_euro(ruecklage_sum),      "#2E6DA4"),
            ("🔧", "Offene Aufgaben",   str(offene_wartung),          WARNING),
            ("✉️",  "Ungelesen",         str(ungelesen),               ACCENT),
        ]
        for col, (icon, label, val, color) in enumerate(kpis):
            card = tk.Frame(kpi_row, bg=BG_CARD, relief="flat", bd=0)
            card.grid(row=0, column=col, padx=6, pady=4, sticky="nsew")
            tk.Frame(card, bg=color, height=4).pack(fill="x")
            tk.Label(card, text=icon,  bg=BG_CARD, font=("Segoe UI", 22)).pack(pady=(12, 2))
            tk.Label(card, text=val,   bg=BG_CARD, fg=TEXT,      font=FONT_H2).pack()
            tk.Label(card, text=label, bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(pady=(0, 12))

        bottom = tk.Frame(self, bg=BG)
        bottom.pack(fill="both", expand=True, padx=28, pady=(0, 20))
        bottom.columnconfigure(0, weight=3)
        bottom.columnconfigure(1, weight=2)

        left = tk.Frame(bottom, bg=BG_CARD)
        left.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        section_header(left, "Letzte Buchungen")
        cols = ("Datum", "Beschreibung", "Betrag", "Typ")
        f, tree = make_table(left, cols, height=8)
        f.pack(fill="both", expand=True, padx=12, pady=8)
        for c, w in zip(cols, [90, 220, 100, 80]):
            tree.heading(c, text=c)
            tree.column(c, width=w, anchor="w")

        conn = get_db()
        for row in conn.execute("SELECT datum,beschreibung,betrag,typ FROM zahlungen ORDER BY erstellt_am DESC LIMIT 15"):
            tree.insert("", "end", values=(
                fmt_date(row["datum"]),
                row["beschreibung"] or "–",
                fmt_euro(row["betrag"]),
                row["typ"]
            ))

        right = tk.Frame(bottom, bg=BG_CARD)
        right.grid(row=0, column=1, padx=(8, 0), sticky="nsew")
        section_header(right, "Offene Aufgaben")

        prio_colors = {"Hoch": DANGER, "Mittel": WARNING, "Niedrig": SUCCESS}
        for row in conn.execute("SELECT titel,prioritaet,einheit,status FROM wartung WHERE status!='Erledigt' ORDER BY CASE prioritaet WHEN 'Hoch' THEN 1 WHEN 'Mittel' THEN 2 ELSE 3 END"):
            item = tk.Frame(right, bg=BG_CARD)
            item.pack(fill="x", padx=12, pady=4)
            pc   = prio_colors.get(row["prioritaet"], TEXT_LIGHT)
            tk.Frame(item, bg=pc, width=4).pack(side="left", fill="y", padx=(0, 8))
            info = tk.Frame(item, bg=BG_CARD)
            info.pack(side="left", fill="x", expand=True)
            tk.Label(info, text=row["titel"],
                     bg=BG_CARD, fg=TEXT, font=("Segoe UI Semibold", 10), anchor="w").pack(fill="x")
            tk.Label(info, text=f"{row['einheit'] or '–'}  ·  {row['prioritaet']}",
                     bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL, anchor="w").pack(fill="x")
        conn.close()

        # Buchungs-Status KPIs
        self._build_buchungsstatus_kpis(bottom)

    def _build_buchungsstatus_kpis(self, parent):
        """KPI-Kacheln für Buchungs-/Abrechnungsstatus."""
        conn = get_db()
        try:
            total   = conn.execute("SELECT COUNT(*) FROM kontoauszug").fetchone()[0]
            zugeord = conn.execute("SELECT COUNT(*) FROM kontoauszug WHERE buchung_status='uebernommen' OR buchung_status='abgerechnet'").fetchone()[0]
            offen   = conn.execute("SELECT COUNT(*) FROM kontoauszug WHERE als_buchung_uebernommen=0 AND kategorie_vorschlag IS NOT NULL AND kategorie_vorschlag!=''").fetchone()[0]
            ungekl  = conn.execute("SELECT COUNT(*) FROM kontoauszug WHERE als_buchung_uebernommen=0 AND (kategorie_vorschlag IS NULL OR kategorie_vorschlag='')").fetchone()[0]
            abr_status = conn.execute("SELECT status, jahr FROM abrechnungen WHERE typ='WEG' ORDER BY jahr DESC LIMIT 1").fetchone()
        finally:
            conn.close()

        abr_text = "Keine Abrechnung" if not abr_status else f"{abr_status['status']} {abr_status['jahr']}"
        abr_farbe = SUCCESS if (abr_status and abr_status["status"] == "Festgestellt") else ACCENT

        frame = tk.Frame(parent, bg=BG_CARD)
        frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=(0, 8), pady=(8, 0), ipady=6)
        tk.Label(frame, text="Buchungs-Status", bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w", padx=12)

        kpis_frame = tk.Frame(frame, bg=BG_CARD)
        kpis_frame.pack(fill="x", padx=12)

        for text, wert, farbe in [
            ("✅ Zugeordnet", f"{zugeord}/{total}", SUCCESS),
            ("🟡 Vorschläge offen", str(offen), ACCENT),
            ("🔴 Ungeklärt", str(ungekl), DANGER if ungekl > 0 else TEXT_LIGHT),
            ("📋 Abrechnung", abr_text, abr_farbe),
        ]:
            card = tk.Frame(kpis_frame, bg=BG_INPUT, bd=0, relief="flat")
            card.pack(side="left", padx=(0, 8), pady=4, ipadx=12, ipady=8)
            tk.Label(card, text=wert, bg=BG_INPUT, fg=farbe, font=FONT_H2).pack()
            tk.Label(card, text=text, bg=BG_INPUT, fg=TEXT_LIGHT, font=FONT_SMALL).pack()

# ── Mieter-Seite ──────────────────────────────────────────────────────────────

class MieterPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_CARD)
        self._build()

    def _build(self):
        section_header(self, "Mieter", "＋ Mieter", self._new)
        cols = ("Name", "Wohnung", "Kaltmiete", "NK-Voraus.", "Einzug", "Auszug", "Telefon", "IBAN")
        f, self.tree = make_table(self, cols, height=16)
        f.pack(fill="both", expand=True, padx=20, pady=10)
        for c, w in zip(cols, [160, 130, 110, 110, 110, 110, 130, 180]):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="w")
        self.tree.bind("<Double-1>", self._edit)
        self._load()
        btn_row = tk.Frame(self, bg=BG_CARD)
        btn_row.pack(fill="x", padx=20, pady=(0, 10))
        if hat_recht("Mieter", "schreiben"):
            make_btn(btn_row, "✏ Bearbeiten", self._edit, color=BG_INPUT, fg=TEXT).pack(side="left", padx=(0, 8))
            make_btn(btn_row, "🏠 Eigentümer als Bewohner", self._eigentuemer_als_bewohner,
                     color=ACCENT, fg=TEXT_WHITE).pack(side="left", padx=(0, 8))
        if hat_recht("Mieter", "loeschen"):
            make_btn(btn_row, "🗑 Löschen",   self._delete, color=DANGER).pack(side="left")

    def _load(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = get_db()
        for r in conn.execute("SELECT m.*, w.bezeichnung FROM mieter m LEFT JOIN wohnungen w ON m.wohnung_id=w.id ORDER BY m.name"):
            full_name = f"{r['vorname'] or ''} {r['name']}".strip()
            self.tree.insert("", "end", iid=r["id"], values=(
                full_name, r["bezeichnung"] or "–",
                fmt_euro(r["kaltmiete"]),
                fmt_euro(r["nebenkosten_vorauszahlung"]),
                fmt_date(r["einzug"]),
                fmt_date(r["auszug"]) if r["auszug"] else "–",
                r["telefon"] or "–",
                r["iban"] or "–"
            ))
        conn.close()
        tree_empty_hint(self.tree)

    def _new(self):
        if not hat_recht("Mieter", "schreiben"):
            messagebox.showwarning("Berechtigung", "Sie haben keine Schreibberechtigung.", parent=self); return
        d = MieterDialog(self)
        self.wait_window(d)
        if d.result:
            v = d.result
            conn = get_db()
            conn.execute("INSERT INTO mieter (vorname,name,strasse,plz,ort,land,telefon,email,iban,wohnung_id,einzug,auszug,kaltmiete,nebenkosten_vorauszahlung,kaution,notizen,personen,spuelmaschinen,waschmaschinen,trockner_wasserkuehlung) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (v.get("vorname",""), v.get("name",""), v.get("strasse",""), v.get("plz",""), v.get("ort",""), v.get("land","Deutschland"), v.get("telefon",""), v.get("email",""), v.get("iban",""),
                 v.get("wohnung_id"), v.get("einzug",""), v.get("auszug"), float(v.get("kaltmiete") or 0), float(v.get("nk") or 0), float(v.get("kaution") or 0), v.get("notizen",""),
                 int(v.get("personen") or 1), int(v.get("spuelmaschinen") or 0), int(v.get("waschmaschinen") or 1), int(v.get("trockner_wasserkuehlung") or 0)))
            conn.commit(); conn.close()
            self._load()

    def _edit(self, event=None):
        if not hat_recht("Mieter", "schreiben"):
            messagebox.showwarning("Berechtigung", "Sie haben keine Schreibberechtigung.", parent=self); return
        sel = self.tree.selection()
        if not sel: return
        mid = int(sel[0])
        conn = get_db()
        row = conn.execute("SELECT * FROM mieter WHERE id=?", (mid,)).fetchone()
        conn.close()
        d = MieterDialog(self, row)
        self.wait_window(d)
        if d.result:
            v = d.result
            conn = get_db()
            conn.execute("UPDATE mieter SET vorname=?,name=?,strasse=?,plz=?,ort=?,land=?,telefon=?,email=?,iban=?,wohnung_id=?,einzug=?,auszug=?,kaltmiete=?,nebenkosten_vorauszahlung=?,kaution=?,notizen=?,personen=?,spuelmaschinen=?,waschmaschinen=?,trockner_wasserkuehlung=? WHERE id=?",
                (v.get("vorname",""), v.get("name",""), v.get("strasse",""), v.get("plz",""), v.get("ort",""), v.get("land","Deutschland"), v.get("telefon",""), v.get("email",""), v.get("iban",""),
                 v.get("wohnung_id"), v.get("einzug",""), v.get("auszug"), float(v.get("kaltmiete") or 0), float(v.get("nk") or 0), float(v.get("kaution") or 0), v.get("notizen",""),
                 int(v.get("personen") or 1), int(v.get("spuelmaschinen") or 0), int(v.get("waschmaschinen") or 1), int(v.get("trockner_wasserkuehlung") or 0), mid))
            conn.commit(); conn.close()
            self._load()

    def _delete(self):
        if not hat_recht("Mieter", "loeschen"):
            messagebox.showwarning("Berechtigung", "Sie haben keine Löschberechtigung.", parent=self); return
        sel = self.tree.selection()
        if not sel: return
        if messagebox.askyesno("Löschen", "Mieter wirklich löschen?"):
            conn = get_db()
            conn.execute("DELETE FROM mieter WHERE id=?", (int(sel[0]),))
            conn.commit(); conn.close()
            self._load()

    def _eigentuemer_als_bewohner(self):
        """Eigentümer als Bewohner (Eigennutzung) seiner Wohnung eintragen."""
        if not hat_recht("Mieter", "schreiben"):
            messagebox.showwarning("Berechtigung", "Keine Schreibberechtigung.", parent=self); return

        # Dialog: Eigentümer auswählen
        conn = get_db()
        eigentuemer = conn.execute("SELECT e.*, w.id as wid, w.bezeichnung as wbez "
                                   "FROM eigentuemer e "
                                   "LEFT JOIN wohnungen w ON w.eigentuemer_id=e.id "
                                   "ORDER BY e.name").fetchall()
        conn.close()

        if not eigentuemer:
            messagebox.showinfo("Info", "Keine Eigentümer vorhanden.", parent=self)
            return

        # Auswahl-Dialog
        win = tk.Toplevel(self)
        win.title("Eigentümer als Bewohner übernehmen")
        win.geometry("480x400")
        win.configure(bg=BG_CARD)
        win.resizable(True, True)
        win.grab_set()
        win._selected = None

        hdr = tk.Frame(win, bg=BG_SIDEBAR, height=48)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Eigentümer als Bewohner übernehmen",
                 bg=BG_SIDEBAR, fg=TEXT_WHITE, font=FONT_H3).pack(side="left", padx=16, pady=12)

        tk.Label(win, text="Wählen Sie einen Eigentümer, der selbst in seiner Wohnung wohnt:",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w", padx=16, pady=(10, 4))

        cols_e = ("Name", "Wohnung")
        f, tree = make_table(win, cols_e, height=10)
        f.pack(fill="both", expand=True, padx=16, pady=4)
        tree.heading("Name", text="Name")
        tree.heading("Wohnung", text="Wohnung")
        tree.column("Name", width=200, anchor="w")
        tree.column("Wohnung", width=200, anchor="w")

        # Group eigentuemer by id to show wohnungen
        et_map = {}
        for e in eigentuemer:
            eid = e["id"]
            if eid not in et_map:
                et_map[eid] = {"row": dict(e), "wohnungen": []}
            if e["wid"]:
                et_map[eid]["wohnungen"].append({"id": e["wid"], "bez": e["wbez"]})

        item_data = {}
        for eid, info in et_map.items():
            r = info["row"]
            name = f"{r.get('vorname','') or ''} {r.get('name','')}".strip()
            for w in info["wohnungen"]:
                iid = f"{eid}_{w['id']}"
                tree.insert("", "end", iid=iid, values=(name, w["bez"] or "–"))
                item_data[iid] = {"eigentuemer": r, "wohnung_id": w["id"], "wohnung_bez": w["bez"]}
            if not info["wohnungen"]:
                iid = f"{eid}_0"
                tree.insert("", "end", iid=iid, values=(name, "– keine Wohnung –"))
                item_data[iid] = {"eigentuemer": r, "wohnung_id": None, "wohnung_bez": None}

        def _uebernehmen():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Auswahl", "Bitte einen Eintrag auswählen.", parent=win)
                return
            data = item_data.get(sel[0])
            if not data:
                return
            e = data["eigentuemer"]
            wid = data["wohnung_id"]

            # Check if already a Mieter with this name
            conn = get_db()
            existing = conn.execute(
                "SELECT id FROM mieter WHERE vorname=? AND name=?",
                (e.get("vorname", ""), e["name"])
            ).fetchone()
            if existing:
                messagebox.showinfo("Hinweis",
                    f"{e.get('vorname','')} {e['name']} ist bereits als Mieter eingetragen.",
                    parent=win)
                conn.close()
                return

            conn.execute(
                "INSERT INTO mieter (vorname,name,strasse,ort,land,telefon,email,iban,wohnung_id,einzug,kaltmiete,nebenkosten_vorauszahlung,kaution,notizen) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,0,0,0,'Eigennutzung')",
                (e.get("vorname",""), e["name"], e.get("strasse",""), e.get("ort",""),
                 e.get("land","Deutschland"), e.get("telefon",""), e.get("email",""),
                 e.get("iban",""), wid, date.today().isoformat()))
            conn.commit()
            conn.close()
            win.destroy()
            self._load()
            messagebox.showinfo("Übernommen",
                f"{e.get('vorname','')} {e['name']} wurde als Bewohner eingetragen.",
                parent=self)

        btn_row = tk.Frame(win, bg=BG_CARD)
        btn_row.pack(fill="x", padx=16, pady=(4, 12))
        make_btn(btn_row, "Abbrechen", win.destroy, color=BG_INPUT, fg=TEXT).pack(side="right", padx=(8, 0))
        make_btn(btn_row, "✔ Übernehmen", _uebernehmen, color=ACCENT2).pack(side="right")


class MieterDialog(BaseDialog):
    def __init__(self, parent, row=None):
        super().__init__(parent, "Mieter" + (" bearbeiten" if row else " hinzufügen"), 520, 700)
        r = dict(row) if row else {}
        # Row 1: Vorname + Name
        two = tk.Frame(self._body, bg=BG_CARD); two.pack(fill="x", padx=20); two.columnconfigure((0,1), weight=1)
        l = tk.Frame(two, bg=BG_CARD); l.grid(row=0, column=0, padx=(0,6), sticky="ew")
        ri = tk.Frame(two, bg=BG_CARD); ri.grid(row=0, column=1, padx=(6,0), sticky="ew")
        self._add_field("Vorname", "vorname", r.get("vorname",""), row=l)
        self._add_field("Name *", "name", r.get("name",""), row=ri)
        # Row 2: Straße (volle Breite)
        self._add_field("Straße", "strasse", r.get("strasse",""))
        # Row 3: PLZ + Ort (PLZ schmal, Ort breit)
        two = tk.Frame(self._body, bg=BG_CARD); two.pack(fill="x", padx=20)
        two.columnconfigure(0, weight=1); two.columnconfigure(1, weight=3)
        l = tk.Frame(two, bg=BG_CARD); l.grid(row=0, column=0, padx=(0,6), sticky="ew")
        ri = tk.Frame(two, bg=BG_CARD); ri.grid(row=0, column=1, padx=(6,0), sticky="ew")
        self._add_field("PLZ", "plz", r.get("plz",""), row=l)
        self._add_field("Ort", "ort", r.get("ort",""), row=ri)
        # Row 4: Land + Telefon
        two = tk.Frame(self._body, bg=BG_CARD); two.pack(fill="x", padx=20); two.columnconfigure((0,1), weight=1)
        l = tk.Frame(two, bg=BG_CARD); l.grid(row=0, column=0, padx=(0,6), sticky="ew")
        ri = tk.Frame(two, bg=BG_CARD); ri.grid(row=0, column=1, padx=(6,0), sticky="ew")
        self._add_field("Land", "land", r.get("land","Deutschland"), row=l)
        self._add_field("Telefon", "telefon", r.get("telefon",""), row=ri)
        # Row 5: E-Mail + IBAN
        two = tk.Frame(self._body, bg=BG_CARD); two.pack(fill="x", padx=20); two.columnconfigure((0,1), weight=1)
        l = tk.Frame(two, bg=BG_CARD); l.grid(row=0, column=0, padx=(0,6), sticky="ew")
        ri = tk.Frame(two, bg=BG_CARD); ri.grid(row=0, column=1, padx=(6,0), sticky="ew")
        self._add_field("E-Mail", "email", r.get("email",""), row=l)
        self._add_field("IBAN", "iban", r.get("iban",""), row=ri)

        # Wohnung dropdown
        conn = get_db()
        self._wohnung_list = conn.execute("SELECT id, bezeichnung FROM wohnungen ORDER BY bezeichnung").fetchall()
        conn.close()
        woh_options = ["– keine –"] + [w["bezeichnung"] for w in self._wohnung_list]
        cur_woh = 0
        if r.get("wohnung_id"):
            for i, w in enumerate(self._wohnung_list):
                if w["id"] == r["wohnung_id"]: cur_woh = i+1; break
        self._add_field("Wohnung", "wohnung_str", woh_options[cur_woh], widget_type="combo", options=woh_options)

        # Mietdaten
        two = tk.Frame(self._body, bg=BG_CARD); two.pack(fill="x", padx=20); two.columnconfigure((0,1), weight=1)
        l = tk.Frame(two, bg=BG_CARD); l.grid(row=0, column=0, padx=(0,6), sticky="ew")
        ri = tk.Frame(two, bg=BG_CARD); ri.grid(row=0, column=1, padx=(6,0), sticky="ew")
        self._add_field("Einzug (JJJJ-MM-TT)", "einzug", r.get("einzug",""), row=l)
        self._add_field("Auszug (JJJJ-MM-TT)", "auszug", r.get("auszug","") or "", row=ri)

        two = tk.Frame(self._body, bg=BG_CARD); two.pack(fill="x", padx=20); two.columnconfigure((0,1), weight=1)
        l = tk.Frame(two, bg=BG_CARD); l.grid(row=0, column=0, padx=(0,6), sticky="ew")
        ri = tk.Frame(two, bg=BG_CARD); ri.grid(row=0, column=1, padx=(6,0), sticky="ew")
        self._add_field("Kaltmiete €", "kaltmiete", r.get("kaltmiete",""), row=l)
        self._add_field("NK-Vorausz. €", "nk", r.get("nebenkosten_vorauszahlung",""), row=ri)

        self._add_field("Kaution €", "kaution", r.get("kaution",""))

        self._add_field("Notizen", "notizen", r.get("notizen",""), widget_type="text")

        # Wasserkosten-Stammdaten
        tk.Frame(self._body, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(10,4))
        tk.Label(self._body, text="Wasserkosten-Stammdaten", bg=BG_CARD, fg=TEXT,
                 font=FONT_H3).pack(anchor="w", padx=20)
        two = tk.Frame(self._body, bg=BG_CARD); two.pack(fill="x", padx=20); two.columnconfigure((0,1), weight=1)
        l = tk.Frame(two, bg=BG_CARD); l.grid(row=0, column=0, padx=(0,6), sticky="ew")
        ri = tk.Frame(two, bg=BG_CARD); ri.grid(row=0, column=1, padx=(6,0), sticky="ew")
        self._add_field("Personen", "personen", r.get("personen", 1), row=l)
        self._add_field("Spülmaschinen", "spuelmaschinen", r.get("spuelmaschinen", 0), row=ri)
        two2 = tk.Frame(self._body, bg=BG_CARD); two2.pack(fill="x", padx=20); two2.columnconfigure((0,1), weight=1)
        l2 = tk.Frame(two2, bg=BG_CARD); l2.grid(row=0, column=0, padx=(0,6), sticky="ew")
        ri2 = tk.Frame(two2, bg=BG_CARD); ri2.grid(row=0, column=1, padx=(6,0), sticky="ew")
        self._add_field("Waschmaschinen", "waschmaschinen", r.get("waschmaschinen", 1), row=l2)
        self._add_field("Trockner (Wasserkühlung)", "trockner_wasserkuehlung", r.get("trockner_wasserkuehlung", 0), row=ri2)

    def _on_save(self):
        v = self._get_values()
        if not v.get("name"):
            messagebox.showwarning("Pflichtfeld", "Name ist erforderlich.", parent=self); return

        # Resolve Wohnung-ID
        woh_str = v.get("wohnung_str","")
        v["wohnung_id"] = None
        for w in self._wohnung_list:
            if w["bezeichnung"] == woh_str:
                v["wohnung_id"] = w["id"]; break

        # Normalisiere Datum
        if v.get("einzug"):
            v["einzug"] = parse_datum(v["einzug"])
        if v.get("auszug"):
            v["auszug"] = parse_datum(v["auszug"])
        else:
            v["auszug"] = None

        self.result = v; self.destroy()

# ── Eigentümer-Seite ──────────────────────────────────────────────────────────

class EigentuemerPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_CARD)
        self._build()

    def _build(self):
        section_header(self, "Eigentümer", "＋ Eigentümer", self._new)
        cols = ("Name", "Ort", "Telefon", "E-Mail", "IBAN", "MEA ‰")
        f, self.tree = make_table(self, cols, height=8)
        f.pack(fill="both", expand=True, padx=20, pady=10)
        for c, w in zip(cols, [180, 130, 120, 200, 180, 80]):
            self.tree.heading(c, text=c); self.tree.column(c, width=w, anchor="w")
        self.tree.bind("<Double-1>", self._edit)
        self._load()
        btn_row = tk.Frame(self, bg=BG_CARD)
        btn_row.pack(fill="x", padx=20, pady=(0, 10))
        if hat_recht("Eigentümer", "schreiben"):
            make_btn(btn_row, "✏ Bearbeiten", self._edit, color=BG_INPUT, fg=TEXT).pack(side="left", padx=(0, 8))
        if hat_recht("Eigentümer", "loeschen"):
            make_btn(btn_row, "🗑 Löschen",   self._delete, color=DANGER).pack(side="left")

    def _load(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = get_db()
        for r in conn.execute("SELECT * FROM eigentuemer ORDER BY name"):
            full_name = f"{r['vorname'] or ''} {r['name']}".strip()
            mea = conn.execute("SELECT SUM(mea_tausendstel) FROM wohnungen WHERE eigentuemer_id=?", (r['id'],)).fetchone()[0]
            mea_str = f"{parse_float(mea):.1f}" if mea else "–"
            self.tree.insert("", "end", iid=r["id"], values=(
                full_name, r["ort"] or "–",
                r["telefon"] or "–",
                r["email"] or "–", r["iban"] or "–", mea_str))
        conn.close()
        tree_empty_hint(self.tree)

    def _new(self):
        if not hat_recht("Eigentümer", "schreiben"):
            messagebox.showwarning("Berechtigung", "Sie haben keine Schreibberechtigung.", parent=self); return
        d = EigentuemerDialog(self)
        self.wait_window(d)
        if d.result:
            v = d.result
            conn = get_db()
            # Berechne anteil_prozent aus Wohnungen (MEA ‰ / 10 = %)
            anteil = float(v.get("anteil") or 33.33)  # Fallback falls noch vorhanden
            conn.execute("INSERT INTO eigentuemer (vorname,name,strasse,plz,ort,land,telefon,email,iban,anteil_prozent,einheit,notizen) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (v.get("vorname",""), v.get("name",""), v.get("strasse",""), v.get("plz",""), v.get("ort",""), v.get("land","Deutschland"), v.get("telefon",""), v.get("email",""), v.get("iban",""), anteil, v.get("einheit",""), v.get("notizen","")))
            conn.commit(); conn.close(); self._load()

    def _edit(self, event=None):
        if not hat_recht("Eigentümer", "schreiben"):
            messagebox.showwarning("Berechtigung", "Sie haben keine Schreibberechtigung.", parent=self); return
        sel = self.tree.selection()
        if not sel: return
        conn = get_db()
        row = conn.execute("SELECT * FROM eigentuemer WHERE id=?", (int(sel[0]),)).fetchone()
        conn.close()
        d = EigentuemerDialog(self, row)
        self.wait_window(d)
        if d.result:
            v = d.result
            conn = get_db()
            # Berechne anteil_prozent aus Wohnungen (MEA ‰ / 10 = %)
            mea_sum = conn.execute(
                "SELECT SUM(mea_tausendstel) FROM wohnungen WHERE eigentuemer_id=?",
                (int(sel[0]),)
            ).fetchone()[0]
            anteil = (mea_sum / 10.0) if mea_sum else float(v.get("anteil") or 33.33)
            conn.execute("UPDATE eigentuemer SET vorname=?,name=?,strasse=?,plz=?,ort=?,land=?,telefon=?,email=?,iban=?,anteil_prozent=?,einheit=?,notizen=? WHERE id=?",
                (v.get("vorname",""), v.get("name",""), v.get("strasse",""), v.get("plz",""), v.get("ort",""), v.get("land","Deutschland"), v.get("telefon",""), v.get("email",""), v.get("iban",""), anteil, v.get("einheit",""), v.get("notizen",""), int(sel[0])))
            conn.commit(); conn.close(); self._load()

    def _delete(self):
        if not hat_recht("Eigentümer", "loeschen"):
            messagebox.showwarning("Berechtigung", "Sie haben keine Löschberechtigung.", parent=self); return
        sel = self.tree.selection()
        if not sel: return
        if messagebox.askyesno("Löschen", "Eigentümer löschen?"):
            conn = get_db()
            conn.execute("DELETE FROM eigentuemer WHERE id=?", (int(sel[0]),))
            conn.commit(); conn.close(); self._load()


class EigentuemerDialog(BaseDialog):
    def __init__(self, parent, row=None):
        super().__init__(parent, "Eigentümer" + (" bearbeiten" if row else " hinzufügen"), 540, 640)
        r = dict(row) if row else {}
        # Row 1: Vorname + Name
        two = tk.Frame(self._body, bg=BG_CARD); two.pack(fill="x", padx=20); two.columnconfigure((0,1), weight=1)
        l = tk.Frame(two, bg=BG_CARD); l.grid(row=0, column=0, padx=(0,6), sticky="ew")
        ri = tk.Frame(two, bg=BG_CARD); ri.grid(row=0, column=1, padx=(6,0), sticky="ew")
        self._add_field("Vorname", "vorname", r.get("vorname",""), row=l)
        self._add_field("Name *", "name", r.get("name",""), row=ri)
        # Row 2: Straße (volle Breite)
        self._add_field("Straße", "strasse", r.get("strasse",""))
        # Row 3: PLZ + Ort (PLZ schmal, Ort breit)
        two = tk.Frame(self._body, bg=BG_CARD); two.pack(fill="x", padx=20)
        two.columnconfigure(0, weight=1); two.columnconfigure(1, weight=3)
        l = tk.Frame(two, bg=BG_CARD); l.grid(row=0, column=0, padx=(0,6), sticky="ew")
        ri = tk.Frame(two, bg=BG_CARD); ri.grid(row=0, column=1, padx=(6,0), sticky="ew")
        self._add_field("PLZ", "plz", r.get("plz",""), row=l)
        self._add_field("Ort", "ort", r.get("ort",""), row=ri)
        # Row 4: Land + Telefon
        two = tk.Frame(self._body, bg=BG_CARD); two.pack(fill="x", padx=20); two.columnconfigure((0,1), weight=1)
        l = tk.Frame(two, bg=BG_CARD); l.grid(row=0, column=0, padx=(0,6), sticky="ew")
        ri = tk.Frame(two, bg=BG_CARD); ri.grid(row=0, column=1, padx=(6,0), sticky="ew")
        self._add_field("Land", "land", r.get("land","Deutschland"), row=l)
        self._add_field("Telefon", "telefon", r.get("telefon",""), row=ri)
        # Row 5: E-Mail + IBAN
        two = tk.Frame(self._body, bg=BG_CARD); two.pack(fill="x", padx=20); two.columnconfigure((0,1), weight=1)
        l = tk.Frame(two, bg=BG_CARD); l.grid(row=0, column=0, padx=(0,6), sticky="ew")
        ri = tk.Frame(two, bg=BG_CARD); ri.grid(row=0, column=1, padx=(6,0), sticky="ew")
        self._add_field("E-Mail", "email", r.get("email",""), row=l)
        self._add_field("IBAN", "iban", r.get("iban",""), row=ri)
        # Row 6: Einheit (Anteil wird aus Wohnungen berechnet)
        self._add_field("Einheit", "einheit", r.get("einheit",""))
        self._add_field("Notizen", "notizen", r.get("notizen",""), widget_type="text")

        # ── Zugeordnete Wohnungen anzeigen (nur bei Bearbeiten) ──────
        if row and r.get("id"):
            woh_frame = tk.Frame(self._body, bg=BG_CARD)
            woh_frame.pack(fill="x", padx=20, pady=(12, 0))
            tk.Label(woh_frame, text="Zugeordnete Wohnungen", bg=BG_CARD,
                     fg=TEXT, font=FONT_H3).pack(anchor="w")
            tk.Frame(woh_frame, bg=BORDER, height=1).pack(fill="x", pady=(2, 4))
            conn = get_db()
            wohnungen = conn.execute(
                "SELECT bezeichnung, typ, lage, mea_tausendstel, nutzflaeche_qm "
                "FROM wohnungen WHERE eigentuemer_id=? ORDER BY bezeichnung",
                (r["id"],)
            ).fetchall()
            if wohnungen:
                for w in wohnungen:
                    wrow = tk.Frame(woh_frame, bg=BG_INPUT)
                    wrow.pack(fill="x", pady=2, ipady=4)
                    mea = f"{parse_float(w['mea_tausendstel']):.1f} ‰" if w["mea_tausendstel"] else "–"
                    flaeche = f"{parse_float(w['nutzflaeche_qm']):.1f} m²" if w["nutzflaeche_qm"] else ""
                    info = f"  {w['bezeichnung']}  ·  {w['typ'] or '–'}  ·  {w['lage'] or '–'}  ·  {mea}"
                    if flaeche:
                        info += f"  ·  {flaeche}"
                    tk.Label(wrow, text=info, bg=BG_INPUT, fg=TEXT,
                             font=FONT_SMALL, anchor="w").pack(fill="x", padx=8)
            else:
                tk.Label(woh_frame, text="  Keine Wohnungen zugeordnet",
                         bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w")

            # MEA-Gesamtsumme anzeigen (Issue #6)
            mea_sum = conn.execute(
                "SELECT SUM(mea_tausendstel) FROM wohnungen WHERE eigentuemer_id=?",
                (r["id"],)
            ).fetchone()[0]
            mea_sum = mea_sum or 0.0
            mea_info_frame = tk.Frame(woh_frame, bg=ACCENT2)
            mea_info_frame.pack(fill="x", pady=(6, 0), ipady=4)
            mea_text = f"MEA gesamt: {mea_sum:.1f} ‰"
            tk.Label(mea_info_frame, text=mea_text, bg=ACCENT2, fg=TEXT_WHITE,
                     font=FONT_H3).pack(anchor="w", padx=8)

            # NK-Vorauszahlung Gesamtsumme anzeigen (Issue #7)
            nk_sum = conn.execute(
                "SELECT COALESCE(SUM(m.nebenkosten_vorauszahlung),0) "
                "FROM wohnungen w LEFT JOIN mieter m ON w.id=m.wohnung_id "
                "WHERE w.eigentuemer_id=? AND (m.auszug IS NULL OR m.auszug='')",
                (r["id"],)
            ).fetchone()[0]
            nk_sum = nk_sum or 0.0
            nk_info_frame = tk.Frame(woh_frame, bg=ACCENT)
            nk_info_frame.pack(fill="x", pady=(2, 0), ipady=4)
            nk_text = f"NK-Vorausz. gesamt: {nk_sum:.2f} €"
            tk.Label(nk_info_frame, text=nk_text, bg=ACCENT, fg=TEXT_WHITE,
                     font=FONT_H3).pack(anchor="w", padx=8)

            conn.close()

    def _on_save(self):
        v = self._get_values()
        if not v.get("name"):
            messagebox.showwarning("Pflichtfeld", "Name ist erforderlich.", parent=self); return
        self.result = v; self.destroy()

# ── Buchhaltung-Seite ─────────────────────────────────────────────────────────



class WohnungenPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_CARD)
        self._build()

    def _build(self):
        section_header(self, "Wohnungen", "＋ Wohnung", self._new)
        cols = ("Bezeichnung", "Typ", "Lage", "Fläche m²", "Zimmer", "MEA ‰", "Eigentümer", "Mieter")
        f, self.tree = make_table(self, cols, height=16)
        f.pack(fill="both", expand=True, padx=20, pady=10)
        for c, w in zip(cols, [120, 80, 100, 80, 70, 80, 150, 150]):
            self.tree.heading(c, text=c); self.tree.column(c, width=w, anchor="w")
        self.tree.bind("<Double-1>", self._edit)
        btn_row = tk.Frame(self, bg=BG_CARD)
        btn_row.pack(fill="x", padx=20, pady=(0, 10))
        if hat_recht("Wohnungen", "schreiben"):
            make_btn(btn_row, "✏ Bearbeiten", self._edit, color=BG_INPUT, fg=TEXT).pack(side="left", padx=(0, 8))
        if hat_recht("Wohnungen", "loeschen"):
            make_btn(btn_row, "🗑 Löschen", self._delete, color=DANGER).pack(side="left")
        self._load()

    def _load(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = get_db()
        rows = conn.execute("SELECT w.*, e.name as ename, e.vorname as evname, m.name as mname, m.vorname as mvname FROM wohnungen w LEFT JOIN eigentuemer e ON w.eigentuemer_id=e.id LEFT JOIN mieter m ON w.mieter_id=m.id ORDER BY w.bezeichnung").fetchall()
        for r in rows:
            ename = f"{r['evname'] or ''} {r['ename'] or ''}".strip() if r['ename'] else "–"
            mname = f"{r['mvname'] or ''} {r['mname'] or ''}".strip() if r['mname'] else "–"
            mea = f"{parse_float(r['mea_tausendstel']):.1f}" if r["mea_tausendstel"] else "–"
            self.tree.insert("", "end", iid=r["id"], values=(
                r["bezeichnung"], r["typ"] or "–", r["lage"] or "–",
                f"{parse_float(r['nutzflaeche_qm']):.1f}" if r["nutzflaeche_qm"] else "–",
                r["zimmer"] or "–", mea,
                ename, mname))
        conn.close()
        tree_empty_hint(self.tree)

    def _new(self):
        if not hat_recht("Wohnungen", "schreiben"):
            messagebox.showwarning("Berechtigung", "Sie haben keine Schreibberechtigung.", parent=self); return
        d = WohnungDialog(self)
        self.wait_window(d)
        if d.result:
            v = d.result
            conn = get_db()
            conn.execute("INSERT INTO wohnungen (bezeichnung,typ,lage,nutzflaeche_qm,zimmer,balkon,keller,stellplatz,heizungsart,mea_tausendstel,eigentuemer_id,mieter_id,miteigentumsanteil,baujahr,notizen) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (v["bezeichnung"], v["typ"], v["lage"], v["nutzflaeche_qm"] or None, v["zimmer"] or None,
                 v["balkon"], v["keller"], v["stellplatz"], v["heizungsart"], v["mea_tausendstel"] or None,
                 v["eigentuemer_id"] or None, v["mieter_id"] or None,
                 v["miteigentumsanteil"] or None, v["baujahr"] or None, v["notizen"]))
            conn.commit()
            sync_mea_eigentuemer(conn)   # #20 MEA-Sync
            conn.commit(); conn.close(); self._load()

    def _edit(self, event=None):
        if not hat_recht("Wohnungen", "schreiben"):
            messagebox.showwarning("Berechtigung", "Sie haben keine Schreibberechtigung.", parent=self); return
        sel = self.tree.selection()
        if not sel: return
        conn = get_db()
        row = conn.execute("SELECT * FROM wohnungen WHERE id=?", (int(sel[0]),)).fetchone()
        conn.close()
        d = WohnungDialog(self, row)
        self.wait_window(d)
        if d.result:
            v = d.result
            conn = get_db()
            conn.execute("UPDATE wohnungen SET bezeichnung=?,typ=?,lage=?,nutzflaeche_qm=?,zimmer=?,balkon=?,keller=?,stellplatz=?,heizungsart=?,mea_tausendstel=?,eigentuemer_id=?,mieter_id=?,miteigentumsanteil=?,baujahr=?,notizen=? WHERE id=?",
                (v["bezeichnung"], v["typ"], v["lage"], v["nutzflaeche_qm"] or None, v["zimmer"] or None,
                 v["balkon"], v["keller"], v["stellplatz"], v["heizungsart"], v["mea_tausendstel"] or None,
                 v["eigentuemer_id"] or None, v["mieter_id"] or None,
                 v["miteigentumsanteil"] or None, v["baujahr"] or None, v["notizen"], int(sel[0])))
            conn.commit()
            sync_mea_eigentuemer(conn)   # #20 MEA-Sync
            conn.commit(); conn.close(); self._load()

    def _delete(self):
        if not hat_recht("Wohnungen", "loeschen"):
            messagebox.showwarning("Berechtigung", "Sie haben keine Löschberechtigung.", parent=self); return
        sel = self.tree.selection()
        if not sel: return
        if messagebox.askyesno("Löschen", "Wohnung löschen?"):
            conn = get_db()
            conn.execute("DELETE FROM wohnungen WHERE id=?", (int(sel[0]),))
            conn.commit(); conn.close(); self._load()


class WohnungDialog(BaseDialog):
    def __init__(self, parent, row=None):
        super().__init__(parent, "Wohnung " + ("bearbeiten" if row else "hinzufügen"), 540, 700)
        r = dict(row) if row else {}

        self._add_field("Bezeichnung *", "bezeichnung", r.get("bezeichnung",""))
        # Row 1: Typ + Etage
        two = tk.Frame(self._body, bg=BG_CARD); two.pack(fill="x", padx=20); two.columnconfigure((0,1), weight=1)
        l = tk.Frame(two, bg=BG_CARD); l.grid(row=0, column=0, padx=(0,6), sticky="ew")
        ri = tk.Frame(two, bg=BG_CARD); ri.grid(row=0, column=1, padx=(6,0), sticky="ew")
        self._add_field("Typ", "typ", r.get("typ","Wohnung"), row=l)
        self._add_field("Etage", "etage", r.get("etage",""), row=ri)
        # Row 2: Lage + Fläche
        two = tk.Frame(self._body, bg=BG_CARD); two.pack(fill="x", padx=20); two.columnconfigure((0,1), weight=1)
        l = tk.Frame(two, bg=BG_CARD); l.grid(row=0, column=0, padx=(0,6), sticky="ew")
        ri = tk.Frame(two, bg=BG_CARD); ri.grid(row=0, column=1, padx=(6,0), sticky="ew")
        self._add_field("Lage", "lage", r.get("lage",""), row=l)
        self._add_field("Nutzfläche m²", "nutzflaeche_qm", r.get("nutzflaeche_qm",""), row=ri)
        # Row 3: Zimmer + Balkon
        two = tk.Frame(self._body, bg=BG_CARD); two.pack(fill="x", padx=20); two.columnconfigure((0,1), weight=1)
        l = tk.Frame(two, bg=BG_CARD); l.grid(row=0, column=0, padx=(0,6), sticky="ew")
        ri = tk.Frame(two, bg=BG_CARD); ri.grid(row=0, column=1, padx=(6,0), sticky="ew")
        self._add_field("Zimmer", "zimmer", r.get("zimmer",""), row=l)
        balkon_opt = ["Nein", "Ja"]
        cur_bal = balkon_opt[1] if r.get("balkon") else balkon_opt[0]
        self._add_field("Balkon", "balkon", cur_bal, widget_type="combo", options=balkon_opt, row=ri)
        # Row 4: Keller + Stellplatz
        two = tk.Frame(self._body, bg=BG_CARD); two.pack(fill="x", padx=20); two.columnconfigure((0,1), weight=1)
        l = tk.Frame(two, bg=BG_CARD); l.grid(row=0, column=0, padx=(0,6), sticky="ew")
        ri = tk.Frame(two, bg=BG_CARD); ri.grid(row=0, column=1, padx=(6,0), sticky="ew")
        self._add_field("Keller", "keller", r.get("keller",""), row=l)
        self._add_field("Stellplatz", "stellplatz", r.get("stellplatz",""), row=ri)

        self._add_field("Heizungsart", "heizungsart", r.get("heizungsart","Zentralheizung"))
        self._add_field("MEA Tausendstel (Miteigentumsanteil)", "mea_tausendstel", r.get("mea_tausendstel",""))
        self._add_field("Baujahr", "baujahr", r.get("baujahr",""))

        # Eigentümer-Dropdown
        conn = get_db()
        self._eigentuemer_list = conn.execute("SELECT id, vorname, name FROM eigentuemer ORDER BY name").fetchall()
        self._mieter_list = conn.execute("SELECT id, vorname, name FROM mieter ORDER BY name").fetchall()
        conn.close()

        et_options = ["– kein –"] + [f"{e['vorname'] or ''} {e['name']}".strip() for e in self._eigentuemer_list]
        mt_options = ["– kein –"] + [f"{m['vorname'] or ''} {m['name']}".strip() for m in self._mieter_list]

        cur_et = 0
        if r.get("eigentuemer_id"):
            for i, e in enumerate(self._eigentuemer_list):
                if e["id"] == r["eigentuemer_id"]: cur_et = i+1; break
        cur_mt = 0
        if r.get("mieter_id"):
            for i, m in enumerate(self._mieter_list):
                if m["id"] == r["mieter_id"]: cur_mt = i+1; break

        self._add_field("Eigentümer", "eigentuemer_str", et_options[cur_et], widget_type="combo", options=et_options)
        self._add_field("Mieter", "mieter_str", mt_options[cur_mt], widget_type="combo", options=mt_options)
        self._add_field("Notizen", "notizen", r.get("notizen",""), widget_type="text")

    def _on_save(self):
        v = self._get_values()
        if not v.get("bezeichnung"):
            messagebox.showwarning("Pflichtfeld", "Bezeichnung ist erforderlich.", parent=self); return

        # Convert balkon to 0/1
        v["balkon"] = 1 if v.get("balkon") == "Ja" else 0

        # Resolve Eigentümer-ID
        et_str = v.get("eigentuemer_str","")
        v["eigentuemer_id"] = None
        for e in self._eigentuemer_list:
            if f"{e['vorname'] or ''} {e['name']}".strip() == et_str:
                v["eigentuemer_id"] = e["id"]; break

        # Resolve Mieter-ID
        mt_str = v.get("mieter_str","")
        v["mieter_id"] = None
        for m in self._mieter_list:
            if f"{m['vorname'] or ''} {m['name']}".strip() == mt_str:
                v["mieter_id"] = m["id"]; break

        self.result = v; self.destroy()

# ── Buchhaltung-Seite ─────────────────────────────────────────────────────────

class BuchhaltungPage(tk.Frame):
    """Buchhaltung mit drei Sub-Tabs:
    1. Buchungen   – manuelle & bestätigte Zahlungen
    2. Vorschläge  – neue Kontoauszug-Einträge warten auf Zuordnung
    3. Regeln      – gelernte Buchungsregeln verwalten
    """

    # Kostenkategorien – zentral aus WEG_KATEGORIEN (einheitliches System)
    KATEGORIEN = WEG_KATEGORIEN_LISTE[:]
    # Metadaten für Kostenarten aus dem globalen System ableiten
    KOSTENARTEN = {
        k: {"kategorie": v[0], "umlagefaehig": v[1], "schluessel": v[2]}
        for k, v in WEG_KATEGORIEN.items()
    }

    def __init__(self, parent):
        super().__init__(parent, bg=BG_CARD)
        self._active_tab = "buchungen"
        # Custom-Kategorien aus Config in Klassenliste laden (#36 fix)
        self._sync_kategorien_from_config()
        self._build()

    @classmethod
    def _sync_kategorien_from_config(cls):
        """Lädt custom_kategorien und deaktivierte_kategorien aus Config
        in die Klassenvariablen KATEGORIEN und KOSTENARTEN (einmalig bei Init)."""
        cfg = load_config()
        custom = cfg.get("custom_kategorien", [])
        for c in custom:
            name = c.get("name", "")
            if name and name not in cls.KATEGORIEN:
                cls.KATEGORIEN.insert(-1, name)   # vor "Kategorie offen"
            if name and name not in cls.KOSTENARTEN:
                cls.KOSTENARTEN[name] = {
                    "kategorie": c.get("kategorie", "Sonstiges"),
                    "umlagefaehig": c.get("umlagefaehig", False),
                    "schluessel": c.get("schluessel", "–"),
                }

    # ── Aufbau ────────────────────────────────────────────────────────────────

    def _build(self):
        # ── Kopfzeile ─────────────────────────────────────────────────────────
        top = tk.Frame(self, bg=BG_CARD)
        top.pack(fill="x", padx=20, pady=(16, 0))
        self._saldo_label = tk.Label(top, text="", bg=BG_CARD, fg=TEXT, font=FONT_H2)
        self._saldo_label.pack(side="left")
        make_btn(top, "＋ Buchung",       self._new_zahlung).pack(side="right")
        make_btn(top, "📄 Jahresabschluss", self._jahresabschluss_pdf,
                 color=BG_INPUT, fg=TEXT).pack(side="right", padx=(0, 8))
        make_btn(top, "📊 Export CSV",  self._export_csv,
                 color=BG_INPUT, fg=TEXT).pack(side="right", padx=(0, 8))

        # ── Sub-Tab-Leiste ─────────────────────────────────────────────────────
        self._tab_btns = {}
        tab_bar = tk.Frame(self, bg=BG_CARD)
        tab_bar.pack(fill="x", padx=20, pady=(8, 0))
        for tid, label in [("buchungen",  "📒  Buchungen"),
                            ("vorschlaege","🔔  Kontoauszug Vorschläge"),
                            ("regeln",    "⚙  Buchungsregeln"),
                            ("kostenarten","📋  Kostenarten"),
                            ("wohngeld",  "💰  Wohngeld Soll/Ist")]:
            btn = tk.Button(tab_bar, text=label, font=FONT_NAV, relief="flat", bd=0,
                            padx=14, pady=7, cursor="hand2",
                            command=lambda t=tid: self._switch_tab(t))
            btn.pack(side="left", padx=2)
            self._tab_btns[tid] = btn
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(4, 0))

        # ── Filter-Zeile (nur Buchungen-Tab) ──────────────────────────────────
        self._filter_frame = tk.Frame(self, bg=BG_CARD)
        self._filter_frame.pack(fill="x", padx=20, pady=(4, 0))
        tk.Label(self._filter_frame, text="Typ:", bg=BG_CARD,
                 fg=TEXT_LIGHT, font=FONT_SMALL).pack(side="left")
        self._typ_var = tk.StringVar(value="Alle")
        for t in ("Alle", "Einnahme", "Ausgabe"):
            tk.Radiobutton(self._filter_frame, text=t, variable=self._typ_var, value=t,
                           bg=BG_CARD, fg=TEXT, font=FONT_SMALL,
                           activebackground=BG_CARD, selectcolor=BG_CARD,
                           command=self._load_buchungen).pack(side="left", padx=6)

        # ── Haupt-Content-Bereich ──────────────────────────────────────────────
        self._content = tk.Frame(self, bg=BG_CARD)
        self._content.pack(fill="both", expand=True, padx=0, pady=0)

        # Buchungen-View
        self._view_buchungen = tk.Frame(self._content, bg=BG_CARD)
        cols_b = ("Datum", "Beschreibung", "Kategorie", "Betrag", "Typ", "Status", "Belegnr.", "📎")
        fb, self.tree_b = make_table(self._view_buchungen, cols_b, height=13)
        fb.pack(fill="both", expand=True, padx=20, pady=6)
        for c, w in zip(cols_b, [90, 210, 110, 100, 80, 80, 80, 28]):
            self.tree_b.heading(c, text=c); self.tree_b.column(c, width=w, anchor="w")
        self.tree_b.tag_configure("einnahme", foreground=SUCCESS)
        self.tree_b.tag_configure("ausgabe",  foreground=DANGER)
        self.tree_b.tag_configure("neu", foreground=ACCENT2, font=("Segoe UI Semibold", 10))
        self.tree_b.bind("<Double-1>", self._edit_buchung)
        btn_b = tk.Frame(self._view_buchungen, bg=BG_CARD)
        btn_b.pack(fill="x", padx=20, pady=(0, 8))
        make_btn(btn_b, "✏ Bearbeiten",       self._edit_buchung, color=BG_INPUT, fg=TEXT).pack(side="left", padx=(0,6))
        make_btn(btn_b, "🗑 Löschen",         self._delete_buchung, color=DANGER).pack(side="left", padx=(0,6))
        make_btn(btn_b, "📎 Beleg öffnen",    self._beleg_oeffnen, color=BG_INPUT, fg=TEXT).pack(side="left")

        # Vorschläge-View
        self._view_vorschlaege = tk.Frame(self._content, bg=BG_CARD)
        # Konto-Filter für Vorschläge
        vs_filter = tk.Frame(self._view_vorschlaege, bg=BG_CARD)
        vs_filter.pack(fill="x", padx=20, pady=(6, 2))
        tk.Label(vs_filter, text="Neue Kontoauszug-Buchungen → Kategorie zuweisen und übernehmen",
            bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(side="left")
        tk.Label(vs_filter, text="  Konto:", bg=BG_CARD, fg=TEXT_LIGHT,
                 font=FONT_SMALL).pack(side="left", padx=(12, 0))
        self._vs_konto_var = tk.StringVar(value="Alle")
        self._vs_konto_combo = ttk.Combobox(vs_filter, textvariable=self._vs_konto_var,
                                             state="readonly", font=FONT_SMALL, width=30)
        self._vs_konto_combo.pack(side="left", padx=(4, 0))
        self._vs_konto_combo.bind("<<ComboboxSelected>>", lambda e: self._load_vorschlaege())

        cols_v = ("Datum", "Auftraggeber", "Verwendungszweck", "Betrag", "Konto", "Vorschlag Kat.")
        fv, self.tree_v = make_table(self._view_vorschlaege, cols_v, height=12)
        fv.pack(fill="both", expand=True, padx=20, pady=4)
        for c, w in zip(cols_v, [88, 180, 250, 100, 90, 120]):
            self.tree_v.heading(c, text=c); self.tree_v.column(c, width=w, anchor="w")
        self.tree_v.tag_configure("mit_vorschlag", foreground="#2E7D32")
        # Mehrfachauswahl aktivieren
        self.tree_v.configure(selectmode="extended")
        btn_v = tk.Frame(self._view_vorschlaege, bg=BG_CARD)
        btn_v.pack(fill="x", padx=20, pady=(0, 8))
        make_btn(btn_v, "✔ Übernehmen",              self._uebernehmen,      color=SUCCESS).pack(side="left", padx=(0,6))
        make_btn(btn_v, "✔✔ Alle grünen übernehmen", self._batch_uebernehmen,color="#2E7D32").pack(side="left", padx=(0,6))
        make_btn(btn_v, "✏ Kategorie korrigieren",    self._korrigieren,      color=ACCENT2).pack(side="left", padx=(0,6))
        make_btn(btn_v, "✗ Falsch zugeordnet",        self._falsch_markieren, color=DANGER).pack(side="left")

        # Regeln-View
        self._view_regeln = tk.Frame(self._content, bg=BG_CARD)
        info_r = tk.Label(self._view_regeln,
            text="Automatisch gelernte Zuordnungsregeln — können hier korrigiert oder gelöscht werden",
            bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL)
        info_r.pack(anchor="w", padx=20, pady=(6, 2))
        cols_r = ("Muster", "Kategorie", "Typ", "Konto", "Treffer", "Korrektur")
        fr, self.tree_r = make_table(self._view_regeln, cols_r, height=12)
        fr.pack(fill="both", expand=True, padx=20, pady=4)
        for c, w in zip(cols_r, [220, 130, 90, 110, 70, 80]):
            self.tree_r.heading(c, text=c); self.tree_r.column(c, width=w, anchor="w")
        btn_r = tk.Frame(self._view_regeln, bg=BG_CARD)
        btn_r.pack(fill="x", padx=20, pady=(0, 8))
        make_btn(btn_r, "✏ Korrigieren", self._edit_regel, color=BG_INPUT, fg=TEXT).pack(side="left", padx=(0,6))
        make_btn(btn_r, "🗑 Löschen",    self._delete_regel, color=DANGER).pack(side="left")

        # Kostenarten-View
        self._view_kostenarten = tk.Frame(self._content, bg=BG_CARD)
        info_k = tk.Label(self._view_kostenarten,
            text="WEG-Kostenkategorien verwalten — deaktivierte Kategorien können nicht mehr zugewiesen werden",
            bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL)
        info_k.pack(anchor="w", padx=20, pady=(6, 2))
        cols_k = ("Kategorie", "Oberkategorie", "Umlagefähig", "Schlüssel", "Status", "Verwendungen")
        fk, self.tree_k = make_table(self._view_kostenarten, cols_k, height=14)
        fk.pack(fill="both", expand=True, padx=20, pady=4)
        for c, w in zip(cols_k, [180, 180, 100, 140, 80, 100]):
            self.tree_k.heading(c, text=c); self.tree_k.column(c, width=w, anchor="w")
        self.tree_k.tag_configure("deaktiviert", foreground=TEXT_LIGHT)
        btn_k = tk.Frame(self._view_kostenarten, bg=BG_CARD)
        btn_k.pack(fill="x", padx=20, pady=(0, 8))
        make_btn(btn_k, "＋ Neue Kategorie", self._new_kostenart, color=ACCENT2).pack(side="left", padx=(0,6))
        make_btn(btn_k, "✏ Bearbeiten", self._edit_kostenart, color=BG_INPUT, fg=TEXT).pack(side="left", padx=(0,6))
        make_btn(btn_k, "🔄 Aktivieren/Deaktivieren", self._toggle_kostenart, color=WARNING, fg=TEXT_WHITE).pack(side="left", padx=(0,6))
        make_btn(btn_k, "🗑 Löschen", self._delete_kostenart, color=DANGER).pack(side="left")

        # ── Tab Wohngeld Soll/Ist (#19) ───────────────────────────────────────
        self._view_wohngeld = tk.Frame(self._content, bg=BG_CARD)
        wg_top = tk.Frame(self._view_wohngeld, bg=BG_CARD)
        wg_top.pack(fill="x", padx=20, pady=(10, 4))
        tk.Label(wg_top, text="Jahr:", bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(side="left")
        self._wg_jahr = tk.StringVar(value=str(date.today().year))
        ttk.Combobox(wg_top, textvariable=self._wg_jahr, width=8,
                     values=[str(y) for y in range(date.today().year, date.today().year - 6, -1)]
                     ).pack(side="left", padx=6)
        make_btn(wg_top, "🔄 Auswertung", self._load_wohngeld).pack(side="left")

        self._wg_kpi = tk.Frame(self._view_wohngeld, bg=BG_CARD)
        self._wg_kpi.pack(fill="x", padx=20, pady=(6, 4))

        tk.Label(self._view_wohngeld,
                 text="Wohngeld-Einnahmen pro Eigentümer (Ist) vs. Kostenpflicht (Soll nach MEA)",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w", padx=20)
        cols_wg = ("Eigentümer", "MEA %", "Soll (Kostenanteil)", "Ist (gezahlt)", "Saldo", "Status")
        fwg, self._tree_wg = make_table(self._view_wohngeld, cols_wg, height=12)
        fwg.pack(fill="both", expand=True, padx=20, pady=(2, 8))
        for c, w in zip(cols_wg, [180, 60, 140, 140, 110, 100]):
            self._tree_wg.heading(c, text=c)
            self._tree_wg.column(c, width=w, anchor="w")

        self._switch_tab("buchungen")

    # ── Tab-Umschalten ────────────────────────────────────────────────────────

    def _switch_tab(self, tab: str):
        self._active_tab = tab
        # Button-Styling
        for tid, btn in self._tab_btns.items():
            if tid == tab:
                btn.config(bg=ACCENT2, fg=TEXT_WHITE)
            else:
                btn.config(bg=BG_CARD, fg=TEXT_LIGHT)
        # Filter-Zeile nur bei Buchungen
        self._filter_frame.pack_forget()
        # Views ein-/ausblenden
        for v in [self._view_buchungen, self._view_vorschlaege, self._view_regeln,
                  self._view_kostenarten, self._view_wohngeld]:
            v.pack_forget()
        if tab == "buchungen":
            self._filter_frame.pack(fill="x", padx=20, pady=(4, 0))
            self._view_buchungen.pack(fill="both", expand=True)
            self._load_buchungen()
        elif tab == "vorschlaege":
            self._view_vorschlaege.pack(fill="both", expand=True)
            self._load_vorschlaege()
        elif tab == "regeln":
            self._view_regeln.pack(fill="both", expand=True)
            self._load_regeln()
        elif tab == "kostenarten":
            self._view_kostenarten.pack(fill="both", expand=True)
            self._load_kostenarten()
        elif tab == "wohngeld":
            self._view_wohngeld.pack(fill="both", expand=True)
            self._load_wohngeld()

    # ── Tab 1: Buchungen ──────────────────────────────────────────────────────

    def _load_buchungen(self):
        for i in self.tree_b.get_children(): self.tree_b.delete(i)
        conn = get_db()
        typ = self._typ_var.get()
        # Parametrisierte Abfrage – kein String-Formatting (SQL-Injection-Schutz)
        if typ != "Alle":
            rows = conn.execute(
                "SELECT * FROM zahlungen WHERE typ=? ORDER BY datum DESC, erstellt_am DESC",
                (typ,)).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM zahlungen ORDER BY datum DESC, erstellt_am DESC").fetchall()
        einnahmen = ausgaben = 0.0
        for r in rows:
            rd = dict(r)
            status = rd.get("status") or "Geprüft"
            tags_list = ["einnahme" if rd["typ"] == "Einnahme" else "ausgabe"]
            if status == "Neu":
                tags_list.append("neu")
            beleg_ind = "📎" if rd.get("beleg_dateipfad") else ""
            self.tree_b.insert("", "end", iid=rd["id"], values=(
                fmt_date(rd["datum"]), rd["beschreibung"] or "–",
                rd["kategorie"] or "–", fmt_euro(rd["betrag"]),
                rd["typ"], status, rd["belegnr"] or "–", beleg_ind), tags=tuple(tags_list))
            if rd["typ"] == "Einnahme": einnahmen += rd["betrag"] or 0
            else:                       ausgaben  += abs(rd["betrag"] or 0)
        conn.close()
        tree_empty_hint(self.tree_b)
        saldo = einnahmen - ausgaben
        color = SUCCESS if saldo >= 0 else DANGER
        self._saldo_label.config(
            text=(f"Saldo: {fmt_euro(saldo)}   |   "
                  f"Einnahmen: {fmt_euro(einnahmen)}   "
                  f"Ausgaben: {fmt_euro(ausgaben)}"),
            fg=color)

    def _new_zahlung(self):
        if not hat_recht("Buchhaltung", "schreiben"):
            messagebox.showwarning("Berechtigung", "Keine Schreibberechtigung.", parent=self); return
        d = ZahlungDialog(self)
        self.wait_window(d)
        if d.result:
            v = d.result
            betrag = float(v["betrag"] or 0)
            if v["typ"] == "Ausgabe": betrag = -abs(betrag)
            conn = get_db()
            conn.execute(
                "INSERT INTO zahlungen (datum,betrag,typ,kategorie,beschreibung,belegnr,status,beleg_dateipfad,rechnungssteller,abrechnungsrelevant,abrechnungsjahr) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (v["datum"], betrag, v["typ"], v["kategorie"], v["beschreibung"], v["belegnr"],
                 v.get("status", "Geprüft"), v.get("beleg_dateipfad"),
                 v.get("rechnungssteller") or None, v.get("abrechnungsrelevant", 1),
                 v.get("abrechnungsjahr") or None))
            conn.commit(); conn.close()
            if self._active_tab == "buchungen": self._load_buchungen()

    def _edit_buchung(self, event=None):
        if not hat_recht("Buchhaltung", "schreiben"):
            messagebox.showwarning("Berechtigung", "Keine Schreibberechtigung.", parent=self); return
        sel = self.tree_b.selection()
        if not sel: return
        conn = get_db()
        row = conn.execute("SELECT * FROM zahlungen WHERE id=?", (int(sel[0]),)).fetchone()
        conn.close()
        d = ZahlungDialog(self, row)
        self.wait_window(d)
        if d.result:
            v = d.result
            betrag = float(v["betrag"] or 0)
            if v["typ"] == "Ausgabe": betrag = -abs(betrag)
            conn = get_db()
            conn.execute(
                "UPDATE zahlungen SET datum=?,betrag=?,typ=?,kategorie=?,beschreibung=?,belegnr=?,status=?,beleg_dateipfad=?,rechnungssteller=?,abrechnungsrelevant=?,abrechnungsjahr=? "
                "WHERE id=?",
                (v["datum"], betrag, v["typ"], v["kategorie"],
                 v["beschreibung"], v["belegnr"], v.get("status", "Geprüft"),
                 v.get("beleg_dateipfad"), v.get("rechnungssteller") or None,
                 v.get("abrechnungsrelevant", 1), v.get("abrechnungsjahr") or None, int(sel[0])))
            conn.commit(); conn.close()
            self._load_buchungen()

    def _beleg_oeffnen(self):
        """Öffnet die hinterlegte Beleg-Datei der ausgewählten Buchung."""
        sel = self.tree_b.selection()
        if not sel:
            messagebox.showinfo("Hinweis", "Bitte eine Buchung auswählen.", parent=self); return
        conn = get_db()
        row = conn.execute("SELECT beleg_dateipfad FROM zahlungen WHERE id=?", (int(sel[0]),)).fetchone()
        conn.close()
        pfad = row["beleg_dateipfad"] if row else None
        if not pfad:
            messagebox.showinfo("Kein Beleg", "Für diese Buchung ist kein Beleg hinterlegt.", parent=self)
            return
        import os, subprocess, sys
        if not os.path.exists(pfad):
            messagebox.showerror("Datei nicht gefunden", f"Die Datei wurde nicht gefunden:\n{pfad}", parent=self)
            return
        try:
            if sys.platform == "win32":
                os.startfile(pfad)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", pfad])
            else:
                subprocess.Popen(["xdg-open", pfad])
        except Exception as e:
            messagebox.showerror("Fehler", f"Datei konnte nicht geöffnet werden:\n{e}", parent=self)

    def _delete_buchung(self):
        if not hat_recht("Buchhaltung", "loeschen"):
            messagebox.showwarning("Berechtigung", "Keine Löschberechtigung.", parent=self); return
        sel = self.tree_b.selection()
        if not sel: return
        anzahl = len(sel)
        frage = f"{anzahl} Buchung(en) unwiderruflich löschen?" if anzahl > 1 else "Buchung unwiderruflich löschen?"
        if messagebox.askyesno("Löschen", frage):
            conn = get_db()
            for iid in sel:
                conn.execute("DELETE FROM zahlungen WHERE id=?", (int(iid),))
            conn.commit(); conn.close()
            self._load_buchungen()

    def _jahresabschluss_pdf(self):
        """#22 Jahresabschluss-PDF: Vollständige Einnahmen/Ausgaben-Übersicht als A4-Dokument."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                            Paragraph, Spacer, HRFlowable)
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
        except ImportError:
            messagebox.showerror("Fehler",
                "reportlab nicht installiert.\nBitte 'pip install reportlab' ausführen.",
                parent=self)
            return

        # Jahr per Dialog erfragen
        jahr_str = simpledialog.askstring(
            "Jahresabschluss", "Jahr eingeben (z.B. 2025):",
            initialvalue=str(date.today().year - 1), parent=self)
        if not jahr_str:
            return
        try:
            jahr = int(jahr_str.strip())
        except ValueError:
            messagebox.showwarning("Jahr", "Bitte eine gültige Jahreszahl eingeben.", parent=self)
            return

        conn = get_db()
        # Einnahmen nach Kategorie
        ein_rows = conn.execute(
            "SELECT kategorie, SUM(betrag) as s FROM zahlungen "
            "WHERE typ='Einnahme' AND strftime('%Y',datum)=? GROUP BY kategorie ORDER BY s DESC",
            (str(jahr),)).fetchall()
        # Ausgaben nach Kategorie
        aus_rows = conn.execute(
            "SELECT kategorie, SUM(betrag) as s FROM zahlungen "
            "WHERE typ='Ausgabe' AND strftime('%Y',datum)=? GROUP BY kategorie ORDER BY s DESC",
            (str(jahr),)).fetchall()
        # Monatliche Übersicht
        monat_rows = conn.execute(
            "SELECT strftime('%m',datum) as m, "
            "SUM(CASE WHEN typ='Einnahme' THEN betrag ELSE 0 END) as ein, "
            "SUM(CASE WHEN typ='Ausgabe' THEN betrag ELSE 0 END) as aus "
            "FROM zahlungen WHERE strftime('%Y',datum)=? GROUP BY m ORDER BY m",
            (str(jahr),)).fetchall()
        conn.close()

        total_ein = sum(r["s"] or 0 for r in ein_rows)
        total_aus = sum(r["s"] or 0 for r in aus_rows)
        jahres_saldo = total_ein - total_aus

        pfad = filedialog.asksaveasfilename(
            parent=self, title="Jahresabschluss speichern",
            defaultextension=".pdf",
            initialfile=f"WEG_Jahresabschluss_{jahr}.pdf",
            filetypes=[("PDF-Dokument", "*.pdf")])
        if not pfad:
            return

        try:
            cfg = load_settings()
            weg_name = cfg.get("weg_name") or "WEG Hausverwaltung"

            doc = SimpleDocTemplate(pfad, pagesize=A4,
                                    leftMargin=2*cm, rightMargin=2*cm,
                                    topMargin=2*cm, bottomMargin=2*cm)
            styles = getSampleStyleSheet()
            H1 = ParagraphStyle("H1", parent=styles["Heading1"],
                                 fontSize=18, textColor=colors.HexColor("#1C2B3A"))
            H2 = ParagraphStyle("H2", parent=styles["Heading2"],
                                 fontSize=13, textColor=colors.HexColor("#1C2B3A"))
            SMALL = ParagraphStyle("sm", parent=styles["Normal"], fontSize=8,
                                   textColor=colors.HexColor("#666666"))
            BOLD  = ParagraphStyle("bd", parent=styles["Normal"], fontSize=10,
                                   fontName="Helvetica-Bold")

            story = [
                Paragraph(weg_name, H1),
                Paragraph(f"Jahresabschluss {jahr} – Einnahmen & Ausgaben", H2),
                Paragraph(f"Erstellt am {date.today().strftime('%d.%m.%Y')}", SMALL),
                Spacer(1, 0.4*cm),
            ]

            # ── Gesamtübersicht ──
            kpi_data = [
                ["Gesamteinnahmen",  fmt_euro(total_ein)],
                ["Gesamtausgaben",   fmt_euro(total_aus)],
                ["Jahresüberschuss" if jahres_saldo >= 0 else "Jahresfehlbetrag",
                 fmt_euro(jahres_saldo)],
            ]
            kpi_t = Table(kpi_data, colWidths=[10*cm, 5*cm])
            kpi_t.setStyle(TableStyle([
                ("FONTNAME",   (0,0), (-1,-1), "Helvetica"),
                ("FONTSIZE",   (0,0), (-1,-1), 11),
                ("FONTNAME",   (0,-1), (-1,-1), "Helvetica-Bold"),
                ("ALIGN",      (1,0), (1,-1), "RIGHT"),
                ("ROWBACKGROUNDS", (0,0), (-1,-1),
                 [colors.HexColor("#F7F5F0"), colors.HexColor("#EEEAE3"),
                  colors.HexColor("#D4EDDA") if jahres_saldo >= 0 else colors.HexColor("#FADADD")]),
                ("GRID",       (0,0), (-1,-1), 0.4, colors.HexColor("#CCCCCC")),
                ("TOPPADDING", (0,0), (-1,-1), 6), ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ]))
            story += [kpi_t, Spacer(1, 0.5*cm)]

            # ── Einnahmen ──
            story.append(Paragraph("Einnahmen nach Kategorie", H2))
            ein_data = [["Kategorie", "Betrag"]]
            for r in ein_rows:
                ein_data.append([r["kategorie"] or "–", fmt_euro(r["s"] or 0)])
            ein_data.append(["Gesamt Einnahmen", fmt_euro(total_ein)])
            ein_t = Table(ein_data, colWidths=[12*cm, 5*cm])
            ein_t.setStyle(TableStyle([
                ("BACKGROUND",  (0,0), (-1,0),  colors.HexColor("#3A7D44")),
                ("TEXTCOLOR",   (0,0), (-1,0),  colors.white),
                ("FONTNAME",    (0,0), (-1,0),  "Helvetica-Bold"),
                ("FONTSIZE",    (0,0), (-1,-1), 9),
                ("ALIGN",       (1,1), (1,-1),  "RIGHT"),
                ("ROWBACKGROUNDS", (0,1), (-1,-2),
                 [colors.white, colors.HexColor("#F7F5F0")]),
                ("BACKGROUND",  (0,-1), (-1,-1), colors.HexColor("#D4EDDA")),
                ("FONTNAME",    (0,-1), (-1,-1), "Helvetica-Bold"),
                ("GRID",        (0,0), (-1,-1), 0.4, colors.HexColor("#CCCCCC")),
                ("TOPPADDING",  (0,0), (-1,-1), 4), ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ]))
            story += [ein_t, Spacer(1, 0.4*cm)]

            # ── Ausgaben ──
            story.append(Paragraph("Ausgaben nach Kategorie", H2))
            aus_data = [["Kategorie", "Betrag"]]
            for r in aus_rows:
                aus_data.append([r["kategorie"] or "–", fmt_euro(r["s"] or 0)])
            aus_data.append(["Gesamt Ausgaben", fmt_euro(total_aus)])
            aus_t = Table(aus_data, colWidths=[12*cm, 5*cm])
            aus_t.setStyle(TableStyle([
                ("BACKGROUND",  (0,0), (-1,0),  colors.HexColor("#C0392B")),
                ("TEXTCOLOR",   (0,0), (-1,0),  colors.white),
                ("FONTNAME",    (0,0), (-1,0),  "Helvetica-Bold"),
                ("FONTSIZE",    (0,0), (-1,-1), 9),
                ("ALIGN",       (1,1), (1,-1),  "RIGHT"),
                ("ROWBACKGROUNDS", (0,1), (-1,-2),
                 [colors.white, colors.HexColor("#F7F5F0")]),
                ("BACKGROUND",  (0,-1), (-1,-1), colors.HexColor("#FADADD")),
                ("FONTNAME",    (0,-1), (-1,-1), "Helvetica-Bold"),
                ("GRID",        (0,0), (-1,-1), 0.4, colors.HexColor("#CCCCCC")),
                ("TOPPADDING",  (0,0), (-1,-1), 4), ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ]))
            story += [aus_t, Spacer(1, 0.4*cm)]

            # ── Monatliche Übersicht ──
            if monat_rows:
                story.append(Paragraph("Monatliche Übersicht", H2))
                monate = ["Jan","Feb","Mär","Apr","Mai","Jun",
                          "Jul","Aug","Sep","Okt","Nov","Dez"]
                mon_data = [["Monat", "Einnahmen", "Ausgaben", "Monatssaldo"]]
                for r in monat_rows:
                    mi = int(r["m"]) - 1
                    mon = monate[mi] if 0 <= mi < 12 else r["m"]
                    ein_m = r["ein"] or 0
                    aus_m = r["aus"] or 0
                    saldo_m = ein_m - aus_m
                    mon_data.append([
                        f"{mon} {jahr}", fmt_euro(ein_m), fmt_euro(aus_m),
                        fmt_euro(saldo_m)])
                mon_t = Table(mon_data, colWidths=[3.5*cm, 4*cm, 4*cm, 4.5*cm])
                mon_t.setStyle(TableStyle([
                    ("BACKGROUND",  (0,0), (-1,0),  colors.HexColor("#1C2B3A")),
                    ("TEXTCOLOR",   (0,0), (-1,0),  colors.white),
                    ("FONTNAME",    (0,0), (-1,0),  "Helvetica-Bold"),
                    ("FONTSIZE",    (0,0), (-1,-1), 9),
                    ("ALIGN",       (1,1), (-1,-1), "RIGHT"),
                    ("ROWBACKGROUNDS", (0,1), (-1,-1),
                     [colors.white, colors.HexColor("#F7F5F0")]),
                    ("GRID",        (0,0), (-1,-1), 0.4, colors.HexColor("#CCCCCC")),
                    ("TOPPADDING",  (0,0), (-1,-1), 4), ("BOTTOMPADDING", (0,0), (-1,-1), 4),
                ]))
                story.append(mon_t)

            doc.build(story)
            if messagebox.askyesno("PDF erstellt",
                f"Jahresabschluss {jahr} gespeichert:\n{pfad}\n\nJetzt öffnen?", parent=self):
                try:
                    if os.name == "nt":
                        os.startfile(pfad)
                    elif os.uname().sysname == "Darwin":
                        subprocess.Popen(["open", pfad])
                    else:
                        subprocess.Popen(["xdg-open", pfad])
                except Exception:
                    pass
        except Exception as exc:
            messagebox.showerror("PDF-Fehler", f"PDF konnte nicht erstellt werden:\n{exc}",
                                 parent=self)

    def _export_csv(self):
        """#31 CSV-Export mit optionalem Jahres- und Typfilter."""
        # Jahreseingabe
        jahr_str = simpledialog.askstring(
            "CSV-Export",
            "Jahr eingeben (leer = alle Jahre):",
            initialvalue=str(date.today().year), parent=self)
        if jahr_str is None:   # Abbruch
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv",
            filetypes=[("CSV", "*.csv")], title="Buchungen exportieren",
            initialfile=f"Buchungen_{jahr_str.strip() or 'alle'}.csv")
        if not path: return
        conn = get_db()
        typ = self._typ_var.get()
        params: list = []
        where_clauses = []
        if jahr_str.strip():
            try:
                int(jahr_str.strip())  # Validierung
                where_clauses.append("strftime('%Y',datum)=?")
                params.append(jahr_str.strip())
            except ValueError:
                messagebox.showwarning("Jahr", "Ungültiges Jahr — alle Jahre werden exportiert.",
                                       parent=self)
        if typ != "Alle":
            where_clauses.append("typ=?")
            params.append(typ)
        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        rows = conn.execute(
            f"SELECT datum,beschreibung,kategorie,betrag,typ,belegnr "
            f"FROM zahlungen {where_sql} ORDER BY datum DESC",
            params).fetchall()
        conn.close()
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["Datum", "Beschreibung", "Kategorie", "Betrag", "Typ", "Belegnr."])
            for r in rows:
                w.writerow([fmt_date(r[0]), r[1], r[2],
                             str(r[3]).replace(".", ","), r[4], r[5]])
        messagebox.showinfo("Export",
            f"Exportiert: {os.path.basename(path)}\n{len(rows)} Buchungen")

    # ── Tab 2: Kontoauszug-Vorschläge ─────────────────────────────────────────

    def _load_vorschlaege(self):
        for i in self.tree_v.get_children(): self.tree_v.delete(i)
        conn = get_db()
        # Konto-Filter aktualisieren
        konten_raw = conn.execute(
            "SELECT DISTINCT iban FROM kontoauszug "
            "WHERE iban IS NOT NULL AND iban != '' "
            "AND (als_buchung_uebernommen IS NULL OR als_buchung_uebernommen=0) "
            "AND (falsch_zugeordnet IS NULL OR falsch_zugeordnet=0) "
            "ORDER BY iban"
        ).fetchall()
        cfg = load_config()
        konto_labels = ["Alle"]
        self._vs_iban_map = {"Alle": None}
        for kr in konten_raw:
            iban = kr["iban"]
            # Bezeichnung aus Einstellungen
            label = KontoauszugPage._konto_bezeichnung(None, iban, cfg)
            konto_labels.append(label)
            self._vs_iban_map[label] = iban
        self._vs_konto_combo["values"] = konto_labels
        if self._vs_konto_var.get() not in konto_labels:
            self._vs_konto_var.set("Alle")

        selected_iban = self._vs_iban_map.get(self._vs_konto_var.get())
        q = ("SELECT * FROM kontoauszug "
             "WHERE (als_buchung_uebernommen IS NULL OR als_buchung_uebernommen=0) "
             "AND (falsch_zugeordnet IS NULL OR falsch_zugeordnet=0) ")
        params = []
        if selected_iban:
            q += "AND iban=? "
            params.append(selected_iban)
        q += "ORDER BY datum DESC, id DESC"
        rows = conn.execute(q, params).fetchall()
        conn.close()
        for row in rows:
            r = dict(row)
            raw = r["buchungstext"] or ""
            gegenkonto = raw.split("||")[0] if "||" in raw else ""
            vzweck     = raw.split("||")[1] if "||" in raw else raw
            vorschlag  = r.get("kategorie_vorschlag") or vorschlag_kategorie(raw)[0]  # 4. Rückgabewert ignoriert
            tag = "mit_vorschlag" if vorschlag else ""
            iban_kurz = f"···{r['iban'][-8:]}" if r.get("iban") else r.get("konto_typ") or "–"
            self.tree_v.insert("", "end", iid=r["id"], values=(
                fmt_date(r["datum"]),
                gegenkonto or "–",
                vzweck or "–",
                fmt_euro(r["betrag"] or 0),
                iban_kurz,
                vorschlag or "–"),
                tags=(tag,) if tag else ())

    def _uebernehmen(self):
        """Kontoauszug-Eintrag als Buchung in zahlungen übernehmen."""
        sel = self.tree_v.selection()
        if not sel:
            messagebox.showinfo("Hinweis", "Bitte einen Eintrag auswählen.", parent=self)
            return
        if not hat_recht("Buchhaltung", "schreiben"):
            messagebox.showwarning("Berechtigung", "Keine Schreibberechtigung.", parent=self)
            return
        conn = get_db()
        row_raw = conn.execute("SELECT * FROM kontoauszug WHERE id=?", (int(sel[0]),)).fetchone()
        conn.close()
        if not row_raw:
            messagebox.showwarning("Fehler", "Eintrag nicht gefunden.", parent=self)
            return
        row = dict(row_raw)
        raw = row["buchungstext"] or ""
        gegenkonto = raw.split("||")[0] if "||" in raw else ""
        vzweck     = raw.split("||")[1] if "||" in raw else raw
        kat_v, typ_v, kto_v, _ = vorschlag_kategorie(raw)  # Konfidenz ignoriert
        # Vorhandenen Kategorie-Vorschlag bevorzugen
        kat_v = row.get("kategorie_vorschlag") or kat_v
        kt = row.get("konto_typ") or kto_v or "Wohngeldkonto"

        # Vorbelegter ZahlungDialog
        pseudo = {
            "datum":       row["datum"] or date.today().isoformat(),
            "betrag":      abs(row["betrag"] or 0),
            "typ":         "Einnahme" if (row["betrag"] or 0) >= 0 else "Ausgabe",
            "kategorie":   kat_v,
            "beschreibung": f"{gegenkonto} – {vzweck}".strip(" –"),
            "belegnr":     "",
            "status":      "Neu",
        }
        d = ZahlungDialog(self, pseudo)
        self.wait_window(d)
        if d.result:
            v = d.result
            betrag = float(v["betrag"] or 0)
            if v["typ"] == "Ausgabe": betrag = -abs(betrag)
            conn = get_db()
            conn.execute(
                "INSERT INTO zahlungen (datum,betrag,typ,kategorie,beschreibung,belegnr,konto_typ,status) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (v["datum"], betrag, v["typ"], v["kategorie"], v["beschreibung"], v["belegnr"],
                 kt, v.get("status", "Neu")))
            zahlung_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute(
                "UPDATE kontoauszug SET als_buchung_uebernommen=1, zugeordnet=1, "
                "kategorie_vorschlag=?, zahlung_id=? WHERE id=?",
                (v["kategorie"], zahlung_id, int(sel[0])))
            conn.commit(); conn.close()
            lerne_buchung(raw, v["kategorie"], v["typ"], kt, ist_korrektur=False)
            self._load_vorschlaege()
            self._saldo_label.config(text="")

    def _batch_uebernehmen(self):
        """Grün markierte Vorschläge automatisch übernehmen.

        Verhalten (Issue #2):
        - Einträge selektiert  → nur die markierten (mit Kategorie) übernehmen
        - Nichts selektiert    → alle grünen Einträge (aktueller Konto-Filter)
        Keine Rückfrage pro Buchung.
        """
        if not hat_recht("Buchhaltung", "schreiben"):
            messagebox.showwarning("Berechtigung", "Keine Schreibberechtigung.", parent=self)
            return

        selected_ids = [int(iid) for iid in self.tree_v.selection()]
        use_selection = bool(selected_ids)
        selected_iban = self._vs_iban_map.get(self._vs_konto_var.get())

        conn = get_db()
        if use_selection:
            # Nur selektierte Einträge verarbeiten
            placeholders = ",".join("?" * len(selected_ids))
            q = (f"SELECT * FROM kontoauszug "
                 f"WHERE id IN ({placeholders}) "
                 f"AND (als_buchung_uebernommen IS NULL OR als_buchung_uebernommen=0) "
                 f"AND (falsch_zugeordnet IS NULL OR falsch_zugeordnet=0) "
                 f"ORDER BY datum")
            rows = conn.execute(q, selected_ids).fetchall()
            quelle = f"{len(selected_ids)} ausgewählte Einträge"
        else:
            # Alle nicht übernommenen Einträge (mit Konto-Filter)
            q = ("SELECT * FROM kontoauszug "
                 "WHERE (als_buchung_uebernommen IS NULL OR als_buchung_uebernommen=0) "
                 "AND (falsch_zugeordnet IS NULL OR falsch_zugeordnet=0) ")
            params = []
            if selected_iban:
                q += "AND iban=? "
                params.append(selected_iban)
            q += "ORDER BY datum"
            rows = conn.execute(q, params).fetchall()
            quelle = "alle grünen Einträge"

        count = 0
        skipped = 0
        lern_queue = []  # (raw, kat, typ, kt) – nach conn.close() ausfuehren
        for row_raw in rows:
            row = dict(row_raw)
            raw = row["buchungstext"] or ""
            kat = row.get("kategorie_vorschlag") or vorschlag_kategorie(raw)[0]  # Konfidenz ignoriert
            if not kat:
                skipped += 1
                continue
            betrag = row["betrag"] or 0
            typ = "Einnahme" if betrag >= 0 else "Ausgabe"
            gegenkonto = raw.split("||")[0] if "||" in raw else ""
            vzweck = raw.split("||")[1] if "||" in raw else raw
            beschr = f"{gegenkonto} – {vzweck}".strip(" –") if gegenkonto else vzweck
            kt = row.get("konto_typ") or "Wohngeldkonto"
            conn.execute(
                "INSERT INTO zahlungen (datum,betrag,typ,kategorie,beschreibung,konto_typ,status) "
                "VALUES (?,?,?,?,?,?,?)",
                (row["datum"], betrag, typ, kat, beschr[:200], kt, "Neu"))
            zahlung_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.execute(
                "UPDATE kontoauszug SET als_buchung_uebernommen=1, zugeordnet=1, "
                "kategorie_vorschlag=?, zahlung_id=? WHERE id=?",
                (kat, zahlung_id, row["id"]))
            lern_queue.append((raw, kat, typ, kt))
            count += 1

        conn.commit()
        conn.close()
        # lerne_buchung erst nach conn.close() -- verhindert "database is locked"
        for _raw, _kat, _typ, _kt in lern_queue:
            lerne_buchung(_raw, _kat, _typ, _kt)

        if count:
            msg = f"{count} Buchung(en) aus {quelle} übernommen."
            if skipped:
                msg += f"\n{skipped} Eintrag/Einträge ohne Kategorie übersprungen."
            messagebox.showinfo("Batch-Übernahme", msg)
        else:
            msg = "Keine Einträge mit Kategorie-Zuordnung gefunden."
            if skipped:
                msg += f"\n{skipped} Eintrag/Einträge haben keine Kategorie."
            messagebox.showinfo("Batch-Übernahme", msg)
        self._load_vorschlaege()
        self._saldo_label.config(text="")

    def _korrigieren(self):
        """Kategorie-Vorschlag für diesen Eintrag manuell korrigieren (Lernen)."""
        sel = self.tree_v.selection()
        if not sel: return
        conn = get_db()
        row_raw = conn.execute("SELECT * FROM kontoauszug WHERE id=?", (int(sel[0]),)).fetchone()
        conn.close()
        if not row_raw: return
        row = dict(row_raw)
        raw = row["buchungstext"] or ""
        kat_v = row.get("kategorie_vorschlag") or vorschlag_kategorie(raw)[0]  # Konfidenz ignoriert
        # Auswahldialog für Kategorie
        win = tk.Toplevel(self)
        win.title("Kategorie korrigieren")
        win.geometry("340x260")
        win.configure(bg=BG_CARD)
        win.grab_set()
        win.resizable(False, False)
        hdr = tk.Frame(win, bg=BG_SIDEBAR, height=44)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="Kategorie wählen", bg=BG_SIDEBAR, fg=TEXT_WHITE,
                 font=FONT_H3).pack(side="left", padx=14, pady=10)
        body = tk.Frame(win, bg=BG_CARD)
        body.pack(fill="both", expand=True, padx=20, pady=12)
        tk.Label(body, text="Kategorie", bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w")
        kat_var = tk.StringVar(value=kat_v)
        cb = ttk.Combobox(body, textvariable=kat_var, values=self.aktive_kategorien(),
                          state="readonly", font=FONT_BODY)
        cb.pack(fill="x", ipady=4)
        typ_var = tk.StringVar(value="Einnahme" if (row["betrag"] or 0) >= 0 else "Ausgabe")
        tk.Label(body, text="Typ", bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w", pady=(8,0))
        cb2 = ttk.Combobox(body, textvariable=typ_var,
                           values=["Einnahme", "Ausgabe"], state="readonly", font=FONT_BODY)
        cb2.pack(fill="x", ipady=4)
        saved = [False]
        def _save():
            saved[0] = True
            conn2 = get_db()
            conn2.execute("UPDATE kontoauszug SET kategorie_vorschlag=? WHERE id=?",
                          (kat_var.get(), int(sel[0])))
            conn2.commit(); conn2.close()
            lerne_buchung(raw, kat_var.get(), typ_var.get(),
                          row.get("konto_typ") or "Wohngeldkonto", ist_korrektur=True)
            win.destroy()
        btn_row = tk.Frame(win, bg=BG_CARD)
        btn_row.pack(fill="x", padx=20, pady=(0,12))
        make_btn(btn_row, "Abbrechen", win.destroy, color=BG_INPUT, fg=TEXT).pack(side="right", padx=(6,0))
        make_btn(btn_row, "Speichern", _save, color=ACCENT2).pack(side="right")
        win.wait_window()
        if saved[0]: self._load_vorschlaege()

    def _falsch_markieren(self):
        """Eintrag als falsch zugeordnet markieren (wird ausgeblendet)."""
        sel = self.tree_v.selection()
        if not sel: return
        conn = get_db()
        conn.execute("UPDATE kontoauszug SET falsch_zugeordnet=1 WHERE id=?", (int(sel[0]),))
        conn.commit(); conn.close()
        self._load_vorschlaege()

    # ── Tab 3: Buchungsregeln ──────────────────────────────────────────────────

    def _load_regeln(self):
        for i in self.tree_r.get_children(): self.tree_r.delete(i)
        conn = get_db()
        for r in conn.execute(
                "SELECT * FROM buchungsregeln ORDER BY treffer DESC, muster"):
            self.tree_r.insert("", "end", iid=r["id"], values=(
                r["muster"], r["kategorie"] or "–",
                r["typ"] or "–", r["konto_typ"] or "–",
                r["treffer"] or 0,
                "✔" if r["ist_korrektur"] else ""))
        conn.close()

    def _edit_regel(self, event=None):
        sel = self.tree_r.selection()
        if not sel: return
        conn = get_db()
        row = conn.execute("SELECT * FROM buchungsregeln WHERE id=?", (int(sel[0]),)).fetchone()
        conn.close()
        if not row: return
        win = tk.Toplevel(self)
        win.title("Buchungsregel bearbeiten")
        win.geometry("400x320")
        win.configure(bg=BG_CARD)
        win.grab_set()
        win.resizable(False, False)
        hdr = tk.Frame(win, bg=BG_SIDEBAR, height=44)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="Buchungsregel bearbeiten", bg=BG_SIDEBAR, fg=TEXT_WHITE,
                 font=FONT_H3).pack(side="left", padx=14, pady=10)
        body = tk.Frame(win, bg=BG_CARD)
        body.pack(fill="both", expand=True, padx=20, pady=12)
        tk.Label(body, text="Muster (Suchtext)", bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w")
        muster_var = tk.StringVar(value=row["muster"])
        make_entry(body, textvariable=muster_var).pack(fill="x", ipady=6)
        tk.Label(body, text="Kategorie", bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w", pady=(8,0))
        kat_var = tk.StringVar(value=row["kategorie"] or "")
        ttk.Combobox(body, textvariable=kat_var, values=self.aktive_kategorien(),
                     state="readonly", font=FONT_BODY).pack(fill="x", ipady=4)
        tk.Label(body, text="Typ", bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w", pady=(8,0))
        typ_var = tk.StringVar(value=row["typ"] or "Einnahme")
        ttk.Combobox(body, textvariable=typ_var, values=["Einnahme","Ausgabe"],
                     state="readonly", font=FONT_BODY).pack(fill="x", ipady=4)
        def _save():
            conn2 = get_db()
            conn2.execute(
                "UPDATE buchungsregeln SET muster=?,kategorie=?,typ=?,ist_korrektur=1 WHERE id=?",
                (muster_var.get(), kat_var.get(), typ_var.get(), int(sel[0])))
            conn2.commit(); conn2.close()
            win.destroy(); self._load_regeln()
        btn_row = tk.Frame(win, bg=BG_CARD)
        btn_row.pack(fill="x", padx=20, pady=(0,12))
        make_btn(btn_row, "Abbrechen", win.destroy, color=BG_INPUT, fg=TEXT).pack(side="right", padx=(6,0))
        make_btn(btn_row, "Speichern", _save, color=ACCENT2).pack(side="right")

    def _delete_regel(self):
        sel = self.tree_r.selection()
        if not sel: return
        if messagebox.askyesno("Löschen", "Buchungsregel löschen?"):
            conn = get_db()
            conn.execute("DELETE FROM buchungsregeln WHERE id=?", (int(sel[0]),))
            conn.commit(); conn.close(); self._load_regeln()

    # ── Tab 4: Kostenarten ──────────────────────────────────────────────────

    # Deaktivierte Kategorien (persistent im Config)
    @staticmethod
    def _deaktivierte_kategorien():
        cfg = load_config()
        return set(cfg.get("deaktivierte_kategorien", []))

    @staticmethod
    def _save_deaktivierte(deaktiviert: set):
        cfg = load_config()
        cfg["deaktivierte_kategorien"] = sorted(deaktiviert)
        save_config(cfg)

    @classmethod
    def aktive_kategorien(cls):
        """Gibt nur aktive Kategorien zurück (für Dropdowns)."""
        deaktiviert = cls._deaktivierte_kategorien()
        return [k for k in cls.KATEGORIEN if k not in deaktiviert]

    def _load_kostenarten(self):
        for i in self.tree_k.get_children(): self.tree_k.delete(i)
        conn = get_db()
        deaktiviert = self._deaktivierte_kategorien()
        for idx, kat_name in enumerate(self.KATEGORIEN):
            meta = self.KOSTENARTEN.get(kat_name, {})
            # Anzahl Verwendungen in Buchungen zählen
            count = conn.execute(
                "SELECT COUNT(*) FROM zahlungen WHERE kategorie=?", (kat_name,)
            ).fetchone()[0]
            # Umlagefähig-Anzeige
            uml = meta.get("umlagefaehig", False)
            if uml is True:
                uml_str = "✔ Ja"
            elif uml == "Teilweise":
                uml_str = "~ Teilweise"
            else:
                uml_str = "✗ Nein"
            status = "Deaktiviert" if kat_name in deaktiviert else "Aktiv"
            tag = "deaktiviert" if kat_name in deaktiviert else ""
            self.tree_k.insert("", "end", iid=str(idx), values=(
                kat_name,
                meta.get("kategorie", "–"),
                uml_str,
                meta.get("schluessel", "–"),
                status,
                count), tags=(tag,) if tag else ())
        conn.close()

    def _load_wohngeld(self):
        """#19 Wohngeld Soll/Ist: Vergleich geleisteter vs. erwarteter Hausgeld-Zahlungen."""
        try:
            jahr = int(self._wg_jahr.get())
        except ValueError:
            return

        conn = get_db()
        # Gesamtausgaben des Jahres (Soll-Basis für MEA-Anteil)
        total_ausgaben = conn.execute(
            "SELECT COALESCE(SUM(betrag),0) FROM zahlungen "
            "WHERE typ='Ausgabe' AND strftime('%Y',datum)=?", (str(jahr),)
        ).fetchone()[0]
        # Tatsächlich gezahltes Hausgeld pro Eigentümer
        hg_ist = conn.execute(
            "SELECT eigentuemer_id, SUM(betrag) as s FROM zahlungen "
            "WHERE typ='Einnahme' AND kategorie='Hausgeld' AND strftime('%Y',datum)=? "
            "GROUP BY eigentuemer_id", (str(jahr),)
        ).fetchall()
        hg_gesamt_ist = conn.execute(
            "SELECT COALESCE(SUM(betrag),0) FROM zahlungen "
            "WHERE typ='Einnahme' AND kategorie='Hausgeld' AND strftime('%Y',datum)=?",
            (str(jahr),)
        ).fetchone()[0]
        eigentuemer = conn.execute(
            "SELECT id, vorname, name, anteil_prozent FROM eigentuemer ORDER BY name"
        ).fetchall()
        conn.close()

        hg_map = {r["eigentuemer_id"]: (r["s"] or 0) for r in hg_ist}
        total_mea = sum(parse_float(e["anteil_prozent"]) or 0 for e in eigentuemer) or 100.0

        # KPI
        for w in self._wg_kpi.winfo_children():
            w.destroy()
        saldo_gesamt = hg_gesamt_ist - total_ausgaben
        for label, wert, color in [
            ("Gesamtausgaben (Soll)", fmt_euro(total_ausgaben), DANGER),
            ("Hausgeld-Einnahmen (Ist)", fmt_euro(hg_gesamt_ist), SUCCESS),
            ("Jahressaldo", fmt_euro(saldo_gesamt),
             SUCCESS if saldo_gesamt >= 0 else DANGER),
        ]:
            karte = tk.Frame(self._wg_kpi, bg=BG_INPUT, padx=14, pady=8)
            karte.pack(side="left", padx=(0, 10))
            tk.Label(karte, text=label, bg=BG_INPUT, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w")
            tk.Label(karte, text=wert,  bg=BG_INPUT, fg=color,      font=FONT_H3).pack(anchor="w")

        # Pro-Eigentümer-Tabelle
        for i in self._tree_wg.get_children():
            self._tree_wg.delete(i)
        for e in eigentuemer:
            anteil_pct  = parse_float(e["anteil_prozent"]) or 0
            soll        = total_ausgaben * anteil_pct / 100
            ist         = hg_map.get(e["id"], 0)
            saldo       = ist - soll
            name        = f"{e['vorname'] or ''} {e['name']}".strip()
            if saldo >= 0:
                status    = "✔ ausgeglichen"
                color_tag = "plus"
            else:
                status    = f"⚠ Rückstand {fmt_euro(abs(saldo))}"
                color_tag = "minus"
            self._tree_wg.insert("", "end", values=(
                name, f"{anteil_pct:.2f}%",
                fmt_euro(soll), fmt_euro(ist),
                fmt_euro(saldo), status), tags=(color_tag,))
        self._tree_wg.tag_configure("plus",  foreground=SUCCESS)
        self._tree_wg.tag_configure("minus", foreground=DANGER)

    def _new_kostenart(self):
        """Neue benutzerdefinierte Kategorie hinzufügen."""
        win = tk.Toplevel(self)
        win.title("Neue Kostenkategorie")
        win.geometry("400x300")
        win.configure(bg=BG_CARD)
        win.grab_set()
        win.resizable(False, False)
        hdr = tk.Frame(win, bg=BG_SIDEBAR, height=44)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="Neue Kostenkategorie", bg=BG_SIDEBAR, fg=TEXT_WHITE,
                 font=FONT_H3).pack(side="left", padx=14, pady=10)
        body = tk.Frame(win, bg=BG_CARD)
        body.pack(fill="both", expand=True, padx=20, pady=12)
        tk.Label(body, text="Name der Kategorie *", bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w")
        name_var = tk.StringVar()
        make_entry(body, textvariable=name_var).pack(fill="x", ipady=6)
        tk.Label(body, text="Oberkategorie", bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w", pady=(8,0))
        ober_var = tk.StringVar(value="Sonstiges")
        ober_vals = sorted(set(m.get("kategorie", "Sonstiges") for m in self.KOSTENARTEN.values()))
        ttk.Combobox(body, textvariable=ober_var, values=ober_vals, font=FONT_BODY).pack(fill="x", ipady=4)
        tk.Label(body, text="Umlageschlüssel", bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w", pady=(8,0))
        schluessel_var = tk.StringVar(value="MEA")
        ttk.Combobox(body, textvariable=schluessel_var,
                     values=["MEA", "Wohnfläche", "Verbrauch/Wohnfläche", "MEA/Fläche", "MEA/Wohneinheiten", "Wohneinheiten/MEA", "–"],
                     font=FONT_BODY).pack(fill="x", ipady=4)
        uml_var = tk.BooleanVar(value=False)
        tk.Checkbutton(body, text="Umlagefähig", variable=uml_var, bg=BG_CARD,
                       fg=TEXT, font=FONT_BODY, activebackground=BG_CARD).pack(anchor="w", pady=(8,0))
        def _save():
            name = name_var.get().strip()
            if not name:
                messagebox.showwarning("Pflichtfeld", "Name der Kategorie ist erforderlich.", parent=win)
                return
            if name in self.KATEGORIEN:
                messagebox.showwarning("Duplikat", f"Kategorie '{name}' existiert bereits.", parent=win)
                return
            # Dynamisch hinzufügen
            self.KATEGORIEN.insert(-1, name)  # Vor "Kategorie offen"
            self.KOSTENARTEN[name] = {
                "kategorie": ober_var.get(),
                "umlagefaehig": uml_var.get(),
                "schluessel": schluessel_var.get()
            }
            # Persistieren in Config
            cfg = load_config()
            custom = cfg.get("custom_kategorien", [])
            custom.append({"name": name, "kategorie": ober_var.get(),
                          "umlagefaehig": uml_var.get(), "schluessel": schluessel_var.get()})
            cfg["custom_kategorien"] = custom
            save_config(cfg)
            win.destroy()
            self._load_kostenarten()
        btn_row = tk.Frame(win, bg=BG_CARD)
        btn_row.pack(fill="x", padx=20, pady=(0,12))
        make_btn(btn_row, "Abbrechen", win.destroy, color=BG_INPUT, fg=TEXT).pack(side="right", padx=(6,0))
        make_btn(btn_row, "Speichern", _save, color=ACCENT2).pack(side="right")

    def _edit_kostenart(self):
        """Bestehende Kategorie bearbeiten (Oberkategorie, Schlüssel, Umlagefähig)."""
        sel = self.tree_k.selection()
        if not sel: return
        idx = int(sel[0])
        if idx >= len(self.KATEGORIEN): return
        kat_name = self.KATEGORIEN[idx]
        meta = self.KOSTENARTEN.get(kat_name, {})
        win = tk.Toplevel(self)
        win.title("Kostenkategorie bearbeiten")
        win.geometry("400x280")
        win.configure(bg=BG_CARD)
        win.grab_set()
        win.resizable(False, False)
        hdr = tk.Frame(win, bg=BG_SIDEBAR, height=44)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text=f"Kategorie: {kat_name}", bg=BG_SIDEBAR, fg=TEXT_WHITE,
                 font=FONT_H3).pack(side="left", padx=14, pady=10)
        body = tk.Frame(win, bg=BG_CARD)
        body.pack(fill="both", expand=True, padx=20, pady=12)
        tk.Label(body, text="Oberkategorie", bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w")
        ober_var = tk.StringVar(value=meta.get("kategorie", "Sonstiges"))
        ober_vals = sorted(set(m.get("kategorie", "Sonstiges") for m in self.KOSTENARTEN.values()))
        ttk.Combobox(body, textvariable=ober_var, values=ober_vals, font=FONT_BODY).pack(fill="x", ipady=4)
        tk.Label(body, text="Umlageschlüssel", bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w", pady=(8,0))
        schluessel_var = tk.StringVar(value=meta.get("schluessel", "MEA"))
        ttk.Combobox(body, textvariable=schluessel_var,
                     values=["MEA", "Wohnfläche", "Verbrauch/Wohnfläche", "MEA/Fläche", "MEA/Wohneinheiten", "Wohneinheiten/MEA", "–"],
                     font=FONT_BODY).pack(fill="x", ipady=4)
        uml = meta.get("umlagefaehig", False)
        uml_var = tk.BooleanVar(value=uml if isinstance(uml, bool) else False)
        tk.Checkbutton(body, text="Umlagefähig", variable=uml_var, bg=BG_CARD,
                       fg=TEXT, font=FONT_BODY, activebackground=BG_CARD).pack(anchor="w", pady=(8,0))
        def _save():
            self.KOSTENARTEN[kat_name] = {
                "kategorie": ober_var.get(),
                "umlagefaehig": uml_var.get(),
                "schluessel": schluessel_var.get()
            }
            win.destroy()
            self._load_kostenarten()
        btn_row = tk.Frame(win, bg=BG_CARD)
        btn_row.pack(fill="x", padx=20, pady=(0,12))
        make_btn(btn_row, "Abbrechen", win.destroy, color=BG_INPUT, fg=TEXT).pack(side="right", padx=(6,0))
        make_btn(btn_row, "Speichern", _save, color=ACCENT2).pack(side="right")

    def _toggle_kostenart(self):
        """Kategorie aktivieren/deaktivieren."""
        sel = self.tree_k.selection()
        if not sel: return
        idx = int(sel[0])
        if idx >= len(self.KATEGORIEN): return
        kat_name = self.KATEGORIEN[idx]
        deaktiviert = self._deaktivierte_kategorien()
        if kat_name in deaktiviert:
            deaktiviert.discard(kat_name)
        else:
            deaktiviert.add(kat_name)
        self._save_deaktivierte(deaktiviert)
        self._load_kostenarten()

    def _delete_kostenart(self):
        """Kategorie löschen (nur wenn nicht in Buchungen verwendet)."""
        sel = self.tree_k.selection()
        if not sel: return
        idx = int(sel[0])
        if idx >= len(self.KATEGORIEN): return
        kat_name = self.KATEGORIEN[idx]
        # Schutz: Verwendete Kategorien nicht löschbar
        conn = get_db()
        count = conn.execute(
            "SELECT COUNT(*) FROM zahlungen WHERE kategorie=?", (kat_name,)
        ).fetchone()[0]
        conn.close()
        if count > 0:
            messagebox.showwarning("Geschützt",
                f"Kategorie '{kat_name}' wird in {count} Buchung(en) verwendet "
                f"und kann nicht gelöscht werden.\n\nSie können die Kategorie stattdessen deaktivieren.",
                parent=self)
            return
        if not messagebox.askyesno("Löschen", f"Kategorie '{kat_name}' wirklich löschen?", parent=self):
            return
        self.KATEGORIEN.remove(kat_name)
        self.KOSTENARTEN.pop(kat_name, None)
        # Aus Config entfernen
        cfg = load_config()
        custom = cfg.get("custom_kategorien", [])
        cfg["custom_kategorien"] = [c for c in custom if c.get("name") != kat_name]
        deakt = set(cfg.get("deaktivierte_kategorien", []))
        deakt.discard(kat_name)
        cfg["deaktivierte_kategorien"] = sorted(deakt)
        save_config(cfg)
        self._load_kostenarten()

    # Compat: alter Name → neuer Name
    def _load(self):
        self._load_buchungen()

    def _import_csv(self):
        pass  # CSV-Import nur in Kontoauszug-Seite


class ZahlungDialog(BaseDialog):
    def __init__(self, parent, row=None):
        super().__init__(parent, "Buchung", 540, 620)
        r = dict(row) if row else {}
        self._add_field("Datum (JJJJ-MM-TT) *", "datum",
                        r.get("datum", date.today().isoformat()))
        self._add_field("Typ *", "typ", r.get("typ", "Einnahme"),
                        widget_type="combo", options=["Einnahme", "Ausgabe"])
        self._add_field("Betrag € *", "betrag", abs(r.get("betrag", 0) or 0))
        self._add_field("Kategorie", "kategorie", r.get("kategorie", ""),
                        widget_type="combo",
                        options=BuchhaltungPage.aktive_kategorien())
        self._add_field("Rechnungssteller", "rechnungssteller",
                        r.get("rechnungssteller", "") or "")   # #35
        self._add_field("Beschreibung", "beschreibung", r.get("beschreibung", ""))
        self._add_field("Belegnummer",  "belegnr",      r.get("belegnr", ""))
        self._add_field("Status", "status", r.get("status", "Neu"),
                        widget_type="combo", options=["Neu", "Geprüft", "Freigegeben"])
        self._add_field("Abrechnungsjahr", "abrechnungsjahr",
                        r.get("abrechnungsjahr", "") or "")

        # Abrechnungsrelevanz-Checkbox
        abr_frame = tk.Frame(self._body, bg=BG_CARD)
        abr_frame.pack(fill="x", padx=20, pady=(2, 4))
        self._abr_var = tk.BooleanVar(value=bool(r.get("abrechnungsrelevant", 1)))
        tk.Checkbutton(abr_frame, text="✅ Abrechnungsrelevant (in Nebenkostenabrechnung einbeziehen)",
                       variable=self._abr_var, bg=BG_CARD, fg=TEXT, font=FONT_BODY,
                       activebackground=BG_CARD, selectcolor=BG_CARD).pack(anchor="w")

        # ── Beleg-Datei + KI-Analyse (#35) ───────────────────────────────────
        tk.Frame(self._body, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(10, 4))
        beleg_frame = tk.Frame(self._body, bg=BG_CARD)
        beleg_frame.pack(fill="x", padx=20, pady=(0, 4))
        tk.Label(beleg_frame, text="Beleg-Datei", bg=BG_CARD, fg=TEXT_LIGHT,
                 font=FONT_SMALL).pack(anchor="w")
        row_f = tk.Frame(beleg_frame, bg=BG_CARD)
        row_f.pack(fill="x")
        self._beleg_var = tk.StringVar(value=r.get("beleg_dateipfad", "") or "")
        beleg_entry = tk.Entry(row_f, textvariable=self._beleg_var,
                               bg=BG_INPUT, fg=TEXT, font=FONT_BODY,
                               relief="flat", bd=0, highlightthickness=1,
                               highlightbackground=BORDER, highlightcolor=ACCENT2)
        beleg_entry.pack(side="left", fill="x", expand=True, ipady=5)
        make_btn(row_f, "📂 Durchsuchen", self._browse_beleg,
                 color=BG_INPUT, fg=TEXT).pack(side="left", padx=(6, 0))

        # KI-Analyse-Button (nur sichtbar wenn KI-Assistent-Recht vorhanden)
        # KI-Analyse-Button (#35): immer anzeigen, aber disabled wenn kein Recht (#7 fix)
        ki_row = tk.Frame(beleg_frame, bg=BG_CARD)
        ki_row.pack(fill="x", pady=(4, 0))
        ki_hat_recht = hat_recht("KI-Assistent", "lesen")
        self._ki_btn = make_btn(ki_row, "🤖 KI-Analyse starten",
                                self._ki_analyse_starten, color=ACCENT2)
        self._ki_btn.pack(side="left")
        if not ki_hat_recht:
            self._ki_btn.config(state="disabled")
        # Modell-Auswahl (#37): Dropdown für KI-Modell direkt im Dialog
        _cfg_tmp = load_config()
        _modelle = KIAssistentPage._alle_ki_modelle(_cfg_tmp)
        _aktiv = _cfg_tmp.get("ki_aktives_modell", "")
        self._ki_modell_var = tk.StringVar(value=_aktiv if _aktiv in _modelle else (_modelle[0] if _modelle else ""))
        _modell_combo = ttk.Combobox(ki_row, textvariable=self._ki_modell_var,
                                     values=_modelle, state="readonly", width=30,
                                     font=FONT_SMALL)
        _modell_combo.pack(side="left", padx=(8, 0))
        if not ki_hat_recht:
            _modell_combo.config(state="disabled")
        self._ki_status_lbl = tk.Label(ki_row,
            text="" if ki_hat_recht else "🔒 Kein Recht für KI-Assistent",
            bg=BG_CARD, fg=TEXT_LIGHT if ki_hat_recht else DANGER, font=FONT_SMALL)
        self._ki_status_lbl.pack(side="left", padx=(10, 0))

    def _browse_beleg(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            parent=self,
            title="Beleg-Datei auswählen",
            filetypes=[
                ("PDF-Dateien", "*.pdf"),
                ("Bilder", "*.png *.jpg *.jpeg *.tif *.tiff"),
                ("Alle Dateien", "*.*"),
            ]
        )
        if path:
            self._beleg_var.set(path)

    # ── KI-Analyse (#35) ──────────────────────────────────────────────────────

    def _ki_analyse_starten(self):
        """Startet KI-Analyse der Beleg-Datei im Hintergrund-Thread (#35)."""
        pfad = self._beleg_var.get().strip()
        if not pfad:
            messagebox.showwarning("Kein Beleg", "Bitte zuerst eine Beleg-Datei auswählen.",
                                   parent=self)
            return
        import os
        if not os.path.isfile(pfad):
            messagebox.showwarning("Datei nicht gefunden",
                                   f"Datei nicht gefunden:\n{pfad}", parent=self)
            return
        # Größenprüfung: max. 20 MB (#13 fix)
        if os.path.getsize(pfad) > 20 * 1024 * 1024:
            messagebox.showwarning("Datei zu groß",
                                   "Die Beleg-Datei ist zu groß (max. 20 MB für KI-Analyse).",
                                   parent=self)
            return
        cfg = load_config()
        # Modell ermitteln: zuerst aus Dialog-Dropdown (#37), dann ki_aktives_modell, dann Fallback
        modell_auswahl = getattr(self, "_ki_modell_var", None)
        modell_auswahl_str = modell_auswahl.get().strip() if modell_auswahl else ""
        if modell_auswahl_str:
            anbieter, modell = KIAssistentPage._parse_modell_auswahl(modell_auswahl_str)
        else:
            aktiv = cfg.get("ki_aktives_modell", "")
            if aktiv:
                anbieter, modell = KIAssistentPage._parse_modell_auswahl(aktiv)
            else:
                anbieter = cfg.get("ki_anbieter", "anthropic")
                modell = cfg.get("ki_modell", "claude-opus-4-6") if anbieter == "anthropic" \
                         else cfg.get("ollama_modell", "llama3.2")

        if hasattr(self, "_ki_status_lbl"):
            self._ki_status_lbl.config(text="⏳ KI analysiert …", fg=TEXT_LIGHT)
        if hasattr(self, "_ki_btn"):
            self._ki_btn.config(state="disabled")

        threading.Thread(target=self._ki_analyse_thread,
                         args=(pfad, anbieter, modell, cfg), daemon=True).start()

    def _ki_analyse_thread(self, pfad: str, anbieter: str, modell: str, cfg: dict):
        """Hintergrund-Thread: liest Datei, sendet an KI, parst Ergebnis (#35)."""
        import os, base64
        kategorien = BuchhaltungPage.aktive_kategorien()
        ext = os.path.splitext(pfad)[1].lower()
        try:
            # ── Datei-Inhalt vorbereiten ──────────────────────────────────
            if ext == ".pdf":
                # PDF als Text extrahieren (pypdf)
                try:
                    import pypdf
                    with open(pfad, "rb") as fh:
                        reader = pypdf.PdfReader(fh)
                        seiten_text = "\n".join(p.extract_text() or "" for p in reader.pages)
                    inhalt_typ = "text"
                    inhalt = seiten_text[:6000]  # max 6000 Zeichen
                except ImportError:
                    inhalt_typ = "text"
                    inhalt = "(PDF konnte nicht gelesen werden – pypdf nicht installiert)"
            elif ext in (".png", ".jpg", ".jpeg", ".tif", ".tiff"):
                with open(pfad, "rb") as fh:
                    raw = fh.read()
                inhalt_typ = "image"
                inhalt = base64.b64encode(raw).decode()
                mime = "image/jpeg" if ext in (".jpg", ".jpeg") else \
                       ("image/png" if ext == ".png" else "image/tiff")
            else:
                inhalt_typ = "text"
                with open(pfad, "r", errors="replace") as fh:
                    inhalt = fh.read(4000)

            # ── KI-Prompt ────────────────────────────────────────────────
            kat_liste = ", ".join(f'"{k}"' for k in kategorien[:30])
            prompt = (
                "Analysiere diesen Buchungsbeleg und extrahiere folgende Felder als JSON.\n"
                "Antworte NUR mit einem JSON-Objekt – kein Text davor oder danach.\n\n"
                "Felder:\n"
                '  "datum": Rechnungsdatum im Format JJJJ-MM-TT (falls nicht gefunden: "")\n'
                '  "belegnr": Rechnungs- oder Belegnummer (falls nicht gefunden: "")\n'
                '  "beschreibung": kurze Beschreibung der Leistung (max. 80 Zeichen)\n'
                f'  "kategorie": passendste Kategorie aus dieser Liste: [{kat_liste}] (oder "")\n'
                '  "rechnungssteller": Name des Absenders/Lieferanten\n'
                '  "betrag": Gesamtbetrag als Dezimalzahl ohne Währungssymbol (z.B. 123.45)\n\n'
            )
            if inhalt_typ == "text":
                prompt += f"Belegtext:\n{inhalt}"

            # ── API-Aufruf ────────────────────────────────────────────────
            antwort_text = ""
            if anbieter == "anthropic":
                key = cfg.get("anthropic_api_key", "").strip()
                if not key:
                    raise ValueError("Kein Anthropic API-Key konfiguriert.")
                if inhalt_typ == "image":
                    messages = [{"role": "user", "content": [
                        {"type": "image", "source": {
                            "type": "base64", "media_type": mime, "data": inhalt}},
                        {"type": "text", "text": prompt}
                    ]}]
                else:
                    messages = [{"role": "user", "content": prompt}]
                payload = json.dumps({
                    "model": modell, "max_tokens": 512,
                    "messages": messages
                }).encode("utf-8")
                req = urllib.request.Request(
                    "https://api.anthropic.com/v1/messages", data=payload,
                    headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                             "content-type": "application/json"})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode())
                # Robuste Fehlerbehandlung Anthropic (#18 fix)
                try:
                    antwort_text = data["content"][0]["text"]
                except (KeyError, IndexError) as e:
                    raise ValueError(f"Unerwartetes Anthropic-Antwortformat: {data}") from e
            else:
                # Ollama: keine Bild-Unterstützung für einfache Modelle
                base_url = cfg.get("ollama_url", "http://localhost:11434").strip().rstrip("/")
                # URL-Schema validieren (SSRF-Prävention, #14 fix)
                import urllib.parse as _urlparse
                parsed = _urlparse.urlparse(base_url)
                if parsed.scheme not in ("http", "https"):
                    raise ValueError(f"Ungültige Ollama-URL (nur http/https erlaubt): {base_url}")
                msgs = [{"role": "user", "content": prompt}]
                payload = json.dumps({"model": modell, "messages": msgs,
                                      "stream": False}).encode("utf-8")
                req = urllib.request.Request(f"{base_url}/api/chat", data=payload,
                    headers={"content-type": "application/json"})
                with urllib.request.urlopen(req, timeout=60) as resp:
                    data = json.loads(resp.read().decode())
                try:
                    antwort_text = data["message"]["content"]
                except KeyError as e:
                    raise ValueError(f"Unerwartetes Ollama-Antwortformat: {data}") from e

            # ── JSON parsen (#15 fix: Regex für verschachtelte Objekte) ────
            import re
            # Versuche direktes JSON-Parsing zuerst
            try:
                ki_daten = json.loads(antwort_text.strip())
            except (json.JSONDecodeError, ValueError):
                # Fallback: JSON-Block aus Fließtext extrahieren
                json_match = re.search(r'\{.*\}', antwort_text, re.DOTALL)
                if not json_match:
                    raise ValueError(f"KI-Antwort enthält kein JSON:\n{antwort_text[:300]}")
                ki_daten = json.loads(json_match.group())
            # Keys normalisieren (Groß-/Kleinschreibung, #20 fix)
            ki_daten = {k.lower(): v for k, v in ki_daten.items()}
            # Widget-Check vor after()-Aufruf (#3 fix)
            if self.winfo_exists():
                self.after(0, lambda d=ki_daten: self._ki_felder_befuellen(d))

        except Exception as ex:
            msg = str(ex)
            if self.winfo_exists():
                self.after(0, lambda m=msg: self._ki_fehler(m))

    def _ki_felder_befuellen(self, daten: dict):
        """Füllt Dialog-Felder mit KI-extrahierten Daten (#35)."""
        def _set(key, val):
            if not val:
                return
            w = self._fields.get(key)
            if not w:
                return
            if hasattr(w, "set"):
                w.set(str(val))
            elif hasattr(w, "delete"):
                w.delete(0, "end")
                w.insert(0, str(val))

        if daten.get("datum"):
            # ISO-Format (YYYY-MM-DD) direkt übernehmen, kein parse_datum nötig (#16 fix)
            raw_datum = str(daten["datum"]).strip()
            import re as _re
            if _re.match(r'^\d{4}-\d{2}-\d{2}$', raw_datum):
                _set("datum", raw_datum)
            else:
                # Fallback: parse_datum für andere Formate
                _set("datum", parse_datum(raw_datum) or raw_datum)
        if daten.get("belegnr"):
            _set("belegnr", daten["belegnr"])
        # Beschreibung NUR befüllen wenn Feld leer (#37: nicht überschreiben)
        if daten.get("beschreibung"):
            w_beschr = self._fields.get("beschreibung")
            aktuell = ""
            if w_beschr and hasattr(w_beschr, "get"):
                aktuell = w_beschr.get().strip() if not hasattr(w_beschr, "index") \
                          else w_beschr.get("1.0", "end-1c").strip()
            if not aktuell:
                _set("beschreibung", daten["beschreibung"])
        if daten.get("kategorie"):
            kat = str(daten["kategorie"])
            if kat in BuchhaltungPage.aktive_kategorien():
                _set("kategorie", kat)
        if daten.get("rechnungssteller"):
            _set("rechnungssteller", daten["rechnungssteller"])
            # Lernfunktion: Buchungsregel anlegen (#35, #5 fix: Typ aus Formular lesen)
            typ_w = self._fields.get("typ")
            buchungs_typ = typ_w.get() if typ_w and hasattr(typ_w, "get") else "Ausgabe"
            lerne_buchung(daten["rechnungssteller"],
                          daten.get("kategorie", ""),
                          buchungs_typ,
                          "Wohngeldkonto",
                          ist_korrektur=False)
            # Dateiname generieren: YYYY-MM-TT_Rechnungssteller_Zähler
            self._beleg_dateiname_generieren(daten)
        if daten.get("betrag"):
            try:
                _set("betrag", abs(float(str(daten["betrag"]).replace(",", "."))))
            except Exception:
                pass

        if hasattr(self, "_ki_status_lbl"):
            self._ki_status_lbl.config(text="✅ KI-Analyse abgeschlossen", fg=SUCCESS)
        if hasattr(self, "_ki_btn"):
            self._ki_btn.config(state="normal")

    def _beleg_dateiname_generieren(self, daten: dict):
        """Generiert Dateiname: YYYY-MM-TT_Rechnungssteller_N (#35)."""
        import os, re
        pfad = self._beleg_var.get().strip()
        if not pfad:
            return
        datum = daten.get("datum", date.today().isoformat()) or date.today().isoformat()
        steller = re.sub(r'[^\w\- ]', '', daten.get("rechnungssteller", "Unbekannt"))
        steller = steller.strip().replace(" ", "_")[:30]
        verz = os.path.dirname(pfad)
        ext = os.path.splitext(pfad)[1]
        zaehler = 1
        while True:
            neu = os.path.join(verz, f"{datum}_{steller}_{zaehler:02d}{ext}")
            if not os.path.exists(neu) or neu == pfad:
                break
            zaehler += 1
        try:
            if pfad != neu:
                import shutil
                shutil.copy2(pfad, neu)
            self._beleg_var.set(neu)
        except Exception:
            pass  # Umbenennung optional

    def _ki_fehler(self, msg: str):
        if hasattr(self, "_ki_status_lbl"):
            self._ki_status_lbl.config(text=f"❌ Fehler: {msg[:60]}", fg=DANGER)
        if hasattr(self, "_ki_btn"):
            self._ki_btn.config(state="normal")
        messagebox.showerror("KI-Fehler", f"KI-Analyse fehlgeschlagen:\n{msg}", parent=self)

    def _on_save(self):
        v = self._get_values()
        if not v.get("datum") or not v.get("betrag"):
            messagebox.showwarning("Pflichtfelder", "Datum und Betrag sind erforderlich.", parent=self); return
        # Normalisiere Datum
        if v.get("datum"):
            v["datum"] = parse_datum(v["datum"])
        v["beleg_dateipfad"] = self._beleg_var.get().strip() or None
        # Abrechnungsrelevanz speichern
        v["abrechnungsrelevant"] = 1 if self._abr_var.get() else 0
        self.result = v; self.destroy()

# ── Wartung-Seite ─────────────────────────────────────────────────────────────

class WartungPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_CARD)
        self._build()

    def _build(self):
        section_header(self, "Wartung & Reparaturen", "＋ Auftrag", self._new)
        fr = tk.Frame(self, bg=BG_CARD)
        fr.pack(fill="x", padx=20, pady=6)
        tk.Label(fr, text="Status:", bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(side="left")
        self._status_var = tk.StringVar(value="Alle")
        for s in ("Alle", "Offen", "In Arbeit", "Erledigt"):
            tk.Radiobutton(fr, text=s, variable=self._status_var, value=s,
                           bg=BG_CARD, fg=TEXT, font=FONT_SMALL,
                           activebackground=BG_CARD, selectcolor=BG_CARD,
                           command=self._load).pack(side="left", padx=6)

        cols = ("Titel", "Einheit", "Priorität", "Status", "Erstellt", "Kosten")
        f, self.tree = make_table(self, cols, height=16)
        f.pack(fill="both", expand=True, padx=20, pady=8)
        for c, w in zip(cols, [200, 120, 80, 90, 90, 90]):
            self.tree.heading(c, text=c); self.tree.column(c, width=w, anchor="w")
        self.tree.bind("<Double-1>", self._edit)

        btn_row = tk.Frame(self, bg=BG_CARD)
        btn_row.pack(fill="x", padx=20, pady=(0, 10))
        if hat_recht("Wartung", "schreiben"):
            make_btn(btn_row, "✏ Bearbeiten",   self._edit,      color=BG_INPUT, fg=TEXT).pack(side="left", padx=(0, 8))
            make_btn(btn_row, "✔ Als erledigt", self._mark_done, color=SUCCESS).pack(side="left", padx=(0, 8))
        if hat_recht("Wartung", "loeschen"):
            make_btn(btn_row, "🗑 Löschen",     self._delete,    color=DANGER).pack(side="left")
        self._load()

    def _load(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = get_db()
        s = self._status_var.get()
        q = "SELECT * FROM wartung"
        params = []
        if s != "Alle":
            q += " WHERE status=?"  # parametrisiert (kein SQL-Injection-Risiko)
            params.append(s)
        q += " ORDER BY CASE prioritaet WHEN 'Hoch' THEN 1 WHEN 'Mittel' THEN 2 ELSE 3 END, erstellt_am DESC"
        for r in conn.execute(q, params):
            self.tree.insert("", "end", iid=r["id"], values=(
                r["titel"], r["einheit"] or "–", r["prioritaet"],
                r["status"], fmt_date(r["erstellt_am"]),
                fmt_euro(r["kosten"]) if r["kosten"] else "–"))
        conn.close()
        tree_empty_hint(self.tree)

    def _new(self):
        if not hat_recht("Wartung", "schreiben"):
            messagebox.showwarning("Berechtigung", "Keine Schreibberechtigung.", parent=self); return
        d = WartungDialog(self)
        self.wait_window(d)
        if d.result:
            v = d.result
            conn = get_db()
            conn.execute("INSERT INTO wartung (titel,beschreibung,prioritaet,status,gemeldet_von,einheit,erstellt_am,kosten,notizen) VALUES (?,?,?,?,?,?,?,?,?)",
                (v["titel"], v["beschreibung"], v["prioritaet"], v["status"],
                 v["gemeldet_von"], v["einheit"], date.today().isoformat(),
                 v["kosten"] or None, v["notizen"]))
            conn.commit(); conn.close(); self._load()

    def _edit(self, event=None):
        if not hat_recht("Wartung", "schreiben"):
            messagebox.showwarning("Berechtigung", "Keine Schreibberechtigung.", parent=self); return
        sel = self.tree.selection()
        if not sel: return
        conn = get_db()
        row = conn.execute("SELECT * FROM wartung WHERE id=?", (int(sel[0]),)).fetchone()
        conn.close()
        d = WartungDialog(self, row)
        self.wait_window(d)
        if d.result:
            v = d.result
            conn = get_db()
            conn.execute("UPDATE wartung SET titel=?,beschreibung=?,prioritaet=?,status=?,gemeldet_von=?,einheit=?,kosten=?,notizen=? WHERE id=?",
                (v["titel"], v["beschreibung"], v["prioritaet"], v["status"],
                 v["gemeldet_von"], v["einheit"], v["kosten"] or None, v["notizen"], int(sel[0])))
            conn.commit(); conn.close(); self._load()

    def _mark_done(self):
        if not hat_recht("Wartung", "schreiben"):
            messagebox.showwarning("Berechtigung", "Keine Schreibberechtigung.", parent=self); return
        sel = self.tree.selection()
        if not sel: return
        conn = get_db()
        conn.execute("UPDATE wartung SET status='Erledigt',erledigt_am=? WHERE id=?",
            (date.today().isoformat(), int(sel[0])))
        conn.commit(); conn.close(); self._load()

    def _delete(self):
        if not hat_recht("Wartung", "loeschen"):
            messagebox.showwarning("Berechtigung", "Keine Löschberechtigung.", parent=self); return
        sel = self.tree.selection()
        if not sel: return
        if messagebox.askyesno("Löschen", "Auftrag löschen?"):
            conn = get_db()
            conn.execute("DELETE FROM wartung WHERE id=?", (int(sel[0]),))
            conn.commit(); conn.close(); self._load()


class WartungDialog(BaseDialog):
    def __init__(self, parent, row=None):
        super().__init__(parent, "Wartungsauftrag", 480, 520)
        r = dict(row) if row else {}
        self._add_field("Titel *", "titel", r.get("titel", ""))
        # Row 1: Priorität + Status
        two = tk.Frame(self._body, bg=BG_CARD)
        two.pack(fill="x", padx=20)
        two.columnconfigure((0, 1), weight=1)
        l  = tk.Frame(two, bg=BG_CARD); l.grid(row=0, column=0, padx=(0, 6), sticky="ew")
        ri = tk.Frame(two, bg=BG_CARD); ri.grid(row=0, column=1, padx=(6, 0), sticky="ew")
        self._add_field("Priorität", "prioritaet", r.get("prioritaet", "Mittel"),
                        widget_type="combo", options=["Hoch", "Mittel", "Niedrig"], row=l)
        self._add_field("Status", "status", r.get("status", "Offen"),
                        widget_type="combo", options=["Offen", "In Arbeit", "Erledigt"], row=ri)
        # Single fields
        self._add_field("Einheit",      "einheit",     r.get("einheit", ""))
        self._add_field("Gemeldet von", "gemeldet_von",r.get("gemeldet_von", ""))
        self._add_field("Kosten €",     "kosten",      r.get("kosten", ""))
        self._add_field("Beschreibung", "beschreibung",r.get("beschreibung", ""), widget_type="text")
        self._add_field("Notizen",      "notizen",     r.get("notizen", ""),      widget_type="text")

    def _on_save(self):
        v = self._get_values()
        if not v.get("titel"):
            messagebox.showwarning("Pflichtfeld", "Titel ist erforderlich.", parent=self); return
        # Normalisiere Datums-Felder
        for field in ["erstellt_am", "erledigt_am"]:
            if v.get(field):
                v[field] = parse_datum(v[field])
        self.result = v; self.destroy()

# ── Nachrichten-Seite ─────────────────────────────────────────────────────────

class NachrichtenPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_CARD)
        self._build()

    def _build(self):
        section_header(self, "Kommunikation", "✉ Neue Nachricht", self._new)
        cols = ("●", "Von", "An", "Betreff", "Priorität", "Datum")
        f, self.tree = make_table(self, cols, height=10)
        f.pack(fill="x", padx=20, pady=8)
        for c, w in zip(cols, [20, 140, 140, 220, 80, 120]):
            self.tree.heading(c, text=c); self.tree.column(c, width=w, anchor="w")
        self.tree.bind("<Double-1>", self._mark_read)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=20)
        tk.Label(self, text="Nachricht", bg=BG_CARD, fg=TEXT_LIGHT,
                 font=FONT_SMALL).pack(anchor="w", padx=20, pady=(8, 2))
        self._preview = tk.Text(self, height=8, bg=BG_INPUT, fg=TEXT,
                                relief="flat", font=FONT_BODY, state="disabled",
                                wrap="word", bd=0, padx=10, pady=8)
        self._preview.pack(fill="x", padx=20)

        btn_row = tk.Frame(self, bg=BG_CARD)
        btn_row.pack(fill="x", padx=20, pady=8)
        if hat_recht("Nachrichten", "schreiben"):
            make_btn(btn_row, "✔ Als gelesen markieren", self._mark_read, color=SUCCESS).pack(side="left", padx=(0, 8))
        if hat_recht("Nachrichten", "loeschen"):
            make_btn(btn_row, "🗑 Löschen", self._delete, color=DANGER).pack(side="left")

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self._load()

    def _load(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = get_db()
        for r in conn.execute("SELECT * FROM nachrichten ORDER BY datum DESC"):
            unread = "●" if not r["gelesen"] else ""
            self.tree.insert("", "end", iid=r["id"], values=(
                unread, r["von"] or "–", r["an"] or "–",
                r["betreff"], r["prioritaet"],
                fmt_date(r["datum"][:10] if r["datum"] else "")))
        conn.close()
        tree_empty_hint(self.tree)

    def _on_select(self, event):
        sel = self.tree.selection()
        if not sel: return
        conn = get_db()
        r = conn.execute("SELECT * FROM nachrichten WHERE id=?", (int(sel[0]),)).fetchone()
        conn.close()
        self._preview.config(state="normal")
        self._preview.delete("1.0", "end")
        if r:
            self._preview.insert("1.0",
                f"Von: {r['von'] or '–'}\nAn: {r['an'] or '–'}\nDatum: {fmt_date(str(r['datum'])[:10])}\n\n{r['inhalt'] or ''}")
        self._preview.config(state="disabled")

    def _new(self):
        if not hat_recht("Nachrichten", "schreiben"):
            messagebox.showwarning("Berechtigung", "Keine Schreibberechtigung.", parent=self); return
        d = NachrichtDialog(self)
        self.wait_window(d)
        if d.result:
            v = d.result
            conn = get_db()
            conn.execute("INSERT INTO nachrichten (von,an,betreff,inhalt,prioritaet) VALUES (?,?,?,?,?)",
                (v["von"], v["an"], v["betreff"], v["inhalt"], v["prioritaet"]))
            conn.commit(); conn.close(); self._load()

    def _mark_read(self, event=None):
        """Markiert die gewählte Nachricht als gelesen (auch per Doppelklick)."""
        sel = self.tree.selection()
        if not sel: return
        conn = get_db()
        conn.execute("UPDATE nachrichten SET gelesen=1 WHERE id=?", (int(sel[0]),))
        conn.commit(); conn.close(); self._load()

    def _delete(self):
        if not hat_recht("Nachrichten", "loeschen"):
            messagebox.showwarning("Berechtigung", "Keine Löschberechtigung.", parent=self); return
        sel = self.tree.selection()
        if not sel: return
        if messagebox.askyesno("Löschen", "Nachricht löschen?"):
            conn = get_db()
            conn.execute("DELETE FROM nachrichten WHERE id=?", (int(sel[0]),))
            conn.commit(); conn.close(); self._load()


class NachrichtDialog(BaseDialog):
    def __init__(self, parent):
        super().__init__(parent, "Neue Nachricht", 480, 460)
        self._add_field("Von",       "von",       "Hausverwaltung")
        self._add_field("An",        "an",        "Alle")
        self._add_field("Betreff *", "betreff",   "")
        self._add_field("Priorität", "prioritaet","Normal",
                        widget_type="combo", options=["Hoch", "Normal", "Niedrig"])
        self._add_field("Nachricht", "inhalt",    "", widget_type="text")

    def _on_save(self):
        v = self._get_values()
        if not v.get("betreff"):
            messagebox.showwarning("Pflichtfeld", "Betreff ist erforderlich.", parent=self); return
        self.result = v; self.destroy()

# ── Dokumente-Seite ───────────────────────────────────────────────────────────

class DokumentePage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_CARD)
        self._build()

    def _build(self):
        section_header(self, "Dokumente & Verträge", "＋ Dokument", self._new)
        cols = ("Titel", "Kategorie", "Beschreibung", "Datei", "Erstellt")
        f, self.tree = make_table(self, cols, height=16)
        f.pack(fill="both", expand=True, padx=20, pady=8)
        for c, w in zip(cols, [200, 120, 220, 180, 90]):
            self.tree.heading(c, text=c); self.tree.column(c, width=w, anchor="w")
        self.tree.bind("<Double-1>", self._open_file)

        btn_row = tk.Frame(self, bg=BG_CARD)
        btn_row.pack(fill="x", padx=20, pady=(0, 10))
        make_btn(btn_row, "📂 Öffnen",  self._open_file, color=ACCENT2).pack(side="left", padx=(0, 8))
        if hat_recht("Dokumente", "schreiben"):
            make_btn(btn_row, "✏ Bearbeiten", self._edit, color=BG_INPUT, fg=TEXT).pack(side="left", padx=(0, 8))
        if hat_recht("Dokumente", "loeschen"):
            make_btn(btn_row, "🗑 Löschen", self._delete,    color=DANGER).pack(side="left")
        self._load()

    def _load(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = get_db()
        for r in conn.execute("SELECT * FROM dokumente ORDER BY erstellt_am DESC"):
            self.tree.insert("", "end", iid=r["id"], values=(
                r["titel"], r["kategorie"] or "–",
                r["beschreibung"] or "–",
                r["dateiname"] or "–",
                fmt_date(r["erstellt_am"])))
        conn.close()
        tree_empty_hint(self.tree)

    def _new(self):
        if not hat_recht("Dokumente", "schreiben"):
            messagebox.showwarning("Berechtigung", "Keine Schreibberechtigung.", parent=self); return
        d = DokumentDialog(self)
        self.wait_window(d)
        if d.result:
            v = d.result
            conn = get_db()
            conn.execute("INSERT INTO dokumente (titel,kategorie,dateiname,dateipfad,beschreibung,erstellt_am) VALUES (?,?,?,?,?,?)",
                (v["titel"], v["kategorie"], v["dateiname"], v["dateipfad"],
                 v["beschreibung"], date.today().isoformat()))
            conn.commit(); conn.close(); self._load()

    def _open_file(self, event=None):
        sel = self.tree.selection()
        if not sel: return
        conn = get_db()
        r = conn.execute("SELECT dateipfad FROM dokumente WHERE id=?", (int(sel[0]),)).fetchone()
        conn.close()
        if r and r["dateipfad"] and os.path.exists(r["dateipfad"]):
            os.startfile(r["dateipfad"])
        else:
            messagebox.showinfo("Info", "Keine Datei verknüpft oder Datei nicht gefunden.")

    def _edit(self, event=None):
        if not hat_recht("Dokumente", "schreiben"):
            messagebox.showwarning("Berechtigung", "Keine Schreibberechtigung.", parent=self); return
        sel = self.tree.selection()
        if not sel: return
        conn = get_db()
        row = conn.execute("SELECT * FROM dokumente WHERE id=?", (int(sel[0]),)).fetchone()
        conn.close()
        d = DokumentDialog(self, row)
        self.wait_window(d)
        if d.result:
            v = d.result
            conn = get_db()
            conn.execute("UPDATE dokumente SET titel=?,kategorie=?,beschreibung=?,dateiname=?,dateipfad=? WHERE id=?",
                (v["titel"], v["kategorie"], v["beschreibung"], v.get("dateiname", ""), v.get("dateipfad", ""), int(sel[0])))
            conn.commit(); conn.close(); self._load()

    def _delete(self):
        if not hat_recht("Dokumente", "loeschen"):
            messagebox.showwarning("Berechtigung", "Keine Löschberechtigung.", parent=self); return
        sel = self.tree.selection()
        if not sel: return
        if messagebox.askyesno("Löschen", "Dokument löschen?"):
            conn = get_db()
            conn.execute("DELETE FROM dokumente WHERE id=?", (int(sel[0]),))
            conn.commit(); conn.close(); self._load()


class DokumentDialog(BaseDialog):
    def __init__(self, parent, row=None):
        super().__init__(parent, "Dokument " + ("bearbeiten" if row else "hinzufügen"), 480, 440)
        r = dict(row) if row else {}
        self._add_field("Titel *",     "titel",       r.get("titel", ""))
        self._add_field("Kategorie",   "kategorie",   r.get("kategorie", "Vertrag"),
                        widget_type="combo",
                        options=["Vertrag", "Beschluss", "Abrechnung", "Protokoll", "Versicherung", "Sonstiges"])
        self._add_field("Beschreibung","beschreibung",r.get("beschreibung", ""))
        self._path_var = tk.StringVar(value=r.get("dateipfad", ""))
        tk.Label(self._body, text="Datei", bg=BG_CARD, fg=TEXT_LIGHT,
                 font=FONT_SMALL).pack(anchor="w", padx=20, pady=(8, 1))
        row = tk.Frame(self._body, bg=BG_CARD)
        row.pack(fill="x", padx=20)
        tk.Entry(row, textvariable=self._path_var, bg=BG_INPUT, fg=TEXT,
                 relief="flat", font=FONT_BODY, state="readonly").pack(side="left", fill="x", expand=True, ipady=6)
        make_btn(row, "…", self._browse, color=BG_INPUT, fg=TEXT).pack(side="left", padx=(4, 0))

    def _browse(self):
        initial_dir = get_pfad("pfad_dokumente", "Dokumente")  # #38
        path = filedialog.askopenfilename(title="Datei auswählen", initialdir=initial_dir)
        if path:
            self._path_var.set(path)

    def _on_save(self):
        v = self._get_values()
        if not v.get("titel"):
            messagebox.showwarning("Pflichtfeld", "Titel ist erforderlich.", parent=self); return
        v["dateipfad"] = self._path_var.get()
        v["dateiname"] = os.path.basename(v["dateipfad"]) if v["dateipfad"] else ""
        self.result = v; self.destroy()

# ── Nebenkosten-Seite ─────────────────────────────────────────────────────────

class NebenkostenPage(tk.Frame):
    """Nebenkostenabrechnung mit drei Tabs:
    1. §28 WEG  – Eigentümer-Jahresabrechnung (Ausgaben aus Buchhaltung, Anteil nach MEA)
    2. §556 BGB – Mieter-Betriebskostenabrechnung (umlagefähige Kosten, Anteil nach Fläche)
    3. Wirtschaftsplan – Soll-Kosten pro Jahr und Kategorie (Soll/Ist-Vergleich)
    """

    def __init__(self, parent):
        super().__init__(parent, bg=BG_CARD)
        self._active_tab = "weg"
        self._build()

    # ── Aufbau ────────────────────────────────────────────────────────────────

    def _build(self):
        top = tk.Frame(self, bg=BG_CARD)
        top.pack(fill="x", padx=20, pady=(16, 0))
        tk.Label(top, text="Nebenkostenabrechnung", bg=BG_CARD, fg=TEXT, font=FONT_H2).pack(side="left")

        # Sub-Tab-Leiste
        self._tab_btns = {}
        tab_bar = tk.Frame(self, bg=BG_CARD)
        tab_bar.pack(fill="x", padx=20, pady=(8, 0))
        for tid, label in [("weg",  "🏛 §28 WEG – Eigentümer"),
                            ("bgb", "👤 §556 BGB – Mieter"),
                            ("wp",  "📋 Wirtschaftsplan"),
                            ("verbrauch", "🔢 Verbrauch")]:
            btn = tk.Button(tab_bar, text=label, font=FONT_NAV, relief="flat", bd=0,
                            padx=14, pady=7, cursor="hand2",
                            command=lambda t=tid: self._switch_tab(t))
            btn.pack(side="left", padx=2)
            self._tab_btns[tid] = btn
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(4, 0))

        # Content-Bereich
        self._content = tk.Frame(self, bg=BG_CARD)
        self._content.pack(fill="both", expand=True)

        # ── Tab §28 WEG ────────────────────────────────────────────────────
        self._view_weg = tk.Frame(self._content, bg=BG_CARD)

        yr_row = tk.Frame(self._view_weg, bg=BG_CARD)
        yr_row.pack(fill="x", padx=20, pady=(10, 4))
        tk.Label(yr_row, text="Jahr:", bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(side="left")
        self._weg_jahr = tk.StringVar(value=str(date.today().year))
        ttk.Combobox(yr_row, textvariable=self._weg_jahr, width=8,
                     values=[str(y) for y in range(date.today().year, date.today().year - 6, -1)]
                     ).pack(side="left", padx=6)
        make_btn(yr_row, "🔄 Auswertung", self._load_weg).pack(side="left")
        make_btn(yr_row, "📄 PDF Export", self._export_pdf_weg,
                 color=BG_INPUT, fg=TEXT).pack(side="left", padx=(8, 0))
        make_btn(yr_row, "🔒 Abrechnung feststellen", self._abrechnung_feststellen).pack(side="left", padx=(6, 0))
        make_btn(yr_row, "📋 Festgestellte Abrechnungen", self._show_abrechnungen,
                 color=BG_INPUT, fg=TEXT).pack(side="left", padx=(6, 0))

        # KPI-Zeile
        self._weg_kpi = tk.Frame(self._view_weg, bg=BG_CARD)
        self._weg_kpi.pack(fill="x", padx=20, pady=(6, 4))

        # Ausgaben-Tabelle (nach Kategorie) — Typ-Spalte kennzeichnet Rücklage-Einlagen
        tk.Label(self._view_weg, text="Ausgaben nach Kategorie (Einlagen separat ausgewiesen, §28 WEG)", bg=BG_CARD,
                 fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w", padx=20)
        cols_kat = ("Kategorie", "Gruppe", "Gesamt", "Umlagefähig", "Typ")
        fk, self._tree_weg_kat = make_table(self._view_weg, cols_kat, height=6)
        fk.pack(fill="x", padx=20, pady=(2, 6))
        for c, w in zip(cols_kat, [200, 160, 100, 90, 110]):
            self._tree_weg_kat.heading(c, text=c)
            self._tree_weg_kat.column(c, width=w, anchor="w")
        # Drill-Down: Doppelklick zeigt Einzelbuchungen der Kategorie
        self._tree_weg_kat.bind("<Double-1>", self._show_kategorie_detail)
        tk.Label(self._view_weg, text="💡 Doppelklick auf Kategorie → Einzelbuchungen anzeigen",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w", padx=20)

        # Eigentümer-Anteil-Tabelle
        tk.Label(self._view_weg, text="Anteil pro Eigentümer (nach MEA)", bg=BG_CARD,
                 fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w", padx=20)
        cols_eig = ("Eigentümer", "MEA %", "Kostenanteil", "Hausgeld (Ist)", "Saldo")
        fe, self._tree_weg_eig = make_table(self._view_weg, cols_eig, height=5)
        fe.pack(fill="x", padx=20, pady=(2, 8))
        for c, w in zip(cols_eig, [180, 60, 110, 110, 100]):
            self._tree_weg_eig.heading(c, text=c)
            self._tree_weg_eig.column(c, width=w, anchor="w")

        # ── Tab §556 BGB ───────────────────────────────────────────────────
        self._view_bgb = tk.Frame(self._content, bg=BG_CARD)

        yr_row2 = tk.Frame(self._view_bgb, bg=BG_CARD)
        yr_row2.pack(fill="x", padx=20, pady=(10, 4))
        tk.Label(yr_row2, text="Jahr:", bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(side="left")
        self._bgb_jahr = tk.StringVar(value=str(date.today().year))
        ttk.Combobox(yr_row2, textvariable=self._bgb_jahr, width=8,
                     values=[str(y) for y in range(date.today().year, date.today().year - 6, -1)]
                     ).pack(side="left", padx=6)
        make_btn(yr_row2, "🔄 Auswertung", self._load_bgb).pack(side="left")
        make_btn(yr_row2, "📄 PDF Export", self._export_pdf_bgb,
                 color=BG_INPUT, fg=TEXT).pack(side="left", padx=(8, 0))

        self._bgb_kpi = tk.Frame(self._view_bgb, bg=BG_CARD)
        self._bgb_kpi.pack(fill="x", padx=20, pady=(6, 4))

        tk.Label(self._view_bgb, text="Umlagefähige Kosten nach Kategorie", bg=BG_CARD,
                 fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w", padx=20)
        cols_uk = ("Kategorie", "Gesamt", "Schlüssel")
        fu, self._tree_bgb_kat = make_table(self._view_bgb, cols_uk, height=5)
        fu.pack(fill="x", padx=20, pady=(2, 6))
        for c, w in zip(cols_uk, [220, 110, 160]):
            self._tree_bgb_kat.heading(c, text=c)
            self._tree_bgb_kat.column(c, width=w, anchor="w")

        tk.Label(self._view_bgb, text="Anteil pro Mieter (nach Wohnfläche)", bg=BG_CARD,
                 fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w", padx=20)
        cols_mi = ("Wohnung", "Mieter", "Fläche m²", "Anteil %", "Kosten", "Vorauszahlung", "Saldo")
        fm, self._tree_bgb_mi = make_table(self._view_bgb, cols_mi, height=5)
        fm.pack(fill="x", padx=20, pady=(2, 8))
        for c, w in zip(cols_mi, [120, 150, 70, 65, 100, 110, 90]):
            self._tree_bgb_mi.heading(c, text=c)
            self._tree_bgb_mi.column(c, width=w, anchor="w")

        # ── Tab Wirtschaftsplan ─────────────────────────────────────────────
        self._view_wp = tk.Frame(self._content, bg=BG_CARD)

        wp_top = tk.Frame(self._view_wp, bg=BG_CARD)
        wp_top.pack(fill="x", padx=20, pady=(10, 4))
        tk.Label(wp_top, text="Jahr:", bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(side="left")
        self._wp_jahr = tk.StringVar(value=str(date.today().year))
        ttk.Combobox(wp_top, textvariable=self._wp_jahr, width=8,
                     values=[str(y) for y in range(date.today().year + 1, date.today().year - 5, -1)]
                     ).pack(side="left", padx=6)
        make_btn(wp_top, "🔄 Laden", self._load_wp).pack(side="left")
        make_btn(wp_top, "📊 Soll/Ist-Vergleich", self._wp_soll_ist,
                 color=BG_INPUT, fg=TEXT).pack(side="left", padx=(8, 0))
        make_btn(wp_top, "📄 PDF Export", self._export_pdf_wp,
                 color=BG_INPUT, fg=TEXT).pack(side="left", padx=(8, 0))
        if hat_recht("Nebenkosten", "schreiben"):
            make_btn(wp_top, "＋ Eintrag", self._wp_new).pack(side="right")
            make_btn(wp_top, "📊 Vorschlag aus Vorjahr", self._wp_vorschlag_erstellen,  # #41
                     color=ACCENT2).pack(side="right", padx=(0, 8))

        cols_wp = ("Kategorie", "Gruppe", "Soll-Betrag", "Notizen")
        fw, self._tree_wp = make_table(self._view_wp, cols_wp, height=16)
        fw.pack(fill="both", expand=True, padx=20, pady=(4, 4))
        for c, w in zip(cols_wp, [220, 160, 110, 220]):
            self._tree_wp.heading(c, text=c)
            self._tree_wp.column(c, width=w, anchor="w")
        self._tree_wp.bind("<Double-1>", self._wp_edit)

        wp_btn = tk.Frame(self._view_wp, bg=BG_CARD)
        wp_btn.pack(fill="x", padx=20, pady=(0, 10))
        if hat_recht("Nebenkosten", "schreiben"):
            make_btn(wp_btn, "✏ Bearbeiten", self._wp_edit,
                     color=BG_INPUT, fg=TEXT).pack(side="left", padx=(0, 8))
        if hat_recht("Nebenkosten", "loeschen"):
            make_btn(wp_btn, "🗑 Löschen", self._wp_delete, color=DANGER).pack(side="left")

        # ── Tab Verbrauch ──────────────────────────────────────────────────────
        self._view_verbrauch = tk.Frame(self._content, bg=BG_CARD)
        ctrl = tk.Frame(self._view_verbrauch, bg=BG_CARD)
        ctrl.pack(fill="x", padx=20, pady=10)
        tk.Label(ctrl, text="Jahr:", bg=BG_CARD, fg=TEXT, font=FONT_BODY).pack(side="left")
        self._vd_jahr_var = tk.StringVar(value=str(date.today().year - 1))
        ttk.Combobox(ctrl, textvariable=self._vd_jahr_var,
                     values=[str(y) for y in range(date.today().year, date.today().year - 5, -1)],
                     width=6, state="readonly").pack(side="left", padx=6)
        tk.Label(ctrl, text="Kategorie:", bg=BG_CARD, fg=TEXT, font=FONT_BODY).pack(side="left", padx=(12, 0))
        self._vd_kat_var = tk.StringVar(value="Heizung")
        ttk.Combobox(ctrl, textvariable=self._vd_kat_var,
                     values=["Heizung", "Wasser/Abwasser", "Strom (Allgemein)"],
                     width=20, state="readonly").pack(side="left", padx=6)
        make_btn(ctrl, "🔄 Laden", self._load_verbrauch_tab).pack(side="left", padx=6)
        tk.Frame(self._view_verbrauch, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(0, 8))
        frame, tree = make_table(self._view_verbrauch, ("Wohnung", "Anfang", "Ende", "Verbrauch", "Einheit", "Ablesedatum"))
        for col, w in [("Wohnung", 160), ("Anfang", 80), ("Ende", 80), ("Verbrauch", 80), ("Einheit", 60), ("Ablesedatum", 100)]:
            tree.column(col, width=w)
            tree.heading(col, text=col)
        frame.pack(fill="both", expand=True, padx=20)
        self._vd_tree = tree
        btn_row = tk.Frame(self._view_verbrauch, bg=BG_CARD)
        btn_row.pack(fill="x", padx=20, pady=8)
        make_btn(btn_row, "✏️ Bearbeiten", self._edit_verbrauch).pack(side="left", padx=(0, 6))

        self._switch_tab("weg")

    # ── Tab-Wechsel ────────────────────────────────────────────────────────────

    def _switch_tab(self, tid):
        self._active_tab = tid
        for t, btn in self._tab_btns.items():
            btn.configure(bg=ACCENT if t == tid else BG_CARD,
                          fg=TEXT_WHITE if t == tid else TEXT)
        for frame in (self._view_weg, self._view_bgb, self._view_wp, self._view_verbrauch):
            frame.pack_forget()
        {"weg": self._view_weg, "bgb": self._view_bgb, "wp": self._view_wp, "verbrauch": self._view_verbrauch}[tid].pack(
            fill="both", expand=True)
        {"weg": self._load_weg, "bgb": self._load_bgb, "wp": self._load_wp, "verbrauch": self._load_verbrauch_tab}[tid]()

    # ── Verbrauchsdaten-Tab ────────────────────────────────────────────────────

    def _load_verbrauch_tab(self):
        """Ladet Verbrauchsdaten aus der DB und zeigt sie in der Tabelle."""
        if not hasattr(self, "_vd_tree"):
            return
        for i in self._vd_tree.get_children():
            self._vd_tree.delete(i)
        jahr = self._vd_jahr_var.get() if hasattr(self, "_vd_jahr_var") else str(date.today().year - 1)
        kat = self._vd_kat_var.get() if hasattr(self, "_vd_kat_var") else "Heizung"
        conn = get_db()
        try:
            wohnungen = conn.execute("SELECT id, bezeichnung FROM wohnungen ORDER BY bezeichnung").fetchall()
            vd_map = {}
            for vd in conn.execute(
                "SELECT * FROM verbrauchsdaten WHERE jahr=? AND kategorie=?", (int(jahr), kat)
            ).fetchall():
                vd_map[vd["wohnung_id"]] = vd
        finally:
            conn.close()
        for w in wohnungen:
            vd = vd_map.get(w["id"])
            if vd:
                anfang = vd["zaehlerstand_anfang"] or 0
                ende = vd["zaehlerstand_ende"] or 0
                verbrauch = max(0, ende - anfang)
                self._vd_tree.insert("", "end", iid=f"w{w['id']}",
                    values=(w["bezeichnung"], f"{anfang:.1f}", f"{ende:.1f}",
                            f"{verbrauch:.1f}", vd["einheit"] or "kWh",
                            fmt_date(vd["ablesedatum"])))
            else:
                self._vd_tree.insert("", "end", iid=f"w{w['id']}",
                    values=(w["bezeichnung"], "–", "–", "–", "kWh", "–"),
                    tags=("leer",))
        self._vd_tree.tag_configure("leer", foreground=TEXT_LIGHT)
        tree_empty_hint(self._vd_tree)

    def _edit_verbrauch(self):
        """Dialog zum Bearbeiten von Verbrauchsdaten einer Wohnung."""
        if not hasattr(self, "_vd_tree"):
            return
        sel = self._vd_tree.selection()
        if not sel:
            messagebox.showinfo("Kein Eintrag", "Bitte eine Wohnung auswählen.", parent=self)
            return
        iid = sel[0]
        wohnung_id = int(iid.replace("w", ""))
        jahr = int(self._vd_jahr_var.get() if hasattr(self, "_vd_jahr_var") else date.today().year - 1)
        kat = self._vd_kat_var.get() if hasattr(self, "_vd_kat_var") else "Heizung"
        conn = get_db()
        try:
            vd = conn.execute("SELECT * FROM verbrauchsdaten WHERE wohnung_id=? AND jahr=? AND kategorie=?",
                              (wohnung_id, jahr, kat)).fetchone()
            wh_name = conn.execute("SELECT bezeichnung FROM wohnungen WHERE id=?", (wohnung_id,)).fetchone()
        finally:
            conn.close()
        dlg = tk.Toplevel(self)
        dlg.title(f"Verbrauch: {wh_name['bezeichnung'] if wh_name else ''} – {kat} – {jahr}")
        dlg.geometry("420x320")
        dlg.configure(bg=BG_CARD)
        dlg.transient(self.winfo_toplevel())
        felder = {}
        for label, key, default in [
            ("Zählerstand Anfang", "anfang", str(vd["zaehlerstand_anfang"] or 0) if vd else "0"),
            ("Zählerstand Ende", "ende", str(vd["zaehlerstand_ende"] or 0) if vd else "0"),
            ("Einheit (kWh / m³)", "einheit", vd["einheit"] if vd else "kWh"),
            ("Ablesedatum", "ablesedatum", vd["ablesedatum"] or "" if vd else ""),
            ("Notizen", "notizen", vd["notizen"] or "" if vd else ""),
        ]:
            row = tk.Frame(dlg, bg=BG_CARD)
            row.pack(fill="x", padx=20, pady=4)
            tk.Label(row, text=label, bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL, width=22, anchor="w").pack(side="left")
            var = tk.StringVar(value=default)
            tk.Entry(row, textvariable=var, bg=BG_INPUT, fg=TEXT, font=FONT_BODY, relief="flat").pack(side="left", fill="x", expand=True)
            felder[key] = var
        def _speichern():
            try:
                anfang = float(felder["anfang"].get().replace(",", ".") or 0)
                ende = float(felder["ende"].get().replace(",", ".") or 0)
            except ValueError:
                messagebox.showerror("Eingabefehler", "Zählerstände müssen Zahlen sein.", parent=dlg)
                return
            conn2 = get_db()
            try:
                conn2.execute(
                    "INSERT INTO verbrauchsdaten (wohnung_id, kategorie, jahr, zaehlerstand_anfang, "
                    "zaehlerstand_ende, einheit, ablesedatum, notizen) VALUES (?,?,?,?,?,?,?,?) "
                    "ON CONFLICT(wohnung_id,kategorie,jahr) DO UPDATE SET "
                    "zaehlerstand_anfang=excluded.zaehlerstand_anfang, "
                    "zaehlerstand_ende=excluded.zaehlerstand_ende, "
                    "einheit=excluded.einheit, ablesedatum=excluded.ablesedatum, "
                    "notizen=excluded.notizen",
                    (wohnung_id, kat, jahr, anfang, ende,
                     felder["einheit"].get(), felder["ablesedatum"].get() or None,
                     felder["notizen"].get() or None)
                )
                conn2.commit()
            finally:
                conn2.close()
            dlg.destroy()
            self._load_verbrauch_tab()
        btn_row = tk.Frame(dlg, bg=BG_CARD)
        btn_row.pack(pady=12)
        make_btn(btn_row, "💾 Speichern", _speichern).pack(side="left", padx=6)
        make_btn(btn_row, "Abbrechen", dlg.destroy, color=BG_INPUT, fg=TEXT).pack(side="left", padx=6)

    # ── §28 WEG Eigentümer ─────────────────────────────────────────────────────

    def _load_weg(self):
        try:
            jahr = int(self._weg_jahr.get())
        except ValueError:
            return

        conn = get_db()
        # Ausgaben aus Buchhaltung
        ausgaben_rows = conn.execute(
            "SELECT kategorie, SUM(betrag) as s FROM zahlungen "
            "WHERE typ='Ausgabe' AND strftime('%Y', datum)=? "
            "GROUP BY kategorie ORDER BY s DESC",
            (str(jahr),)).fetchall()
        # Hausgeld-Einnahmen pro Eigentümer
        hausgeld_rows = conn.execute(
            "SELECT eigentuemer_id, SUM(betrag) as s FROM zahlungen "
            "WHERE typ='Einnahme' AND kategorie='Hausgeld' AND strftime('%Y', datum)=? "
            "GROUP BY eigentuemer_id",
            (str(jahr),)).fetchall()
        hausgeld_gesamt = conn.execute(
            "SELECT SUM(betrag) FROM zahlungen "
            "WHERE typ='Einnahme' AND kategorie='Hausgeld' AND strftime('%Y', datum)=?",
            (str(jahr),)).fetchone()[0] or 0
        eigentuemer = conn.execute(
            "SELECT id, vorname, name, anteil_prozent FROM eigentuemer ORDER BY name").fetchall()
        conn.close()

        hausgeld_map = {r["eigentuemer_id"]: (r["s"] or 0) for r in hausgeld_rows}
        total_ausgaben   = sum(r["s"] or 0 for r in ausgaben_rows)
        # Rücklage-Einlagen separat (§28 WEG: nicht Betriebskosten)
        total_einlagen   = sum(r["s"] or 0 for r in ausgaben_rows
                               if (r["kategorie"] or "") in WEG_EINLAGE_KATEGORIEN)
        total_betrieb    = total_ausgaben - total_einlagen

        # KPI
        for w in self._weg_kpi.winfo_children():
            w.destroy()
        for label, wert, color in [
            ("Bewirtschaftungskosten", fmt_euro(total_betrieb),  DANGER),
            ("Rücklage-Einlage",       fmt_euro(total_einlagen), "#2E6DA4"),
            ("Hausgeld-Einnahmen",     fmt_euro(hausgeld_gesamt), SUCCESS),
            ("Saldo",                  fmt_euro(hausgeld_gesamt - total_ausgaben),
             SUCCESS if hausgeld_gesamt >= total_ausgaben else DANGER),
        ]:
            karte = tk.Frame(self._weg_kpi, bg=BG_INPUT, padx=14, pady=8)
            karte.pack(side="left", padx=(0, 10))
            tk.Label(karte, text=label, bg=BG_INPUT, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w")
            tk.Label(karte, text=wert,  bg=BG_INPUT, fg=color,      font=FONT_H3).pack(anchor="w")

        # Kategorie-Tabelle — Einlagen farblich hervorgehoben
        for i in self._tree_weg_kat.get_children():
            self._tree_weg_kat.delete(i)
        for r in ausgaben_rows:
            kat = r["kategorie"] or "Kategorie offen"
            meta = WEG_KATEGORIEN.get(kat, ("Sonstiges", False, "–"))
            umlage = "✔ ja" if meta[1] else "–"
            ist_einlage = kat in WEG_EINLAGE_KATEGORIEN
            typ = "Rücklage-Einlage" if ist_einlage else "Betriebskosten"
            tag = "einlage" if ist_einlage else ""
            self._tree_weg_kat.insert("", "end", values=(
                kat, meta[0], fmt_euro(r["s"] or 0), umlage, typ), tags=(tag,))
        self._tree_weg_kat.tag_configure("einlage", foreground="#2E6DA4")

        # Eigentümer-Anteil-Tabelle
        for i in self._tree_weg_eig.get_children():
            self._tree_weg_eig.delete(i)
        for e in eigentuemer:
            anteil_pct = parse_float(e["anteil_prozent"]) or 0
            kostenanteil = total_ausgaben * anteil_pct / 100
            hg_ist = hausgeld_map.get(e["id"], 0)
            saldo = hg_ist - kostenanteil
            color_tag = "plus" if saldo >= 0 else "minus"
            name = f"{e['vorname'] or ''} {e['name']}".strip()
            self._tree_weg_eig.insert("", "end", values=(
                name, f"{anteil_pct:.1f}%",
                fmt_euro(kostenanteil), fmt_euro(hg_ist),
                fmt_euro(saldo)), tags=(color_tag,))
        self._tree_weg_eig.tag_configure("plus",  foreground=SUCCESS)
        self._tree_weg_eig.tag_configure("minus", foreground=DANGER)

    # ── §556 BGB Mieter ────────────────────────────────────────────────────────

    def _load_bgb(self):
        try:
            jahr = int(self._bgb_jahr.get())
        except ValueError:
            return

        conn = get_db()
        # Nur umlagefähige Ausgaben
        platzhalter = ",".join("?" * len(WEG_KATEGORIEN_UMLAGE))
        umlage_rows = conn.execute(
            f"SELECT kategorie, SUM(betrag) as s FROM zahlungen "
            f"WHERE typ='Ausgabe' AND strftime('%Y', datum)=? AND kategorie IN ({platzhalter}) "
            f"GROUP BY kategorie ORDER BY s DESC",
            [str(jahr)] + WEG_KATEGORIEN_UMLAGE).fetchall() if WEG_KATEGORIEN_UMLAGE else []
        total_umlage = sum(r["s"] or 0 for r in umlage_rows)

        # ALLE Wohnungen – Leerstand-Anteil trägt Eigentümer (#24)
        # Aktiver Mieter: eingezogen vor Jahresende UND (nicht ausgezogen ODER Auszug >= Jahresbeginn)
        jahr_start = f"{jahr}-01-01"
        jahr_ende  = f"{jahr}-12-31"
        wohnungen = conn.execute(
            "SELECT w.id, w.bezeichnung, w.flaeche_qm, "
            "  m.id as mieter_id, m.vorname, m.name, m.nebenkosten_vorauszahlung "
            "FROM wohnungen w "
            "LEFT JOIN mieter m ON ("
            "  w.mieter_id = m.id "
            "  AND (m.einzug IS NULL OR m.einzug <= ?) "
            "  AND (m.auszug IS NULL OR m.auszug >= ?)"
            ")",
            (jahr_ende, jahr_start)).fetchall()
        conn.close()

        # Alle Wohnungen für Umlageschlüssel-Berechnung laden
        conn2 = get_db()
        try:
            alle_wohnungen_raw = conn2.execute("SELECT * FROM wohnungen").fetchall()
        finally:
            conn2.close()
        alle_wohnungen = [dict(w) for w in alle_wohnungen_raw]
        total_flaeche = sum(parse_float(w.get("flaeche_qm") or 0) for w in alle_wohnungen)

        # KPI – inkl. Leerstand-Info (#24)
        leerstand_count = sum(1 for w in wohnungen if w["mieter_id"] is None)
        for ww in self._bgb_kpi.winfo_children():
            ww.destroy()
        kpi_items = [
            ("Umlagefähige Kosten", fmt_euro(total_umlage), DANGER),
            ("Gesamtfläche",        f"{total_flaeche:.1f} m²", TEXT),
        ]
        if leerstand_count:
            kpi_items.append((f"Leerstände", f"{leerstand_count} Wohnung{'en' if leerstand_count > 1 else ''}", "#C8A96E"))
        for label, wert, color in kpi_items:
            karte = tk.Frame(self._bgb_kpi, bg=BG_INPUT, padx=14, pady=8)
            karte.pack(side="left", padx=(0, 10))
            tk.Label(karte, text=label, bg=BG_INPUT, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w")
            tk.Label(karte, text=wert,  bg=BG_INPUT, fg=color,      font=FONT_H3).pack(anchor="w")

        # Umlagefähige Kategorie-Tabelle
        for i in self._tree_bgb_kat.get_children():
            self._tree_bgb_kat.delete(i)
        for r in umlage_rows:
            kat = r["kategorie"] or "–"
            schluessel = WEG_KATEGORIEN.get(kat, ("–", True, "Wohnfläche"))[2]
            self._tree_bgb_kat.insert("", "end", values=(
                kat, fmt_euro(r["s"] or 0), schluessel))

        # Kosten-Dict: Kategorie → Betrag
        kosten_dict = {r["kategorie"]: abs(r["s"] or 0) for r in umlage_rows}

        # Mieter-Tabelle – Pro-Rata-Temporis + echte Umlageschlüssel (#smart-workflow)
        for i in self._tree_bgb_mi.get_children():
            self._tree_bgb_mi.delete(i)
        for w in wohnungen:
            ist_leerstand = w["mieter_id"] is None
            # Zeitanteil (Pro-Rata-Temporis) – nur wenn Mieter vorhanden
            einzug = None
            auszug = None
            if not ist_leerstand:
                # Mieter-Daten laden um Einzug/Auszug zu erhalten
                conn3 = get_db()
                try:
                    mi = conn3.execute("SELECT einzug, auszug FROM mieter WHERE id=?",
                                       (w["mieter_id"],)).fetchone()
                    if mi:
                        einzug = mi["einzug"]
                        auszug = mi["auszug"]
                finally:
                    conn3.close()
            zeitfaktor = pro_rata_temporis(einzug, auszug, int(jahr)) if not ist_leerstand else 1.0

            # Kosten summieren nach Umlageschlüssel pro Kategorie
            kosten = 0.0
            wh_id = None
            conn4 = get_db()
            try:
                wh = conn4.execute("SELECT id FROM wohnungen WHERE bezeichnung=?",
                                   (w["bezeichnung"],)).fetchone()
                if wh:
                    wh_id = wh["id"]
            finally:
                conn4.close()
            if wh_id:
                for kat, kat_kosten in kosten_dict.items():
                    kat_info = BuchhaltungPage.KOSTENARTEN.get(kat, {})
                    schluessel = kat_info.get("schluessel", "Wohnflaeche")
                    if not schluessel or schluessel in ("–", "-"):
                        schluessel = "Wohnflaeche"
                    anteil = self._berechne_umlageanteil(wh_id, schluessel, int(jahr), alle_wohnungen)
                    kosten += kat_kosten * anteil * zeitfaktor
            else:
                # Fallback: Wohnfläche
                flaeche = parse_float(w["flaeche_qm"]) or 0
                anteil_pct = (flaeche / total_flaeche) if total_flaeche else 0
                kosten = total_umlage * anteil_pct * zeitfaktor

            flaeche = parse_float(w["flaeche_qm"]) or 0
            anteil_pct = (flaeche / total_flaeche * 100) if total_flaeche else 0

            if ist_leerstand:
                mieter_name   = "⚠ Leerstand (Eigentümer)"
                vorauszahlung = 0.0
                saldo         = -kosten
                color_tag     = "leerstand"
            else:
                mieter_name   = f"{w['vorname'] or ''} {w['name']}".strip()
                vorauszahlung = (parse_float(w["nebenkosten_vorauszahlung"]) or 0) * 12 * zeitfaktor
                saldo         = vorauszahlung - kosten
                color_tag     = "plus" if saldo >= 0 else "minus"
            self._tree_bgb_mi.insert("", "end", values=(
                w["bezeichnung"], mieter_name,
                f"{flaeche:.1f}", f"{anteil_pct:.1f}%",
                fmt_euro(kosten), fmt_euro(vorauszahlung),
                fmt_euro(saldo)), tags=(color_tag,))
        self._tree_bgb_mi.tag_configure("plus",      foreground=SUCCESS)
        self._tree_bgb_mi.tag_configure("minus",     foreground=DANGER)
        self._tree_bgb_mi.tag_configure("leerstand", foreground="#C8A96E")

    # ── Wirtschaftsplan ────────────────────────────────────────────────────────

    def _load_wp(self):
        try:
            jahr = int(self._wp_jahr.get())
        except ValueError:
            return
        for i in self._tree_wp.get_children():
            self._tree_wp.delete(i)
        conn = get_db()
        rows = conn.execute(
            "SELECT * FROM wirtschaftsplan WHERE jahr=? ORDER BY kategorie",
            (jahr,)).fetchall()
        conn.close()
        for r in rows:
            meta = WEG_KATEGORIEN.get(r["kategorie"], ("Sonstiges", False, "–"))
            self._tree_wp.insert("", "end", iid=r["id"], values=(
                r["kategorie"], meta[0],
                fmt_euro(r["betrag_soll"]), r["notizen"] or "–"))

    def _wp_new(self):
        if not hat_recht("Nebenkosten", "schreiben"):
            messagebox.showwarning("Berechtigung", "Keine Schreibberechtigung.", parent=self); return
        try:
            jahr = int(self._wp_jahr.get())
        except ValueError:
            messagebox.showwarning("Jahr", "Bitte zuerst ein gültiges Jahr wählen.", parent=self); return
        d = WirtschaftsplanDialog(self, jahr=jahr)
        self.wait_window(d)
        if d.result:
            v = d.result
            conn = get_db()
            try:
                conn.execute(
                    "INSERT OR REPLACE INTO wirtschaftsplan (jahr, kategorie, betrag_soll, notizen) "
                    "VALUES (?,?,?,?)",
                    (v["jahr"], v["kategorie"], v["betrag_soll"], v["notizen"]))
                conn.commit()
            finally:
                conn.close()
            self._load_wp()

    def _wp_edit(self, event=None):
        if not hat_recht("Nebenkosten", "schreiben"):
            messagebox.showwarning("Berechtigung", "Keine Schreibberechtigung.", parent=self); return
        sel = self._tree_wp.selection()
        if not sel: return
        conn = get_db()
        row = conn.execute("SELECT * FROM wirtschaftsplan WHERE id=?", (int(sel[0]),)).fetchone()
        conn.close()
        d = WirtschaftsplanDialog(self, row=row)
        self.wait_window(d)
        if d.result:
            v = d.result
            conn = get_db()
            try:
                conn.execute(
                    "UPDATE wirtschaftsplan SET kategorie=?, betrag_soll=?, notizen=? WHERE id=?",
                    (v["kategorie"], v["betrag_soll"], v["notizen"], int(sel[0])))
                conn.commit()
            finally:
                conn.close()
            self._load_wp()

    def _wp_delete(self):
        if not hat_recht("Nebenkosten", "loeschen"):
            messagebox.showwarning("Berechtigung", "Keine Löschberechtigung.", parent=self); return
        sel = self._tree_wp.selection()
        if not sel: return
        if messagebox.askyesno("Löschen", "Wirtschaftsplan-Eintrag löschen?", parent=self):
            conn = get_db()
            try:
                conn.execute("DELETE FROM wirtschaftsplan WHERE id=?", (int(sel[0]),))
                conn.commit()
            finally:
                conn.close()
            self._load_wp()

    def _wp_vorschlag_erstellen(self):  # #41
        """Erstellt Wirtschaftsplan-Vorschläge aus Vorjahres-Ist-Daten."""
        try:
            aktuelles_jahr = int(self._wp_jahr.get())
        except ValueError:
            messagebox.showwarning("Eingabe", "Ungültige Jahreszahl.", parent=self); return
        vorjahr = aktuelles_jahr - 1

        # Vorjahres-Istdaten aus Buchungen laden
        conn = get_db()
        try:
            ist_daten = {}
            for r in conn.execute(
                "SELECT kategorie, SUM(betrag) as summe FROM zahlungen "
                "WHERE strftime('%Y', datum)=? AND typ='Ausgabe' "
                "GROUP BY kategorie ORDER BY kategorie",
                (str(vorjahr),)):
                ist_daten[r["kategorie"]] = r["summe"] or 0.0

            # Vorjahres-Soll-Daten
            soll_daten = {}
            for r in conn.execute(
                "SELECT kategorie, betrag_soll FROM wirtschaftsplan WHERE jahr=?", (vorjahr,)):
                soll_daten[r["kategorie"]] = r["betrag_soll"] or 0.0

            # Bereits vorhandene Einträge für Zieljahr
            ziel_vorhanden = {r["kategorie"] for r in
                              conn.execute("SELECT kategorie FROM wirtschaftsplan WHERE jahr=?", (aktuelles_jahr,))}
        finally:
            conn.close()

        if not ist_daten and not soll_daten:
            messagebox.showinfo("Keine Daten",
                f"Für {vorjahr} wurden keine Buchungen oder Wirtschaftsplan-Daten gefunden.",
                parent=self); return

        # Dialog öffnen
        dlg = WirtschaftsplanVorschlagDialog(self, vorjahr, aktuelles_jahr, ist_daten, soll_daten, ziel_vorhanden)
        self.wait_window(dlg)
        if dlg.result:
            conn = get_db()
            try:
                for kat, betrag in dlg.result.items():
                    conn.execute(
                        "INSERT OR REPLACE INTO wirtschaftsplan (jahr, kategorie, betrag_soll) VALUES (?,?,?)",
                        (aktuelles_jahr, kat, betrag))
                conn.commit()
            finally:
                conn.close()
            self._load_wp()
            messagebox.showinfo("Fertig",
                f"✅ {len(dlg.result)} Wirtschaftsplan-Positionen für {aktuelles_jahr} erstellt.",
                parent=self)

    def _wp_soll_ist(self):
        try:
            jahr = int(self._wp_jahr.get())
        except ValueError:
            return
        conn = get_db()
        soll_rows = conn.execute(
            "SELECT kategorie, betrag_soll FROM wirtschaftsplan WHERE jahr=?",
            (jahr,)).fetchall()
        ist_rows = conn.execute(
            "SELECT kategorie, SUM(betrag) as s FROM zahlungen "
            "WHERE typ='Ausgabe' AND strftime('%Y', datum)=? GROUP BY kategorie",
            (str(jahr),)).fetchall()
        conn.close()

        if not soll_rows:
            messagebox.showinfo(
                "Keine Daten",
                f"Für {jahr} sind noch keine Wirtschaftsplan-Positionen eingetragen.\n"
                "Bitte zuerst Positionen hinzufügen.",
                parent=self)
            return

        ist_map = {r["kategorie"]: (r["s"] or 0) for r in ist_rows}
        soll_map = {r["kategorie"]: (r["betrag_soll"] or 0) for r in soll_rows}
        alle_kat = sorted(set(list(soll_map.keys()) + list(ist_map.keys())))

        win = tk.Toplevel(self)
        win.title(f"Wirtschaftsplan Soll/Ist {jahr}")
        win.geometry("640x520")
        win.configure(bg=BG_CARD)
        win.grab_set()

        hdr = tk.Frame(win, bg=BG_SIDEBAR, height=46)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text=f"  Soll/Ist-Vergleich {jahr}", bg=BG_SIDEBAR,
                 fg=TEXT_WHITE, font=FONT_H3).pack(side="left", padx=20, pady=10)

        cols = ("Kategorie", "Soll", "Ist", "Abweichung", "Status")
        f, tree = make_table(win, cols, height=18)
        f.pack(fill="both", expand=True, padx=16, pady=10)
        for c, w in zip(cols, [200, 100, 100, 100, 80]):
            tree.heading(c, text=c); tree.column(c, width=w, anchor="w")

        total_soll = total_ist = 0
        for kat in alle_kat:
            soll = soll_map.get(kat, 0)
            ist = ist_map.get(kat, 0)
            abw = soll - ist
            total_soll += soll; total_ist += ist
            # "Überzogen" nur wenn ein Soll-Wert geplant war und überschritten wurde
            if soll == 0:
                status = "– kein Soll"
                color_tag = "neutral"
            elif abw >= 0:
                status = "✔ OK"
                color_tag = "ok"
            else:
                status = "⚠ Überzogen"
                color_tag = "over"
            tree.insert("", "end", values=(
                kat, fmt_euro(soll), fmt_euro(ist),
                fmt_euro(abw), status), tags=(color_tag,))

        tree.tag_configure("ok",      foreground=SUCCESS)
        tree.tag_configure("over",    foreground=DANGER)
        tree.tag_configure("neutral", foreground=TEXT_LIGHT)

        # Summenzeile
        total_abw = total_soll - total_ist
        summe_frame = tk.Frame(win, bg=BG_INPUT, padx=20, pady=8)
        summe_frame.pack(fill="x", padx=16, pady=(0, 12))
        for label, wert, color in [
            ("Gesamt Soll:", fmt_euro(total_soll), TEXT),
            ("Gesamt Ist:",  fmt_euro(total_ist),  TEXT),
            ("Abweichung:",  fmt_euro(total_abw),  SUCCESS if total_abw >= 0 else DANGER),
        ]:
            tk.Label(summe_frame, text=label, bg=BG_INPUT, fg=TEXT_LIGHT,
                     font=FONT_SMALL).pack(side="left", padx=(0, 4))
            tk.Label(summe_frame, text=wert, bg=BG_INPUT, fg=color,
                     font=FONT_BODY).pack(side="left", padx=(0, 20))

    # ── PDF-Export ─────────────────────────────────────────────────────────────

    def _get_weg_name(self) -> str:
        """Liest WEG-Namen aus Einstellungen für PDF-Header."""
        try:
            cfg = load_settings()
            return cfg.get("weg_name") or "WEG Hausverwaltung"
        except Exception:
            return "WEG Hausverwaltung"

    def _pdf_speichern(self, vorschlag: str) -> str | None:
        """Datei-Speichern-Dialog, gibt Pfad zurück oder None."""
        pfad = filedialog.asksaveasfilename(
            parent=self,
            title="PDF speichern",
            defaultextension=".pdf",
            initialfile=vorschlag,
            filetypes=[("PDF-Dokument", "*.pdf"), ("Alle Dateien", "*.*")])
        return pfad or None

    def _pdf_oeffnen(self, pfad: str):
        """Öffnet das gespeicherte PDF plattformübergreifend."""
        try:
            if os.name == "nt":
                os.startfile(pfad)
            elif os.uname().sysname == "Darwin":
                subprocess.Popen(["open", pfad])
            else:
                subprocess.Popen(["xdg-open", pfad])
        except Exception:
            pass

    def _abrechnung_feststellen(self):
        """Erstellt einen unveränderlichen Snapshot der aktuellen Abrechnung."""
        jahr = int(self._weg_jahr.get() if hasattr(self, "_weg_jahr") else date.today().year - 1)

        # Prüfen ob bereits festgestellt
        conn = get_db()
        try:
            existing = conn.execute(
                "SELECT * FROM abrechnungen WHERE jahr=? AND typ='WEG'", (jahr,)
            ).fetchone()
        finally:
            conn.close()

        if existing and existing["status"] == "Festgestellt":
            messagebox.showinfo("Bereits festgestellt",
                f"Die WEG-Abrechnung {jahr} wurde bereits am "
                f"{fmt_date(existing['festgestellt_am'])} festgestellt.\n"
                "Sie kann nicht erneut festgestellt werden.", parent=self)
            return

        if not messagebox.askyesno("Abrechnung feststellen",
            f"WEG-Jahresabrechnung {jahr} jetzt feststellen?\n\n"
            "Nach der Feststellung können keine Buchungen mehr hinzugefügt "
            "oder geändert werden, ohne eine neue Abrechnung zu erstellen.\n\n"
            "Fortfahren?", parent=self):
            return

        # Positionen einfrieren
        conn = get_db()
        try:
            # Abrechnung anlegen oder Status setzen
            if existing:
                conn.execute("DELETE FROM abrechnung_positionen WHERE abrechnung_id=?", (existing["id"],))
                conn.execute("DELETE FROM abrechnung_anteile WHERE abrechnung_id=?", (existing["id"],))
                abr_id = existing["id"]
                conn.execute(
                    "UPDATE abrechnungen SET status='Festgestellt', festgestellt_am=CURRENT_TIMESTAMP WHERE id=?",
                    (abr_id,)
                )
            else:
                conn.execute(
                    "INSERT INTO abrechnungen (jahr, typ, status, festgestellt_am) VALUES (?,?,?,CURRENT_TIMESTAMP)",
                    (jahr, "WEG", "Festgestellt")
                )
                abr_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

            # Alle relevanten Buchungen einfrieren
            buchungen = conn.execute(
                "SELECT id, kategorie, betrag FROM zahlungen "
                "WHERE typ='Ausgabe' AND strftime('%Y',datum)=? "
                "AND (abrechnungsrelevant IS NULL OR abrechnungsrelevant=1)",
                (str(jahr),)
            ).fetchall()

            for b in buchungen:
                kat_info = BuchhaltungPage.KOSTENARTEN.get(b["kategorie"], {})
                schluessel = kat_info.get("schluessel", "Wohnflaeche")
                conn.execute(
                    "INSERT INTO abrechnung_positionen (abrechnung_id, zahlung_id, kategorie, betrag, umlageschluessel) "
                    "VALUES (?,?,?,?,?)",
                    (abr_id, b["id"], b["kategorie"], abs(b["betrag"]), schluessel)
                )
                # Buchungen als 'abgerechnet' markieren
                conn.execute(
                    "UPDATE kontoauszug SET buchung_status='abgerechnet' WHERE zahlung_id=?",
                    (b["id"],)
                )

            conn.commit()
        finally:
            conn.close()

        messagebox.showinfo("✅ Festgestellt",
            f"WEG-Abrechnung {jahr} wurde festgestellt.\n"
            f"{len(buchungen)} Buchungen eingefroren.", parent=self)

    def _show_abrechnungen(self):
        """Zeigt alle festgestellten Abrechnungen."""
        dlg = tk.Toplevel(self)
        dlg.title("Festgestellte Abrechnungen")
        dlg.geometry("600x400")
        dlg.configure(bg=BG_CARD)
        dlg.transient(self.winfo_toplevel())

        tk.Label(dlg, text="Festgestellte Abrechnungen",
                 bg=BG_CARD, fg=TEXT, font=FONT_H2).pack(padx=20, pady=(16, 8), anchor="w")

        frame, tree = make_table(dlg, ("Jahr", "Typ", "Status", "Festgestellt am", "Positionen"))
        for col, w in [("Jahr", 60), ("Typ", 60), ("Status", 100), ("Festgestellt am", 140), ("Positionen", 80)]:
            tree.column(col, width=w)
            tree.heading(col, text=col)
        frame.pack(fill="both", expand=True, padx=16, pady=8)

        conn = get_db()
        try:
            for a in conn.execute("SELECT * FROM abrechnungen ORDER BY jahr DESC, typ").fetchall():
                n = conn.execute("SELECT COUNT(*) FROM abrechnung_positionen WHERE abrechnung_id=?",
                                 (a["id"],)).fetchone()[0]
                tree.insert("", "end", values=(
                    a["jahr"], a["typ"], a["status"],
                    fmt_date(a["festgestellt_am"]) if a["festgestellt_am"] else "–",
                    str(n)
                ))
        finally:
            conn.close()

        tree_empty_hint(tree)
        make_btn(dlg, "Schließen", dlg.destroy, color=BG_INPUT, fg=TEXT).pack(pady=12)

    # ── Drill-Down: Einzelbuchungen pro Kategorie ─────────────────────────────

    def _show_kategorie_detail(self, event=None):
        """Drill-Down: Doppelklick auf Kategorie zeigt Einzelbuchungen."""
        tree = event.widget if event else None
        if not tree:
            return
        sel = tree.selection()
        if not sel:
            return
        vals = tree.item(sel[0], "values")
        if not vals or vals[0] in ("", "(Keine Einträge vorhanden)"):
            return
        kategorie = vals[0]
        try:
            jahr = int(self._weg_jahr.get() if hasattr(self, "_weg_jahr") else date.today().year - 1)
        except ValueError:
            return

        dlg = tk.Toplevel(self)
        dlg.title(f"Buchungen: {kategorie} ({jahr})")
        dlg.geometry("720x420")
        dlg.configure(bg=BG_CARD)
        dlg.transient(self.winfo_toplevel())

        tk.Label(dlg, text=f"Einzelbuchungen – {kategorie} – {jahr}",
                 bg=BG_CARD, fg=TEXT, font=FONT_H2).pack(padx=20, pady=(16, 8), anchor="w")

        frame, tree2 = make_table(dlg, ("Datum", "Beschreibung", "Rechnungssteller", "Betrag", "Relevant"))
        for col, w in [("Datum", 90), ("Beschreibung", 230), ("Rechnungssteller", 150), ("Betrag", 100), ("Relevant", 70)]:
            tree2.column(col, width=w, anchor="w" if col != "Betrag" else "e")
            tree2.heading(col, text=col)
        frame.pack(fill="both", expand=True, padx=16, pady=8)

        conn = get_db()
        try:
            rows = conn.execute(
                "SELECT datum, beschreibung, rechnungssteller, betrag, abrechnungsrelevant "
                "FROM zahlungen WHERE typ='Ausgabe' AND kategorie=? AND strftime('%Y',datum)=? "
                "ORDER BY datum",
                (kategorie, str(jahr))
            ).fetchall()
        finally:
            conn.close()

        summe = 0.0
        for row in rows:
            relevant = "✅" if (row["abrechnungsrelevant"] is None or row["abrechnungsrelevant"] != 0) else "❌"
            betrag_abs = abs(row["betrag"] or 0)
            tree2.insert("", "end", values=(
                fmt_date(row["datum"]),
                row["beschreibung"] or "",
                row["rechnungssteller"] or "",
                fmt_euro(betrag_abs),
                relevant
            ))
            if row["abrechnungsrelevant"] is None or row["abrechnungsrelevant"] != 0:
                summe += betrag_abs

        tree_empty_hint(tree2)
        tk.Label(dlg, text=f"Summe (abrechnungsrelevant): {fmt_euro(summe)}",
                 bg=BG_CARD, fg=TEXT, font=FONT_H3).pack(padx=16, pady=(0, 4), anchor="e")
        make_btn(dlg, "Schließen", dlg.destroy, color=BG_INPUT, fg=TEXT).pack(pady=(0, 12))

    # ── Echte Umlageschlüssel-Berechnung ─────────────────────────────────────

    def _berechne_umlageanteil(self, wohnung_id: int, schluessel: str, jahr: int,
                               alle_wohnungen: list) -> float:
        """Berechnet den Umlageanteil (0.0–1.0) einer Wohnung nach dem angegebenen Schlüssel.

        Unterstützte Schlüssel: Wohnflaeche, MEA, Kopfanzahl, Verbrauch, HeizKV
        """
        conn = get_db()
        try:
            w = conn.execute("SELECT * FROM wohnungen WHERE id=?", (wohnung_id,)).fetchone()
            if not w:
                return 0.0

            if schluessel in ("Wohnflaeche", "Wohnfläche", "–", "-", ""):
                gesamt = sum(parse_float(wh.get("flaeche_qm") or 0) for wh in alle_wohnungen)
                eigene = parse_float(w["flaeche_qm"] or 0)
                return eigene / gesamt if gesamt > 0 else 0.0

            elif schluessel == "MEA":
                gesamt = sum(parse_float(wh.get("mea_tausendstel") or 0) for wh in alle_wohnungen)
                eigene = parse_float(w["mea_tausendstel"] or 0)
                return eigene / gesamt if gesamt > 0 else 0.0

            elif schluessel == "Kopfanzahl":
                gesamt = sum(max(1, wh.get("bewohner_anzahl") or 1) for wh in alle_wohnungen)
                eigene = max(1, w["bewohner_anzahl"] or 1)
                return eigene / gesamt if gesamt > 0 else 0.0

            elif schluessel == "Verbrauch":
                vd = conn.execute(
                    "SELECT zaehlerstand_anfang, zaehlerstand_ende FROM verbrauchsdaten "
                    "WHERE wohnung_id=? AND jahr=?", (wohnung_id, jahr)
                ).fetchone()
                eigene = max(0.0, (parse_float(vd["zaehlerstand_ende"] or 0) -
                                   parse_float(vd["zaehlerstand_anfang"] or 0))) if vd else 0.0
                wh_ids = [wh["id"] for wh in alle_wohnungen if wh.get("id")]
                if wh_ids:
                    ph = ",".join("?" * len(wh_ids))
                    gesamt_v = conn.execute(
                        f"SELECT COALESCE(SUM(zaehlerstand_ende - zaehlerstand_anfang), 0) "
                        f"FROM verbrauchsdaten WHERE jahr=? AND wohnung_id IN ({ph})",
                        [jahr] + wh_ids
                    ).fetchone()[0] or 0.0
                else:
                    gesamt_v = 0.0
                return eigene / gesamt_v if gesamt_v > 0 else 0.0

            elif schluessel == "HeizKV":
                # §7 HeizKV: 70% Verbrauch, 30% Wohnfläche
                v_anteil = self._berechne_umlageanteil(wohnung_id, "Verbrauch", jahr, alle_wohnungen)
                f_anteil = self._berechne_umlageanteil(wohnung_id, "Wohnflaeche", jahr, alle_wohnungen)
                return 0.70 * v_anteil + 0.30 * f_anteil

            else:
                # Fallback: Wohnfläche
                return self._berechne_umlageanteil(wohnung_id, "Wohnflaeche", jahr, alle_wohnungen)
        finally:
            conn.close()

    def _export_pdf_weg(self):
        """PDF-Export §28 WEG Eigentümer-Jahresabrechnung."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                            Paragraph, Spacer)
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
        except ImportError:
            messagebox.showerror("Fehler",
                "reportlab ist nicht installiert.\n"
                "Bitte 'pip install reportlab' ausführen.", parent=self)
            return

        try:
            jahr = int(self._weg_jahr.get())
        except ValueError:
            messagebox.showwarning("Jahr", "Bitte zuerst eine Auswertung laden.", parent=self); return

        # Daten laden
        conn = get_db()
        ausgaben_rows = conn.execute(
            "SELECT kategorie, SUM(betrag) as s FROM zahlungen "
            "WHERE typ='Ausgabe' AND strftime('%Y', datum)=? "
            "GROUP BY kategorie ORDER BY s DESC", (str(jahr),)).fetchall()
        hausgeld_rows = conn.execute(
            "SELECT eigentuemer_id, SUM(betrag) as s FROM zahlungen "
            "WHERE typ='Einnahme' AND kategorie='Hausgeld' AND strftime('%Y', datum)=? "
            "GROUP BY eigentuemer_id", (str(jahr),)).fetchall()
        hausgeld_gesamt = conn.execute(
            "SELECT SUM(betrag) FROM zahlungen "
            "WHERE typ='Einnahme' AND kategorie='Hausgeld' AND strftime('%Y', datum)=?",
            (str(jahr),)).fetchone()[0] or 0
        eigentuemer = conn.execute(
            "SELECT id, vorname, name, anteil_prozent FROM eigentuemer ORDER BY name").fetchall()
        conn.close()

        hausgeld_map  = {r["eigentuemer_id"]: (r["s"] or 0) for r in hausgeld_rows}
        total_ausgaben = sum(r["s"] or 0 for r in ausgaben_rows)
        total_einlagen = sum(r["s"] or 0 for r in ausgaben_rows
                             if (r["kategorie"] or "") in WEG_EINLAGE_KATEGORIEN)
        total_betrieb  = total_ausgaben - total_einlagen

        pfad = self._pdf_speichern(f"WEG_§28_Jahresabrechnung_{jahr}.pdf")
        if not pfad:
            return

        try:
            doc = SimpleDocTemplate(pfad, pagesize=A4,
                                    leftMargin=2*cm, rightMargin=2*cm,
                                    topMargin=2*cm, bottomMargin=2*cm)
            styles = getSampleStyleSheet()
            H1 = ParagraphStyle("H1", parent=styles["Heading1"],
                                 fontSize=16, textColor=colors.HexColor("#1C2B3A"))
            H2 = ParagraphStyle("H2", parent=styles["Heading2"],
                                 fontSize=12, textColor=colors.HexColor("#1C2B3A"))
            NORMAL = styles["Normal"]
            SMALL  = ParagraphStyle("small", parent=NORMAL, fontSize=8,
                                    textColor=colors.HexColor("#666666"))

            weg_name = self._get_weg_name()
            story = [
                Paragraph(weg_name, H1),
                Paragraph(f"§28 WEG – Jahresabrechnung {jahr}", H2),
                Paragraph(f"Erstellt am {date.today().strftime('%d.%m.%Y')}", SMALL),
                Spacer(1, 0.5*cm),
            ]

            # KPI-Tabelle
            kpi_data = [
                ["Bewirtschaftungskosten", fmt_euro(total_betrieb)],
                ["Rücklage-Einlage",        fmt_euro(total_einlagen)],
                ["Hausgeld-Einnahmen",      fmt_euro(hausgeld_gesamt)],
                ["Saldo",                   fmt_euro(hausgeld_gesamt - total_ausgaben)],
            ]
            kpi_t = Table(kpi_data, colWidths=[10*cm, 5*cm])
            kpi_t.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#F7F5F0")),
                ("FONTNAME",   (0,0), (-1,-1), "Helvetica"),
                ("FONTSIZE",   (0,0), (-1,-1), 10),
                ("ALIGN",      (1,0), (1,-1), "RIGHT"),
                ("ROWBACKGROUNDS", (0,0), (-1,-1),
                 [colors.HexColor("#F7F5F0"), colors.HexColor("#EEEAE3")]),
                ("GRID",       (0,0), (-1,-1), 0.4, colors.HexColor("#CCCCCC")),
                ("TOPPADDING", (0,0), (-1,-1), 5),
                ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ]))
            story += [kpi_t, Spacer(1, 0.4*cm)]

            # Ausgaben-Tabelle
            story.append(Paragraph("Ausgaben nach Kategorie", H2))
            kat_data = [["Kategorie", "Gruppe", "Betrag", "Typ"]]
            for r in ausgaben_rows:
                kat = r["kategorie"] or "Kategorie offen"
                meta = WEG_KATEGORIEN.get(kat, ("Sonstiges", False, "–"))
                typ  = "Rücklage-Einlage" if kat in WEG_EINLAGE_KATEGORIEN else "Betriebskosten"
                kat_data.append([kat, meta[0], fmt_euro(r["s"] or 0), typ])
            kat_data.append(["Gesamt", "", fmt_euro(total_ausgaben), ""])

            kat_t = Table(kat_data, colWidths=[5*cm, 4.5*cm, 3*cm, 3.5*cm])
            kat_t.setStyle(TableStyle([
                ("BACKGROUND",  (0,0), (-1,0),  colors.HexColor("#1C2B3A")),
                ("TEXTCOLOR",   (0,0), (-1,0),  colors.white),
                ("FONTNAME",    (0,0), (-1,0),  "Helvetica-Bold"),
                ("FONTSIZE",    (0,0), (-1,-1), 9),
                ("ALIGN",       (2,1), (2,-1),  "RIGHT"),
                ("ROWBACKGROUNDS", (0,1), (-1,-2),
                 [colors.white, colors.HexColor("#F7F5F0")]),
                ("BACKGROUND",  (0,-1), (-1,-1), colors.HexColor("#EEEAE3")),
                ("FONTNAME",    (0,-1), (-1,-1), "Helvetica-Bold"),
                ("GRID",        (0,0), (-1,-1), 0.4, colors.HexColor("#CCCCCC")),
                ("TOPPADDING",  (0,0), (-1,-1), 4),
                ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ]))
            story += [kat_t, Spacer(1, 0.4*cm)]

            # Eigentümer-Tabelle
            story.append(Paragraph("Anteil pro Eigentümer (nach MEA)", H2))
            eig_data = [["Eigentümer", "MEA %", "Kostenanteil", "Hausgeld (Ist)", "Saldo"]]
            for e in eigentuemer:
                anteil_pct = parse_float(e["anteil_prozent"]) or 0
                kostenanteil = total_ausgaben * anteil_pct / 100
                hg_ist = hausgeld_map.get(e["id"], 0)
                saldo  = hg_ist - kostenanteil
                name   = f"{e['vorname'] or ''} {e['name']}".strip()
                eig_data.append([name, f"{anteil_pct:.1f}%",
                                  fmt_euro(kostenanteil), fmt_euro(hg_ist), fmt_euro(saldo)])

            eig_t = Table(eig_data, colWidths=[4.5*cm, 2*cm, 3*cm, 3*cm, 3.5*cm])
            eig_t.setStyle(TableStyle([
                ("BACKGROUND",  (0,0), (-1,0),  colors.HexColor("#1C2B3A")),
                ("TEXTCOLOR",   (0,0), (-1,0),  colors.white),
                ("FONTNAME",    (0,0), (-1,0),  "Helvetica-Bold"),
                ("FONTSIZE",    (0,0), (-1,-1), 9),
                ("ALIGN",       (1,1), (-1,-1), "RIGHT"),
                ("ROWBACKGROUNDS", (0,1), (-1,-1),
                 [colors.white, colors.HexColor("#F7F5F0")]),
                ("GRID",        (0,0), (-1,-1), 0.4, colors.HexColor("#CCCCCC")),
                ("TOPPADDING",  (0,0), (-1,-1), 4),
                ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ]))
            story.append(eig_t)

            doc.build(story)
            if messagebox.askyesno("PDF erstellt",
                f"PDF gespeichert:\n{pfad}\n\nJetzt öffnen?", parent=self):
                self._pdf_oeffnen(pfad)
        except Exception as exc:
            messagebox.showerror("PDF-Fehler", f"PDF konnte nicht erstellt werden:\n{exc}",
                                 parent=self)

    def _export_pdf_bgb(self):
        """PDF-Export §556 BGB Mieter-Betriebskostenabrechnung."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                            Paragraph, Spacer)
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
        except ImportError:
            messagebox.showerror("Fehler",
                "reportlab ist nicht installiert.\n"
                "Bitte 'pip install reportlab' ausführen.", parent=self)
            return

        try:
            jahr = int(self._bgb_jahr.get())
        except ValueError:
            messagebox.showwarning("Jahr", "Bitte zuerst eine Auswertung laden.", parent=self); return

        # Daten laden
        conn = get_db()
        platzhalter = ",".join("?" * len(WEG_KATEGORIEN_UMLAGE))
        umlage_rows = conn.execute(
            f"SELECT kategorie, SUM(betrag) as s FROM zahlungen "
            f"WHERE typ='Ausgabe' AND strftime('%Y', datum)=? AND kategorie IN ({platzhalter}) "
            f"GROUP BY kategorie ORDER BY s DESC",
            [str(jahr)] + WEG_KATEGORIEN_UMLAGE).fetchall() if WEG_KATEGORIEN_UMLAGE else []
        total_umlage = sum(r["s"] or 0 for r in umlage_rows)
        jahr_start = f"{jahr}-01-01"
        jahr_ende  = f"{jahr}-12-31"
        wohnungen = conn.execute(
            "SELECT w.id, w.bezeichnung, w.flaeche_qm, "
            "  m.id as mieter_id, m.vorname, m.name, m.nebenkosten_vorauszahlung "
            "FROM wohnungen w "
            "LEFT JOIN mieter m ON ("
            "  w.mieter_id = m.id "
            "  AND (m.einzug IS NULL OR m.einzug <= ?) "
            "  AND (m.auszug IS NULL OR m.auszug >= ?)"
            ")",
            (jahr_ende, jahr_start)).fetchall()
        conn.close()

        total_flaeche = sum(parse_float(w["flaeche_qm"]) or 0 for w in wohnungen)

        pfad = self._pdf_speichern(f"WEG_§556_Betriebskosten_{jahr}.pdf")
        if not pfad:
            return

        try:
            doc = SimpleDocTemplate(pfad, pagesize=A4,
                                    leftMargin=2*cm, rightMargin=2*cm,
                                    topMargin=2*cm, bottomMargin=2*cm)
            styles = getSampleStyleSheet()
            H1 = ParagraphStyle("H1", parent=styles["Heading1"],
                                 fontSize=16, textColor=colors.HexColor("#1C2B3A"))
            H2 = ParagraphStyle("H2", parent=styles["Heading2"],
                                 fontSize=12, textColor=colors.HexColor("#1C2B3A"))
            SMALL = ParagraphStyle("small", parent=styles["Normal"], fontSize=8,
                                   textColor=colors.HexColor("#666666"))

            weg_name = self._get_weg_name()
            story = [
                Paragraph(weg_name, H1),
                Paragraph(f"§556 BGB – Betriebskostenabrechnung {jahr}", H2),
                Paragraph(f"Erstellt am {date.today().strftime('%d.%m.%Y')}", SMALL),
                Spacer(1, 0.5*cm),
            ]

            # Umlagefähige Kosten
            story.append(Paragraph("Umlagefähige Kosten nach Kategorie", H2))
            uk_data = [["Kategorie", "Gesamt", "Schlüssel"]]
            for r in umlage_rows:
                kat = r["kategorie"] or "–"
                schluessel = WEG_KATEGORIEN.get(kat, ("–", True, "Wohnfläche"))[2]
                uk_data.append([kat, fmt_euro(r["s"] or 0), schluessel])
            uk_data.append(["Gesamt umlagefähig", fmt_euro(total_umlage), ""])

            uk_t = Table(uk_data, colWidths=[7*cm, 4*cm, 5*cm])
            uk_t.setStyle(TableStyle([
                ("BACKGROUND",  (0,0), (-1,0),  colors.HexColor("#1C2B3A")),
                ("TEXTCOLOR",   (0,0), (-1,0),  colors.white),
                ("FONTNAME",    (0,0), (-1,0),  "Helvetica-Bold"),
                ("FONTSIZE",    (0,0), (-1,-1), 9),
                ("ALIGN",       (1,1), (1,-1),  "RIGHT"),
                ("ROWBACKGROUNDS", (0,1), (-1,-2),
                 [colors.white, colors.HexColor("#F7F5F0")]),
                ("BACKGROUND",  (0,-1), (-1,-1), colors.HexColor("#EEEAE3")),
                ("FONTNAME",    (0,-1), (-1,-1), "Helvetica-Bold"),
                ("GRID",        (0,0), (-1,-1), 0.4, colors.HexColor("#CCCCCC")),
                ("TOPPADDING",  (0,0), (-1,-1), 4),
                ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ]))
            story += [uk_t, Spacer(1, 0.5*cm)]

            # Mieter-Abrechnung
            story.append(Paragraph(
                f"Abrechnung pro Mieter/Wohnung  |  Gesamtfläche: {total_flaeche:.1f} m²", H2))
            mi_data = [["Wohnung", "Mieter", "Fläche m²", "Anteil %",
                        "Kosten", "Vorauszahlung", "Saldo"]]
            for w in wohnungen:
                flaeche    = parse_float(w["flaeche_qm"]) or 0
                anteil_pct = (flaeche / total_flaeche * 100) if total_flaeche else 0
                kosten     = total_umlage * anteil_pct / 100
                if w["mieter_id"] is None:
                    mieter_name   = "Leerstand (Eigentümer)"
                    vorauszahlung = 0.0
                    saldo         = -kosten
                else:
                    mieter_name   = f"{w['vorname'] or ''} {w['name']}".strip()
                    vorauszahlung = (parse_float(w["nebenkosten_vorauszahlung"]) or 0) * 12
                    saldo         = vorauszahlung - kosten
                mi_data.append([
                    w["bezeichnung"], mieter_name,
                    f"{flaeche:.1f}", f"{anteil_pct:.1f}%",
                    fmt_euro(kosten), fmt_euro(vorauszahlung), fmt_euro(saldo)])

            mi_t = Table(mi_data, colWidths=[2.5*cm, 4*cm, 1.8*cm, 1.8*cm, 2.5*cm, 2.8*cm, 2.6*cm])
            mi_t.setStyle(TableStyle([
                ("BACKGROUND",  (0,0), (-1,0),  colors.HexColor("#1C2B3A")),
                ("TEXTCOLOR",   (0,0), (-1,0),  colors.white),
                ("FONTNAME",    (0,0), (-1,0),  "Helvetica-Bold"),
                ("FONTSIZE",    (0,0), (-1,-1), 8),
                ("ALIGN",       (2,1), (-1,-1), "RIGHT"),
                ("ROWBACKGROUNDS", (0,1), (-1,-1),
                 [colors.white, colors.HexColor("#F7F5F0")]),
                ("GRID",        (0,0), (-1,-1), 0.4, colors.HexColor("#CCCCCC")),
                ("TOPPADDING",  (0,0), (-1,-1), 4),
                ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ]))
            story.append(mi_t)

            doc.build(story)
            if messagebox.askyesno("PDF erstellt",
                f"PDF gespeichert:\n{pfad}\n\nJetzt öffnen?", parent=self):
                self._pdf_oeffnen(pfad)
        except Exception as exc:
            messagebox.showerror("PDF-Fehler", f"PDF konnte nicht erstellt werden:\n{exc}",
                                 parent=self)

    def _export_pdf_wp(self):
        """PDF-Export Wirtschaftsplan mit Soll/Ist-Vergleich."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                            Paragraph, Spacer)
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
        except ImportError:
            messagebox.showerror("Fehler",
                "reportlab ist nicht installiert.\n"
                "Bitte 'pip install reportlab' ausführen.", parent=self)
            return

        try:
            jahr = int(self._wp_jahr.get())
        except ValueError:
            messagebox.showwarning("Jahr", "Bitte zuerst ein Jahr wählen.", parent=self); return

        conn = get_db()
        soll_rows = conn.execute(
            "SELECT kategorie, betrag_soll FROM wirtschaftsplan WHERE jahr=?",
            (jahr,)).fetchall()
        ist_rows = conn.execute(
            "SELECT kategorie, SUM(betrag) as s FROM zahlungen "
            "WHERE typ='Ausgabe' AND strftime('%Y', datum)=? GROUP BY kategorie",
            (str(jahr),)).fetchall()
        conn.close()

        if not soll_rows:
            messagebox.showinfo("Keine Daten",
                f"Für {jahr} sind noch keine Wirtschaftsplan-Positionen vorhanden.",
                parent=self)
            return

        ist_map  = {r["kategorie"]: (r["s"] or 0) for r in ist_rows}
        soll_map = {r["kategorie"]: (r["betrag_soll"] or 0) for r in soll_rows}
        alle_kat = sorted(set(list(soll_map.keys()) + list(ist_map.keys())))

        pfad = self._pdf_speichern(f"WEG_Wirtschaftsplan_SollIst_{jahr}.pdf")
        if not pfad:
            return

        try:
            doc = SimpleDocTemplate(pfad, pagesize=A4,
                                    leftMargin=2*cm, rightMargin=2*cm,
                                    topMargin=2*cm, bottomMargin=2*cm)
            styles = getSampleStyleSheet()
            H1 = ParagraphStyle("H1", parent=styles["Heading1"],
                                 fontSize=16, textColor=colors.HexColor("#1C2B3A"))
            H2 = ParagraphStyle("H2", parent=styles["Heading2"],
                                 fontSize=12, textColor=colors.HexColor("#1C2B3A"))
            SMALL = ParagraphStyle("small", parent=styles["Normal"], fontSize=8,
                                   textColor=colors.HexColor("#666666"))

            weg_name = self._get_weg_name()
            story = [
                Paragraph(weg_name, H1),
                Paragraph(f"Wirtschaftsplan – Soll/Ist-Vergleich {jahr}", H2),
                Paragraph(f"Erstellt am {date.today().strftime('%d.%m.%Y')}", SMALL),
                Spacer(1, 0.5*cm),
            ]

            wi_data = [["Kategorie", "Soll", "Ist", "Abweichung", "Status"]]
            total_soll = total_ist = 0
            for kat in alle_kat:
                soll   = soll_map.get(kat, 0)
                ist    = ist_map.get(kat, 0)
                abw    = soll - ist
                total_soll += soll
                total_ist  += ist
                if soll == 0:
                    status = "– kein Soll"
                elif abw >= 0:
                    status = "✔ OK"
                else:
                    status = "⚠ Überzogen"
                wi_data.append([kat, fmt_euro(soll), fmt_euro(ist), fmt_euro(abw), status])

            total_abw = total_soll - total_ist
            wi_data.append(["Gesamt", fmt_euro(total_soll), fmt_euro(total_ist),
                             fmt_euro(total_abw),
                             "✔ OK" if total_abw >= 0 else "⚠ Überzogen"])

            wi_t = Table(wi_data, colWidths=[5.5*cm, 3*cm, 3*cm, 3*cm, 2.5*cm])
            # Rote Zeilen für "Überzogen", grün für "OK"
            style_cmds = [
                ("BACKGROUND",  (0,0), (-1,0),  colors.HexColor("#1C2B3A")),
                ("TEXTCOLOR",   (0,0), (-1,0),  colors.white),
                ("FONTNAME",    (0,0), (-1,0),  "Helvetica-Bold"),
                ("FONTSIZE",    (0,0), (-1,-1), 9),
                ("ALIGN",       (1,1), (-1,-1), "RIGHT"),
                ("ROWBACKGROUNDS", (0,1), (-1,-2),
                 [colors.white, colors.HexColor("#F7F5F0")]),
                ("BACKGROUND",  (0,-1), (-1,-1), colors.HexColor("#EEEAE3")),
                ("FONTNAME",    (0,-1), (-1,-1), "Helvetica-Bold"),
                ("GRID",        (0,0), (-1,-1), 0.4, colors.HexColor("#CCCCCC")),
                ("TOPPADDING",  (0,0), (-1,-1), 4),
                ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ]
            for i, kat in enumerate(alle_kat, start=1):
                soll = soll_map.get(kat, 0)
                ist  = ist_map.get(kat, 0)
                if soll > 0 and ist > soll:
                    style_cmds.append(
                        ("TEXTCOLOR", (4, i), (4, i), colors.HexColor("#C0392B")))
                elif soll > 0:
                    style_cmds.append(
                        ("TEXTCOLOR", (4, i), (4, i), colors.HexColor("#3A7D44")))
            wi_t.setStyle(TableStyle(style_cmds))
            story.append(wi_t)

            doc.build(story)
            if messagebox.askyesno("PDF erstellt",
                f"PDF gespeichert:\n{pfad}\n\nJetzt öffnen?", parent=self):
                self._pdf_oeffnen(pfad)
        except Exception as exc:
            messagebox.showerror("PDF-Fehler", f"PDF konnte nicht erstellt werden:\n{exc}",
                                 parent=self)


class WirtschaftsplanDialog(BaseDialog):
    def __init__(self, parent, row=None, jahr=None):
        super().__init__(parent, "Wirtschaftsplan-Eintrag", 480, 380)
        r = dict(row) if row else {}
        _jahr = r.get("jahr", jahr or date.today().year)
        self._add_field("Jahr *", "jahr", str(_jahr))
        self._add_field("Kategorie *", "kategorie",
                        r.get("kategorie", "Heizung"),
                        widget_type="combo",
                        options=WEG_KATEGORIEN_LISTE)
        self._add_field("Soll-Betrag € *", "betrag_soll", r.get("betrag_soll", ""))
        self._add_field("Notizen", "notizen", r.get("notizen", ""))

    def _on_save(self):
        v = self._get_values()
        if not v.get("kategorie"):
            messagebox.showwarning("Pflichtfeld", "Kategorie ist erforderlich.", parent=self); return
        try:
            v["betrag_soll"] = float(str(v.get("betrag_soll", "0")).replace(",", ".") or 0)
        except ValueError:
            messagebox.showwarning("Betrag", "Bitte einen gültigen Betrag eingeben.", parent=self); return
        try:
            v["jahr"] = int(v.get("jahr", date.today().year))
        except ValueError:
            messagebox.showwarning("Jahr", "Bitte ein gültiges Jahr eingeben.", parent=self); return
        self.result = v; self.destroy()


class WirtschaftsplanVorschlagDialog(tk.Toplevel):  # #41
    """Dialog zum Erstellen von Wirtschaftsplan-Vorschlägen aus Vorjahres-Ist-Daten."""

    PREISANPASSBARE = ["Heizung", "Warmwasser", "Wasser/Abwasser", "Allgemeinstrom",
                       "Fernwärme", "Gaskosten", "Stromkosten", "Wasserkosten"]

    def __init__(self, parent, vorjahr: int, zieljahr: int, ist_daten: dict,
                 soll_daten: dict, bereits_vorhanden: set):
        super().__init__(parent)
        self.title(f"Wirtschaftsplan {zieljahr} – Vorschlag aus {vorjahr}")
        self.transient(parent)
        self.grab_set()
        self.resizable(True, True)
        self.configure(bg=BG_CARD)
        self.geometry("780x620")
        self.result = None

        self._vorjahr = vorjahr
        self._zieljahr = zieljahr
        self._ist_daten = ist_daten
        self._soll_daten = soll_daten
        self._bereits_vorhanden = bereits_vorhanden
        self._anpassung_vars = {}  # kategorie → prozent-StringVar
        self._uebernehmen_vars = {}  # kategorie → BooleanVar

        self._build()

    def _build(self):
        # Kopfzeile
        hdr = tk.Frame(self, bg=BG_CARD)
        hdr.pack(fill="x", padx=20, pady=(16, 8))
        tk.Label(hdr, text=f"📊 Wirtschaftsplan {self._zieljahr} – Vorschlag",
                 bg=BG_CARD, fg=TEXT, font=FONT_H2).pack(side="left")
        tk.Label(hdr, text=f"Basis: Ist-Ausgaben {self._vorjahr}",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(side="right", padx=(0,4))

        # Hinweis
        tk.Label(self, text="✏ Passen Sie die Prozentwerte an (positiv = Erhöhung, negativ = Senkung).\n"
                            "Deaktivieren Sie Positionen, die nicht übernommen werden sollen.",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL, justify="left"
                 ).pack(anchor="w", padx=20, pady=(0, 8))

        # Tabellen-Bereich
        frame_outer = tk.Frame(self, bg=BG_CARD, relief="sunken", bd=1)
        frame_outer.pack(fill="both", expand=True, padx=20, pady=(0, 8))
        canvas = tk.Canvas(frame_outer, bg=BG_CARD, highlightthickness=0)
        vsb = ttk.Scrollbar(frame_outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        inner = tk.Frame(canvas, bg=BG_CARD)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))

        # Spaltenköpfe
        hdr_f = tk.Frame(inner, bg=BG_INPUT)
        hdr_f.pack(fill="x")
        for txt, w in [("✓", 30), ("Kategorie", 200), (f"Ist {self._vorjahr} (€)", 120),
                       (f"Soll {self._vorjahr} (€)", 120), ("Anpassung %", 90), (f"Vorschlag {self._zieljahr} (€)", 130)]:
            tk.Label(hdr_f, text=txt, bg=BG_INPUT, fg=TEXT, font=FONT_SMALL,
                     width=max(len(txt), 8), anchor="w", padx=4).pack(side="left")

        # Alle Kategorien aus Ist + Soll
        alle_kats = sorted(set(list(self._ist_daten.keys()) + list(self._soll_daten.keys())))

        for kat in alle_kats:
            ist = self._ist_daten.get(kat, 0.0)
            soll = self._soll_daten.get(kat, 0.0)
            basis = ist if ist > 0 else soll  # Ist bevorzugen, Soll als Fallback

            row_f = tk.Frame(inner, bg=BG_CARD)
            row_f.pack(fill="x", pady=1)

            # Checkbox
            uebVar = tk.BooleanVar(value=kat not in self._bereits_vorhanden)
            self._uebernehmen_vars[kat] = uebVar
            tk.Checkbutton(row_f, variable=uebVar, bg=BG_CARD, activebackground=BG_CARD).pack(side="left", padx=4)

            # Kategorie
            farbe = SUCCESS if kat in self._bereits_vorhanden else TEXT
            tk.Label(row_f, text=kat, bg=BG_CARD, fg=farbe, font=FONT_BODY,
                     width=22, anchor="w").pack(side="left")

            # Ist
            tk.Label(row_f, text=fmt_euro(ist), bg=BG_CARD, fg=TEXT, font=FONT_SMALL,
                     width=14, anchor="e").pack(side="left")
            # Soll Vorjahr
            tk.Label(row_f, text=fmt_euro(soll), bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL,
                     width=14, anchor="e").pack(side="left")

            # Anpassung %
            prozVar = tk.StringVar(value="0")
            self._anpassung_vars[kat] = (prozVar, basis)
            e = tk.Entry(row_f, textvariable=prozVar, width=6, bg=BG_INPUT, fg=TEXT, font=FONT_BODY, relief="flat")
            e.pack(side="left", padx=4)

            # Vorschau-Label
            vorschau_lbl = tk.Label(row_f, text=fmt_euro(basis), bg=BG_CARD, fg=ACCENT2,
                                    font=FONT_SMALL, width=15, anchor="e")
            vorschau_lbl.pack(side="left", padx=4)

            # Live-Update der Vorschau
            def _update(_, v=prozVar, b=basis, lbl=vorschau_lbl):
                try:
                    pct = float(v.get().replace(",", "."))
                    neu = b * (1 + pct / 100)
                    lbl.config(text=fmt_euro(max(0, neu)))
                except Exception:
                    lbl.config(text="–")
            prozVar.trace_add("write", _update)

        # Hinweis für bereits vorhandene
        if self._bereits_vorhanden:
            tk.Label(self, text=f"🟢 Grün = bereits in {self._zieljahr} vorhanden (Checkbox deaktiviert)",
                     bg=BG_CARD, fg=SUCCESS, font=FONT_SMALL).pack(anchor="w", padx=20)

        # Globale Anpassung
        glob_f = tk.Frame(self, bg=BG_CARD)
        glob_f.pack(fill="x", padx=20, pady=(4, 12))
        tk.Label(glob_f, text="Alle um % anpassen:", bg=BG_CARD, fg=TEXT_LIGHT,
                 font=FONT_SMALL).pack(side="left", padx=(0, 8))
        self._glob_var = tk.StringVar(value="0")
        tk.Entry(glob_f, textvariable=self._glob_var, width=6, bg=BG_INPUT, fg=TEXT, font=FONT_BODY, relief="flat").pack(side="left")
        make_btn(glob_f, "Anwenden", self._glob_anwenden, color=ACCENT2).pack(side="left", padx=8)

        # Buttons
        btn_f = tk.Frame(self, bg=BG_CARD)
        btn_f.pack(fill="x", padx=20, pady=(0, 16))
        make_btn(btn_f, "✅ Übernehmen", self._on_save, color=SUCCESS).pack(side="right")
        make_btn(btn_f, "Abbrechen", self.destroy, color=BG_INPUT, fg=TEXT).pack(side="right", padx=(0, 8))

    def _glob_anwenden(self):
        """Wendet globale Preisanpassung auf alle aktivierten Kategorien an."""
        try:
            pct = float(self._glob_var.get().replace(",", "."))
        except Exception:
            messagebox.showwarning("Eingabe", "Ungültiger Prozentwert.", parent=self); return
        for kat, (var, _) in self._anpassung_vars.items():
            if self._uebernehmen_vars[kat].get():
                var.set(str(round(pct, 2)))

    def _on_save(self):
        result = {}
        for kat, (prozVar, basis) in self._anpassung_vars.items():
            if not self._uebernehmen_vars[kat].get():
                continue
            try:
                pct = float(prozVar.get().replace(",", "."))
                betrag = basis * (1 + pct / 100)
                betrag = max(0, round(betrag, 2))
            except Exception:
                betrag = basis
            result[kat] = betrag
        if not result:
            messagebox.showwarning("Keine Auswahl", "Bitte mindestens eine Kategorie auswählen.", parent=self); return
        self.result = result
        self.destroy()


class NebenkostenDialog(BaseDialog):
    """Legacy-Dialog für manuelle Nebenkosteneinträge (Rückwärtskompatibilität)."""
    def __init__(self, parent, row=None):
        super().__init__(parent, "Nebenkosteneintrag", 460, 420)
        r = dict(row) if row else {}
        two = tk.Frame(self._body, bg=BG_CARD)
        two.pack(fill="x", padx=20)
        two.columnconfigure((0, 1), weight=1)
        l  = tk.Frame(two, bg=BG_CARD); l.grid(row=0, column=0, padx=(0, 6), sticky="ew")
        ri = tk.Frame(two, bg=BG_CARD); ri.grid(row=0, column=1, padx=(6, 0), sticky="ew")
        self._add_field("Jahr", "jahr", r.get("jahr", date.today().year), row=l)
        self._add_field("Monat (1-12)", "monat", r.get("monat", ""), row=ri)
        self._add_field("Kategorie *", "kategorie", r.get("kategorie", "Heizung"),
                        widget_type="combo", options=WEG_KATEGORIEN_LISTE)
        self._add_field("Betrag €", "betrag", r.get("betrag", ""))
        self._add_field("Umlageschlüssel", "umlage", r.get("umlageschluessel", "Wohnfläche"),
                        widget_type="combo",
                        options=["Wohnfläche", "Personenanzahl", "Einheiten gleich", "Verbrauch"])
        self._add_field("Notizen", "notizen", r.get("notizen", ""))

    def _on_save(self):
        v = self._get_values()
        if not v.get("kategorie"):
            messagebox.showwarning("Pflichtfeld", "Kategorie ist erforderlich.", parent=self); return
        self.result = v; self.destroy()

# ── Kontoauszug-Seite ─────────────────────────────────────────────────────────



class AufteilungenPage(tk.Frame):  # #39
    def __init__(self, parent):
        super().__init__(parent, bg=BG_CARD)
        self._build()

    def _build(self):
        section_header(self, "Aufteilungen", "＋ Aufteilung", self._new)
        tk.Label(self, text="Umlageschlüssel und Verteilungsregeln für Nebenkosten",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w", padx=20, pady=(0,8))
        cols = ("Name", "Typ", "Wohnungen", "Aktiv", "Notizen")  # #39: Spalten geändert
        f, self.tree = make_table(self, cols, height=16)
        f.pack(fill="both", expand=True, padx=20, pady=8)
        for c, w in zip(cols, [180, 160, 200, 60, 200]):  # #39: Breiten angepasst
            self.tree.heading(c, text=c); self.tree.column(c, width=w, anchor="w")
        self.tree.bind("<Double-1>", self._edit)
        btn_row = tk.Frame(self, bg=BG_CARD)
        btn_row.pack(fill="x", padx=20, pady=(0,10))
        if hat_recht("Aufteilungen", "schreiben"):
            make_btn(btn_row, "✏ Bearbeiten", self._edit, color=BG_INPUT, fg=TEXT).pack(side="left", padx=(0,8))
            make_btn(btn_row, "⏸ De/Aktivieren", self._toggle_aktiv, color=BG_INPUT, fg=TEXT).pack(side="left", padx=(0,8))  # #39
        if hat_recht("Aufteilungen", "loeschen"):
            make_btn(btn_row, "🗑 Löschen", self._delete, color=DANGER).pack(side="left")
        self._load()

    def _load(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = get_db()
        for r in conn.execute("SELECT * FROM aufteilungen ORDER BY name"):
            # Zugeordnete Wohnungen ermitteln (#39)
            wohn_names = []
            try:
                for wh in conn.execute(
                    "SELECT w.bezeichnung FROM aufteilung_wohnungen aw "
                    "JOIN wohnungen w ON w.id=aw.wohnung_id WHERE aw.aufteilung_id=?", (r["id"],)):
                    wohn_names.append(wh["bezeichnung"])
            except Exception:
                pass
            aktiv_str = "✅" if r.get("aktiv", 1) else "❌"  # #39
            wohn_str = ", ".join(wohn_names) if wohn_names else (r.get("bezug") or "–")  # #39
            self.tree.insert("", "end", iid=r["id"], values=(
                r["name"], r["typ"] or "–", wohn_str, aktiv_str, r["notizen"] or "–"))
        conn.close()
        tree_empty_hint(self.tree)

    def _new(self):
        if not hat_recht("Aufteilungen", "schreiben"):
            messagebox.showwarning("Berechtigung", "Keine Schreibberechtigung.", parent=self); return
        d = AufteilungDialog(self)
        self.wait_window(d)
        if d.result:
            v = d.result
            conn = get_db()
            try:
                cur = conn.execute(
                    "INSERT INTO aufteilungen (name,beschreibung,typ,bezug,wert,notizen,ist_benutzerdefiniert) VALUES (?,?,?,?,?,?,1)",  # #39
                    (v["name"], v["beschreibung"], v["typ"], v["bezug"], v["wert"] or None, v["notizen"]))
                aid = cur.lastrowid
                for wid in v.get("wohnung_ids", []):  # #39
                    conn.execute("INSERT OR IGNORE INTO aufteilung_wohnungen (aufteilung_id, wohnung_id) VALUES (?,?)", (aid, wid))
                conn.commit()
            finally:
                conn.close()
            self._load()

    def _edit(self, event=None):
        if not hat_recht("Aufteilungen", "schreiben"):
            messagebox.showwarning("Berechtigung", "Keine Schreibberechtigung.", parent=self); return
        sel = self.tree.selection()
        if not sel: return
        conn = get_db()
        row = conn.execute("SELECT * FROM aufteilungen WHERE id=?", (int(sel[0]),)).fetchone()
        conn.close()
        d = AufteilungDialog(self, row)
        self.wait_window(d)
        if d.result:
            v = d.result
            conn = get_db()
            try:
                conn.execute(
                    "UPDATE aufteilungen SET name=?,beschreibung=?,typ=?,bezug=?,wert=?,notizen=? WHERE id=?",
                    (v["name"], v["beschreibung"], v["typ"], v["bezug"], v["wert"] or None, v["notizen"], int(sel[0])))
                conn.execute("DELETE FROM aufteilung_wohnungen WHERE aufteilung_id=?", (int(sel[0]),))  # #39
                for wid in v.get("wohnung_ids", []):  # #39
                    conn.execute("INSERT OR IGNORE INTO aufteilung_wohnungen (aufteilung_id, wohnung_id) VALUES (?,?)",
                                 (int(sel[0]), wid))
                conn.commit()
            finally:
                conn.close()
            self._load()

    def _toggle_aktiv(self):  # #39
        """Aktiviert/deaktiviert eine Aufteilung."""
        if not hat_recht("Aufteilungen", "schreiben"):
            messagebox.showwarning("Berechtigung", "Keine Schreibberechtigung.", parent=self); return
        sel = self.tree.selection()
        if not sel: return
        conn = get_db()
        try:
            r = conn.execute("SELECT aktiv FROM aufteilungen WHERE id=?", (int(sel[0]),)).fetchone()
            if not r: return
            neu = 0 if r["aktiv"] else 1
            conn.execute("UPDATE aufteilungen SET aktiv=? WHERE id=?", (neu, int(sel[0])))
            conn.commit()
        finally:
            conn.close()
        self._load()

    def _delete(self):
        if not hat_recht("Aufteilungen", "loeschen"):
            messagebox.showwarning("Berechtigung", "Keine Löschberechtigung.", parent=self); return
        sel = self.tree.selection()
        if not sel: return
        aid = int(sel[0])
        # Prüfen ob SuperAdmin (nur SuperAdmin darf löschen) #39
        conn = get_db()
        try:
            benutzer = conn.execute(
                "SELECT r.ist_superadmin FROM benutzer b JOIN rollen r ON r.id=b.rolle_id WHERE b.id=?",
                (_CURRENT_USER["id"],)).fetchone() if _CURRENT_USER else None
            ist_admin = benutzer and benutzer["ist_superadmin"]
            # Prüfen ob verwendet (in aufteilung_wohnungen) #39
            verwendet = conn.execute(
                "SELECT COUNT(*) FROM aufteilung_wohnungen WHERE aufteilung_id=?", (aid,)).fetchone()[0]
        finally:
            conn.close()
        if not ist_admin:  # #39
            messagebox.showwarning("Berechtigung",
                "Nur Super-Admins können Aufteilungstypen löschen.\n"
                "Nutzen Sie 'De/Aktivieren' um den Typ zu deaktivieren.", parent=self); return
        if verwendet:  # #39
            messagebox.showwarning("Verwendet",
                "Dieser Aufteilungstyp ist noch Wohnungen zugeordnet und kann nicht gelöscht werden.\n"
                "Bitte zuerst die Wohnungszuordnungen entfernen.", parent=self); return
        if messagebox.askyesno("Löschen", "Aufteilung löschen?"):
            conn = get_db()
            try:
                conn.execute("DELETE FROM aufteilungen WHERE id=?", (aid,))
                conn.commit()
            finally:
                conn.close()
            self._load()


class AufteilungDialog(BaseDialog):
    TYPEN = ["Wohnfläche", "Personenanzahl", "Einheiten gleich", "Verbrauch",
             "MEA", "Wasserkosten nach Punkten", "Ausgewählte Wohnungen", "Sonstiges"]  # #39

    def __init__(self, parent, row=None):
        super().__init__(parent, "Aufteilung " + ("bearbeiten" if row else "hinzufügen"), 520, 640)  # #39
        r = dict(row) if row else {}
        self._row_id = r.get("id")
        self._add_field("Name *", "name", r.get("name",""))
        # Widgetreferenzen direkt speichern – _fields enthält nur StringVar, nicht das Widget selbst
        self._typ_combo   = self._add_field("Typ", "typ", r.get("typ","Wohnfläche"),
                                            widget_type="combo", options=self.TYPEN)
        self._bezug_entry = self._add_field("Bezug / Einheit", "bezug", r.get("bezug",""))
        self._add_field("Wert", "wert", r.get("wert",""))
        self._add_field("Beschreibung", "beschreibung", r.get("beschreibung",""))
        self._add_field("Notizen", "notizen", r.get("notizen",""), widget_type="text")

        # Wohnungsauswahl (für Typ "Ausgewählte Wohnungen") #39
        self._wohn_frame = tk.LabelFrame(self._body, text="Wohnungen auswählen",
                                          bg=BG_CARD, fg=TEXT, font=FONT_SMALL)
        self._wohn_listbox = tk.Listbox(self._wohn_frame, selectmode="multiple",
                                         height=5, font=FONT_BODY, bg=BG_INPUT, fg=TEXT,
                                         selectbackground=ACCENT2, selectforeground="white")
        sb = ttk.Scrollbar(self._wohn_frame, orient="vertical", command=self._wohn_listbox.yview)
        self._wohn_listbox.configure(yscrollcommand=sb.set)
        self._wohn_listbox.pack(side="left", fill="both", expand=True, padx=(8,0), pady=6)
        sb.pack(side="right", fill="y", pady=6, padx=(0,8))
        # Wohnungen laden
        conn = get_db()
        self._wohn_ids = []
        for wh in conn.execute("SELECT id, bezeichnung FROM wohnungen ORDER BY bezeichnung"):
            self._wohn_ids.append(wh["id"])
            self._wohn_listbox.insert("end", wh["bezeichnung"])
        # Bereits zugeordnete Wohnungen vorauswählen
        if self._row_id:
            sel_ids = {r2["wohnung_id"] for r2 in
                       conn.execute("SELECT wohnung_id FROM aufteilung_wohnungen WHERE aufteilung_id=?",
                                    (self._row_id,)).fetchall()}
            for i, wid in enumerate(self._wohn_ids):
                if wid in sel_ids:
                    self._wohn_listbox.selection_set(i)
        conn.close()

        # Hinweis-Label: wird bei Typ "Wasserkosten nach Punkten" eingeblendet
        self._wk_hinweis = tk.Label(self._body, bg=BG_CARD, fg=ACCENT2, font=FONT_SMALL,
            text="\u2139  Bezug/Einheit wird automatisch aus der\n   Wasserkosten-Berechnung \u00fcbernommen.",
            justify="left", anchor="w")
        self._wk_hinweis.pack(fill="x", padx=20, pady=(0, 6))

        # Auf Combobox-Widget binden (nicht auf StringVar)
        self._typ_combo.bind("<<ComboboxSelected>>", self._on_typ_change)
        self._on_typ_change()  # Initialzustand setzen

    def _on_typ_change(self, event=None):
        """Zeigt/versteckt den Wasserkosten-Hinweis und Wohnungsauswahl je nach gewähltem Typ."""
        typ = self._fields["typ"].get()
        if typ == "Wasserkosten nach Punkten":
            self._wk_hinweis.pack(fill="x", padx=20, pady=(0, 6))
            self._wohn_frame.pack_forget()
            self._bezug_entry.configure(state="disabled")
            if not self._fields["bezug"].get():
                self._bezug_entry.configure(state="normal")
                self._bezug_entry.delete(0, "end")
                self._bezug_entry.insert(0, "Aus Wasserkosten-Berechnung")
                self._bezug_entry.configure(state="disabled")
        elif typ == "Ausgewählte Wohnungen":  # #39
            self._wk_hinweis.pack_forget()
            self._wohn_frame.pack(fill="x", padx=20, pady=(0, 8))
            self._bezug_entry.configure(state="normal")
        else:
            self._wk_hinweis.pack_forget()
            self._wohn_frame.pack_forget()
            self._bezug_entry.configure(state="normal")

    def _on_save(self):
        v = self._get_values()
        if not v.get("name"):
            messagebox.showwarning("Pflichtfeld", "Name ist erforderlich.", parent=self); return
        # Bezug automatisch setzen bei Wasserkosten-Typ
        if v.get("typ") == "Wasserkosten nach Punkten":
            v["bezug"] = "Wasserkosten nach Punkten"
        # Wohnungsauswahl speichern (#39)
        if v.get("typ") == "Ausgewählte Wohnungen":
            sel_indices = self._wohn_listbox.curselection()
            v["wohnung_ids"] = [self._wohn_ids[i] for i in sel_indices]
            if not v["wohnung_ids"]:
                messagebox.showwarning("Pflichtfeld", "Bitte mindestens eine Wohnung auswählen.", parent=self); return
        else:
            v["wohnung_ids"] = []
        self.result = v; self.destroy()

# ── Kontoauszug-Seite ──────────────────────────────────────────────────────

class KontoauszugPage(tk.Frame):
    """Kontoauszug-Seite: Import von CAMT.052 XML (Sparkasse) und CSV."""

    CAMT_NS = "urn:iso:std:iso:20022:tech:xsd:camt.052.001.08"

    def __init__(self, parent):
        super().__init__(parent, bg=BG_CARD)
        self._build()

    # ── UI aufbauen ───────────────────────────────────────────────────────────

    def _build(self):
        # Kopfzeile mit zwei Import-Schaltflächen
        row = tk.Frame(self, bg=BG_CARD)
        row.pack(fill="x", padx=20, pady=(18, 6))
        tk.Label(row, text="Kontoauszug", bg=BG_CARD, fg=TEXT,
                 font=FONT_H2).pack(side="left")
        make_btn(row, "📥 CAMT.052 XML", self._import_xml,
                 color=ACCENT2).pack(side="right")
        make_btn(row, "📄 CSV", self._import_csv_action,
                 color=BG_INPUT, fg=TEXT).pack(side="right", padx=(0, 8))
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=20)

        # Konto-Filter-Zeile
        filter_row = tk.Frame(self, bg=BG_CARD)
        filter_row.pack(fill="x", padx=20, pady=(6, 0))
        tk.Label(filter_row, text="Konto:", bg=BG_CARD, fg=TEXT_LIGHT,
                 font=FONT_SMALL).pack(side="left")
        self._konto_var = tk.StringVar(value="Alle")
        self._konto_combo = ttk.Combobox(filter_row, textvariable=self._konto_var,
                                          state="readonly", font=FONT_SMALL, width=40)
        self._konto_combo.pack(side="left", padx=(6, 0))
        self._konto_combo.bind("<<ComboboxSelected>>", lambda e: self._load())

        # Info-Zeile (wird nach Import aktualisiert)
        self._info_var = tk.StringVar(
            value="Kontoauszug importieren: CAMT.052 XML (Sparkasse Bodensee) oder CSV")
        tk.Label(self, textvariable=self._info_var,
                 bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(
                 anchor="w", padx=20, pady=(4, 0))

        # Status-Legende
        legende_frame = tk.Frame(self, bg=BG_CARD)
        legende_frame.pack(fill="x", padx=20, pady=(4, 0))
        for text, farbe in [
            ("● Importiert", TEXT_LIGHT),
            ("● Vorschlag", "#E67E22"),
            ("● Übernommen", SUCCESS),
            ("● Abgerechnet", ACCENT2),
        ]:
            tk.Label(legende_frame, text=text, bg=BG_CARD, fg=farbe, font=FONT_SMALL).pack(side="left", padx=6)

        # Saldo-Kacheln (pro Konto)
        self._saldo_frame = tk.Frame(self, bg=BG_CARD)
        self._saldo_frame.pack(fill="x", padx=20, pady=(4, 0))

        # Buchungstabelle
        cols = ("Datum", "Auftraggeber / Empfänger", "Verwendungszweck", "Betrag", "✔")
        f, self.tree = make_table(self, cols, height=14)
        f.pack(fill="both", expand=True, padx=20, pady=6)
        for col, w in zip(cols, [90, 200, 310, 110, 36]):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w,
                             anchor="e" if col == "Betrag" else "w")
        # Farb-Tags: Grün = Gutschrift, Rot = Lastschrift, Fett = Neu
        self.tree.tag_configure("crdt", foreground=SUCCESS)
        self.tree.tag_configure("dbit", foreground=DANGER)
        self.tree.tag_configure("neu", font=("Segoe UI Semibold", 10))
        # Status-Tags (Buchungs-Pipeline)
        self.tree.tag_configure("status_importiert", foreground=TEXT_LIGHT)
        self.tree.tag_configure("status_vorschlag",  foreground="#E67E22")  # Orange
        self.tree.tag_configure("status_uebernommen", foreground=SUCCESS)
        self.tree.tag_configure("status_abgerechnet", foreground=ACCENT2)
        # Klick auf Zeile: "Neu"-Markierung entfernen
        self.tree.bind("<<TreeviewSelect>>", self._on_row_click)

        # Aktions-Buttons (unten)
        btn_row = tk.Frame(self, bg=BG_CARD)
        btn_row.pack(fill="x", padx=20, pady=(0, 10))
        make_btn(btn_row, "🗑 Alle löschen", self._clear,
                 color=DANGER).pack(side="left")

        self._load()

    # ── Tabelle befüllen ─────────────────────────────────────────────────────

    def _load(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        conn = get_db()
        # Konto-Filter aktualisieren
        konten_raw = conn.execute(
            "SELECT DISTINCT iban FROM kontoauszug WHERE iban IS NOT NULL AND iban != '' ORDER BY iban"
        ).fetchall()
        cfg = load_config()
        konto_labels = ["Alle"]
        self._iban_map = {"Alle": None}
        for kr in konten_raw:
            iban = kr["iban"]
            label = self._konto_bezeichnung(iban, cfg)
            konto_labels.append(label)
            self._iban_map[label] = iban
        self._konto_combo["values"] = konto_labels
        if self._konto_var.get() not in konto_labels:
            self._konto_var.set("Alle")

        # Gefilterte Abfrage
        selected_iban = self._iban_map.get(self._konto_var.get())
        if selected_iban:
            rows = conn.execute(
                "SELECT * FROM kontoauszug WHERE iban=? ORDER BY datum DESC, id DESC",
                (selected_iban,)).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM kontoauszug ORDER BY datum DESC, id DESC").fetchall()
        conn.close()
        for r in rows:
            rd = dict(r)
            betrag = rd["betrag"] or 0.0
            tags_list = ["crdt" if betrag >= 0 else "dbit"]
            # Neue Buchungen fett markieren
            if rd.get("ist_neu"):
                tags_list.append("neu")
            # Status-Tag hinzufügen
            status_val = rd.get("buchung_status") or "importiert"
            tags_list.append(f"status_{status_val}")
            raw = rd["buchungstext"] or ""
            if "||" in raw:
                gegenkonto, vzweck = raw.split("||", 1)
            else:
                gegenkonto, vzweck = "", raw
            self.tree.insert("", "end", iid=rd["id"], values=(
                fmt_date(rd["datum"]),
                gegenkonto or "–",
                vzweck or "–",
                fmt_euro(betrag),
                "✔" if rd["zugeordnet"] else ""),
                tags=tuple(tags_list))
        tree_empty_hint(self.tree)
        self._refresh_saldo_kacheln()

    def _konto_bezeichnung(self, iban, cfg=None):
        """Gibt die Konto-Bezeichnung für eine IBAN zurück (aus Einstellungen oder Standard)."""
        if not cfg:
            cfg = load_config()
        iban_clean = (iban or "").replace(" ", "")
        # Prüfe alle konfigurierten IBANs (nur Wohngeld + Rücklage)
        for key, bez_key in [("iban_wohngeld", "bez_wohngeld"),
                              ("iban_ruecklage", "bez_ruecklage")]:
            cfg_iban = cfg.get(key, "").replace(" ", "")
            if cfg_iban and cfg_iban == iban_clean:
                bez = cfg.get(bez_key, "")
                if bez:
                    return f"{bez} (···{iban_clean[-4:]})"
                # Fallback: Key-basiert
                namen = {"iban_wohngeld": "Wohngeldkonto", "iban_ruecklage": "Rücklagenkonto"}
                return f"{namen.get(key, 'Konto')} (···{iban_clean[-4:]})"
        return f"Konto ···{iban_clean[-4:]}" if iban_clean else "Unbekannt"

    def _on_row_click(self, event=None):
        """Markierung 'Neu' entfernen, sobald eine Zeile angeklickt wird."""
        sel = self.tree.selection()
        if not sel:
            return
        row_id = int(sel[0])
        # Prüfe ob die Zeile „neu" ist
        tags = self.tree.item(sel[0], "tags")
        if "neu" in tags:
            # Fett-Tag entfernen
            new_tags = tuple(t for t in tags if t != "neu")
            self.tree.item(sel[0], tags=new_tags)
            # In DB markieren
            conn = get_db()
            conn.execute("UPDATE kontoauszug SET ist_neu=0 WHERE id=?", (row_id,))
            conn.commit()
            conn.close()
            self._refresh_saldo_kacheln()

    def _refresh_saldo_kacheln(self):
        """Zeigt pro importiertem Konto eine Kachel mit Bezeichnung, IBAN, Kontostand, Buchungen, neue."""
        for w in self._saldo_frame.winfo_children():
            w.destroy()
        conn = get_db()
        konten = conn.execute(
            "SELECT iban, COUNT(*) AS n, SUM(betrag) AS s, "
            "SUM(CASE WHEN ist_neu=1 THEN 1 ELSE 0 END) AS neu "
            "FROM kontoauszug "
            "WHERE iban IS NOT NULL AND iban != '' "
            "GROUP BY iban"
        ).fetchall()
        gesamt = conn.execute(
            "SELECT COUNT(*) AS n FROM kontoauszug").fetchone()["n"]
        conn.close()
        if gesamt == 0:
            return
        cfg = load_config()
        for k in konten:
            kd = dict(k)
            iban = kd["iban"] or ""
            bezeichnung = self._konto_bezeichnung(iban, cfg)
            iban_fmt = " ".join([iban[i:i+4] for i in range(0, len(iban), 4)]) if iban else "–"
            saldo_wert = kd["s"] or 0.0
            farbe = SUCCESS if saldo_wert >= 0 else DANGER
            n_gesamt = kd["n"] or 0
            n_neu = kd.get("neu") or 0

            card = tk.Frame(self._saldo_frame, bg=BG_INPUT, relief="flat", cursor="hand2")
            card.pack(side="left", padx=(0, 10), pady=4, ipadx=14, ipady=8)
            # Klick auf Kachel → Filter auf dieses Konto
            card.bind("<Button-1>", lambda e, lbl=bezeichnung: self._filter_konto(lbl))
            for child_widget in [card]:
                child_widget.bind("<Button-1>", lambda e, lbl=bezeichnung: self._filter_konto(lbl))

            tk.Label(card, text=bezeichnung,
                     bg=BG_INPUT, fg=TEXT, font=("Segoe UI Semibold", 10)).pack(anchor="w")
            tk.Label(card, text=iban_fmt,
                     bg=BG_INPUT, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w")
            tk.Label(card, text=fmt_euro(saldo_wert),
                     bg=BG_INPUT, fg=farbe, font=FONT_H3).pack(anchor="w")
            info_text = f"{n_gesamt} Buchungen"
            if n_neu:
                info_text += f"  ·  {n_neu} neu"
            tk.Label(card, text=info_text,
                     bg=BG_INPUT, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w")
            # Alle Labels auch klickbar machen
            for child in card.winfo_children():
                child.bind("<Button-1>", lambda e, lbl=bezeichnung: self._filter_konto(lbl))

    def _filter_konto(self, label):
        """Setzt den Konto-Filter auf das geklickte Konto."""
        self._konto_var.set(label)
        self._load()

    # ── CAMT.052 XML Import ───────────────────────────────────────────────────

    def _get_default_import_dir(self):
        """Gibt den Standard-Importpfad zurück, legt ihn ggf. an (#38)."""
        return get_pfad("pfad_kontoauszug_import", "Kontoauszüge")

    def _import_xml(self):
        """CAMT.052 XML-Dateien oder -Ordner (Sparkasse Bodensee / ISO 20022) importieren."""
        default_dir = self._get_default_import_dir()
        # Dialog: Mehrere Dateien ODER einen Ordner wählen
        choice = messagebox.askyesnocancel(
            "CAMT.052 Import",
            "Mehrere Dateien auswählen?\n\n"
            "Ja = Dateien auswählen\n"
            "Nein = Ordner auswählen (alle XML-Dateien darin)\n"
            "Abbrechen = Import abbrechen")
        if choice is None:
            return
        if choice:  # Ja → Dateien wählen
            kw = {}
            if default_dir:
                kw["initialdir"] = default_dir
            paths = filedialog.askopenfilenames(
                filetypes=[("CAMT.052 XML", "*.xml"), ("Alle Dateien", "*.*")],
                title="CAMT.052 Kontoauszüge (XML) importieren", **kw)
            if not paths:
                return
        else:  # Nein → Ordner wählen
            kw = {}
            if default_dir:
                kw["initialdir"] = default_dir
            folder = filedialog.askdirectory(title="Ordner mit CAMT.052 XML-Dateien wählen", **kw)
            if not folder:
                return
            paths = sorted(glob.glob(os.path.join(folder, "*.xml")))
            if not paths:
                messagebox.showwarning("Keine Dateien", "Keine XML-Dateien im gewählten Ordner gefunden.")
                return

        gesamt_buchungen = 0
        gesamt_auto = 0
        gesamt_duplikate = 0
        fehler_dateien = []
        letzte_bank = ""
        letzte_iban = ""
        letzte_saldo = None

        # EINE gemeinsame DB-Verbindung für den gesamten Import (verhindert "database is locked")
        conn = get_db()
        cfg = load_config()
        iban_ruecklage = cfg.get("iban_ruecklage", "DE14690500011007212085").replace(" ", "")
        iban_wohngeld  = cfg.get("iban_wohngeld",  "DE11690500010000081703").replace(" ", "")

        total_files = len(paths)
        for idx, path in enumerate(paths):
            # Fortschrittsanzeige aktualisieren
            self._info_var.set(f"Importiere Datei {idx + 1} von {total_files}...")
            self.update_idletasks()
            try:
                buchungen, iban, bank, saldo, saldo_datum = self._parse_camt(path)
                # Konto-Typ bestimmen anhand IBAN
                iban_clean = iban.replace(" ", "")
                if iban_clean == iban_ruecklage:
                    konto_typ = "Rücklagenkonto"
                elif iban_clean == iban_wohngeld:
                    konto_typ = "Wohngeldkonto"
                else:
                    konto_typ = "Unbekannt"

                auto_count = 0
                dup_count = 0
                imp_count = 0
                datei_lern_queue = []  # (buchungstext, kat, typ, kt)
                for datum, buchungstext, betrag in buchungen:
                    # Dublettenprüfung: gleiche Buchung bereits vorhanden?
                    existing = conn.execute(
                        "SELECT COUNT(*) FROM kontoauszug WHERE datum=? AND buchungstext=? AND betrag=? AND iban=?",
                        (datum, buchungstext, betrag, iban)).fetchone()[0]
                    if existing:
                        dup_count += 1
                        continue

                    # Kategorie-Vorschlag ermitteln
                    kat, typ, kt, _ = vorschlag_kategorie(buchungstext)  # Konfidenz ignoriert
                    if not kt or kt in ("Girokonto", "Wohngeldkonto"):
                        kt = konto_typ
                    conn.execute(
                        "INSERT INTO kontoauszug (datum, buchungstext, betrag, iban, konto_typ, kategorie_vorschlag) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (datum, buchungstext, betrag, iban, konto_typ, kat or None))
                    ka_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                    imp_count += 1
                    # Auto-Transfer: wenn Kategorie erkannt, direkt als Buchung übernehmen
                    if kat:
                        if betrag < 0:
                            typ = "Ausgabe"
                        else:
                            typ = "Einnahme"
                        # Verwendungszweck als Beschreibung
                        if "||" in buchungstext:
                            gegenkonto, vzweck = buchungstext.split("||", 1)
                            beschr = f"{gegenkonto} – {vzweck}" if gegenkonto else vzweck
                        else:
                            beschr = buchungstext
                        # Sicherheits-Dublettencheck für zahlungen (verhindert Duplikate bei Re-Import)
                        z_exists = conn.execute(
                            "SELECT id FROM zahlungen WHERE datum=? AND betrag=? AND kategorie=? AND konto_typ=?",
                            (datum, betrag, kat, kt)).fetchone()
                        if z_exists:
                            # Zahlung existiert bereits – nur kontoauszug verknüpfen
                            conn.execute(
                                "UPDATE kontoauszug SET als_buchung_uebernommen=1, zugeordnet=1, zahlung_id=? WHERE id=?",
                                (z_exists[0], ka_id))
                        else:
                            conn.execute(
                                "INSERT INTO zahlungen (datum,betrag,typ,kategorie,beschreibung,konto_typ,status) "
                                "VALUES (?,?,?,?,?,?,?)",
                                (datum, betrag, typ, kat, beschr[:200], kt, "Neu"))
                            zahlung_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                            conn.execute(
                                "UPDATE kontoauszug SET als_buchung_uebernommen=1, zugeordnet=1, zahlung_id=? WHERE id=?",
                                (zahlung_id, ka_id))
                            datei_lern_queue.append((buchungstext, kat, typ, kt))
                            auto_count += 1
                conn.commit()
                # lerne_buchung nach commit – verhindert "database is locked"
                for _bt, _kat, _typ, _kt in datei_lern_queue:
                    lerne_buchung(_bt, _kat, _typ, _kt)
                gesamt_buchungen += imp_count
                gesamt_auto += auto_count
                gesamt_duplikate += dup_count
                letzte_bank = bank
                letzte_iban = iban
                letzte_saldo = saldo
            except Exception as exc:
                fehler_dateien.append(f"{os.path.basename(path)}: {exc}")
        conn.close()

        # Ergebnis-Meldung (breites scrollbares Fenster statt messagebox)
        saldo_str = fmt_euro(letzte_saldo) if letzte_saldo is not None else "–"
        msg = f"{gesamt_buchungen} Buchung(en) aus {len(paths)} Datei(en) importiert"
        if gesamt_duplikate:
            msg += f"\n{gesamt_duplikate} Duplikat(e) übersprungen"
        if gesamt_auto:
            msg += f"\nDavon automatisch gebucht: {gesamt_auto}"
        if fehler_dateien:
            msg += f"\n\n⚠ Fehler in {len(fehler_dateien)} Datei(en):\n" + "\n".join(fehler_dateien)
        self._zeige_import_ergebnis("CAMT.052 Import", msg)
        if letzte_iban:
            self._info_var.set(
                f"Zuletzt importiert: {letzte_bank} · ···{letzte_iban[-8:]} · Saldo {saldo_str}")
        self._load()

    def _zeige_import_ergebnis(self, titel, text):
        """Zeigt das Import-Ergebnis in einem breiten, scrollbaren Fenster."""
        import tkinter.scrolledtext as scrolledtext
        win = tk.Toplevel(self)
        win.title(titel)
        win.geometry("700x350")
        win.configure(bg=BG_CARD)
        win.transient(self)
        win.grab_set()
        st = scrolledtext.ScrolledText(win, wrap="word", font=FONT_BODY,
                                       bg=BG_INPUT, fg=TEXT, relief="flat",
                                       padx=12, pady=10)
        st.pack(fill="both", expand=True, padx=16, pady=(16, 8))
        st.insert("end", text)
        st.config(state="disabled")
        make_btn(win, "OK", win.destroy, color=ACCENT2).pack(pady=(0, 14))
        win.wait_window()

    def _parse_camt(self, path):
        """Parst eine CAMT.052.001.08 XML-Datei der Sparkasse Bodensee.

        Rückgabe: (buchungen_list, iban, bank_name, schlusssaldo, saldo_datum)
            buchungen_list = [(datum_iso, buchungstext, betrag), ...]
        """
        NS = {"ns": self.CAMT_NS}
        root = ET.parse(path).getroot()

        rpt = root.find("ns:BkToCstmrAcctRpt/ns:Rpt", NS)
        if rpt is None:
            raise ValueError(
                "Kein <Rpt>-Element gefunden.\n"
                "Bitte sicherstellen, dass es sich um eine CAMT.052-Datei handelt.")

        # Kontoinformationen
        iban = rpt.findtext("ns:Acct/ns:Id/ns:IBAN", "", NS)
        bank = rpt.findtext(
            "ns:Acct/ns:Svcr/ns:FinInstnId/ns:Nm", "Unbekannte Bank", NS)

        # Schlusssaldo (CLBD = Closing Booked)
        saldo_schluss = None
        saldo_datum   = None
        for bal in rpt.findall("ns:Bal", NS):
            cd = bal.findtext("ns:Tp/ns:CdOrPrtry/ns:Cd", "", NS)
            if cd == "CLBD":
                amt = float(bal.findtext("ns:Amt", "0", NS))
                cdi = bal.findtext("ns:CdtDbtInd", "CRDT", NS)
                saldo_schluss = amt if cdi == "CRDT" else -amt
                saldo_datum   = bal.findtext("ns:Dt/ns:Dt", "", NS)

        # Buchungen (Ntry-Elemente)
        buchungen = []
        for ntry in rpt.findall("ns:Ntry", NS):
            amt  = float(ntry.findtext("ns:Amt", "0", NS))
            cdi  = ntry.findtext("ns:CdtDbtInd", "CRDT", NS)
            datum = ntry.findtext("ns:BookgDt/ns:Dt", "", NS)
            betrag = amt if cdi == "CRDT" else -amt

            # Transaktionsdetails (Name der Gegenseite + Verwendungszweck)
            tx = ntry.find("ns:NtryDtls/ns:TxDtls", NS)
            gegenkonto     = ""
            verwendungszweck = ""
            if tx is not None:
                # Gutschrift → Auftraggeber ist Debtor; Lastschrift → Empfänger ist Creditor
                if cdi == "CRDT":
                    gegenkonto = tx.findtext(
                        "ns:RltdPties/ns:Dbtr/ns:Pty/ns:Nm", "", NS)
                else:
                    gegenkonto = tx.findtext(
                        "ns:RltdPties/ns:Cdtr/ns:Pty/ns:Nm", "", NS)
                verwendungszweck = tx.findtext("ns:RmtInf/ns:Ustrd", "", NS)

            # Buchungsart (z. B. "GUTSCHRIFT ÜBERWEISUNG DAUERAUFTRAG")
            buchungsart = ntry.findtext("ns:AddtlNtryInf", "", NS)

            # Verwendungszweck mit Buchungsart zusammenführen
            vzweck_voll = " · ".join(filter(None, [verwendungszweck, buchungsart]))

            # Speicherformat: "Gegenkonto||Verwendungszweck"
            buchungstext = f"{gegenkonto}||{vzweck_voll}"
            buchungen.append((datum, buchungstext, betrag))

        return buchungen, iban, bank, saldo_schluss, saldo_datum

    # ── CSV Import (Rückwärtskompatibilität) ─────────────────────────────────

    def _import_csv_action(self):
        """Sparkassen-CSV oder generisches Semikolon-CSV importieren (Mehrfachauswahl)."""
        default_dir = self._get_default_import_dir()
        # Dialog: Mehrere Dateien ODER einen Ordner wählen
        choice = messagebox.askyesnocancel(
            "CSV Import",
            "Mehrere Dateien auswählen?\n\n"
            "Ja = Dateien auswählen\n"
            "Nein = Ordner auswählen (alle CSV-Dateien darin)\n"
            "Abbrechen = Import abbrechen")
        if choice is None:
            return
        if choice:  # Ja → Dateien wählen
            kw = {}
            if default_dir:
                kw["initialdir"] = default_dir
            paths = filedialog.askopenfilenames(
                filetypes=[("CSV-Dateien", "*.csv"), ("Alle Dateien", "*.*")],
                title="Kontoauszug CSV-Dateien importieren", **kw)
            if not paths:
                return
        else:  # Nein → Ordner wählen
            kw = {}
            if default_dir:
                kw["initialdir"] = default_dir
            folder = filedialog.askdirectory(title="Ordner mit CSV-Dateien wählen", **kw)
            if not folder:
                return
            paths = sorted(glob.glob(os.path.join(folder, "*.csv")))
            if not paths:
                messagebox.showwarning("Keine Dateien", "Keine CSV-Dateien im gewählten Ordner gefunden.")
                return

        gesamt_imported = 0
        gesamt_duplikate = 0
        fehler_dateien = []

        for path in paths:
            try:
                conn = get_db()
                imported = 0
                dup_count = 0
                with open(path, newline="", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f, delimiter=";")
                    for row in reader:
                        datum = row.get("Datum", "").strip()
                        text  = row.get(
                            "Buchungstext", row.get("Verwendungszweck", "")).strip()
                        bstr  = (row.get("Betrag", "0")
                                 .replace(".", "").replace(",", ".").strip())
                        sstr  = (row.get("Saldo", "")
                                 .replace(".", "").replace(",", ".").strip())
                        try:
                            betrag = float(bstr)
                        except ValueError:
                            continue
                        saldo = None
                        try:
                            saldo = float(sstr)
                        except ValueError:
                            pass
                        try:
                            datum = datetime.strptime(
                                datum, "%d.%m.%Y").strftime("%Y-%m-%d")
                        except ValueError:
                            pass
                        # Dublettenprüfung
                        existing = conn.execute(
                            "SELECT COUNT(*) FROM kontoauszug WHERE datum=? AND buchungstext=? AND betrag=?",
                            (datum, text, betrag)).fetchone()[0]
                        if existing:
                            dup_count += 1
                            continue
                        conn.execute(
                            "INSERT INTO kontoauszug "
                            "(datum, buchungstext, betrag, saldo) VALUES (?,?,?,?)",
                            (datum, text, betrag, saldo))
                        imported += 1
                conn.commit()
                conn.close()
                gesamt_imported += imported
                gesamt_duplikate += dup_count
            except Exception as exc:
                fehler_dateien.append(f"{os.path.basename(path)}: {exc}")

        msg = f"{gesamt_imported} Buchung(en) aus {len(paths)} Datei(en) importiert."
        if gesamt_duplikate:
            msg += f"\n{gesamt_duplikate} Duplikat(e) übersprungen."
        if fehler_dateien:
            msg += f"\n\n⚠ Fehler in {len(fehler_dateien)} Datei(en):\n" + "\n".join(fehler_dateien[:5])
        messagebox.showinfo("CSV Import", msg)
        self._load()

    # ── Löschen ───────────────────────────────────────────────────────────────

    def _clear(self):
        if messagebox.askyesno("Alle löschen",
                               "Alle importierten Kontoauszugsbuchungen löschen?"):
            conn = get_db()
            conn.execute("DELETE FROM kontoauszug")
            conn.commit()
            conn.close()
            self._info_var.set(
                "Kontoauszug importieren: CAMT.052 XML (Sparkasse Bodensee) oder CSV")
            self._load()


# ══════════════════════════════════════════════════════════════════════════════
# HAUPT-FENSTER
# ══════════════════════════════════════════════════════════════════════════════



class WasserkostenPage(tk.Frame):
    """Wasserkosten-Aufteilung nach Punkteschlüssel.

    Tab 1 – Jahreskosten  : Stadtwerke-Rechnung (Frischwasser, Abwasser,
                            Niederschlagswasser, Gutschrift)
    Tab 2 – Punktetabelle : Personen/Spülmaschine/Waschmaschine/Trockner je Wohnung
    Tab 3 – Auswertung    : Kosten je Punkt, WE-Aufteilung, Eigentümer-Summen,
                            Plausibilitätscheck, Vorjahresvergleich
    """

    TYPEN = ["Frischwasser", "Abwasser", "Niederschlagswasser"]

    def __init__(self, parent):
        super().__init__(parent, bg=BG_CARD)
        self._jahr_var = tk.StringVar(value=str(date.today().year))
        self._kosten_vars = {}
        self._gutschrift_var = {}
        self._gesamt_label = None
        self._ausw_inner = None
        self._ausw_result = None
        self._build()

    # ── Aufbau ────────────────────────────────────────────────────────────────

    def _build(self):
        # Kopfzeile
        top = tk.Frame(self, bg=BG_CARD)
        top.pack(fill="x", padx=20, pady=(16, 0))
        tk.Label(top, text="Wasserkosten-Aufteilung", bg=BG_CARD,
                 fg=TEXT, font=FONT_H2).pack(side="left")
        tk.Label(top, text="  Abrechnungsjahr:", bg=BG_CARD,
                 fg=TEXT_LIGHT, font=FONT_BODY).pack(side="left", padx=(20, 4))
        jahre = [str(y) for y in range(date.today().year + 1, date.today().year - 6, -1)]
        cb = ttk.Combobox(top, textvariable=self._jahr_var, values=jahre,
                          state="readonly", width=6, font=FONT_BODY)
        cb.pack(side="left")
        cb.bind("<<ComboboxSelected>>", lambda e: self._refresh())
        make_btn(top, "Aktualisieren", self._refresh,
                 color=BG_INPUT, fg=TEXT).pack(side="left", padx=8)

        # Tab-Leiste
        self._tab_btns = {}
        tab_bar = tk.Frame(self, bg=BG_CARD)
        tab_bar.pack(fill="x", padx=20, pady=(10, 0))
        for tid, label in [("kosten",     "Jahreskosten"),
                            ("punkte",    "Punktetabelle"),
                            ("auswertung","Auswertung")]:
            btn = tk.Button(tab_bar, text=label, font=FONT_NAV, relief="flat", bd=0,
                            padx=14, pady=7, cursor="hand2",
                            command=lambda t=tid: self._switch_tab(t))
            btn.pack(side="left", padx=2)
            self._tab_btns[tid] = btn
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(4, 0))

        self._content = tk.Frame(self, bg=BG_CARD)
        self._content.pack(fill="both", expand=True)

        self._build_kosten_tab()
        self._build_punkte_tab()
        self._build_auswertung_tab()
        self._switch_tab("kosten")

    # ── Tab 1: Jahreskosten ───────────────────────────────────────────────────

    def _build_kosten_tab(self):
        self._view_kosten = tk.Frame(self._content, bg=BG_CARD)
        canvas = tk.Canvas(self._view_kosten, bg=BG_CARD, highlightthickness=0)
        sb = ttk.Scrollbar(self._view_kosten, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        inner = tk.Frame(canvas, bg=BG_CARD)
        wid = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(wid, width=e.width))

        body = inner
        tk.Label(body, text="1.  Wasserkosten laut Stadtwerke-Jahresabrechnung",
                 bg=BG_CARD, fg=TEXT, font=FONT_H3).pack(anchor="w", padx=20, pady=(16, 4))
        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", padx=20)

        # Tabellenkopf
        hdr = tk.Frame(body, bg=BG_INPUT)
        hdr.pack(fill="x", padx=20, pady=(6, 0))
        for txt, w in [("Position", 26), ("Verbrauch (m3)", 16),
                       ("Kosten (EUR)", 16), ("Ablesedatum", 16)]:
            tk.Label(hdr, text=txt, bg=BG_INPUT, fg=TEXT_LIGHT,
                     font=FONT_SMALL, width=w, anchor="w").pack(side="left", padx=6, pady=4)

        # Eingabezeilen
        for typ in self.TYPEN:
            self._kosten_vars[typ] = self._kosten_row(body, typ)
        self._gutschrift_var = self._kosten_row(body, "Gutschrift / Erstattung",
                                                 is_gutschrift=True)

        # Gesamt
        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(8, 0))
        gr = tk.Frame(body, bg=BG_CARD)
        gr.pack(fill="x", padx=20, pady=4)
        tk.Label(gr, text="Wasserkosten gesamt (netto):",
                 bg=BG_CARD, fg=TEXT, font=FONT_H3, width=28, anchor="w").pack(side="left")
        self._gesamt_label = tk.Label(gr, text="–", bg=BG_CARD, fg=ACCENT2, font=FONT_H3)
        self._gesamt_label.pack(side="left", padx=8)

        btn_row = tk.Frame(body, bg=BG_CARD)
        btn_row.pack(fill="x", padx=20, pady=12)
        make_btn(btn_row, "Speichern", self._save_kosten, color=SUCCESS).pack(side="left")
        make_btn(btn_row, "Gesamt berechnen", self._update_gesamt,
                 color=BG_INPUT, fg=TEXT).pack(side="left", padx=8)

    def _kosten_row(self, parent, typ, is_gutschrift=False):
        """Eingabezeile für einen Kostentyp."""
        row = tk.Frame(parent, bg=BG_CARD)
        row.pack(fill="x", padx=20, pady=2)
        fg = WARNING if is_gutschrift else TEXT
        tk.Label(row, text=typ, bg=BG_CARD, fg=fg, font=FONT_BODY,
                 width=26, anchor="w").pack(side="left")
        d = {}
        for key in (["kosten", "datum"] if is_gutschrift else ["verbrauch", "kosten", "datum"]):
            v = tk.StringVar()
            e = make_entry(row, textvariable=v, width=14)
            e.pack(side="left", padx=4, ipady=4)
            if key == "datum":
                e.insert(0, "JJJJ-MM-TT")
                e.bind("<FocusIn>",  lambda ev, en=e: (en.get() == "JJJJ-MM-TT" and en.delete(0, "end")))
                e.bind("<FocusOut>", lambda ev, en=e, vv=v: (not en.get() and en.insert(0, "JJJJ-MM-TT")))
            d[key] = v
        if is_gutschrift:
            tk.Label(row, text="(negativer Betrag oder 0)", bg=BG_CARD,
                     fg=TEXT_LIGHT, font=FONT_SMALL).pack(side="left", padx=4)
        return d

    def _load_kosten(self):
        """Lädt gespeicherte Kostenwerte."""
        jahr = self._jahr_int()
        if not jahr:
            return
        conn = get_db()
        rows = conn.execute(
            "SELECT typ, verbrauch_m3, kosten_eur, ablesedatum "
            "FROM wasserkosten_positionen WHERE jahr=?", (jahr,)).fetchall()
        conn.close()
        by_typ = {r["typ"]: dict(r) for r in rows}
        for typ, vd in self._kosten_vars.items():
            d = by_typ.get(typ, {})
            if "verbrauch" in vd:
                vd["verbrauch"].set(str(d.get("verbrauch_m3", "") or ""))
            vd["kosten"].set(str(d.get("kosten_eur", "") or ""))
            dat = str(d.get("ablesedatum", "") or "")
            vd["datum"].set(dat if dat else "")
        d = by_typ.get("Gutschrift / Erstattung", {})
        self._gutschrift_var["kosten"].set(str(d.get("kosten_eur", "") or ""))
        self._update_gesamt()

    def _save_kosten(self):
        """Speichert Jahreskosten-Eingaben."""
        jahr = self._jahr_int()
        if not jahr:
            messagebox.showwarning("Fehler", "Kein gültiges Jahr.", parent=self)
            return
        conn = get_db()
        conn.execute("DELETE FROM wasserkosten_positionen WHERE jahr=?", (jahr,))
        for typ, vd in self._kosten_vars.items():
            v_m3  = self._flt(vd.get("verbrauch", tk.StringVar()).get())
            v_eur = self._flt(vd["kosten"].get())
            v_dat = vd["datum"].get().strip()
            v_dat = v_dat if (v_dat and v_dat != "JJJJ-MM-TT") else None
            conn.execute(
                "INSERT INTO wasserkosten_positionen "
                "(jahr, typ, verbrauch_m3, kosten_eur, ablesedatum) VALUES (?,?,?,?,?)",
                (jahr, typ, v_m3, v_eur, v_dat))
        gut = self._flt(self._gutschrift_var["kosten"].get())
        if gut:
            conn.execute(
                "INSERT INTO wasserkosten_positionen (jahr, typ, verbrauch_m3, kosten_eur) "
                "VALUES (?,?,0,?)", (jahr, "Gutschrift / Erstattung", gut))
        conn.commit()
        conn.close()
        self._update_gesamt()
        messagebox.showinfo("Gespeichert", f"Jahreskosten {jahr} gespeichert.", parent=self)

    def _update_gesamt(self):
        """Zeigt Wasserkosten netto."""
        total = sum(self._flt(vd["kosten"].get()) for vd in self._kosten_vars.values())
        total -= abs(self._flt(self._gutschrift_var.get("kosten", tk.StringVar()).get()))
        if self._gesamt_label:
            self._gesamt_label.config(text=fmt_euro(total),
                                      fg=SUCCESS if total >= 0 else DANGER)

    # ── Tab 2: Punktetabelle ──────────────────────────────────────────────────

    def _build_punkte_tab(self):
        self._view_punkte = tk.Frame(self._content, bg=BG_CARD)
        info = tk.Label(self._view_punkte,
            text="Punkte = Personen + Spuelmaschine (1 Pkt) + Waschmaschine (1 Pkt) "
                 "+ Trockner mit Wasserku. (1 Pkt)  |  Gewertete Punkte = Punkte x Monate / 12",
            bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL)
        info.pack(anchor="w", padx=20, pady=(8, 2))

        cols = ("Wohnung / Mieter", "Eigentuemer", "Pers.",
                "Spuelm.", "Waschm.", "Trockner", "Monate", "Punkte", "Gew. Pkt.")
        f, self.tree_p = make_table(self._view_punkte, cols, height=12)
        f.pack(fill="both", expand=True, padx=20, pady=4)
        for c, w in zip(cols, [160, 160, 50, 60, 60, 70, 60, 60, 80]):
            self.tree_p.heading(c, text=c)
            self.tree_p.column(c, width=w, anchor="center")
        self.tree_p.column("Wohnung / Mieter", anchor="w")
        self.tree_p.column("Eigentuemer", anchor="w")
        self.tree_p.bind("<Double-1>", self._edit_wohnung)

        btn_row = tk.Frame(self._view_punkte, bg=BG_CARD)
        btn_row.pack(fill="x", padx=20, pady=(0, 8))
        make_btn(btn_row, "Aus Stammdaten", self._import_wohnungen,
                 color=ACCENT2).pack(side="left", padx=(0, 6))
        make_btn(btn_row, "Neu", self._new_wohnung,
                 color=BG_INPUT, fg=TEXT).pack(side="left", padx=(0, 6))
        make_btn(btn_row, "Bearbeiten", self._edit_wohnung,
                 color=BG_INPUT, fg=TEXT).pack(side="left", padx=(0, 6))
        make_btn(btn_row, "🗑 Löschen", self._delete_wohnung,
                 color=DANGER).pack(side="left")

    def _load_punkte(self):
        for i in self.tree_p.get_children():
            self.tree_p.delete(i)
        jahr = self._jahr_int()
        if not jahr:
            return
        conn = get_db()
        rows = conn.execute(
            "SELECT * FROM wasserkosten_wohnungsdaten WHERE jahr=? ORDER BY wohnung_bezeichnung",
            (jahr,)).fetchall()
        conn.close()
        for r in rows:
            rd = dict(r)
            basis = (rd["personen"] + rd["spuelmaschinen"] +
                     rd["waschmaschinen"] + rd["trockner_wasserkuehlung"])
            gew = round(basis * (rd["monate"] or 12) / 12, 2)
            self.tree_p.insert("", "end", iid=rd["id"], values=(
                rd["wohnung_bezeichnung"], rd["eigentuemer"] or "",
                rd["personen"], rd["spuelmaschinen"], rd["waschmaschinen"],
                rd["trockner_wasserkuehlung"], rd["monate"], basis, gew))

    def _new_wohnung(self):
        self._wohnung_dialog(None)

    def _edit_wohnung(self, event=None):
        sel = self.tree_p.selection()
        if not sel:
            return
        conn = get_db()
        row = conn.execute(
            "SELECT * FROM wasserkosten_wohnungsdaten WHERE id=?", (int(sel[0]),)
        ).fetchone()
        conn.close()
        if row:
            self._wohnung_dialog(dict(row))

    def _delete_wohnung(self):
        sel = self.tree_p.selection()
        if not sel:
            return
        if messagebox.askyesno("Entfernen", "Diesen Eintrag entfernen?", parent=self):
            conn = get_db()
            conn.execute("DELETE FROM wasserkosten_wohnungsdaten WHERE id=?", (int(sel[0]),))
            conn.commit()
            conn.close()
            self._load_punkte()

    def _wohnung_dialog(self, row):
        """Dialog zum Anlegen/Bearbeiten einer Wohnungs-Punktezeile."""
        jahr = self._jahr_int()
        if not jahr:
            messagebox.showwarning("Fehler", "Kein gueltiges Jahr.", parent=self)
            return
        win = tk.Toplevel(self)
        win.title("Wohnung Punktedaten")
        win.geometry("420x480")
        win.configure(bg=BG_CARD)
        win.grab_set()
        win.resizable(True, True)
        hdr = tk.Frame(win, bg=BG_SIDEBAR, height=44)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Bearbeiten" if row else "Neue Wohnung",
                 bg=BG_SIDEBAR, fg=TEXT_WHITE, font=FONT_H3).pack(side="left", padx=14, pady=10)

        # Button-Zeile zuerst packen (side="bottom") -- verhindert Verdraengen durch body
        br = tk.Frame(win, bg=BG_CARD)
        br.pack(fill="x", side="bottom", padx=20, pady=(0, 14))
        make_btn(br, "Abbrechen", win.destroy, color=BG_INPUT, fg=TEXT).pack(side="right", padx=(6, 0))

        body = tk.Frame(win, bg=BG_CARD)
        body.pack(fill="both", expand=True, padx=20, pady=12)

        def lf(lbl, dflt=""):
            tk.Label(body, text=lbl, bg=BG_CARD, fg=TEXT_LIGHT,
                     font=FONT_SMALL).pack(anchor="w", pady=(6, 1))
            v = tk.StringVar(value=str(dflt))
            make_entry(body, textvariable=v).pack(fill="x", ipady=5)
            return v

        r = row or {}
        wohn_v  = lf("Wohnung / Mieter *",             r.get("wohnung_bezeichnung", ""))
        eig_v   = lf("Eigentuemer",                     r.get("eigentuemer", ""))
        pers_v  = lf("Personen",                        r.get("personen", 1))
        spuel_v = lf("Spuelmaschinen (je 1 Pkt)",       r.get("spuelmaschinen", 0))
        wasch_v = lf("Waschmaschinen (je 1 Pkt)",       r.get("waschmaschinen", 1))
        trock_v = lf("Trockner Wasserkuehlung (1 Pkt)", r.get("trockner_wasserkuehlung", 0))
        mon_v   = lf("Monate im Abrechnungsjahr",       r.get("monate", 12))

        def _save():
            wohn = wohn_v.get().strip()
            if not wohn:
                messagebox.showwarning("Pflichtfeld", "Wohnung ist erforderlich.", parent=win)
                return
            conn = get_db()
            vals = (jahr, wohn, eig_v.get().strip(),
                    self._int(pers_v.get()), self._int(spuel_v.get()),
                    self._int(wasch_v.get()), self._int(trock_v.get()),
                    max(0.0, min(12.0, self._flt(mon_v.get()) or 12.0)))
            if row:
                conn.execute(
                    "UPDATE wasserkosten_wohnungsdaten SET "
                    "wohnung_bezeichnung=?, eigentuemer=?, personen=?, spuelmaschinen=?, "
                    "waschmaschinen=?, trockner_wasserkuehlung=?, monate=? WHERE id=?",
                    (wohn, vals[2], vals[3], vals[4], vals[5], vals[6], vals[7], row["id"]))
            else:
                conn.execute(
                    "INSERT INTO wasserkosten_wohnungsdaten "
                    "(jahr, wohnung_bezeichnung, eigentuemer, personen, spuelmaschinen, "
                    "waschmaschinen, trockner_wasserkuehlung, monate) VALUES (?,?,?,?,?,?,?,?)",
                    vals)
            conn.commit()
            conn.close()
            win.destroy()
            self._load_punkte()

        make_btn(br, "Speichern", _save, color=SUCCESS).pack(side="right")

    def _import_wohnungen(self):
        """Uebernimmt Wohnungen aus Stammdaten."""
        jahr = self._jahr_int()
        if not jahr:
            return
        conn = get_db()
        wohnungen = conn.execute(
            "SELECT w.bezeichnung, COALESCE(e.name,'') AS eig, "
            "COALESCE(m.personen,1) AS personen, COALESCE(m.spuelmaschinen,0) AS spuel, "
            "COALESCE(m.waschmaschinen,1) AS wasch, COALESCE(m.trockner_wasserkuehlung,0) AS trockner "
            "FROM wohnungen w "
            "LEFT JOIN eigentuemer e ON w.eigentuemer_id=e.id "
            "LEFT JOIN mieter m ON w.id=m.wohnung_id AND (m.auszug IS NULL OR m.auszug='') "
            "ORDER BY w.bezeichnung").fetchall()
        if not wohnungen:
            messagebox.showinfo("Keine Wohnungen",
                "Keine Wohnungen in den Stammdaten.\nBitte zuerst Wohnungen anlegen.",
                parent=self)
            conn.close()
            return
        added = 0
        for w in wohnungen:
            if not conn.execute(
                "SELECT id FROM wasserkosten_wohnungsdaten WHERE jahr=? AND wohnung_bezeichnung=?",
                    (jahr, w["bezeichnung"])).fetchone():
                conn.execute(
                    "INSERT INTO wasserkosten_wohnungsdaten "
                    "(jahr, wohnung_bezeichnung, eigentuemer, personen, spuelmaschinen, "
                    "waschmaschinen, trockner_wasserkuehlung, monate) VALUES (?,?,?,?,?,?,?,12)",
                    (jahr, w["bezeichnung"], w["eig"], w["personen"], w["spuel"], w["wasch"], w["trockner"]))
                added += 1
        conn.commit()
        conn.close()
        if added:
            messagebox.showinfo("Uebernommen",
                f"{added} Wohnung(en) uebernommen.\nBitte Werte anpassen.", parent=self)
        else:
            messagebox.showinfo("Vorhanden", "Alle Wohnungen bereits eingetragen.", parent=self)
        self._load_punkte()

    # ── Tab 3: Auswertung ─────────────────────────────────────────────────────

    def _build_auswertung_tab(self):
        self._view_auswertung = tk.Frame(self._content, bg=BG_CARD)
        canvas = tk.Canvas(self._view_auswertung, bg=BG_CARD, highlightthickness=0)
        sb = ttk.Scrollbar(self._view_auswertung, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        self._ausw_inner = tk.Frame(canvas, bg=BG_CARD)
        wid = canvas.create_window((0, 0), window=self._ausw_inner, anchor="nw")
        self._ausw_inner.bind("<Configure>",
                              lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(wid, width=e.width))

        br = tk.Frame(self._ausw_inner, bg=BG_CARD)
        br.pack(fill="x", padx=20, pady=(10, 4))
        make_btn(br, "Auswertung berechnen", self._berechne_auswertung,
                 color=SUCCESS).pack(side="left")
        self._ausw_result = tk.Frame(self._ausw_inner, bg=BG_CARD)
        self._ausw_result.pack(fill="both", expand=True, padx=20)

    def _berechne_auswertung(self):
        for w in self._ausw_result.winfo_children():
            w.destroy()
        jahr = self._jahr_int()
        if not jahr:
            tk.Label(self._ausw_result, text="Kein gueltiges Jahr.",
                     bg=BG_CARD, fg=DANGER, font=FONT_BODY).pack(anchor="w")
            return

        conn = get_db()
        pos_rows = conn.execute(
            "SELECT typ, verbrauch_m3, kosten_eur FROM wasserkosten_positionen WHERE jahr=?",
            (jahr,)).fetchall()
        kosten_by_typ = {r["typ"]: dict(r) for r in pos_rows}
        wohn_rows = conn.execute(
            "SELECT * FROM wasserkosten_wohnungsdaten WHERE jahr=? ORDER BY wohnung_bezeichnung",
            (jahr,)).fetchall()
        wohnungen = [dict(r) for r in wohn_rows]
        vj_rows = conn.execute(
            "SELECT eigentuemer, wasserkosten_eur FROM wasserkosten_vorjahr WHERE jahr=?",
            (jahr - 1,)).fetchall()
        vorjahr = {r["eigentuemer"]: r["wasserkosten_eur"] for r in vj_rows}
        conn.close()

        if not wohnungen:
            tk.Label(self._ausw_result,
                     text="Keine Wohnungsdaten fuer dieses Jahr. Bitte Punktetabelle ausfullen.",
                     bg=BG_CARD, fg=WARNING, font=FONT_BODY).pack(anchor="w", pady=8)
            return

        gesamt_brutto = sum(
            kosten_by_typ.get(t, {}).get("kosten_eur", 0) or 0 for t in self.TYPEN)
        gutschrift = abs(kosten_by_typ.get("Gutschrift / Erstattung", {}).get("kosten_eur", 0) or 0)
        gesamt_netto = gesamt_brutto - gutschrift

        for w in wohnungen:
            basis = (w["personen"] + w["spuelmaschinen"] +
                     w["waschmaschinen"] + w["trockner_wasserkuehlung"])
            w["basis_punkte"] = basis
            w["gew_punkte"]   = round(basis * (w["monate"] or 12) / 12, 4)

        gesamt_gew = sum(w["gew_punkte"] for w in wohnungen)
        kje_punkt  = (gesamt_netto / gesamt_gew) if gesamt_gew else 0

        for w in wohnungen:
            w["wasserkosten"] = round(w["gew_punkte"] * kje_punkt, 2)
            w["anteil"]       = (w["gew_punkte"] / gesamt_gew * 100) if gesamt_gew else 0

        # Eigentuemer aggregieren
        eig_dict = {}
        for w in wohnungen:
            eig = w["eigentuemer"] or "Unbekannt"
            if eig not in eig_dict:
                eig_dict[eig] = {"wohnungen": [], "gew_punkte": 0.0, "wasserkosten": 0.0}
            eig_dict[eig]["wohnungen"].append(w["wohnung_bezeichnung"])
            eig_dict[eig]["gew_punkte"]   += w["gew_punkte"]
            eig_dict[eig]["wasserkosten"] += w["wasserkosten"]

        gesamt_check = sum(w["wasserkosten"] for w in wohnungen)
        plausibel    = abs(gesamt_check - gesamt_netto) < 0.10

        body = self._ausw_result

        def section(txt):
            tk.Label(body, text=txt, bg=BG_CARD, fg=TEXT, font=FONT_H3).pack(
                anchor="w", pady=(14, 2))
            tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=(0, 4))

        def info_row(lbl, val, color=TEXT):
            r = tk.Frame(body, bg=BG_CARD)
            r.pack(fill="x", pady=1)
            tk.Label(r, text=lbl, bg=BG_CARD, fg=TEXT_LIGHT,
                     font=FONT_BODY, width=36, anchor="w").pack(side="left")
            tk.Label(r, text=val, bg=BG_CARD, fg=color,
                     font=FONT_BODY, anchor="w").pack(side="left")

        # Abschnitt 1: Ueberblick
        section(f"1.  Wasserkosten {jahr} - Ueberblick")
        for typ in self.TYPEN:
            d = kosten_by_typ.get(typ, {})
            info_row(typ, f"{d.get('verbrauch_m3', 0) or 0:.0f} m3  ->  {fmt_euro(d.get('kosten_eur', 0) or 0)}")
        if gutschrift:
            info_row("Gutschrift / Erstattung", f"- {fmt_euro(gutschrift)}", WARNING)
        info_row("Wasserkosten netto (Aufteilungsbasis)", fmt_euro(gesamt_netto), ACCENT2)

        # Abschnitt 2: Schluessel
        section("2.  Berechnungsschluessel")
        info_row("Gesamtpunkte (gewichtet)", f"{gesamt_gew:.2f} Punkte")
        info_row("Kosten je Punkt", fmt_euro(kje_punkt), ACCENT2)

        # Abschnitt 3: WE-Aufteilung
        section("3.  Aufteilung je Wohneinheit")
        hf = tk.Frame(body, bg=BG_INPUT)
        hf.pack(fill="x", pady=(0, 2))
        for txt, w in [("Wohneinheit", 20), ("Eigentuemer", 20), ("Gew.Pkt.", 10),
                       ("Wasserkosten", 14), ("Anteil %", 10)]:
            tk.Label(hf, text=txt, bg=BG_INPUT, fg=TEXT_LIGHT,
                     font=FONT_SMALL, width=w, anchor="w").pack(side="left", padx=4, pady=3)
        for w in wohnungen:
            rf = tk.Frame(body, bg=BG_CARD)
            rf.pack(fill="x")
            for val, width, anc in [
                (w["wohnung_bezeichnung"], 20, "w"),
                (w["eigentuemer"] or "-", 20, "w"),
                (f"{w['gew_punkte']:.2f}", 10, "e"),
                (fmt_euro(w["wasserkosten"]), 14, "e"),
                (f"{w['anteil']:.1f} %", 10, "e"),
            ]:
                tk.Label(rf, text=val, bg=BG_CARD, fg=TEXT,
                         font=FONT_BODY, width=width, anchor=anc).pack(side="left", padx=4)
        sf = tk.Frame(body, bg=BG_INPUT)
        sf.pack(fill="x", pady=(2, 0))
        for val, width, anc in [("GESAMT", 20, "w"), ("", 20, "w"),
                                  (f"{gesamt_gew:.2f}", 10, "e"),
                                  (fmt_euro(gesamt_check), 14, "e"), ("100.0 %", 10, "e")]:
            tk.Label(sf, text=val, bg=BG_INPUT, fg=TEXT,
                     font=("Segoe UI Semibold", 10), width=width, anchor=anc).pack(
                side="left", padx=4, pady=3)

        # Abschnitt 4: Eigentuemer
        section("4.  Aufteilung je Eigentuemer")
        he = tk.Frame(body, bg=BG_INPUT)
        he.pack(fill="x", pady=(0, 2))
        for txt, w in [("Eigentuemer", 22), ("Wohneinheiten", 18), ("Gew.Pkt.", 10),
                       ("Wasserkosten", 14), ("Anteil %", 10)]:
            tk.Label(he, text=txt, bg=BG_INPUT, fg=TEXT_LIGHT,
                     font=FONT_SMALL, width=w, anchor="w").pack(side="left", padx=4, pady=3)
        gesamt_eig = 0.0
        for eig, ed in sorted(eig_dict.items()):
            re2 = tk.Frame(body, bg=BG_CARD)
            re2.pack(fill="x")
            anteil = ed["gew_punkte"] / gesamt_gew * 100 if gesamt_gew else 0
            for val, width, anc in [
                (eig, 22, "w"),
                ("+".join(ed["wohnungen"]), 18, "w"),
                (f"{ed['gew_punkte']:.2f}", 10, "e"),
                (fmt_euro(ed["wasserkosten"]), 14, "e"),
                (f"{anteil:.1f} %", 10, "e"),
            ]:
                tk.Label(re2, text=val, bg=BG_CARD, fg=TEXT,
                         font=FONT_BODY, width=width, anchor=anc).pack(side="left", padx=4)
            gesamt_eig += ed["wasserkosten"]
        se = tk.Frame(body, bg=BG_INPUT)
        se.pack(fill="x", pady=(2, 0))
        for val, width, anc in [("GESAMT", 22, "w"), ("", 18, "w"),
                                  (f"{gesamt_gew:.2f}", 10, "e"),
                                  (fmt_euro(gesamt_eig), 14, "e"), ("100.0 %", 10, "e")]:
            tk.Label(se, text=val, bg=BG_INPUT, fg=TEXT,
                     font=("Segoe UI Semibold", 10), width=width, anchor=anc).pack(
                side="left", padx=4, pady=3)

        # Abschnitt 5: Plausibilitaetscheck
        section("5.  Plausibilitaetscheck")
        info_row("Summe WE-Kosten", fmt_euro(gesamt_check))
        info_row("Wasserkosten netto (Eingabe)", fmt_euro(gesamt_netto))
        diff = gesamt_check - gesamt_netto
        info_row("Differenz (Rundung)", fmt_euro(diff))
        check_txt = "OK - Stimmt" if plausibel else "FEHLER - Differenz zu gross!"
        check_col = SUCCESS if plausibel else DANGER
        tk.Label(body, text=check_txt, bg=BG_CARD, fg=check_col,
                 font=("Segoe UI Semibold", 11)).pack(anchor="w", pady=4)

        # Abschnitt 6: Vorjahresvergleich
        if vorjahr:
            section(f"6.  Vergleich mit Vorjahr ({jahr - 1})")
            hv = tk.Frame(body, bg=BG_INPUT)
            hv.pack(fill="x", pady=(0, 2))
            for txt, w in [("Eigentuemer", 22), (f"Wert {jahr - 1}", 14),
                           (f"Aktuell {jahr}", 14), ("Differenz", 14)]:
                tk.Label(hv, text=txt, bg=BG_INPUT, fg=TEXT_LIGHT,
                         font=FONT_SMALL, width=w, anchor="w").pack(side="left", padx=4, pady=3)
            for eig, ed in sorted(eig_dict.items()):
                vj = vorjahr.get(eig)
                if vj is None:
                    continue
                d_vj = ed["wasserkosten"] - vj
                rv = tk.Frame(body, bg=BG_CARD)
                rv.pack(fill="x")
                for val, width, col in [
                    (eig, 22, TEXT),
                    (fmt_euro(vj), 14, TEXT_LIGHT),
                    (fmt_euro(ed["wasserkosten"]), 14, TEXT),
                    (fmt_euro(d_vj), 14, SUCCESS if d_vj <= 0 else DANGER),
                ]:
                    tk.Label(rv, text=val, bg=BG_CARD, fg=col,
                             font=FONT_BODY, width=width,
                             anchor="w" if width == 22 else "e").pack(side="left", padx=4)

        # Als-Vorjahr-Speichern
        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=(16, 4))
        vr = tk.Frame(body, bg=BG_CARD)
        vr.pack(fill="x", pady=(0, 16))
        tk.Label(vr, text=f"Werte {jahr} als Vorjahresvergleich fuer {jahr + 1} speichern:",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(side="left", padx=(0, 8))
        make_btn(vr, "Als Vorjahr speichern",
                 lambda: self._save_als_vorjahr(eig_dict, jahr),
                 color=BG_INPUT, fg=TEXT).pack(side="left")

    def _save_als_vorjahr(self, eig_dict, jahr):
        conn = get_db()
        conn.execute("DELETE FROM wasserkosten_vorjahr WHERE jahr=?", (jahr,))
        for eig, ed in eig_dict.items():
            conn.execute(
                "INSERT INTO wasserkosten_vorjahr (jahr, eigentuemer, wasserkosten_eur) VALUES (?,?,?)",
                (jahr, eig, round(ed["wasserkosten"], 2)))
        conn.commit()
        conn.close()
        messagebox.showinfo("Gespeichert",
            f"Werte {jahr} als Vorjahr fuer {jahr + 1} gespeichert.", parent=self)

    # ── Tab-Umschalten ────────────────────────────────────────────────────────

    def _switch_tab(self, tab):
        for tid, btn in self._tab_btns.items():
            btn.config(bg=ACCENT2 if tid == tab else BG_CARD,
                       fg=TEXT_WHITE if tid == tab else TEXT_LIGHT)
        for v in [self._view_kosten, self._view_punkte, self._view_auswertung]:
            v.pack_forget()
        if tab == "kosten":
            self._view_kosten.pack(fill="both", expand=True)
            self._load_kosten()
        elif tab == "punkte":
            self._view_punkte.pack(fill="both", expand=True)
            self._load_punkte()
        elif tab == "auswertung":
            self._view_auswertung.pack(fill="both", expand=True)

    def _refresh(self):
        self._load_kosten()
        self._load_punkte()
        if self._ausw_result:
            for w in self._ausw_result.winfo_children():
                w.destroy()

    # ── Hilfsmethoden ─────────────────────────────────────────────────────────

    def _jahr_int(self):
        try:
            return int(self._jahr_var.get())
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _flt(val):
        try:
            return float(str(val).replace(",", ".").strip() or 0)
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def _int(val):
        try:
            return max(0, int(str(val).strip() or 0))
        except (ValueError, TypeError):
            return 0


# ── EinstellungenPage ─────────────────────────────────────────────────────────


class KIAssistentPage(tk.Frame):
    """KI-Assistent: Chat mit Claude, Auto-Kategorisierung, Anomalie-Check."""

    # DB-Schema als Kontext für das Sprachmodell
    _SCHEMA_KONTEXT = """
Du bist ein Assistent für eine WEG-Hausverwaltungs-Software (Python/SQLite).
Die Datenbank enthält folgende Tabellen:

eigentuemer(id, name, vorname, strasse, plz, ort, telefon, email, iban, einheit)
wohnungen(id, bezeichnung, typ, lage, nutzflaeche_qm, zimmer, mea_tausendstel, eigentuemer_id, mieter_id)
mieter(id, name, vorname, strasse, plz, ort, telefon, email, einzug, auszug, kaltmiete, wohnungs_id, personen, spuelmaschinen, waschmaschinen, trockner_wasserkuehlung)
zahlungen(id, datum, betrag, kategorie, beschreibung, typ, konto_typ, status)
kontoauszug(id, datum, buchungstext, betrag, saldo, iban, konto_typ, kategorie_vorschlag, als_buchung_uebernommen, zugeordnet, zahlung_id)
wartung(id, titel, beschreibung, prioritaet, status, gemeldet_von, einheit, erstellt_am, erledigt_am)
nebenkosten(id, jahr, bezeichnung, betrag, umlageschluessel)
nachrichten(id, datum, betreff, inhalt, absender, empfaenger, gelesen)
dokumente(id, datum, titel, pfad, kategorie, wohnungs_id)
benutzer(id, benutzername, rolle, aktiv)

Beträge: positiv = Einnahmen, negativ = Ausgaben.
kontoauszug.buchungstext = "Gegenkonto||Verwendungszweck" (mit || getrennt).
kontoauszug.kategorie_vorschlag: automatisch erkannte Kategorie beim Import.
kontoauszug.als_buchung_uebernommen: 1 = bereits in zahlungen übernommen.
Kategorien (zahlungen.kategorie): Wohngeld, Rücklage, Betriebskosten, Instandhaltung, Verwaltung, Versicherung, Wasser, Strom, Heizung, Müll, Sonstiges.
zahlungen.status: Neu, Geprüft, Freigegeben.

Wenn du SQL-Abfragen generierst, antworte im Format:
SQL: <deine Abfrage>
ANTWORT: <kurze Erklärung was die Abfrage zurückgibt>

Für allgemeine Fragen antworte direkt ohne SQL.
Antworte immer auf Deutsch.
"""

    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self._messages = []   # Liste von (rolle, text) Tuples
        self._build()

    def _build(self):
        # ── Titel ────────────────────────────────────────────────────────────
        header = tk.Frame(self, bg=BG_CARD, pady=0)
        header.pack(fill="x")
        tk.Label(header, text="🤖  KI-Assistent", bg=BG_CARD, fg=TEXT,
                 font=FONT_H2).pack(side="left", padx=20, pady=14)
        tk.Label(header, text="Powered by Claude (Anthropic API)",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(side="left", padx=4, pady=14)
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # ── Haupt-Layout: Chat links, Aktionen rechts ─────────────────────
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True, padx=16, pady=12)
        main.columnconfigure(0, weight=3)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        # ── Linke Spalte: Chat ────────────────────────────────────────────
        chat_frame = tk.Frame(main, bg=BG_CARD, bd=0, relief="flat")
        chat_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        chat_frame.rowconfigure(0, weight=1)
        chat_frame.columnconfigure(0, weight=1)

        # Chat-Verlauf
        self._chat_text = tk.Text(
            chat_frame, wrap="word", state="disabled",
            bg=BG_CARD, fg=TEXT, font=FONT_BODY,
            relief="flat", padx=12, pady=8, cursor="arrow",
            spacing3=6
        )
        chat_sb = ttk.Scrollbar(chat_frame, command=self._chat_text.yview)
        self._chat_text.configure(yscrollcommand=chat_sb.set)
        chat_sb.grid(row=0, column=1, sticky="ns")
        self._chat_text.grid(row=0, column=0, sticky="nsew")

        # Farb-Tags für Chat
        self._chat_text.tag_configure("user_bubble", foreground=ACCENT2,
                                       font=("Segoe UI Semibold", 10), lmargin1=10, lmargin2=10)
        self._chat_text.tag_configure("ki_bubble", foreground=TEXT,
                                       font=FONT_BODY, lmargin1=10, lmargin2=10)
        self._chat_text.tag_configure("sql_result", foreground=SUCCESS,
                                       font=("Consolas", 9), lmargin1=20, lmargin2=20)
        self._chat_text.tag_configure("error_msg", foreground=DANGER,
                                       font=FONT_SMALL, lmargin1=10, lmargin2=10)
        self._chat_text.tag_configure("hint", foreground=TEXT_LIGHT,
                                       font=FONT_SMALL, lmargin1=10)

        # Willkommensnachricht
        self._append_chat("hint",
            "Stell mir Fragen zur Hausverwaltung \u2013 z.B.:\n"
            "  \u2022 Welche Eigentuemer haben diesen Monat nicht bezahlt?\n"
            "  \u2022 Wie hoch sind die Ausgaben in Q1 2026?\n"
            "  \u2022 Gibt es ueberfaellige Wartungsaufgaben?\n"
            "  \u2022 Zeige alle Buchungen ueber 500 Euro\n")

        # Eingabe-Zeile
        input_row = tk.Frame(chat_frame, bg=BG_INPUT, pady=8)
        input_row.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        self._entry = make_entry(input_row)
        self._entry.pack(side="left", fill="x", expand=True, padx=(10, 6), ipady=7)
        self._entry.bind("<Return>", lambda e: self._send())
        make_btn(input_row, "➤ Senden", self._send, color=ACCENT2).pack(side="left", padx=(0, 10))

        # Fokus auf Entry setzen sobald Seite geladen
        self.after(100, lambda: self._entry.focus_set())

        # ── Rechte Spalte: Schnell-Aktionen ───────────────────────────────
        right = tk.Frame(main, bg=BG_CARD)
        right.grid(row=0, column=1, sticky="nsew")

        tk.Label(right, text="Schnell-Aktionen", bg=BG_CARD, fg=TEXT,
                 font=FONT_H3).pack(anchor="w", padx=12, pady=(12, 4))
        tk.Frame(right, bg=BORDER, height=1).pack(fill="x", padx=10, pady=(0, 8))

        make_btn(right, "🏷  Auto-Kategorisierung", self._auto_kategorisierung,
                 color=ACCENT2).pack(fill="x", padx=10, pady=(0, 6))
        make_btn(right, "⚠  Anomalie-Check", self._anomalie_check,
                 color="#C8960E").pack(fill="x", padx=10, pady=(0, 6))
        make_btn(right, "📊  Monats-Bericht", self._monatsbericht,
                 color=SUCCESS).pack(fill="x", padx=10, pady=(0, 6))
        make_btn(right, "💰  Offene Forderungen", self._offene_forderungen,
                 color=ACCENT2).pack(fill="x", padx=10, pady=(0, 6))

        # Modell-Auswahl
        tk.Frame(right, bg=BORDER, height=1).pack(fill="x", padx=10, pady=(8, 8))
        self._modell_label = tk.Label(right, text="KI-Modell", bg=BG_CARD, fg=TEXT_LIGHT,
                 font=FONT_SMALL)
        self._modell_label.pack(anchor="w", padx=12)
        self._modell_var = tk.StringVar()
        self._modell_cb = ttk.Combobox(right, textvariable=self._modell_var,
                                        state="readonly", font=FONT_SMALL)
        self._modell_cb.pack(fill="x", padx=10, pady=(2, 8))
        self._modell_cb.bind("<<ComboboxSelected>>", self._modell_geaendert)

        # Provider-Status
        tk.Frame(right, bg=BORDER, height=1).pack(fill="x", padx=10, pady=(0, 8))
        self._api_status = tk.Label(right, text="", bg=BG_CARD, fg=SUCCESS,
                                     font=FONT_SMALL, wraplength=180, anchor="w", justify="left")
        self._api_status.pack(anchor="w", padx=12, pady=4)
        make_btn(right, "🔄  Provider neu laden", self._provider_aktualisieren,
                 color=BG_INPUT, fg=TEXT).pack(fill="x", padx=10, pady=(0, 4))
        make_btn(right, "⚙  Einstellungen öffnen", self._zu_einstellungen,
                 color=TEXT_LIGHT).pack(fill="x", padx=10, pady=(0, 8))

        # Header-Label Referenz für späteren Update
        self._header_label = header.winfo_children()[1] if len(header.winfo_children()) > 1 else None
        self._provider_aktualisieren()  # Initial befüllen

    # ── Hilfsmethoden Modell-Auswahl ─────────────────────────────────────────

    @staticmethod
    def _alle_ki_modelle(cfg: dict) -> list:
        """Gibt alle konfigurierten KI-Modelle beider Anbieter zurück.
        Format je Eintrag: "modellname  [Anbieter]" (#33 fix).
        Nur Anbieter werden angeboten für die Konfigurationsdaten vorhanden sind."""
        modelle = []
        # Anthropic: verfügbar wenn API-Key gesetzt
        if cfg.get("anthropic_api_key", "").strip():
            for m in ["claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5-20251001"]:
                modelle.append(f"{m}  [Anthropic]")
        # Ollama: verfügbar wenn URL konfiguriert
        if cfg.get("ollama_url", "").strip():
            ollama_m = cfg.get("ollama_modell", "llama3.2").strip() or "llama3.2"
            modelle.append(f"{ollama_m}  [Ollama]")
        return modelle or ["claude-opus-4-6  [Anthropic]"]

    @staticmethod
    def _parse_modell_auswahl(auswahl: str) -> tuple:
        """Zerlegt 'modellname  [Anbieter]' → (anbieter, modell).
        Rückgabe z.B. ('anthropic', 'claude-opus-4-6') oder ('ollama', 'gemma3:4b')."""
        if "  [Anthropic]" in auswahl:
            return "anthropic", auswahl.replace("  [Anthropic]", "").strip()
        if "  [Ollama]" in auswahl:
            return "ollama", auswahl.replace("  [Ollama]", "").strip()
        return "anthropic", auswahl.strip()

    def _provider_aktualisieren(self):
        """Befüllt Dropdown mit ALLEN konfigurierten KI-Modellen beider Anbieter (#33 fix)."""
        cfg = load_config()
        modelle = self._alle_ki_modelle(cfg)
        self._modell_cb.configure(values=modelle)
        self._modell_label.config(text="KI-Modell")

        # Aktive Auswahl wiederherstellen
        aktiv = cfg.get("ki_aktives_modell", "")
        if aktiv and aktiv in modelle:
            self._modell_var.set(aktiv)
        elif modelle:
            # Fallback: Ersten Eintrag wählen, der zum gespeicherten Anbieter passt
            anbieter = cfg.get("ki_anbieter", "anthropic")
            tag = "[Anthropic]" if anbieter == "anthropic" else "[Ollama]"
            passend = [m for m in modelle if tag in m]
            self._modell_var.set(passend[0] if passend else modelle[0])

        # Statuszeile: Info über beide Anbieter
        status_parts = []
        key = cfg.get("anthropic_api_key", "").strip()
        if key:
            status_parts.append("✅ Anthropic: API-Key konfiguriert")
        else:
            status_parts.append("⚠️ Anthropic: kein API-Key")
        ollama_url = cfg.get("ollama_url", "").strip()
        if ollama_url:
            status_parts.append(f"⏳ Ollama: {ollama_url} – wird geprüft …")
            threading.Thread(target=self._ollama_ping, args=(ollama_url,), daemon=True).start()
        self._api_status.config(text="\n".join(status_parts), fg=TEXT_LIGHT)

    def _ollama_ping(self, base_url: str):
        """Prüft ob Ollama erreichbar ist und aktualisiert Statuslabel."""
        try:
            req = urllib.request.Request(base_url.rstrip("/") + "/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=4) as r:
                data = json.loads(r.read().decode())
            modelle = [m["name"] for m in data.get("models", [])]
            info = f"✅ Ollama verbunden\nModelle: {', '.join(modelle[:4]) or '–'}"
            self.after(0, lambda: self._api_status.config(text=info, fg=SUCCESS))
        except Exception as ex:
            info = f"❌ Ollama nicht erreichbar:\n{ex}"
            self.after(0, lambda: self._api_status.config(text=info, fg=DANGER))

    def _modell_geaendert(self, event=None):
        """Gewähltes Modell in Konfiguration speichern (#33 fix: provider:modell)."""
        auswahl = self._modell_var.get()
        cfg = load_config()
        cfg["ki_aktives_modell"] = auswahl
        anbieter, modell = self._parse_modell_auswahl(auswahl)
        cfg["ki_anbieter"] = anbieter
        if anbieter == "ollama":
            cfg["ollama_modell"] = modell
        else:
            cfg["ki_modell"] = modell
        save_config(cfg)

    def _zu_einstellungen(self):
        """Zur Einstellungen-Seite navigieren."""
        app = self.winfo_toplevel()
        if hasattr(app, "_switch"):
            # Einstellungen ist der letzte Eintrag in PAGES
            idx = len(app.PAGES) - 1
            app._switch(idx)

    # ── Chat-Ausgabe ──────────────────────────────────────────────────────────

    def _append_chat(self, tag, text):
        self._chat_text.configure(state="normal")
        self._chat_text.insert("end", text + "\n", tag)
        self._chat_text.configure(state="disabled")
        self._chat_text.see("end")

    # ── Senden & API-Call ─────────────────────────────────────────────────────

    def _send(self):
        frage = self._entry.get().strip()
        if not frage:
            return
        self._entry.delete(0, "end")
        self._append_chat("user_bubble", f"👤 Du: {frage}")
        self._messages.append({"role": "user", "content": frage})
        # Anbieter aus aktiver Modell-Auswahl ableiten (#33 fix)
        auswahl = self._modell_var.get()
        anbieter, _ = self._parse_modell_auswahl(auswahl)
        warte_text = "⏳ Ollama denkt …" if anbieter == "ollama" else "⏳ Claude denkt …"
        self._append_chat("hint", warte_text)
        threading.Thread(target=self._api_call_thread,
                         args=(list(self._messages),), daemon=True).start()

    def _api_call_thread(self, messages):
        cfg = load_config()
        # Anbieter aus aktueller Dropdown-Auswahl ableiten (#33 fix)
        auswahl = self._modell_var.get() if hasattr(self, "_modell_var") else ""
        if auswahl:
            anbieter, modell = self._parse_modell_auswahl(auswahl)
        else:
            anbieter = cfg.get("ki_anbieter", "anthropic")
            modell = ""

        if anbieter == "ollama":
            self._ollama_call_thread(messages, cfg, modell or None)
        else:
            self._anthropic_call_thread(messages, cfg, modell or None)

    def _anthropic_call_thread(self, messages, cfg, modell_override=None):
        """API-Call an Anthropic Claude."""
        key = cfg.get("anthropic_api_key", "").strip()
        if not key:
            self.after(0, lambda: self._append_chat("error_msg",
                "❌ Kein Anthropic API-Key. Bitte in Einstellungen → KI-Administration eintragen."))
            return
        try:
            modell = modell_override or cfg.get("ki_modell", "claude-opus-4-6")
            payload = json.dumps({
                "model": modell,
                "max_tokens": 1024,
                "system": self._SCHEMA_KONTEXT,
                "messages": messages
            }).encode("utf-8")
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=payload,
                headers={
                    "x-api-key": key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                }
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            antwort = data["content"][0]["text"]
            self._messages.append({"role": "assistant", "content": antwort})
            if "SQL:" in antwort:
                self.after(0, lambda a=antwort: self._handle_sql_response(a))
            else:
                self.after(0, lambda a=antwort: self._append_chat("ki_bubble", f"🤖 Claude: {a}"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            self.after(0, lambda b=body: self._append_chat("error_msg", f"❌ API-Fehler: {b[:200]}"))
        except Exception as ex:
            self.after(0, lambda x=str(ex): self._append_chat("error_msg", f"❌ Fehler: {x}"))

    def _ollama_call_thread(self, messages, cfg, modell_override=None):
        """API-Call an lokales Ollama (POST /api/chat)."""
        base_url = cfg.get("ollama_url", "http://localhost:11434").strip().rstrip("/")
        modell   = modell_override or cfg.get("ollama_modell", "llama3.2").strip() or "llama3.2"
        # System-Nachricht als erstes Element in messages-Liste (Ollama-Format)
        ollama_msgs = [{"role": "system", "content": self._SCHEMA_KONTEXT}] + messages
        try:
            payload = json.dumps({
                "model":    modell,
                "messages": ollama_msgs,
                "stream":   False
            }).encode("utf-8")
            req = urllib.request.Request(
                f"{base_url}/api/chat",
                data=payload,
                headers={"content-type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            antwort = data["message"]["content"]
            self._messages.append({"role": "assistant", "content": antwort})
            label = f"🤖 {modell}"
            if "SQL:" in antwort:
                self.after(0, lambda a=antwort: self._handle_sql_response(a))
            else:
                self.after(0, lambda a=antwort, l=label:
                           self._append_chat("ki_bubble", f"{l}: {a}"))
        except urllib.error.URLError as e:
            self.after(0, lambda x=str(e): self._append_chat("error_msg",
                f"❌ Ollama nicht erreichbar ({base_url}):\n{x}\n"
                "Bitte sicherstellen dass Ollama läuft: ollama serve"))
        except Exception as ex:
            self.after(0, lambda x=str(ex): self._append_chat("error_msg",
                f"❌ Ollama-Fehler: {x}"))

    def _handle_sql_response(self, antwort):
        """SQL aus KI-Antwort extrahieren, ausführen, Ergebnis anzeigen."""
        lines = antwort.split("\n")
        sql_line = next((l for l in lines if l.startswith("SQL:")), None)
        erklärung_lines = [l for l in lines if not l.startswith("SQL:")]
        erklärung = "\n".join(erklärung_lines).strip()
        if erklärung:
            self._append_chat("ki_bubble", f"🤖 Claude: {erklärung}")
        if sql_line:
            sql = sql_line[4:].strip()
            try:
                conn = get_db()
                rows = conn.execute(sql).fetchall()
                conn.close()
                if rows:
                    # Spaltenköpfe
                    cols = rows[0].keys() if hasattr(rows[0], "keys") else []
                    header = "  |  ".join(str(c) for c in cols)
                    self._append_chat("sql_result", f"📋 Ergebnis:\n{header}")
                    self._append_chat("sql_result", "─" * min(len(header), 60))
                    for row in rows[:25]:
                        self._append_chat("sql_result",
                            "  |  ".join(str(v) if v is not None else "–" for v in row))
                    if len(rows) > 25:
                        self._append_chat("hint", f"  … und {len(rows)-25} weitere Zeilen")
                else:
                    self._append_chat("hint", "  (Keine Ergebnisse)")
            except Exception as ex:
                self._append_chat("error_msg", f"❌ SQL-Fehler: {ex}")

    # ── Schnell-Aktionen ──────────────────────────────────────────────────────

    def _auto_kategorisierung(self):
        """Unkategorisierte Buchungen der KI zur Kategorisierung vorlegen."""
        conn = get_db()
        rows = conn.execute(
            "SELECT id, datum, betrag, buchungstext "
            "FROM kontoauszug WHERE (kategorie_vorschlag IS NULL OR kategorie_vorschlag='') "
            "AND (als_buchung_uebernommen IS NULL OR als_buchung_uebernommen=0) LIMIT 20"
        ).fetchall()
        conn.close()
        if not rows:
            self._append_chat("hint", "✅ Keine unkategorisierten Buchungen gefunden.")
            return
        def _split_bt(bt):
            """buchungstext 'Gegenkonto||Verwendungszweck' aufteilen."""
            if bt and "||" in bt:
                gk, vz = bt.split("||", 1)
                return gk.strip(), vz.strip()
            return (bt or ""), ""
        liste = "\n".join(
            f"  ID {r['id']} | {r['datum']} | {r['betrag']:+.2f} € | {_split_bt(r['buchungstext'])[0] or '–'} | {_split_bt(r['buchungstext'])[1] or '–'}"
            for r in rows
        )
        frage = (
            f"Bitte kategorisiere folgende {len(rows)} Bankbuchungen. "
            f"Mögliche Kategorien: Wohngeld, Rücklage, Betriebskosten, Instandhaltung, "
            f"Verwaltung, Versicherung, Wasser, Strom, Heizung, Müll, Sonstiges.\n\n"
            f"{liste}\n\n"
            f"Nenne für jede Buchung: ID | Kategorie | Begründung (kurz)"
        )
        self._append_chat("user_bubble", "👤 Auto-Kategorisierung gestartet …")
        self._messages.append({"role": "user", "content": frage})
        self._append_chat("hint", "⏳ Claude analysiert Buchungen …")
        threading.Thread(target=self._api_call_thread,
                         args=(list(self._messages),), daemon=True).start()

    def _anomalie_check(self):
        """KI prüft auf Anomalien: fehlende Zahlungen, ungewöhnliche Beträge."""
        conn = get_db()
        heute = date.today()
        monat = heute.strftime("%Y-%m")
        # Statistiken aus zahlungen-Tabelle sammeln (hat echte kategorie-Spalte)
        zahlungen_stats = conn.execute(
            "SELECT kategorie, SUM(betrag) as gesamt, COUNT(*) as anzahl "
            "FROM zahlungen WHERE datum LIKE ? GROUP BY kategorie",
            (f"{monat}%",)
        ).fetchall()
        eigentuemer = conn.execute("SELECT COUNT(*) as n FROM eigentuemer").fetchone()["n"]
        wohngeld = conn.execute(
            "SELECT COUNT(*) as n FROM zahlungen "
            "WHERE datum LIKE ? AND kategorie='Wohngeld' AND betrag > 0",
            (f"{monat}%",)
        ).fetchone()["n"]
        conn.close()

        stats = f"Monat: {monat}\nEigentümer gesamt: {eigentuemer}\nWohngeld-Eingänge: {wohngeld}\n"
        if zahlungen_stats:
            stats += "Buchungen nach Kategorie:\n"
            for r in zahlungen_stats:
                stats += f"  {r['kategorie'] or 'Ohne'}: {r['gesamt']:+.2f} € ({r['anzahl']} Buchungen)\n"

        frage = (
            f"Führe einen Anomalie-Check für die WEG durch:\n{stats}\n"
            f"Analysiere: 1) Fehlende Wohngeld-Zahlungen (erwartet {eigentuemer}), "
            f"2) Ungewöhnliche Beträge, 3) Handlungsempfehlungen. "
            f"Antworte strukturiert mit konkreten Befunden."
        )
        self._append_chat("user_bubble", f"👤 Anomalie-Check für {monat} …")
        self._messages.append({"role": "user", "content": frage})
        self._append_chat("hint", "⏳ Claude prüft …")
        threading.Thread(target=self._api_call_thread,
                         args=(list(self._messages),), daemon=True).start()

    def _monatsbericht(self):
        """Monatlicher Finanzbericht vom aktuellen Monat."""
        conn = get_db()
        monat = date.today().strftime("%Y-%m")
        einnahmen = conn.execute(
            "SELECT SUM(betrag) FROM zahlungen WHERE datum LIKE ? AND betrag > 0",
            (f"{monat}%",)
        ).fetchone()[0] or 0
        ausgaben = conn.execute(
            "SELECT SUM(betrag) FROM zahlungen WHERE datum LIKE ? AND betrag < 0",
            (f"{monat}%",)
        ).fetchone()[0] or 0
        kategorien = conn.execute(
            "SELECT kategorie, SUM(betrag) as s FROM zahlungen "
            "WHERE datum LIKE ? GROUP BY kategorie ORDER BY s",
            (f"{monat}%",)
        ).fetchall()
        conn.close()
        saldo = einnahmen + ausgaben
        details = "\n".join(f"  {r['kategorie'] or 'Ohne'}: {r['s']:+.2f} €" for r in kategorien)
        frage = (
            f"Erstelle einen Monats-Finanzbericht für {monat}:\n"
            f"Einnahmen: {einnahmen:+.2f} €\nAusgaben: {ausgaben:+.2f} €\nSaldo: {saldo:+.2f} €\n"
            f"Nach Kategorien:\n{details}\n\n"
            f"Kommentiere die Zahlen und gib eine Einschätzung zur finanziellen Lage der WEG."
        )
        self._append_chat("user_bubble", f"👤 Monats-Bericht {monat} …")
        self._messages.append({"role": "user", "content": frage})
        self._append_chat("hint", "⏳ Claude erstellt Bericht …")
        threading.Thread(target=self._api_call_thread,
                         args=(list(self._messages),), daemon=True).start()

    def _offene_forderungen(self):
        """Wer hat diesen Monat Wohngeld noch nicht bezahlt?"""
        conn = get_db()
        monat = date.today().strftime("%Y-%m")
        alle = conn.execute(
            "SELECT e.id, e.vorname || ' ' || e.name as name "
            "FROM eigentuemer e ORDER BY e.name"
        ).fetchall()
        # Wohngeld-Buchungen aus zahlungen (hat echte kategorie-Spalte)
        wohngeld_eingaenge = conn.execute(
            "SELECT beschreibung, betrag, datum "
            "FROM zahlungen WHERE datum LIKE ? AND kategorie='Wohngeld' AND betrag > 0",
            (f"{monat}%",)
        ).fetchall()
        conn.close()
        eingaenge_str = "\n".join(
            f"  {r['datum']} | {r['beschreibung'] or '–'} | {r['betrag']:.2f} €"
            for r in wohngeld_eingaenge
        ) or "  (keine)"
        alle_str = "\n".join(f"  {r['name']}" for r in alle)
        frage = (
            f"Offene Forderungen Wohngeld {monat}:\n"
            f"Alle Eigentümer:\n{alle_str}\n\n"
            f"Wohngeld-Eingänge diesen Monat:\n{eingaenge_str}\n\n"
            f"Analysiere wer wahrscheinlich noch nicht gezahlt hat (Name-Matching) "
            f"und formuliere eine freundliche Erinnerungsnotiz."
        )
        self._append_chat("user_bubble", f"👤 Offene Forderungen {monat} …")
        self._messages.append({"role": "user", "content": frage})
        self._append_chat("hint", "⏳ Claude analysiert …")
        threading.Thread(target=self._api_call_thread,
                         args=(list(self._messages),), daemon=True).start()


class EinstellungenPage(tk.Frame):
    """Einstellungen-Seite: Tabs für Stammdaten, Bankdaten, Speicherpfade, KI."""

    def __init__(self, parent):
        super().__init__(parent, bg=BG_CARD)
        self._cfg = load_config()
        self._vars = {}
        self._build()

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=BG_CARD)
        hdr.pack(fill="x", padx=20, pady=(18, 0))
        tk.Label(hdr, text="Einstellungen", bg=BG_CARD, fg=TEXT, font=FONT_H2).pack(side="left")
        make_btn(hdr, "💾 Speichern", self._save, color=SUCCESS).pack(side="right")
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(6, 0))

        tk.Label(self, text=f"Konfiguration: {CONFIG_PATH}",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w", padx=20, pady=(4, 6))

        # Notebook mit 4 Tabs
        style = ttk.Style()
        style.configure("EinstellTab.TNotebook", background=BG_CARD, borderwidth=0)
        style.configure("EinstellTab.TNotebook.Tab", font=FONT_BODY, padding=[12, 6])
        nb = ttk.Notebook(self, style="EinstellTab.TNotebook")
        nb.pack(fill="both", expand=True, padx=20, pady=8)

        # ── Tab 1: Stammdaten ─────────────────────────────────────────────────
        t1_outer, t1 = self._scrollable_tab(nb)
        nb.add(t1_outer, text="🏛 Stammdaten")
        self._section(t1, "WEG-Stammdaten")
        self._path_field(t1, "WEG-Name", "weg_name", is_path=False)
        self._path_field(t1, "Straße", "weg_strasse", is_path=False)
        self._path_field(t1, "PLZ", "weg_plz", is_path=False)
        self._path_field(t1, "Ort", "weg_ort", is_path=False)
        self._path_field(t1, "E-Mail", "weg_email", is_path=False)
        self._path_field(t1, "Telefon", "weg_telefon", is_path=False)

        # ── Tab 2: Bankdaten ──────────────────────────────────────────────────
        t2_outer, t2 = self._scrollable_tab(nb)
        nb.add(t2_outer, text="🏦 Bankdaten")
        self._section(t2, "Wohngeldkonto")
        self._path_field(t2, "Konto-Bezeichnung", "bez_wohngeld", is_path=False)
        self._iban_field(t2, "IBAN", "iban_wohngeld")
        self._section(t2, "Rücklagenkonto")
        self._path_field(t2, "Konto-Bezeichnung", "bez_ruecklage", is_path=False)
        self._iban_field(t2, "IBAN", "iban_ruecklage")

        # ── Tab 3: Speicherpfade ──────────────────────────────────────────────
        t3_outer, t3 = self._scrollable_tab(nb)
        nb.add(t3_outer, text="📁 Speicherpfade")
        self._section(t3, "Kontoauszüge")
        self._path_field(t3, "Standard-Importordner Kontoauszüge", "pfad_kontoauszug_import", is_path=True, is_dir=True)
        self._section(t3, "Belege & Dokumente")
        self._path_field(t3, "Ordner für Rechnungsbelege", "pfad_belege", is_path=True, is_dir=True)
        self._path_field(t3, "Ordner Dokumente / allgemein", "pfad_dokumente", is_path=True, is_dir=True)
        self._section(t3, "Datenbank")
        self._path_field(t3, "Ordner Datenbank-Backup", "pfad_backup", is_path=True, is_dir=True)
        self._path_field(t3, "Datenbankdatei (hausverwaltung.db)", "pfad_datenbank", is_path=True, is_dir=False)
        # ── Backup/Restore Aktionen (#30) ────────────────────────────────────
        self._section(t3, "Backup & Wiederherstellung")
        tk.Label(t3,
                 text="Backup: Kopiert die Datenbank in den oben gewählten Backup-Ordner.\n"
                      "Wiederherstellen: Ersetzt die aktuelle Datenbank durch eine Backup-Datei.",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL, justify="left"
                 ).pack(anchor="w", padx=20, pady=(0, 8))
        btn_backup_row = tk.Frame(t3, bg=BG_CARD)
        btn_backup_row.pack(fill="x", padx=20, pady=(0, 12))
        make_btn(btn_backup_row, "💾 Backup erstellen", self._db_backup,
                 color=ACCENT2).pack(side="left", padx=(0, 12))
        make_btn(btn_backup_row, "♻ Datenbank wiederherstellen", self._db_restore,
                 color=DANGER).pack(side="left")

        # ── Tab 4: KI-Administration (nur für Berechtigte) ────────────────────
        t4_outer, t4 = self._scrollable_tab(nb)
        nb.add(t4_outer, text="🤖 KI-Administration")
        if not hat_recht("KI-Administration", "lesen"):
            tk.Label(t4,
                     text="🔒  Kein Zugriff auf KI-Administration.\n"
                          "Bitte unter Rollen & Rechte die Berechtigung erteilen.",
                     bg=BG_CARD, fg=DANGER, font=FONT_BODY,
                     justify="center").pack(expand=True)
        else:
            self._build_ki_admin_tab(t4)

    def _build_ki_admin_tab(self, t4):
        """Inhalt des KI-Administration Tabs (ausgelagert für Zugriffsschutz #34)."""
        self._section(t4, "KI-Anbieter")

        # Anbieter-Auswahl (Radio)
        anbieter_frame = tk.Frame(t4, bg=BG_CARD)
        anbieter_frame.pack(fill="x", padx=20, pady=(4, 8))
        tk.Label(anbieter_frame, text="Anbieter:", bg=BG_CARD, fg=TEXT_LIGHT,
                 font=FONT_SMALL).pack(side="left", padx=(0, 12))
        self._ki_anbieter_var = tk.StringVar(value=self._cfg.get("ki_anbieter", "anthropic"))
        for val, lbl in [("anthropic", "Anthropic (Claude API)"), ("ollama", "Ollama (lokal)")]:
            tk.Radiobutton(anbieter_frame, text=lbl, variable=self._ki_anbieter_var, value=val,
                           bg=BG_CARD, fg=TEXT, font=FONT_BODY,
                           activebackground=BG_CARD, selectcolor=BG_CARD,
                           command=self._toggle_ki_provider).pack(side="left", padx=8)

        # Anthropic-Felder
        self._anthropic_frame = tk.Frame(t4, bg=BG_CARD)
        self._anthropic_frame.pack(fill="x")
        self._section(self._anthropic_frame, "Anthropic API")
        tk.Label(self._anthropic_frame, text="API-Key unter https://console.anthropic.com/keys",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w", padx=20, pady=(0,4))
        self._path_field(self._anthropic_frame, "Anthropic API-Key (sk-ant-…)", "anthropic_api_key", is_path=False)
        self._path_field(self._anthropic_frame, "Modell (Standard: claude-opus-4-6)", "ki_modell", is_path=False)

        # Ollama-Felder
        self._ollama_frame = tk.Frame(t4, bg=BG_CARD)
        self._ollama_frame.pack(fill="x")
        self._section(self._ollama_frame, "Ollama (lokales LLM)")
        tk.Label(self._ollama_frame, text="Ollama muss lokal installiert und gestartet sein (https://ollama.com)",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w", padx=20, pady=(0,4))
        self._path_field(self._ollama_frame, "Ollama Server-URL", "ollama_url", is_path=False)
        self._path_field(self._ollama_frame, "Ollama Modell (z.B. llama3.2)", "ollama_modell", is_path=False)

        # Hinweis: Zugriffsrechte werden unter Rollen & Rechte verwaltet (#34)
        self._section(t4, "Zugriffsverwaltung")
        tk.Label(t4,
                 text="Die Zugriffsrechte für KI-Assistent und KI-Administration werden\n"
                      "unter  🔐 Rollen & Rechte  verwaltet – nicht hier.",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL,
                 justify="left").pack(anchor="w", padx=20, pady=(0,8))

        # Provider-Sichtbarkeit initial setzen
        self._toggle_ki_provider()

    def _scrollable_tab(self, nb):
        """Erstellt einen scrollbaren Frame als Tab-Inhalt.
        Gibt (outer, inner) zurück: outer wird dem Notebook hinzugefügt,
        inner ist der scrollbare Inhaltsbereich für Widgets."""
        outer = tk.Frame(nb, bg=BG_CARD)
        canvas = tk.Canvas(outer, bg=BG_CARD, highlightthickness=0)
        vsb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        inner = tk.Frame(canvas, bg=BG_CARD)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))
        return outer, inner  # outer → nb.add(), inner → widget parent

    def _toggle_ki_provider(self):
        """Zeigt/versteckt Anthropic- vs. Ollama-Felder je nach gewähltem Anbieter."""
        anbieter = self._ki_anbieter_var.get()
        if anbieter == "anthropic":
            self._anthropic_frame.pack(fill="x")
            self._ollama_frame.pack_forget()
        else:
            self._anthropic_frame.pack_forget()
            self._ollama_frame.pack(fill="x")

    def _section(self, parent, title):
        tk.Label(parent, text=title, bg=BG_CARD, fg=TEXT, font=FONT_H3).pack(
            anchor="w", padx=20, pady=(16,4))
        tk.Frame(parent, bg=BG_INPUT, height=1).pack(fill="x", padx=20, pady=(0,4))

    def _iban_field(self, parent, label, key):
        """IBAN-Feld mit automatischer Formatierung (#### #### #### ...).
        Gespeichert wird ohne Leerzeichen, angezeigt mit Leerzeichen alle 4 Stellen."""
        tk.Label(parent, text=label, bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(
            anchor="w", padx=20, pady=(6,1))
        row = tk.Frame(parent, bg=BG_CARD)
        row.pack(fill="x", padx=20, pady=(0,2))
        # Intern ohne Leerzeichen speichern, anzeigen mit Leerzeichen
        raw_value = self._cfg.get(key, "").replace(" ", "")
        display_value = " ".join([raw_value[i:i+4] for i in range(0, len(raw_value), 4)]) if raw_value else ""
        var = tk.StringVar(value=display_value)
        self._vars[key] = var
        entry = make_entry(row, textvariable=var)
        entry.pack(side="left", fill="x", expand=True, ipady=6)
        # Auto-Format bei Tastendruck
        def _format_iban(*args):
            current = var.get().replace(" ", "").upper()
            formatted = " ".join([current[i:i+4] for i in range(0, len(current), 4)])
            if var.get() != formatted:
                entry.icursor(len(formatted))
                var.set(formatted)
        var.trace_add("write", _format_iban)

    def _path_field(self, parent, label, key, is_path=True, is_dir=True):
        tk.Label(parent, text=label, bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(
            anchor="w", padx=20, pady=(6,1))
        row = tk.Frame(parent, bg=BG_CARD)
        row.pack(fill="x", padx=20, pady=(0,2))
        var = tk.StringVar(value=self._cfg.get(key, ""))
        self._vars[key] = var
        entry = make_entry(row, textvariable=var)
        entry.pack(side="left", fill="x", expand=True, ipady=6)
        if is_path:
            def browse(v=var, d=is_dir):
                if d:
                    p = filedialog.askdirectory(title=f"{label} wählen")
                else:
                    p = filedialog.askopenfilename(title=f"{label} wählen",
                        filetypes=[("Datenbankdatei", "*.db"), ("Alle", "*.*")])
                if p: v.set(p)
            make_btn(row, "…", browse, color=BG_INPUT, fg=TEXT).pack(side="left", padx=(4,0))

    def _save(self):
        iban_keys = {"iban_wohngeld", "iban_ruecklage"}
        for key, var in self._vars.items():
            val = var.get()
            # IBAN ohne Leerzeichen speichern
            if key in iban_keys:
                val = val.replace(" ", "")
            self._cfg[key] = val
        # KI-Anbieter-Auswahl speichern
        if hasattr(self, "_ki_anbieter_var"):
            self._cfg["ki_anbieter"] = self._ki_anbieter_var.get()
        save_config(self._cfg)
        # Verzeichnisse für Speicherpfade automatisch anlegen (#38)
        for pk, sd in [("pfad_kontoauszug_import", "Kontoauszüge"),
                       ("pfad_belege", "Belege"),
                       ("pfad_dokumente", "Dokumente"),
                       ("pfad_backup", "Backup")]:
            p = self._cfg.get(pk, "")
            if p:
                try: Path(p).mkdir(parents=True, exist_ok=True)
                except Exception: pass
        messagebox.showinfo("Gespeichert", "Einstellungen wurden gespeichert.\n" + str(CONFIG_PATH))

    def _db_backup(self):
        """#30 Backup erstellen: Datenbank in Backup-Ordner kopieren."""
        import shutil
        backup_ordner = self._vars.get("pfad_backup", tk.StringVar()).get().strip()
        if not backup_ordner:
            backup_ordner = str(Path.home())
            messagebox.showinfo("Backup-Ordner",
                "Kein Backup-Ordner konfiguriert. Backup wird im Home-Verzeichnis gespeichert.",
                parent=self)
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            ziel = os.path.join(backup_ordner, f"hausverwaltung_backup_{ts}.db")
            shutil.copy2(str(DB_PATH), ziel)
            messagebox.showinfo("Backup erstellt",
                f"Datenbank-Backup gespeichert:\n{ziel}", parent=self)
        except Exception as exc:
            messagebox.showerror("Backup-Fehler",
                f"Backup konnte nicht erstellt werden:\n{exc}", parent=self)

    def _db_restore(self):
        """#30 Wiederherstellen: Datenbank aus Backup-Datei ersetzen."""
        import shutil
        if not messagebox.askyesno(
            "⚠ Warnung",
            "Die aktuelle Datenbank wird durch die Backup-Datei ersetzt!\n"
            "Alle nicht gesicherten Änderungen gehen verloren.\n\n"
            "Fortfahren?", icon="warning", parent=self):
            return
        quelle = filedialog.askopenfilename(
            parent=self, title="Backup-Datei wählen",
            filetypes=[("Datenbank-Backup", "*.db"), ("Alle Dateien", "*.*")])
        if not quelle:
            return
        # Erst eigenes Backup anlegen
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            auto_backup = str(DB_PATH) + f".vor_restore_{ts}.bak"
            shutil.copy2(str(DB_PATH), auto_backup)
        except Exception:
            auto_backup = None
        try:
            shutil.copy2(quelle, str(DB_PATH))
            info = f"Datenbank erfolgreich wiederhergestellt aus:\n{quelle}"
            if auto_backup:
                info += f"\n\nAutomatisches Sicherheits-Backup der alten Datenbank:\n{auto_backup}"
            messagebox.showinfo("Wiederhergestellt", info, parent=self)
        except Exception as exc:
            messagebox.showerror("Fehler",
                f"Wiederherstellung fehlgeschlagen:\n{exc}", parent=self)

# ══════════════════════════════════════════════════════════════════════════════
# HAUPTANWENDUNG
# ══════════════════════════════════════════════════════════════════════════════

# ── Benutzerverwaltung-Seite ──────────────────────────────────────────────────

class BenutzerverwaltungPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_CARD)
        self._build()
    
    def _build(self):
        section_header(self, "Benutzerverwaltung", "＋ Benutzer", self._new)
        cols = ("Benutzername", "Rolle", "Aktiv", "PW-Skip", "Erstellt")
        f, self.tree = make_table(self, cols, height=12)
        f.pack(fill="both", expand=True, padx=20, pady=10)
        for c, w in zip(cols, [180, 140, 60, 70, 140]):
            self.tree.heading(c, text=c); self.tree.column(c, width=w, anchor="w")
        btn_row = tk.Frame(self, bg=BG_CARD)
        btn_row.pack(fill="x", padx=20, pady=(0,10))
        if hat_recht("Benutzer", "schreiben"):
            make_btn(btn_row, "✏ Bearbeiten", self._edit, color=BG_INPUT, fg=TEXT).pack(side="left", padx=(0,8))
            make_btn(btn_row, "🔑 Passwort ändern", self._change_pw, color=WARNING, fg=TEXT_WHITE).pack(side="left", padx=(0,8))
        if hat_recht("Benutzer", "loeschen"):
            make_btn(btn_row, "🗑 Löschen", self._delete, color=DANGER).pack(side="left")
        self._load()

    def _load(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = get_db()
        for row in conn.execute("SELECT b.*, COALESCE(ro.name, b.rolle) AS rolle_name FROM benutzer b LEFT JOIN rollen ro ON b.rolle_id=ro.id ORDER BY b.benutzername"):
            r = dict(row)
            self.tree.insert("", "end", iid=r["id"], values=(
                r["benutzername"], r.get("rolle_name") or "–",
                "✔" if r["aktiv"] else "✗",
                "✔" if r.get("passwort_skip") else "–",
                fmt_date(str(r["erstellt_am"])[:10] if r["erstellt_am"] else "")))
        conn.close()
        tree_empty_hint(self.tree)

    def _new(self):
        if not hat_recht("Benutzer", "schreiben"):
            messagebox.showwarning("Berechtigung", "Keine Schreibberechtigung.", parent=self); return
        d = BenutzerDialog(self)
        self.wait_window(d)
        if d.result:
            import hashlib
            v = d.result
            pw_hash = hashlib.sha256(v["passwort"].encode()).hexdigest()
            conn = get_db()
            try:
                conn.execute(
                    "INSERT INTO benutzer (benutzername, passwort_hash, rolle, rolle_id, passwort_skip) "
                    "VALUES (?,?,?,?,?)",
                    (v["benutzername"], pw_hash, v.get("rolle_name", "Benutzer"),
                     v.get("rolle_id"), v.get("passwort_skip", 0)))
                conn.commit()
            except Exception as e:
                messagebox.showerror("Fehler", f"Benutzername bereits vergeben.\n{e}")
            conn.close(); self._load()

    def _edit(self, event=None):
        if not hat_recht("Benutzer", "schreiben"):
            messagebox.showwarning("Berechtigung", "Keine Schreibberechtigung.", parent=self); return
        sel = self.tree.selection()
        if not sel: return
        conn = get_db()
        row = conn.execute("SELECT * FROM benutzer WHERE id=?", (int(sel[0]),)).fetchone()
        conn.close()
        d = BenutzerDialog(self, row)
        self.wait_window(d)
        if d.result:
            v = d.result
            conn = get_db()
            conn.execute(
                "UPDATE benutzer SET benutzername=?, rolle=?, rolle_id=?, aktiv=?, passwort_skip=? WHERE id=?",
                (v["benutzername"], v.get("rolle_name", "Benutzer"), v.get("rolle_id"),
                 v.get("aktiv", 1), v.get("passwort_skip", 0), int(sel[0])))
            conn.commit(); conn.close(); self._load()

    def _change_pw(self):
        if not hat_recht("Benutzer", "schreiben"):
            messagebox.showwarning("Berechtigung", "Keine Schreibberechtigung.", parent=self); return
        sel = self.tree.selection()
        if not sel: return
        # Dialog: Manuell eingeben oder automatisch generieren?
        choice = messagebox.askyesnocancel(
            "Passwort ändern",
            "Passwort automatisch generieren?\n\n"
            "Ja = Automatisch generieren\n"
            "Nein = Manuell eingeben\n"
            "Abbrechen = Abbrechen")
        if choice is None:
            return
        import hashlib
        if choice:  # Automatisch generieren
            import secrets, string
            chars = string.ascii_letters + string.digits + "!@#$%"
            new_pw = ''.join(secrets.choice(chars) for _ in range(12))
            messagebox.showinfo("Generiertes Passwort",
                                f"Das neue Passwort lautet:\n\n{new_pw}\n\n"
                                "Bitte notieren Sie es, da es nur jetzt sichtbar ist.",
                                parent=self)
        else:  # Manuell eingeben
            new_pw = simpledialog.askstring("Passwort ändern", "Neues Passwort:", show="●", parent=self)
            if not new_pw:
                return
        pw_hash = hashlib.sha256(new_pw.encode()).hexdigest()
        conn = get_db()
        conn.execute("UPDATE benutzer SET passwort_hash=? WHERE id=?", (pw_hash, int(sel[0])))
        conn.commit(); conn.close()
        messagebox.showinfo("Gespeichert", "Passwort wurde geändert.")

    def _delete(self):
        if not hat_recht("Benutzer", "loeschen"):
            messagebox.showwarning("Berechtigung", "Keine Löschberechtigung.", parent=self); return
        sel = self.tree.selection()
        if not sel: return
        uid = int(sel[0])
        # Superadmin-Schutz
        conn = get_db()
        user = conn.execute("SELECT b.*, r.ist_superadmin FROM benutzer b LEFT JOIN rollen r ON b.rolle_id=r.id WHERE b.id=?", (uid,)).fetchone()
        conn.close()
        if user and user["ist_superadmin"]:
            messagebox.showinfo("Gesperrt", "Superadmin-Benutzer können nicht gelöscht werden.", parent=self)
            return
        if messagebox.askyesno("Löschen", "Benutzer löschen?"):
            conn = get_db()
            conn.execute("DELETE FROM benutzer WHERE id=?", (uid,))
            conn.commit(); conn.close(); self._load()


class BenutzerDialog(BaseDialog):
    def __init__(self, parent, row=None):
        super().__init__(parent, "Benutzer " + ("bearbeiten" if row else "hinzufügen"), 420, 480)
        r = dict(row) if row else {}
        self._is_edit = bool(row)
        self._add_field("Benutzername *", "benutzername", r.get("benutzername",""))
        # Rollen aus DB laden
        conn = get_db()
        rollen = conn.execute("SELECT id, name FROM rollen WHERE aktiv=1 ORDER BY name").fetchall()
        conn.close()
        self._rollen_map = {ro["name"]: ro["id"] for ro in rollen}
        rollen_namen = [ro["name"] for ro in rollen]
        # Aktuelle Rolle des Benutzers ermitteln
        current_rolle = ""
        if r.get("rolle_id"):
            for ro in rollen:
                if ro["id"] == r["rolle_id"]:
                    current_rolle = ro["name"]
                    break
        if not current_rolle and rollen_namen:
            current_rolle = rollen_namen[0]
        self._add_field("Rolle", "rolle_name", current_rolle,
                        widget_type="combo", options=rollen_namen)
        if not row:
            # Neuer Benutzer: Passwort-Feld + Generieren-Button
            pw_frame = tk.Frame(self._body, bg=BG_CARD)
            pw_frame.pack(fill="x", padx=20, pady=(6, 0))
            tk.Label(pw_frame, text="Passwort *", bg=BG_CARD, fg=TEXT_LIGHT,
                     font=FONT_SMALL).pack(anchor="w")
            pw_row = tk.Frame(pw_frame, bg=BG_CARD)
            pw_row.pack(fill="x")
            self._pw_var = tk.StringVar(value="")
            pw_entry = tk.Entry(pw_row, textvariable=self._pw_var, font=FONT_BODY,
                                bg=BG_INPUT, fg=TEXT, relief="flat", show="●")
            pw_entry.pack(side="left", fill="x", expand=True, ipady=5)
            make_btn(pw_row, "🎲 Generieren", self._generate_pw,
                     color=ACCENT2).pack(side="right", padx=(6, 0))
            self._fields["passwort"] = self._pw_var
        else:
            self._fields["passwort"] = tk.StringVar(value="(unverändert)")
        # Passwortabfrage abschaltbar
        self._pw_skip_var = tk.IntVar(value=int(r.get("passwort_skip", 0)))
        tk.Checkbutton(self._body, text="Passwortabfrage beim Login überspringen",
                       variable=self._pw_skip_var,
                       bg=BG_CARD, fg=TEXT, font=FONT_BODY,
                       activebackground=BG_CARD, selectcolor=BG_INPUT).pack(anchor="w", padx=20, pady=(8, 0))
        # Aktiv-Checkbox (nur bei Bearbeiten)
        if row:
            self._aktiv_var = tk.IntVar(value=int(r.get("aktiv", 1)))
            tk.Checkbutton(self._body, text="Aktiv", variable=self._aktiv_var,
                           bg=BG_CARD, fg=TEXT, font=FONT_BODY,
                           activebackground=BG_CARD, selectcolor=BG_INPUT).pack(anchor="w", padx=20, pady=(8, 0))

    def _generate_pw(self):
        """Generiert ein zufälliges 12-Zeichen-Passwort."""
        import secrets, string
        chars = string.ascii_letters + string.digits + "!@#$%"
        pw = ''.join(secrets.choice(chars) for _ in range(12))
        self._pw_var.set(pw)
        # Kurz anzeigen
        messagebox.showinfo("Generiertes Passwort",
                            f"Das generierte Passwort lautet:\n\n{pw}\n\n"
                            "Bitte notieren Sie es, da es nur jetzt sichtbar ist.",
                            parent=self)

    def _on_save(self):
        v = self._get_values()
        if not v.get("benutzername"):
            messagebox.showwarning("Pflichtfeld", "Benutzername ist erforderlich.", parent=self); return
        # Passwort bei neuem Benutzer prüfen
        if not self._is_edit and not self._pw_var.get():
            messagebox.showwarning("Pflichtfeld", "Passwort ist erforderlich.", parent=self); return
        v["passwort"] = self._pw_var.get() if hasattr(self, "_pw_var") else "(unverändert)"
        # rolle_id aus Map
        rolle_name = v.get("rolle_name", "")
        v["rolle_id"] = self._rollen_map.get(rolle_name)
        v["passwort_skip"] = self._pw_skip_var.get()
        if hasattr(self, "_aktiv_var"):
            v["aktiv"] = self._aktiv_var.get()
        self.result = v; self.destroy()

# ── Rollenverwaltung-Seite ────────────────────────────────────────────────────

class RollenverwaltungPage(tk.Frame):
    """Rollen & Rechte verwalten: CRUD für Rollen, Berechtigungsmatrix pro Rolle."""

    BEREICHE = ["Übersicht", "Eigentümer", "Wohnungen", "Mieter", "Kontoauszug",
                "Buchhaltung", "Wartung", "Nebenkosten", "Aufteilungen",
                "Nachrichten", "Dokumente", "Benutzer", "Rollen & Rechte",
                "Einstellungen", "KI-Assistent", "KI-Administration", "Ista-Wärme"]

    def __init__(self, parent):
        super().__init__(parent, bg=BG_CARD)
        self._build()

    def _build(self):
        section_header(self, "Rollen & Rechte", "＋ Rolle", self._new)

        main = tk.Frame(self, bg=BG_CARD)
        main.pack(fill="both", expand=True, padx=20, pady=8)
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=3)

        # ── Linke Spalte: Rollenliste ────────────────────────────────
        left = tk.Frame(main, bg=BG_CARD)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        tk.Label(left, text="Rollen", bg=BG_CARD, fg=TEXT, font=FONT_H3).pack(anchor="w", pady=(0, 6))
        cols_r = ("Name", "Status")
        fr, self.tree_rollen = make_table(left, cols_r, height=10)
        fr.pack(fill="both", expand=True)
        self.tree_rollen.heading("Name", text="Name")
        self.tree_rollen.heading("Status", text="Status")
        self.tree_rollen.column("Name", width=140, anchor="w")
        self.tree_rollen.column("Status", width=60, anchor="center")
        self.tree_rollen.bind("<<TreeviewSelect>>", self._on_rolle_select)

        btn_r = tk.Frame(left, bg=BG_CARD)
        btn_r.pack(fill="x", pady=(6, 0))
        make_btn(btn_r, "✏ Bearbeiten", self._edit_rolle, color=BG_INPUT, fg=TEXT).pack(side="left", padx=(0, 4))
        make_btn(btn_r, "🔒 Deaktivieren", self._toggle_aktiv, color=WARNING, fg=TEXT_WHITE).pack(side="left", padx=(0, 4))
        make_btn(btn_r, "🗑 Löschen", self._delete_rolle, color=DANGER).pack(side="left")

        # ── Rechte Spalte: Berechtigungsmatrix ───────────────────────
        right = tk.Frame(main, bg=BG_CARD)
        right.grid(row=0, column=1, sticky="nsew")

        tk.Label(right, text="Berechtigungen", bg=BG_CARD, fg=TEXT, font=FONT_H3).pack(anchor="w", pady=(0, 6))
        self._rechte_info = tk.Label(right, text="← Rolle auswählen", bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL)
        self._rechte_info.pack(anchor="w")

        # Berechtigungsmatrix als Grid
        self._matrix_frame = tk.Frame(right, bg=BG_CARD)
        self._matrix_frame.pack(fill="both", expand=True, pady=(6, 0))

        # Zusätzliche Rollen-Optionen
        self._opts_frame = tk.Frame(right, bg=BG_CARD)
        self._opts_frame.pack(fill="x", pady=(6, 0))
        self._rolle_pw_skip_var = tk.IntVar(value=0)
        self._pw_skip_cb = tk.Checkbutton(self._opts_frame,
            text="Passwortabfrage für alle Benutzer dieser Rolle überspringen",
            variable=self._rolle_pw_skip_var, bg=BG_CARD, fg=TEXT, font=FONT_BODY,
            activebackground=BG_CARD, selectcolor=BG_INPUT,
            command=self._save_rolle_pw_skip)
        self._pw_skip_cb.pack(anchor="w")

        self._checks = {}  # {(bereich, aktion): IntVar}
        self._selected_rolle_id = None

        self._load_rollen()

    def _load_rollen(self):
        for i in self.tree_rollen.get_children():
            self.tree_rollen.delete(i)
        conn = get_db()
        for r in conn.execute("SELECT * FROM rollen ORDER BY ist_superadmin DESC, name"):
            status = "🔑 Super" if r["ist_superadmin"] else ("✔ Aktiv" if r["aktiv"] else "✗ Inaktiv")
            self.tree_rollen.insert("", "end", iid=r["id"], values=(r["name"], status))
        conn.close()

    def _on_rolle_select(self, event=None):
        sel = self.tree_rollen.selection()
        if not sel:
            return
        self._selected_rolle_id = int(sel[0])
        conn = get_db()
        rolle = conn.execute("SELECT * FROM rollen WHERE id=?", (self._selected_rolle_id,)).fetchone()
        conn.close()
        if not rolle:
            return
        rd = dict(rolle)
        self._rechte_info.config(text=f"Berechtigungen für: {rd['name']}"
                                      + (" (Superadmin – alle Rechte)" if rd["ist_superadmin"] else ""))
        self._rolle_pw_skip_var.set(int(rd.get("passwort_skip", 0)))
        self._build_matrix(rolle)

    def _build_matrix(self, rolle):
        for w in self._matrix_frame.winfo_children():
            w.destroy()
        self._checks = {}

        is_super = bool(rolle["ist_superadmin"])
        rolle_id = rolle["id"]

        # Rechte aus DB laden
        conn = get_db()
        rechte_rows = conn.execute("SELECT * FROM rechte WHERE rolle_id=?", (rolle_id,)).fetchall()
        conn.close()
        rechte_map = {}
        for r in rechte_rows:
            rechte_map[r["bereich"]] = {"lesen": r["lesen"], "schreiben": r["schreiben"], "loeschen": r["loeschen"]}

        # Header
        header = tk.Frame(self._matrix_frame, bg=BG_INPUT)
        header.pack(fill="x", pady=(0, 2))
        tk.Label(header, text="Bereich", bg=BG_INPUT, fg=TEXT, font=("Segoe UI Semibold", 9), width=18, anchor="w").pack(side="left", padx=4)
        for a in ("Lesen", "Schreiben", "Löschen"):
            tk.Label(header, text=a, bg=BG_INPUT, fg=TEXT, font=("Segoe UI Semibold", 9), width=10, anchor="center").pack(side="left")

        # Scrollbar
        canvas = tk.Canvas(self._matrix_frame, bg=BG_CARD, highlightthickness=0)
        vsb = ttk.Scrollbar(self._matrix_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=BG_CARD)
        canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        for bereich in self.BEREICHE:
            row_f = tk.Frame(inner, bg=BG_CARD)
            row_f.pack(fill="x", pady=1)
            tk.Label(row_f, text=bereich, bg=BG_CARD, fg=TEXT, font=FONT_SMALL, width=18, anchor="w").pack(side="left", padx=4)
            r = rechte_map.get(bereich, {"lesen": 0, "schreiben": 0, "loeschen": 0})
            for aktion in ("lesen", "schreiben", "loeschen"):
                var = tk.IntVar(value=1 if is_super else int(r.get(aktion, 0)))
                cb = tk.Checkbutton(row_f, variable=var, bg=BG_CARD,
                                    activebackground=BG_CARD, selectcolor=BG_INPUT,
                                    state="disabled" if is_super else "normal",
                                    command=self._save_rechte)
                cb.pack(side="left", padx=26)
                self._checks[(bereich, aktion)] = var

    def _save_rechte(self):
        if not self._selected_rolle_id:
            return
        conn = get_db()
        # Superadmin check
        rolle = conn.execute("SELECT * FROM rollen WHERE id=?", (self._selected_rolle_id,)).fetchone()
        if rolle and rolle["ist_superadmin"]:
            conn.close()
            return
        # Delete old and insert new
        conn.execute("DELETE FROM rechte WHERE rolle_id=?", (self._selected_rolle_id,))
        for bereich in self.BEREICHE:
            l = self._checks.get((bereich, "lesen"), tk.IntVar(value=0)).get()
            s = self._checks.get((bereich, "schreiben"), tk.IntVar(value=0)).get()
            d = self._checks.get((bereich, "loeschen"), tk.IntVar(value=0)).get()
            conn.execute("INSERT INTO rechte (rolle_id, bereich, lesen, schreiben, loeschen) VALUES (?,?,?,?,?)",
                         (self._selected_rolle_id, bereich, l, s, d))
        conn.commit()
        conn.close()

    def _save_rolle_pw_skip(self):
        """Passwort-Skip für die ausgewählte Rolle speichern."""
        if not self._selected_rolle_id:
            return
        conn = get_db()
        conn.execute("UPDATE rollen SET passwort_skip=? WHERE id=?",
                     (self._rolle_pw_skip_var.get(), self._selected_rolle_id))
        conn.commit()
        conn.close()

    def _new(self):
        if not hat_recht("Rollen & Rechte", "schreiben"):
            messagebox.showwarning("Berechtigung", "Keine Berechtigung.", parent=self)
            return
        name = simpledialog.askstring("Neue Rolle", "Rollenname:", parent=self)
        if not name:
            return
        beschreibung = simpledialog.askstring("Neue Rolle", "Beschreibung (optional):", parent=self) or ""
        conn = get_db()
        try:
            conn.execute("INSERT INTO rollen (name, beschreibung) VALUES (?,?)", (name, beschreibung))
            rolle_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            # Default: alles Lesen, kein Schreiben/Löschen
            for b in self.BEREICHE:
                conn.execute("INSERT INTO rechte (rolle_id, bereich, lesen, schreiben, loeschen) VALUES (?,?,1,0,0)",
                             (rolle_id, b))
            conn.commit()
        except Exception as e:
            messagebox.showerror("Fehler", f"Rolle konnte nicht erstellt werden:\n{e}", parent=self)
        conn.close()
        self._load_rollen()

    def _edit_rolle(self, event=None):
        sel = self.tree_rollen.selection()
        if not sel:
            return
        if not hat_recht("Rollen & Rechte", "schreiben"):
            messagebox.showwarning("Berechtigung", "Keine Berechtigung.", parent=self)
            return
        rid = int(sel[0])
        conn = get_db()
        rolle = conn.execute("SELECT * FROM rollen WHERE id=?", (rid,)).fetchone()
        conn.close()
        if not rolle:
            return
        if rolle["ist_superadmin"]:
            messagebox.showinfo("Gesperrt", "Die Superadmin-Rolle kann nicht bearbeitet werden.", parent=self)
            return
        name = simpledialog.askstring("Rolle bearbeiten", "Rollenname:", initialvalue=rolle["name"], parent=self)
        if not name:
            return
        beschreibung = simpledialog.askstring("Rolle bearbeiten", "Beschreibung:",
                                              initialvalue=rolle["beschreibung"] or "", parent=self) or ""
        conn = get_db()
        conn.execute("UPDATE rollen SET name=?, beschreibung=? WHERE id=?", (name, beschreibung, rid))
        conn.commit()
        conn.close()
        self._load_rollen()

    def _toggle_aktiv(self):
        sel = self.tree_rollen.selection()
        if not sel:
            return
        if not hat_recht("Rollen & Rechte", "schreiben"):
            messagebox.showwarning("Berechtigung", "Keine Berechtigung.", parent=self)
            return
        rid = int(sel[0])
        conn = get_db()
        rolle = conn.execute("SELECT * FROM rollen WHERE id=?", (rid,)).fetchone()
        if rolle and rolle["ist_superadmin"]:
            messagebox.showinfo("Gesperrt", "Die Superadmin-Rolle kann nicht deaktiviert werden.", parent=self)
            conn.close()
            return
        new_val = 0 if rolle["aktiv"] else 1
        conn.execute("UPDATE rollen SET aktiv=? WHERE id=?", (new_val, rid))
        conn.commit()
        conn.close()
        self._load_rollen()

    def _delete_rolle(self):
        sel = self.tree_rollen.selection()
        if not sel:
            return
        if not hat_recht("Rollen & Rechte", "loeschen"):
            messagebox.showwarning("Berechtigung", "Keine Löschberechtigung.", parent=self)
            return
        rid = int(sel[0])
        conn = get_db()
        rolle = conn.execute("SELECT * FROM rollen WHERE id=?", (rid,)).fetchone()
        if rolle and rolle["ist_superadmin"]:
            messagebox.showinfo("Gesperrt", "Die Superadmin-Rolle kann nicht gelöscht werden.", parent=self)
            conn.close()
            return
        # Check if any users have this role
        users_count = conn.execute("SELECT COUNT(*) FROM benutzer WHERE rolle_id=?", (rid,)).fetchone()[0]
        conn.close()
        if users_count > 0:
            messagebox.showwarning("Nicht möglich",
                                   f"Es gibt noch {users_count} Benutzer mit dieser Rolle.\n"
                                   "Bitte zuerst die Benutzer einer anderen Rolle zuweisen.",
                                   parent=self)
            return
        if messagebox.askyesno("Löschen", f"Rolle '{rolle['name']}' wirklich löschen?", parent=self):
            conn = get_db()
            conn.execute("DELETE FROM rechte WHERE rolle_id=?", (rid,))
            conn.execute("DELETE FROM rollen WHERE id=?", (rid,))
            conn.commit()
            conn.close()
            self._selected_rolle_id = None
            self._load_rollen()
            for w in self._matrix_frame.winfo_children():
                w.destroy()
            self._rechte_info.config(text="← Rolle auswählen")


# ── Login-Dialog ──────────────────────────────────────────────────────────────

class LoginDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Hausverwaltung – Anmelden")
        self.geometry("360x240")
        self.configure(bg=BG_CARD)
        self.resizable(False, False)
        self.grab_set()
        self.result = None
        
        hdr = tk.Frame(self, bg=BG_SIDEBAR, height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="⌂  Hausverwaltung", bg=BG_SIDEBAR, fg=TEXT_WHITE, font=FONT_H3).pack(side="left", padx=16, pady=14)
        
        body = tk.Frame(self, bg=BG_CARD)
        body.pack(fill="both", expand=True, padx=24, pady=16)
        
        tk.Label(body, text="Benutzername", bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w")
        self._user_var = tk.StringVar(value="admin")
        user_e = make_entry(body, textvariable=self._user_var)
        user_e.pack(fill="x", ipady=6)
        
        tk.Label(body, text="Passwort", bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w", pady=(8,0))
        self._pw_var = tk.StringVar()
        pw_e = make_entry(body, textvariable=self._pw_var, show="●")
        pw_e.pack(fill="x", ipady=6)
        pw_e.bind("<Return>", lambda e: self._login())
        
        make_btn(body, "Anmelden", self._login).pack(fill="x", pady=(12,0))
        user_e.focus_set()
        
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 360) // 2
        y = (self.winfo_screenheight() - 240) // 2
        self.geometry(f"360x240+{x}+{y}")
    
    def _login(self):
        import hashlib
        username = self._user_var.get().strip()
        password = self._pw_var.get()
        conn = get_db()
        # Prüfe ob Benutzer Passwortabfrage überspringt
        user_check = conn.execute(
            "SELECT b.*, r.passwort_skip AS rolle_pw_skip "
            "FROM benutzer b LEFT JOIN rollen r ON b.rolle_id=r.id "
            "WHERE b.benutzername=? AND b.aktiv=1",
            (username,)).fetchone()
        if user_check:
            u = dict(user_check)
            # Passwortabfrage überspringen: entweder pro Benutzer oder pro Rolle
            if u.get("passwort_skip") or u.get("rolle_pw_skip"):
                conn.close()
                self.result = u
                self.destroy()
                return
        # Normaler Passwort-Login
        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        user = conn.execute(
            "SELECT * FROM benutzer WHERE benutzername=? AND passwort_hash=? AND aktiv=1",
            (username, pw_hash)
        ).fetchone()
        conn.close()
        if user:
            self.result = dict(user)
            self.destroy()
        else:
            messagebox.showerror("Fehler", "Benutzername oder Passwort falsch.", parent=self)
            self._pw_var.set("")

# ── Ista-Wärmeabrechnung ───────────────────────────────────────────────────────

class IstaPage(tk.Frame):
    """Ista-Wärmeabrechnung: Import von Ista-PDFs, Zuordnung zu Wohnungen,
    Übernahme in Buchhaltung und Nebenkosten. Unterstützt die Heizkostenverordnung (HeizKV)."""

    def __init__(self, parent):
        super().__init__(parent, bg=BG_CARD)
        if not hat_recht("Ista-Wärme", "lesen"):
            tk.Label(self, text="🔒 Kein Zugriff auf Ista-Wärme.\nBitte Administrator kontaktieren.",
                     bg=BG_CARD, fg=DANGER, font=FONT_H2).pack(expand=True)
            return
        self._build()

    def _build(self):
        # Header
        section_header(self, "🔥 Ista-Wärmeabrechnung",
                        "📥 Ista-PDF importieren", self._import_pdf)

        # Info-Banner
        info = tk.Frame(self, bg="#EBF5FB", bd=0)
        info.pack(fill="x", padx=20, pady=(8, 4))
        tk.Label(info,
                 text="ℹ  Ista liefert Heizkostenabrechnungen als PDF. "
                      "Importieren Sie das PDF und ordnen Sie die Wohnungseinheiten zu. "
                      "Die Kosten werden automatisch in die Nebenkosten-Abrechnung übernommen.",
                 bg="#EBF5FB", fg="#1A5276", font=FONT_SMALL,
                 wraplength=900, justify="left").pack(padx=12, pady=8, anchor="w")

        # Tabs
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=20, pady=8)

        t1 = ttk.Frame(nb); nb.add(t1, text="📋 Abrechnungen")
        t2 = ttk.Frame(nb); nb.add(t2, text="🏠 Positionen & Zuordnung")
        t3 = ttk.Frame(nb); nb.add(t3, text="💰 Übernahme in Buchhaltung")
        t4 = ttk.Frame(nb); nb.add(t4, text="📖 Ista-Leitfaden")

        self._build_tab_abrechnungen(t1)
        self._build_tab_positionen(t2)
        self._build_tab_uebernahme(t3)
        self._build_tab_leitfaden(t4)

    # ── Tab 1: Abrechnungs-Übersicht ──────────────────────────────────────────

    def _build_tab_abrechnungen(self, parent):
        ctrl = tk.Frame(parent, bg=BG_CARD)
        ctrl.pack(fill="x", padx=0, pady=(8, 4))
        make_btn(ctrl, "📥 Ista-PDF importieren", self._import_pdf).pack(side="left", padx=(8, 6))
        make_btn(ctrl, "🗑 Löschen", self._delete_abrechnung, color=DANGER).pack(side="left")
        make_btn(ctrl, "🔄 Aktualisieren", self._load_abrechnungen, color=BG_INPUT, fg=TEXT).pack(side="right", padx=8)

        frame, self._tree_abr = make_table(parent,
            ("Jahr", "Zeitraum", "Heizkosten", "Warmwasser", "Gesamt", "Einheiten", "Objekt"))
        for col, w in [("Jahr", 55), ("Zeitraum", 140), ("Heizkosten", 100),
                        ("Warmwasser", 100), ("Gesamt", 100), ("Einheiten", 70), ("Objekt", 200)]:
            self._tree_abr.column(col, width=w, anchor="e" if col in ("Heizkosten","Warmwasser","Gesamt","Einheiten") else "w")
            self._tree_abr.heading(col, text=col)
        frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self._tree_abr.bind("<<TreeviewSelect>>", lambda e: self._load_positionen())

        self._load_abrechnungen()

    def _load_abrechnungen(self):
        for i in self._tree_abr.get_children():
            self._tree_abr.delete(i)
        conn = get_db()
        try:
            rows = conn.execute(
                "SELECT a.*, COUNT(p.id) as n_pos FROM ista_abrechnungen a "
                "LEFT JOIN ista_positionen p ON p.abrechnung_id=a.id "
                "GROUP BY a.id ORDER BY a.abrechnungsjahr DESC, a.import_datum DESC"
            ).fetchall()
        finally:
            conn.close()
        for r in rows:
            zeitraum = ""
            if r["abrechnungszeitraum_von"] and r["abrechnungszeitraum_bis"]:
                zeitraum = f"{fmt_date(r['abrechnungszeitraum_von'])} – {fmt_date(r['abrechnungszeitraum_bis'])}"
            self._tree_abr.insert("", "end", iid=str(r["id"]), values=(
                r["abrechnungsjahr"] or "–",
                zeitraum or "–",
                fmt_euro(r["gesamtkosten_heizung"] or 0),
                fmt_euro(r["gesamtkosten_warmwasser"] or 0),
                fmt_euro(r["gesamtkosten_gesamt"] or 0),
                str(r["n_pos"]),
                r["objekt_adresse"] or "–",
            ))
        tree_empty_hint(self._tree_abr, "(Keine Ista-Abrechnungen – PDF importieren)")

    # ── Tab 2: Positionen & Wohnungs-Zuordnung ────────────────────────────────

    def _build_tab_positionen(self, parent):
        ctrl = tk.Frame(parent, bg=BG_CARD)
        ctrl.pack(fill="x", padx=8, pady=(8, 4))
        tk.Label(ctrl, text="Wohnung zuordnen:", bg=BG_CARD, fg=TEXT, font=FONT_BODY).pack(side="left")
        self._zuordnung_wohnung_var = tk.StringVar()
        self._zuordnung_combo = ttk.Combobox(ctrl, textvariable=self._zuordnung_wohnung_var,
                                              state="readonly", width=30)
        self._zuordnung_combo.pack(side="left", padx=6)
        make_btn(ctrl, "✅ Zuordnung speichern", self._save_zuordnung).pack(side="left", padx=4)
        make_btn(ctrl, "🤖 Auto-Zuordnung", self._auto_zuordnung, color=ACCENT).pack(side="left", padx=4)

        # Erklärung
        tk.Label(parent,
                 text="Wählen Sie links eine Abrechnung → rechts erscheinen die Ista-Einheiten. "
                      "Klicken Sie auf eine Einheit und ordnen Sie rechts die Wohnung zu.",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w", padx=8)

        frame, self._tree_pos = make_table(parent,
            ("Ista-Einheit", "Mieter (Ista)", "Zugeordnete Wohnung",
             "Heizkosten", "Warmwasser", "Gesamt", "Vorauszahlung", "Saldo"))
        for col, w in [
            ("Ista-Einheit", 120), ("Mieter (Ista)", 160), ("Zugeordnete Wohnung", 150),
            ("Heizkosten", 90), ("Warmwasser", 90), ("Gesamt", 90),
            ("Vorauszahlung", 100), ("Saldo", 90)
        ]:
            self._tree_pos.column(col, width=w,
                anchor="e" if col in ("Heizkosten","Warmwasser","Gesamt","Vorauszahlung","Saldo") else "w")
            self._tree_pos.heading(col, text=col)
        frame.pack(fill="both", expand=True, padx=8, pady=(4, 8))
        self._tree_pos.bind("<<TreeviewSelect>>", self._on_pos_select)

        # Wohnungs-Combo befüllen
        self._refresh_wohnungen_combo()

    def _refresh_wohnungen_combo(self):
        conn = get_db()
        try:
            wohnungen = conn.execute(
                "SELECT id, bezeichnung FROM wohnungen ORDER BY bezeichnung"
            ).fetchall()
        finally:
            conn.close()
        self._wohnungen_map = {w["bezeichnung"]: w["id"] for w in wohnungen}
        self._wohnungen_map_r = {w["id"]: w["bezeichnung"] for w in wohnungen}
        werte = ["(keine Zuordnung)"] + [w["bezeichnung"] for w in wohnungen]
        self._zuordnung_combo["values"] = werte

    def _load_positionen(self):
        for i in self._tree_pos.get_children():
            self._tree_pos.delete(i)
        sel = self._tree_abr.selection()
        if not sel:
            return
        abr_id = int(sel[0])
        conn = get_db()
        try:
            rows = conn.execute(
                "SELECT p.*, w.bezeichnung as wohnung_bez "
                "FROM ista_positionen p "
                "LEFT JOIN wohnungen w ON w.id=p.wohnung_id "
                "WHERE p.abrechnung_id=? ORDER BY p.ista_einheit_nr",
                (abr_id,)
            ).fetchall()
        finally:
            conn.close()
        for r in rows:
            saldo = (r["nachzahlung_guthaben"] or 0)
            tag = "plus" if saldo >= 0 else "minus"
            self._tree_pos.insert("", "end", iid=str(r["id"]), values=(
                r["ista_einheit_nr"] or r["ista_einheit_bezeichnung"] or "–",
                r["mieter_name"] or "–",
                r["wohnung_bez"] or "⚠ nicht zugeordnet",
                fmt_euro(r["heizkosten_gesamt"] or 0),
                fmt_euro(r["warmwasserkosten_gesamt"] or 0),
                fmt_euro(r["gesamtkosten"] or 0),
                fmt_euro(r["vorauszahlung"] or 0),
                fmt_euro(saldo),
            ), tags=(tag,))
        self._tree_pos.tag_configure("plus",  foreground=SUCCESS)
        self._tree_pos.tag_configure("minus", foreground=DANGER)
        tree_empty_hint(self._tree_pos)

    def _on_pos_select(self, event=None):
        sel = self._tree_pos.selection()
        if not sel:
            return
        pos_id = int(sel[0])
        conn = get_db()
        try:
            p = conn.execute("SELECT wohnung_id FROM ista_positionen WHERE id=?", (pos_id,)).fetchone()
        finally:
            conn.close()
        if p and p["wohnung_id"]:
            bez = self._wohnungen_map_r.get(p["wohnung_id"], "")
            self._zuordnung_wohnung_var.set(bez)
        else:
            self._zuordnung_wohnung_var.set("(keine Zuordnung)")

    def _save_zuordnung(self):
        if not hat_recht("Ista-Wärme", "schreiben"):
            messagebox.showwarning("Berechtigung", "Keine Schreibberechtigung.", parent=self); return
        sel = self._tree_pos.selection()
        if not sel:
            messagebox.showinfo("Hinweis", "Bitte zuerst eine Ista-Position auswählen.", parent=self); return
        pos_id = int(sel[0])
        bez = self._zuordnung_wohnung_var.get()
        wohnung_id = self._wohnungen_map.get(bez) if bez != "(keine Zuordnung)" else None
        conn = get_db()
        try:
            conn.execute("UPDATE ista_positionen SET wohnung_id=? WHERE id=?", (wohnung_id, pos_id))
            conn.commit()
        finally:
            conn.close()
        self._load_positionen()
        messagebox.showinfo("Gespeichert", f"Wohnung '{bez}' zugeordnet.", parent=self)

    def _auto_zuordnung(self):
        """Versucht automatische Zuordnung nach ähnlichem Namen."""
        sel = self._tree_abr.selection()
        if not sel:
            messagebox.showinfo("Hinweis", "Bitte zuerst eine Abrechnung auswählen.", parent=self)
            return
        abr_id = int(sel[0])
        conn = get_db()
        try:
            positionen = conn.execute(
                "SELECT id, ista_einheit_bezeichnung, mieter_name FROM ista_positionen "
                "WHERE abrechnung_id=? AND wohnung_id IS NULL", (abr_id,)
            ).fetchall()
            wohnungen = conn.execute("SELECT id, bezeichnung FROM wohnungen").fetchall()
        finally:
            conn.close()

        zugeordnet = 0
        for pos in positionen:
            ista_bez = (pos["ista_einheit_bezeichnung"] or "").lower().strip()
            best_id = None
            best_score = 0
            for w in wohnungen:
                w_bez = w["bezeichnung"].lower().strip()
                # Einfaches Substring-Matching
                if ista_bez in w_bez or w_bez in ista_bez:
                    score = max(len(ista_bez), len(w_bez))
                    if score > best_score:
                        best_score = score
                        best_id = w["id"]
            if best_id:
                conn2 = get_db()
                try:
                    conn2.execute("UPDATE ista_positionen SET wohnung_id=? WHERE id=?", (best_id, pos["id"]))
                    conn2.commit()
                finally:
                    conn2.close()
                zugeordnet += 1

        self._load_positionen()
        messagebox.showinfo("Auto-Zuordnung",
            f"{zugeordnet} von {len(positionen)} Einheiten automatisch zugeordnet.\n"
            "Bitte restliche Zuordnungen manuell durchführen.", parent=self)

    # ── Tab 3: Übernahme in Buchhaltung ───────────────────────────────────────

    def _build_tab_uebernahme(self, parent):
        tk.Label(parent,
                 text="Übernehmen Sie die Ista-Kosten als Buchungen in die Buchhaltung "
                      "und als Verbrauchsdaten in die Nebenkostenabrechnung.",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL,
                 wraplength=800).pack(padx=12, pady=(12, 4), anchor="w")

        ctrl = tk.Frame(parent, bg=BG_CARD)
        ctrl.pack(fill="x", padx=8, pady=8)
        make_btn(ctrl, "💰 Als Buchungen übernehmen",
                 self._uebernehmen_als_buchungen).pack(side="left", padx=(0, 8))
        make_btn(ctrl, "🔢 Verbrauchsdaten übernehmen",
                 self._uebernehmen_verbrauch, color=SUCCESS).pack(side="left", padx=(0, 8))
        make_btn(ctrl, "📊 Alles übernehmen",
                 self._uebernehmen_alles, color=ACCENT).pack(side="left")

        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=8, pady=8)

        # Status-Anzeige
        self._uebernahme_status = tk.Text(parent, bg=BG_INPUT, fg=TEXT, font=FONT_SMALL,
                                           height=14, relief="flat", state="disabled")
        self._uebernahme_status.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def _log_uebernahme(self, text: str):
        self._uebernahme_status.config(state="normal")
        self._uebernahme_status.insert("end", text + "\n")
        self._uebernahme_status.see("end")
        self._uebernahme_status.config(state="disabled")

    def _get_selected_abrechnung(self):
        sel = self._tree_abr.selection()
        if not sel:
            messagebox.showinfo("Hinweis", "Bitte zuerst eine Abrechnung auswählen.", parent=self)
            return None
        return int(sel[0])

    def _uebernehmen_als_buchungen(self):
        if not hat_recht("Ista-Wärme", "schreiben"): return
        abr_id = self._get_selected_abrechnung()
        if abr_id is None: return

        conn = get_db()
        try:
            abr = conn.execute("SELECT * FROM ista_abrechnungen WHERE id=?", (abr_id,)).fetchone()
            positionen = conn.execute(
                "SELECT * FROM ista_positionen WHERE abrechnung_id=? AND wohnung_id IS NOT NULL",
                (abr_id,)
            ).fetchall()
        finally:
            conn.close()

        if not positionen:
            messagebox.showwarning("Keine Positionen",
                "Keine zugeordneten Positionen gefunden.\n"
                "Bitte zuerst Wohnungen im Tab 'Positionen & Zuordnung' zuordnen.", parent=self)
            return

        if not messagebox.askyesno("Buchungen erstellen",
            f"Für {len(positionen)} Wohnungen Buchungen erstellen?\n"
            "Pro Wohnung werden Heizkosten und Warmwasserkosten als Ausgaben erfasst.", parent=self):
            return

        self._uebernahme_status.config(state="normal")
        self._uebernahme_status.delete("1.0", "end")
        self._uebernahme_status.config(state="disabled")

        erstellt = 0
        for pos in positionen:
            conn2 = get_db()
            try:
                # Heizkosten-Buchung
                if (pos["heizkosten_gesamt"] or 0) > 0:
                    conn2.execute(
                        "INSERT INTO zahlungen (datum, betrag, typ, kategorie, beschreibung, "
                        "konto_typ, status, eigentuemer_id, abrechnungsrelevant, abrechnungsjahr, "
                        "rechnungssteller) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (
                            abr["abrechnungszeitraum_bis"] or f"{abr['abrechnungsjahr']}-12-31",
                            -abs(pos["heizkosten_gesamt"]),
                            "Ausgabe", "Heizung",
                            f"Ista Heizkosten {abr['abrechnungsjahr']} – {pos['ista_einheit_bezeichnung'] or pos['ista_einheit_nr'] or ''}",
                            "Wohngeldkonto", "Geprüft",
                            None, 1, abr["abrechnungsjahr"], "Ista GmbH"
                        )
                    )
                    conn2.commit()
                    erstellt += 1

                # Warmwasser-Buchung
                if (pos["warmwasserkosten_gesamt"] or 0) > 0:
                    conn2.execute(
                        "INSERT INTO zahlungen (datum, betrag, typ, kategorie, beschreibung, "
                        "konto_typ, status, eigentuemer_id, abrechnungsrelevant, abrechnungsjahr, "
                        "rechnungssteller) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (
                            abr["abrechnungszeitraum_bis"] or f"{abr['abrechnungsjahr']}-12-31",
                            -abs(pos["warmwasserkosten_gesamt"]),
                            "Ausgabe", "Warmwasser",
                            f"Ista Warmwasserkosten {abr['abrechnungsjahr']} – {pos['ista_einheit_bezeichnung'] or pos['ista_einheit_nr'] or ''}",
                            "Wohngeldkonto", "Geprüft",
                            None, 1, abr["abrechnungsjahr"], "Ista GmbH"
                        )
                    )
                    conn2.commit()
                    erstellt += 1

                conn2.execute(
                    "UPDATE ista_positionen SET als_zahlung_uebernommen=1 WHERE id=?",
                    (pos["id"],)
                )
                conn2.commit()
            finally:
                conn2.close()
            self._log_uebernahme(f"✅ {pos['ista_einheit_bezeichnung'] or pos['ista_einheit_nr']}: "
                                  f"Heizung {fmt_euro(pos['heizkosten_gesamt'] or 0)}, "
                                  f"Warmwasser {fmt_euro(pos['warmwasserkosten_gesamt'] or 0)}")

        self._log_uebernahme(f"\n✅ Fertig: {erstellt} Buchungen erstellt.")
        messagebox.showinfo("Buchungen erstellt", f"{erstellt} Buchungen in die Buchhaltung übertragen.", parent=self)

    def _uebernehmen_verbrauch(self):
        """Überträgt Ista-HKE-Werte als Verbrauchsdaten (für HeizKV-Berechnung)."""
        if not hat_recht("Ista-Wärme", "schreiben"): return
        abr_id = self._get_selected_abrechnung()
        if abr_id is None: return

        conn = get_db()
        try:
            abr = conn.execute("SELECT * FROM ista_abrechnungen WHERE id=?", (abr_id,)).fetchone()
            positionen = conn.execute(
                "SELECT * FROM ista_positionen WHERE abrechnung_id=? AND wohnung_id IS NOT NULL",
                (abr_id,)
            ).fetchall()
        finally:
            conn.close()

        if not positionen:
            messagebox.showwarning("Keine Positionen", "Keine zugeordneten Positionen.", parent=self)
            return

        jahr = abr["abrechnungsjahr"]
        uebernommen = 0
        for pos in positionen:
            if not (pos["hke"] or 0) > 0:
                continue
            conn2 = get_db()
            try:
                conn2.execute(
                    "INSERT INTO verbrauchsdaten (wohnung_id, kategorie, jahr, "
                    "zaehlerstand_anfang, zaehlerstand_ende, einheit, notizen) "
                    "VALUES (?,?,?,?,?,?,?) "
                    "ON CONFLICT(wohnung_id,kategorie,jahr) DO UPDATE SET "
                    "zaehlerstand_ende=excluded.zaehlerstand_ende, "
                    "notizen=excluded.notizen",
                    (pos["wohnung_id"], "Heizung", jahr,
                     0, pos["hke"], "HKE",
                     f"Ista-Import: {pos['hke_anteil_pct'] or 0:.1f}% Anteil")
                )
                conn2.commit()
                uebernommen += 1
            finally:
                conn2.close()
            self._log_uebernahme(f"🔢 {pos['ista_einheit_bezeichnung'] or pos['ista_einheit_nr']}: "
                                  f"{pos['hke'] or 0:.2f} HKE = {pos['hke_anteil_pct'] or 0:.1f}%")

        self._log_uebernahme(f"\n✅ {uebernommen} Verbrauchsdatensätze übertragen.")
        messagebox.showinfo("Verbrauch übertragen",
            f"{uebernommen} Verbrauchsdatensätze (HKE) für HeizKV-Berechnung gespeichert.", parent=self)

    def _uebernehmen_alles(self):
        self._uebernehmen_als_buchungen()
        self._uebernehmen_verbrauch()

    # ── Tab 4: Leitfaden ──────────────────────────────────────────────────────

    def _build_tab_leitfaden(self, parent):
        text = tk.Text(parent, bg=BG_CARD, fg=TEXT, font=FONT_BODY,
                       relief="flat", wrap="word", state="normal",
                       padx=20, pady=12)
        text.pack(fill="both", expand=True)

        leitfaden = """📖 ISTA-WÄRMEABRECHNUNG – LEITFADEN

═══════════════════════════════════════════════════════════

1️⃣  PDF VON ISTA HERUNTERLADEN
────────────────────────────────
• Gehen Sie auf das Ista-Kundenportal (www.ista.com/de)
• Laden Sie die Jahresabrechnung als PDF herunter
• Ista liefert üblicherweise eine Gesamtabrechnung sowie
  individuelle Einzelabrechnungen pro Wohnung

2️⃣  PDF IN DIE APP IMPORTIEREN
────────────────────────────────
• Klicken Sie auf "📥 Ista-PDF importieren"
• Wählen Sie das heruntergeladene Ista-PDF
• Die App versucht, die Daten automatisch zu extrahieren
• Falls der automatische Import nicht vollständig ist,
  können Sie Daten manuell ergänzen

3️⃣  WOHNUNGEN ZUORDNEN (Tab "Positionen & Zuordnung")
──────────────────────────────────────────────────────
• Ista verwendet interne Einheitenbezeichnungen
  (z.B. "WE 01", "EG links")
• Ordnen Sie jede Ista-Einheit der entsprechenden
  Wohnung in der App zu
• "🤖 Auto-Zuordnung" versucht eine automatische
  Zuordnung anhand der Bezeichnung

4️⃣  KOSTEN ÜBERNEHMEN (Tab "Übernahme in Buchhaltung")
────────────────────────────────────────────────────────
• "💰 Als Buchungen übernehmen": Erstellt Ausgabe-
  Buchungen für Heizung und Warmwasser in der Buchhaltung
• "🔢 Verbrauchsdaten übernehmen": Speichert die
  Heizkosteneinheiten (HKE) für die HeizKV-Berechnung
  in der Nebenkostenabrechnung
• "📊 Alles übernehmen": Führt beide Schritte aus

5️⃣  NEBENKOSTENABRECHNUNG ERSTELLEN
─────────────────────────────────────
• Gehen Sie zur Seite "Nebenkosten"
• Die Ista-Kosten sind jetzt in der Buchhaltung
• Im Tab "§556 BGB Mieter" werden die Kosten mit dem
  Umlageschlüssel "HeizKV" (70% Verbrauch / 30% Fläche)
  automatisch auf die Mieter verteilt

═══════════════════════════════════════════════════════════

📌 WICHTIGE HINWEISE ZUR HEIZKOSTENVERORDNUNG (HeizKV)

• §7 HeizKV: Mindestens 50%, maximal 70% der Kosten
  nach Verbrauch abrechnen (Standard: 70%)
• Die restlichen 30% nach Wohnfläche
• Ausnahme: Bei Wärmepumpen oder bestimmten Anlagen
  gelten andere Regelungen
• Ista übernimmt die HKV-konforme Abrechnung und
  liefert die Anteile pro Wohnung

📌 ISTA-ABRECHNUNG vs. EIGENE ABRECHNUNG

• Die Ista-Abrechnung ist bereits HKV-konform und
  enthält die endgültigen Kosten pro Wohnung
• Diese Werte werden direkt übernommen – keine
  erneute Berechnung notwendig
• Die HKE-Werte dienen nur als Verbrauchsnachweis

═══════════════════════════════════════════════════════════

📞 KONTAKT ISTA
• Kundenservice: 0800 100 64 64 (kostenlos)
• Online-Portal: www.ista.com/de
• E-Mail: service.de@ista.com
"""
        text.insert("1.0", leitfaden)
        text.config(state="disabled")

    # ── PDF-Import ────────────────────────────────────────────────────────────

    def _import_pdf(self):
        if not hat_recht("Ista-Wärme", "schreiben"):
            messagebox.showwarning("Berechtigung", "Keine Schreibberechtigung.", parent=self); return

        from tkinter import filedialog
        pdf_pfad = filedialog.askopenfilename(
            parent=self,
            title="Ista-Abrechnung (PDF) auswählen",
            filetypes=[("PDF-Dateien", "*.pdf"), ("Alle Dateien", "*.*")]
        )
        if not pdf_pfad:
            return

        import os
        if not os.path.isfile(pdf_pfad):
            messagebox.showerror("Fehler", f"Datei nicht gefunden:\n{pdf_pfad}", parent=self)
            return

        # Extraktion-Dialog anzeigen
        dlg = tk.Toplevel(self)
        dlg.title("Ista-PDF wird verarbeitet …")
        dlg.geometry("560x420")
        dlg.configure(bg=BG_CARD)
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()

        tk.Label(dlg, text="📥 Ista-PDF Import",
                 bg=BG_CARD, fg=TEXT, font=FONT_H2).pack(padx=20, pady=(16, 4), anchor="w")
        tk.Label(dlg, text=f"Datei: {os.path.basename(pdf_pfad)}",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(padx=20, anchor="w")

        status_lbl = tk.Label(dlg, text="⏳ Text wird extrahiert …",
                               bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_BODY)
        status_lbl.pack(padx=20, pady=8, anchor="w")

        log_txt = tk.Text(dlg, bg=BG_INPUT, fg=TEXT, font=FONT_SMALL,
                           height=12, relief="flat", state="disabled")
        log_txt.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        def _log(msg):
            log_txt.config(state="normal")
            log_txt.insert("end", msg + "\n")
            log_txt.see("end")
            log_txt.config(state="disabled")
            dlg.update()

        def _update_status(msg):
            status_lbl.config(text=msg)
            dlg.update()

        self._parsed_daten = None

        def _do_import():
            try:
                _update_status("⏳ PDF-Text extrahieren …")
                _log(f"📄 Lese PDF: {os.path.basename(pdf_pfad)}")

                # PDF-Text extrahieren
                pdf_text = ""
                try:
                    import pypdf
                    with open(pdf_pfad, "rb") as fh:
                        reader = pypdf.PdfReader(fh)
                        for i, page in enumerate(reader.pages):
                            txt = page.extract_text() or ""
                            pdf_text += txt
                            _log(f"   Seite {i+1}: {len(txt)} Zeichen extrahiert")
                except ImportError:
                    _log("⚠ pypdf nicht installiert – KI-basierte Extraktion wird versucht")

                _log(f"\n📝 Gesamt: {len(pdf_text)} Zeichen")

                if not pdf_text.strip():
                    _log("⚠ Kein Text extrahiert – PDF evtl. gescannt (Bild-PDF)")
                    _log("  Manuelle Eingabe erforderlich")

                _update_status("🤖 KI analysiert Ista-Daten …")
                _log("\n🤖 Starte KI-Analyse …")

                # KI-Extraktion versuchen
                cfg = load_config()
                ki_daten = None

                if pdf_text.strip():
                    ki_daten = self._ki_extrahieren(pdf_text[:8000], cfg, _log)

                if ki_daten:
                    self._parsed_daten = ki_daten
                    _update_status("✅ Extraktion erfolgreich – bitte prüfen")
                    _log(f"\n✅ KI-Extraktion: {len(ki_daten.get('positionen', []))} Einheiten erkannt")
                    _log(f"   Jahr: {ki_daten.get('abrechnungsjahr', '?')}")
                    _log(f"   Objekt: {ki_daten.get('objekt_adresse', '?')}")
                    _log(f"   Gesamtkosten: {ki_daten.get('gesamtkosten_gesamt', '?')}")
                else:
                    _update_status("⚠ Automatische Extraktion unvollständig")
                    _log("\n⚠ KI-Extraktion nicht möglich – manuelle Eingabe erforderlich")
                    self._parsed_daten = {
                        "abrechnungsjahr": date.today().year - 1,
                        "gesamtkosten_heizung": 0,
                        "gesamtkosten_warmwasser": 0,
                        "gesamtkosten_gesamt": 0,
                        "objekt_adresse": "",
                        "positionen": [],
                    }

                _log("\n─────────────────────────────")
                _log("Klicken Sie auf 'Speichern & Importieren' um fortzufahren.")

                btn_row = tk.Frame(dlg, bg=BG_CARD)
                btn_row.pack(fill="x", padx=20, pady=(0, 12))
                make_btn(btn_row, "💾 Speichern & Importieren",
                          lambda: self._save_import(dlg, pdf_pfad, self._parsed_daten)).pack(side="left", padx=(0, 8))
                make_btn(btn_row, "✏️ Manuell eingeben",
                          lambda: self._manuell_eingeben(dlg, pdf_pfad)).pack(side="left", padx=(0, 8))
                make_btn(btn_row, "Abbrechen", dlg.destroy, color=BG_INPUT, fg=TEXT).pack(side="left")

            except Exception as ex:
                _update_status(f"❌ Fehler: {ex}")
                _log(f"\n❌ Fehler: {ex}")

        # Import in Thread damit UI nicht einfriert
        import threading
        threading.Thread(target=_do_import, daemon=True).start()

    def _ki_extrahieren(self, pdf_text: str, cfg: dict, _log) -> dict:
        """Versucht KI-basierte Extraktion der Ista-Daten."""
        prompt = (
            "Analysiere diese Ista-Heizkostenabrechnung und extrahiere die Daten als JSON.\n"
            "Antworte NUR mit einem JSON-Objekt.\n\n"
            "Felder:\n"
            '  "abrechnungsjahr": Abrechnungsjahr (Integer, z.B. 2025)\n'
            '  "abrechnungszeitraum_von": Startdatum YYYY-MM-DD\n'
            '  "abrechnungszeitraum_bis": Enddatum YYYY-MM-DD\n'
            '  "objekt_adresse": Objektadresse\n'
            '  "ista_auftragsnummer": Auftragsnummer falls vorhanden\n'
            '  "gesamtkosten_heizung": Gesamte Heizkosten als Zahl\n'
            '  "gesamtkosten_warmwasser": Gesamte Warmwasserkosten als Zahl\n'
            '  "gesamtkosten_gesamt": Gesamtkosten als Zahl\n'
            '  "positionen": Array mit einem Objekt pro Wohneinheit:\n'
            '    [\n'
            '      {\n'
            '        "ista_einheit_nr": "WE01",\n'
            '        "ista_einheit_bezeichnung": "EG links",\n'
            '        "mieter_name": "Name des Mieters",\n'
            '        "hke": Heizkosteneinheiten als Zahl,\n'
            '        "hke_anteil_pct": prozentualer HKE-Anteil,\n'
            '        "warmwasser_m3": Warmwasserverbrauch in m³,\n'
            '        "warmwasser_anteil_pct": prozentualer WW-Anteil,\n'
            '        "heizkosten_grundkosten": Grundkostenanteil Heizung,\n'
            '        "heizkosten_verbrauchskosten": Verbrauchskostenanteil,\n'
            '        "heizkosten_gesamt": Heizkosten gesamt,\n'
            '        "warmwasserkosten_gesamt": Warmwasserkosten gesamt,\n'
            '        "gesamtkosten": Gesamtkosten dieser Einheit,\n'
            '        "vorauszahlung": Geleistete Vorauszahlungen,\n'
            '        "nachzahlung_guthaben": Nachzahlung (positiv) oder Guthaben (negativ)\n'
            '      }\n'
            '    ]\n\n'
            f"Ista-Abrechnungstext:\n{pdf_text}"
        )

        try:
            aktiv = cfg.get("ki_aktives_modell", "")
            if aktiv:
                anbieter, modell = KIAssistentPage._parse_modell_auswahl(aktiv)
            else:
                anbieter = cfg.get("ki_anbieter", "anthropic")
                modell = cfg.get("ki_modell", "claude-opus-4-6")

            _log(f"   Anbieter: {anbieter}, Modell: {modell}")

            import urllib.request, json as _json
            if anbieter == "anthropic":
                key = cfg.get("anthropic_api_key", "").strip()
                if not key:
                    _log("   ⚠ Kein Anthropic API-Key – KI-Analyse übersprungen")
                    return None
                payload = _json.dumps({
                    "model": modell,
                    "max_tokens": 2048,
                    "messages": [{"role": "user", "content": prompt}]
                }).encode("utf-8")
                req = urllib.request.Request(
                    "https://api.anthropic.com/v1/messages", data=payload,
                    headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                             "content-type": "application/json"})
                with urllib.request.urlopen(req, timeout=60) as resp:
                    data = _json.loads(resp.read().decode())
                antwort = data["content"][0]["text"]
            else:
                base_url = cfg.get("ollama_url", "http://localhost:11434").strip().rstrip("/")
                payload = _json.dumps({
                    "model": modell,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False
                }).encode("utf-8")
                req = urllib.request.Request(f"{base_url}/api/chat", data=payload,
                    headers={"content-type": "application/json"})
                with urllib.request.urlopen(req, timeout=90) as resp:
                    data = _json.loads(resp.read().decode())
                antwort = data["message"]["content"]

            # JSON parsen
            import re
            try:
                ki_daten = _json.loads(antwort.strip())
            except Exception:
                m = re.search(r'\{.*\}', antwort, re.DOTALL)
                if not m:
                    return None
                ki_daten = _json.loads(m.group())

            ki_daten = {k.lower(): v for k, v in ki_daten.items()}
            return ki_daten

        except Exception as ex:
            _log(f"   ⚠ KI-Fehler: {ex}")
            return None

    def _save_import(self, dlg, pdf_pfad, daten: dict):
        """Speichert die importierten Ista-Daten in die DB."""
        if not daten:
            return
        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO ista_abrechnungen (abrechnungsjahr, abrechnungszeitraum_von, "
                "abrechnungszeitraum_bis, pdf_pfad, gesamtkosten_heizung, gesamtkosten_warmwasser, "
                "gesamtkosten_gesamt, objekt_adresse, ista_auftragsnummer) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    daten.get("abrechnungsjahr") or date.today().year - 1,
                    daten.get("abrechnungszeitraum_von"),
                    daten.get("abrechnungszeitraum_bis"),
                    pdf_pfad,
                    daten.get("gesamtkosten_heizung") or 0,
                    daten.get("gesamtkosten_warmwasser") or 0,
                    daten.get("gesamtkosten_gesamt") or 0,
                    daten.get("objekt_adresse") or "",
                    daten.get("ista_auftragsnummer") or "",
                )
            )
            abr_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

            for pos in (daten.get("positionen") or []):
                pos = {k.lower(): v for k, v in pos.items()}
                conn.execute(
                    "INSERT INTO ista_positionen (abrechnung_id, ista_einheit_nr, "
                    "ista_einheit_bezeichnung, mieter_name, hke, hke_anteil_pct, "
                    "warmwasser_m3, warmwasser_anteil_pct, heizkosten_grundkosten, "
                    "heizkosten_verbrauchskosten, heizkosten_gesamt, warmwasserkosten_gesamt, "
                    "gesamtkosten, vorauszahlung, nachzahlung_guthaben) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        abr_id,
                        str(pos.get("ista_einheit_nr") or ""),
                        str(pos.get("ista_einheit_bezeichnung") or ""),
                        str(pos.get("mieter_name") or ""),
                        float(pos.get("hke") or 0),
                        float(pos.get("hke_anteil_pct") or 0),
                        float(pos.get("warmwasser_m3") or 0),
                        float(pos.get("warmwasser_anteil_pct") or 0),
                        float(pos.get("heizkosten_grundkosten") or 0),
                        float(pos.get("heizkosten_verbrauchskosten") or 0),
                        float(pos.get("heizkosten_gesamt") or 0),
                        float(pos.get("warmwasserkosten_gesamt") or 0),
                        float(pos.get("gesamtkosten") or 0),
                        float(pos.get("vorauszahlung") or 0),
                        float(pos.get("nachzahlung_guthaben") or 0),
                    )
                )
            conn.commit()
        finally:
            conn.close()

        dlg.destroy()
        self._load_abrechnungen()
        messagebox.showinfo("✅ Import erfolgreich",
            f"Ista-Abrechnung {daten.get('abrechnungsjahr')} importiert.\n"
            f"{len(daten.get('positionen') or [])} Einheiten gespeichert.\n\n"
            "Bitte jetzt im Tab 'Positionen & Zuordnung' die Wohnungen zuordnen.",
            parent=self)

    def _manuell_eingeben(self, dlg, pdf_pfad):
        """Manuelle Eingabe der Ista-Daten wenn automatische Extraktion fehlschlägt."""
        dlg.destroy()
        dlg2 = tk.Toplevel(self)
        dlg2.title("Ista-Daten manuell eingeben")
        dlg2.geometry("560x500")
        dlg2.configure(bg=BG_CARD)
        dlg2.transient(self.winfo_toplevel())

        tk.Label(dlg2, text="Ista-Abrechnung manuell erfassen",
                 bg=BG_CARD, fg=TEXT, font=FONT_H2).pack(padx=20, pady=(16, 4), anchor="w")

        felder = {}
        for label, key, default in [
            ("Abrechnungsjahr *", "abrechnungsjahr", str(date.today().year - 1)),
            ("Zeitraum von (JJJJ-MM-TT)", "abrechnungszeitraum_von", f"{date.today().year-1}-01-01"),
            ("Zeitraum bis (JJJJ-MM-TT)", "abrechnungszeitraum_bis", f"{date.today().year-1}-12-31"),
            ("Objekt-Adresse", "objekt_adresse", ""),
            ("Ista-Auftragsnummer", "ista_auftragsnummer", ""),
            ("Gesamtkosten Heizung (€)", "gesamtkosten_heizung", "0"),
            ("Gesamtkosten Warmwasser (€)", "gesamtkosten_warmwasser", "0"),
            ("Gesamtkosten Gesamt (€)", "gesamtkosten_gesamt", "0"),
        ]:
            row = tk.Frame(dlg2, bg=BG_CARD)
            row.pack(fill="x", padx=20, pady=3)
            tk.Label(row, text=label, bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL,
                     width=28, anchor="w").pack(side="left")
            var = tk.StringVar(value=default)
            tk.Entry(row, textvariable=var, bg=BG_INPUT, fg=TEXT, font=FONT_BODY,
                     relief="flat", bd=0).pack(side="left", fill="x", expand=True, ipady=4)
            felder[key] = var

        tk.Label(dlg2, text="💡 Tipp: Nach dem Speichern können Sie Einzel-Positionen\n"
                             "im Tab 'Positionen & Zuordnung' manuell ergänzen.",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(padx=20, pady=(8, 4), anchor="w")

        def _save():
            try:
                daten = {
                    "abrechnungsjahr": int(felder["abrechnungsjahr"].get() or date.today().year - 1),
                    "abrechnungszeitraum_von": felder["abrechnungszeitraum_von"].get() or None,
                    "abrechnungszeitraum_bis": felder["abrechnungszeitraum_bis"].get() or None,
                    "objekt_adresse": felder["objekt_adresse"].get(),
                    "ista_auftragsnummer": felder["ista_auftragsnummer"].get(),
                    "gesamtkosten_heizung": float(felder["gesamtkosten_heizung"].get().replace(",", ".") or 0),
                    "gesamtkosten_warmwasser": float(felder["gesamtkosten_warmwasser"].get().replace(",", ".") or 0),
                    "gesamtkosten_gesamt": float(felder["gesamtkosten_gesamt"].get().replace(",", ".") or 0),
                    "positionen": [],
                }
                self._save_import(dlg2, pdf_pfad, daten)
            except ValueError as e:
                messagebox.showerror("Eingabefehler", f"Ungültige Eingabe: {e}", parent=dlg2)

        btn_row = tk.Frame(dlg2, bg=BG_CARD)
        btn_row.pack(pady=12)
        make_btn(btn_row, "💾 Speichern", _save).pack(side="left", padx=6)
        make_btn(btn_row, "Abbrechen", dlg2.destroy, color=BG_INPUT, fg=TEXT).pack(side="left", padx=6)

    def _delete_abrechnung(self):
        if not hat_recht("Ista-Wärme", "loeschen"):
            messagebox.showwarning("Berechtigung", "Keine Lösch-Berechtigung.", parent=self); return
        sel = self._tree_abr.selection()
        if not sel:
            messagebox.showinfo("Kein Eintrag", "Bitte eine Abrechnung auswählen.", parent=self); return
        abr_id = int(sel[0])
        if not messagebox.askyesno("Löschen",
            "Abrechnung und alle zugehörigen Positionen löschen?\nDies kann nicht rückgängig gemacht werden.",
            parent=self):
            return
        conn = get_db()
        try:
            conn.execute("DELETE FROM ista_positionen WHERE abrechnung_id=?", (abr_id,))
            conn.execute("DELETE FROM ista_abrechnungen WHERE id=?", (abr_id,))
            conn.commit()
        finally:
            conn.close()
        self._load_abrechnungen()
        for i in self._tree_pos.get_children():
            self._tree_pos.delete(i)


# ══════════════════════════════════════════════════════════════════════════════
# HAUSVERWALTUNG-APP
# ══════════════════════════════════════════════════════════════════════════════

class HausverwaltungApp(tk.Tk):
    PAGES = [
        ("🏠", "Übersicht",      DashboardPage),
        ("🏛", "Eigentümer",     EigentuemerPage),
        ("🏘", "Wohnungen",      WohnungenPage),
        ("👥", "Mieter",         MieterPage),
        ("🏦", "Kontoauszug",    KontoauszugPage),
        ("💰", "Buchhaltung",    BuchhaltungPage),
        ("🔧", "Wartung",        WartungPage),
        ("📋", "Nebenkosten",    NebenkostenPage),
        ("🔥", "Ista-Wärme",     IstaPage),
        ("💧", "Wasserkosten",   WasserkostenPage),
        ("⚖",  "Aufteilungen",   AufteilungenPage),
        ("✉️",  "Nachrichten",    NachrichtenPage),
        ("📁", "Dokumente",      DokumentePage),
        ("🤖", "KI-Assistent",   KIAssistentPage),
        ("👤", "Benutzer",       BenutzerverwaltungPage),
        ("🔐", "Rollen & Rechte",RollenverwaltungPage),
        ("⚙",  "Einstellungen",  EinstellungenPage),
    ]

    def __init__(self):
        super().__init__()
        self.withdraw()
        init_db()
        # Optionale Pakete prüfen und Hinweis anzeigen (#38)
        _fehlend = _prüfe_pakete()
        if _fehlend:
            _dlg = AbhängigkeitenDialog(self, _fehlend)
            self.wait_window(_dlg)
        login = LoginDialog(self)
        self.wait_window(login)
        if not login.result:
            self.destroy()
            return
        global _CURRENT_USER
        self._current_user = login.result
        _CURRENT_USER = login.result
        self.deiconify()
        _cfg_t = load_config()
        _titel_name = _cfg_t.get("weg_name", "").strip() or "Hausverwaltung"
        self.title(f"{_titel_name} v{APP_VERSION} – {login.result['benutzername']}")
        self.geometry("1280x800")
        self.minsize(1024, 680)
        self.configure(bg=BG_SIDEBAR)
        self._active = None
        self._build_ui()
        self._switch(0)

    def _build_ui(self):
        sidebar = tk.Frame(self, bg=BG_SIDEBAR, width=200)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        logo = tk.Frame(sidebar, bg=BG_SIDEBAR, height=72)
        logo.pack(fill="x")
        logo.pack_propagate(False)
        tk.Label(logo, text="⌂", bg=BG_SIDEBAR, fg=ACCENT,
                 font=("Georgia", 28)).pack(side="left", padx=(16, 6), pady=14)
        info = tk.Frame(logo, bg=BG_SIDEBAR)
        info.pack(side="left", pady=16)
        _cfg = load_config()
        _weg_name = _cfg.get("weg_name", "").strip() or "Hausverwaltung"
        # Neue Einzelfelder bevorzugen, Fallback auf altes kombiniertes Feld
        _weg_strasse = _cfg.get("weg_strasse", "").strip()
        _weg_plz    = _cfg.get("weg_plz", "").strip()
        _weg_ort    = _cfg.get("weg_ort", "").strip()
        if _weg_strasse or _weg_plz or _weg_ort:
            _plz_ort = f"{_weg_plz} {_weg_ort}".strip()
            _weg_adr = ", ".join(filter(None, [_weg_strasse, _plz_ort])) or "Musterstra\u00dfe 12"
        else:
            _weg_adr = _cfg.get("weg_adresse", "").strip() or "Musterstra\u00dfe 12"
        tk.Label(info, text=_weg_name, bg=BG_SIDEBAR, fg=TEXT_WHITE,
                 font=("Segoe UI Semibold", 10)).pack(anchor="w")
        tk.Label(info, text=_weg_adr, bg=BG_SIDEBAR, fg=SIDEBAR_FG,
                 font=FONT_SMALL).pack(anchor="w")

        tk.Frame(sidebar, bg="#2C3E50", height=1).pack(fill="x", padx=12)

        self._nav_btns = []
        nav_frame = tk.Frame(sidebar, bg=BG_SIDEBAR)
        nav_frame.pack(fill="x", pady=8)

        for i, (icon, label, PageClass) in enumerate(self.PAGES):
            btn = tk.Button(nav_frame,
                text=f"  {icon}  {label}",
                command=lambda idx=i: self._switch(idx),
                bg=BG_SIDEBAR, fg=SIDEBAR_FG,
                font=FONT_NAV, relief="flat", bd=0,
                anchor="w", padx=8, pady=8,
                activebackground="#253545",
                activeforeground=TEXT_WHITE,
                cursor="hand2")
            btn.pack(fill="x", padx=8, pady=1)
            self._nav_btns.append(btn)

        ver_btn = tk.Button(sidebar, text=f"v{APP_VERSION}  •  SQLite",
                            bg=BG_SIDEBAR, fg="#4A6A80", font=("Segoe UI", 8),
                            relief="flat", bd=0, cursor="hand2",
                            activebackground=BG_SIDEBAR, activeforeground=SIDEBAR_ACT,
                            command=self._show_version_info)
        ver_btn.pack(side="bottom", pady=8)

        self._content = tk.Frame(self, bg=BG_CARD)
        self._content.pack(side="left", fill="both", expand=True)

    def _switch(self, idx: int):
        if self._active == idx:
            return
        # Berechtigungsprüfung (Übersicht ist immer zugänglich)
        _, label, _ = self.PAGES[idx]
        if idx > 0 and not hat_recht(label, "lesen"):
            messagebox.showwarning("Kein Zugriff",
                                   f"Sie haben keine Berechtigung für '{label}'.")
            return
        self._active = idx
        for i, btn in enumerate(self._nav_btns):
            if btn is None:
                continue  # ausgeblendete Seite (z.B. Wasserkosten ohne Aufteilung)
            if i == idx:
                btn.config(bg="#253545", fg=SIDEBAR_ACT)
            else:
                btn.config(bg=BG_SIDEBAR, fg=SIDEBAR_FG)
        for w in self._content.winfo_children():
            w.destroy()
        _, _, PageClass = self.PAGES[idx]
        page = PageClass(self._content)
        page.pack(fill="both", expand=True)

    def _show_version_info(self):
        """Zeigt ein Versions-Info-Fenster mit App- und Git-Informationen."""
        git = _git_info()

        win = tk.Toplevel(self)
        win.title("Über Hausverwaltung")
        win.geometry("480x420")
        win.configure(bg=BG_CARD)
        win.resizable(False, False)
        win.grab_set()

        # Header
        hdr = tk.Frame(win, bg=BG_SIDEBAR, height=64)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="⌂", bg=BG_SIDEBAR, fg=ACCENT,
                 font=("Georgia", 28)).pack(side="left", padx=(20, 8), pady=10)
        hdr_info = tk.Frame(hdr, bg=BG_SIDEBAR)
        hdr_info.pack(side="left", pady=10)
        tk.Label(hdr_info, text=APP_NAME, bg=BG_SIDEBAR, fg=TEXT_WHITE,
                 font=("Georgia", 16, "bold")).pack(anchor="w")
        tk.Label(hdr_info, text=APP_AUTHOR, bg=BG_SIDEBAR, fg=SIDEBAR_FG,
                 font=FONT_SMALL).pack(anchor="w")

        body = tk.Frame(win, bg=BG_CARD)
        body.pack(fill="both", expand=True, padx=24, pady=16)

        # Version info
        def _row(parent, label, value, color=TEXT):
            r = tk.Frame(parent, bg=BG_CARD)
            r.pack(fill="x", pady=3)
            tk.Label(r, text=label, bg=BG_CARD, fg=TEXT_LIGHT,
                     font=FONT_SMALL, width=16, anchor="w").pack(side="left")
            tk.Label(r, text=value, bg=BG_CARD, fg=color,
                     font=("Consolas", 10), anchor="w").pack(side="left", fill="x")

        tk.Label(body, text="Versionsinformationen", bg=BG_CARD, fg=TEXT,
                 font=FONT_H3).pack(anchor="w", pady=(0, 8))
        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=(0, 8))

        dirty_marker = "  (ungespeicherte Änderungen)" if git["dirty"] else ""
        _row(body, "App-Version:", f"v{APP_VERSION}")
        _row(body, "Git-Tag:", git["tag"])
        _row(body, "Git-Branch:", git["branch"])
        _row(body, "Git-Commit:", f"{git['commit_short']}{dirty_marker}",
             WARNING if git["dirty"] else TEXT)
        _row(body, "Commit-Datum:", git["date"])

        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=(12, 8))
        tk.Label(body, text="Technologie", bg=BG_CARD, fg=TEXT,
                 font=FONT_H3).pack(anchor="w", pady=(0, 8))
        _row(body, "Sprache:", "Python 3 · Tkinter")
        _row(body, "Datenbank:", "SQLite 3")
        _row(body, "Architektur:", "Single-File Desktop-App")
        _row(body, "DB-Pfad:", str(DB_PATH))

        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=(12, 8))
        tk.Label(body, text="Änderungshistorie", bg=BG_CARD, fg=TEXT,
                 font=FONT_H3).pack(anchor="w", pady=(0, 4))

        changelog = tk.Text(body, height=6, bg=BG_INPUT, fg=TEXT,
                            relief="flat", font=FONT_SMALL, bd=0,
                            padx=8, pady=6, wrap="word")
        changelog.pack(fill="both", expand=True)
        changelog.insert("1.0",
            "v0.3.0 — Scrollbare Dialoge, Größenpersistenz, "
            "Rollenverwaltung-UI,\n"
            "           Eigentümer-Wohnungszuordnung, Eigennutzung, "
            "Versionierung\n\n"
            "v0.2.0 — RBAC (Rollen & Rechte), Buchhaltung-Intelligenz,\n"
            "           Erweiterte Stammdaten (Adresse, IBAN, MEA ‰),\n"
            "           Benutzerverwaltung, Login, Kontoauszug Auto-Transfer\n\n"
            "v0.1.0 — Initiale App: GUI, SQLite, CRUD, CAMT.052-Import,\n"
            "           Dashboard, Einstellungen, CSV-Import")
        changelog.config(state="disabled")

        # Close button
        make_btn(win, "Schließen", win.destroy,
                 color=BG_INPUT, fg=TEXT).pack(pady=(0, 12))

        # Center on parent
        win.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - 480) // 2
        y = self.winfo_y() + (self.winfo_height() - 420) // 2
        win.geometry(f"+{x}+{y}")


# ── Abhängigkeits-Prüfung beim Start ────────────────────────────────────────

OPTIONALE_PAKETE = [
    {
        "name": "pypdf",
        "pip": "pypdf",
        "beschreibung": "PDF-Textextraktion",
        "verwendet_fuer": "Ista-Wärme PDF-Import, Dokumente (PDF lesen)",
        "install_cmd": ["pip", "install", "pypdf", "--break-system-packages"],
    },
    {
        "name": "reportlab",
        "pip": "reportlab",
        "beschreibung": "PDF-Export",
        "verwendet_fuer": "Jahresabrechnung, Wirtschaftsplan, Nebenkosten PDF",
        "install_cmd": ["pip", "install", "reportlab", "--break-system-packages"],
    },
]

def _prüfe_pakete() -> list:
    """Gibt Liste der fehlenden optionalen Pakete zurück."""
    fehlend = []
    for pkg in OPTIONALE_PAKETE:
        try:
            __import__(pkg["name"])
        except ImportError:
            fehlend.append(pkg)
    return fehlend


class AbhängigkeitenDialog(tk.Toplevel):
    """Zeigt fehlende optionale Pakete und bietet automatische Installation an."""

    def __init__(self, parent, fehlende_pakete: list):
        super().__init__(parent)
        self.title("Fehlende Komponenten")
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)
        self.configure(bg=BG_CARD)
        self.geometry("580x420")
        self._pakete = fehlende_pakete
        self._status_vars = {}
        self._build()
        # Zentrieren
        self.update_idletasks()
        pw = parent.winfo_width(); ph = parent.winfo_height()
        px = parent.winfo_x();    py = parent.winfo_y()
        self.geometry(f"+{px + (pw - 580) // 2}+{py + (ph - 420) // 2}")

    def _build(self):
        # Kopf
        hdr = tk.Frame(self, bg=ACCENT2, padx=20, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="⚠  Fehlende Komponenten gefunden",
                 bg=ACCENT2, fg="white", font=FONT_H2).pack(anchor="w")
        tk.Label(hdr,
                 text="Einige optionale Funktionen sind nicht verfügbar, "
                      "weil folgende Python-Pakete fehlen.",
                 bg=ACCENT2, fg="white", font=FONT_SMALL, wraplength=520,
                 justify="left").pack(anchor="w", pady=(4, 0))

        # Paket-Liste
        for pkg in self._pakete:
            f = tk.Frame(self, bg=BG_CARD, pady=6)
            f.pack(fill="x", padx=20)
            tk.Frame(f, bg=BORDER, height=1).pack(fill="x", pady=(0, 8))
            top = tk.Frame(f, bg=BG_CARD)
            top.pack(fill="x")
            tk.Label(top, text=f"📦 {pkg['name']}",
                     bg=BG_CARD, fg=TEXT, font=("Segoe UI Semibold", 11)).pack(side="left")
            status_var = tk.StringVar(value="")
            self._status_vars[pkg["name"]] = status_var
            tk.Label(top, textvariable=status_var, bg=BG_CARD, fg=SUCCESS,
                     font=FONT_SMALL).pack(side="right")
            tk.Label(f, text=f"Funktion: {pkg['beschreibung']}  |  Wird benötigt für: {pkg['verwendet_fuer']}",
                     bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL,
                     wraplength=520, justify="left").pack(anchor="w", pady=(2, 4))
            install_cmd_str = " ".join(pkg["install_cmd"])
            tk.Label(f, text=f"$ {install_cmd_str}",
                     bg=BG_INPUT, fg=TEXT, font=("Courier New", 9),
                     padx=8, pady=4).pack(anchor="w", fill="x")

        # Buttons
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(12, 0))
        btn_f = tk.Frame(self, bg=BG_CARD)
        btn_f.pack(fill="x", padx=20, pady=12)

        make_btn(btn_f, "⬇  Alle jetzt installieren",
                 self._alle_installieren, color=SUCCESS).pack(side="left")
        make_btn(btn_f, "Später",
                 self.destroy, color=BG_INPUT, fg=TEXT).pack(side="right")

        tk.Label(self, text="Die App startet auch ohne diese Pakete – betroffene Funktionen zeigen dann Hinweise.",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL,
                 wraplength=540, justify="center").pack(pady=(0, 12))

    def _alle_installieren(self):
        """Installiert alle fehlenden Pakete via pip."""
        import subprocess, sys
        for pkg in self._pakete:
            sv = self._status_vars.get(pkg["name"])
            if sv:
                sv.set("⏳ Installiere…")
            self.update()
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install",
                     pkg["pip"], "--break-system-packages"],
                    capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    if sv: sv.set("✅ Installiert")
                else:
                    if sv: sv.set(f"❌ Fehler: {result.stderr[:60]}")
            except subprocess.TimeoutExpired:
                if sv: sv.set("❌ Timeout")
            except Exception as exc:
                if sv: sv.set(f"❌ {exc}")
            self.update()

        # Prüfen ob alle installiert
        noch_fehlend = _prüfe_pakete()
        if not noch_fehlend:
            messagebox.showinfo("Installation abgeschlossen",
                "✅ Alle Pakete erfolgreich installiert!\n\n"
                "Bitte starten Sie die App neu, damit die Änderungen wirksam werden.",
                parent=self)
            self.destroy()
        else:
            namen = ", ".join(p["name"] for p in noch_fehlend)
            messagebox.showwarning("Teilweise fehlgeschlagen",
                f"Folgende Pakete konnten nicht installiert werden:\n{namen}\n\n"
                "Bitte installieren Sie diese manuell in der Kommandozeile.",
                parent=self)


if __name__ == "__main__":
    app = HausverwaltungApp()
    app.mainloop()
