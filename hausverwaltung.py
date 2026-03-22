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

APP_VERSION = "0.6.0"
APP_NAME    = "Hausverwaltung"
APP_AUTHOR  = "WEG Welte Rapp Bilgery"


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

# ── Datenbank ────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
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
        "ALTER TABLE eigentuemer ADD COLUMN ort TEXT",
        "ALTER TABLE eigentuemer ADD COLUMN land TEXT DEFAULT 'Deutschland'",
        "ALTER TABLE eigentuemer ADD COLUMN iban TEXT",
        "ALTER TABLE mieter ADD COLUMN strasse TEXT",
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
    ]:
        try:
            c.execute(sql)
            conn.commit()
        except Exception:
            pass  # Spalte existiert bereits
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
                    "Benutzer","Rollen & Rechte","Einstellungen"]
        for b in bereiche:
            c.execute("INSERT INTO rechte (rolle_id,bereich,lesen,schreiben,loeschen) VALUES (?,?,1,1,1)", (admin_id, b))
            c.execute("INSERT INTO rechte (rolle_id,bereich,lesen,schreiben,loeschen) VALUES (?,?,1,1,0)", (benutzer_id, b))
        c.execute("UPDATE rechte SET lesen=0,schreiben=0,loeschen=0 WHERE rolle_id=? AND bereich IN ('Benutzer','Rollen & Rechte','Einstellungen')", (benutzer_id,))
        conn.commit()
    # Assign Superadmin role to admin user
    sa_role = c.execute("SELECT id FROM rollen WHERE ist_superadmin=1").fetchone()
    if sa_role:
        c.execute("UPDATE benutzer SET rolle_id=? WHERE benutzername='admin' AND (rolle_id IS NULL OR rolle_id=0)", (sa_role[0],))
        conn.commit()

    if not c.execute("SELECT COUNT(*) FROM eigentuemer").fetchone()[0]:
        _insert_demo(c)
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

def vorschlag_kategorie(buchungstext: str) -> tuple:
    """Gibt (kategorie, typ, konto_typ) als Vorschlag zurück, basierend auf gelernten Regeln.

    Matching-Strategie:
    1. Exaktes Muster-Match im Buchungstext (höchste Priorität)
    2. Auftraggeber/Empfänger-Match (vor dem ||)
    3. Keyword-Match im Verwendungszweck (nach dem ||)
    """
    if not buchungstext:
        return "", "Einnahme", "Wohngeldkonto"
    conn = get_db()
    regeln = conn.execute(
        "SELECT * FROM buchungsregeln ORDER BY treffer DESC, ist_korrektur DESC"
    ).fetchall()
    conn.close()
    text_lower = buchungstext.lower()
    # Auftraggeber/Empfänger und Verwendungszweck trennen
    if "||" in buchungstext:
        auftraggeber, vzweck = buchungstext.split("||", 1)
        auftraggeber = auftraggeber.strip().lower()
        vzweck = vzweck.strip().lower()
    else:
        auftraggeber = ""
        vzweck = text_lower

    # 1. Exaktes Muster-Match im gesamten Text (Priorität 1)
    for regel in regeln:
        muster = regel["muster"].lower()
        if muster in text_lower:
            return regel["kategorie"] or "", regel["typ"] or "Einnahme", regel["konto_typ"] or "Wohngeldkonto"

    # 2. Auftraggeber-Match (Priorität 2)
    if auftraggeber:
        auftr_bereinigt = _bereinige_text(auftraggeber)
        for regel in regeln:
            muster = _bereinige_text(regel["muster"])
            if muster and muster in auftr_bereinigt:
                return regel["kategorie"] or "", regel["typ"] or "Einnahme", regel["konto_typ"] or "Wohngeldkonto"

    # 3. Keyword-Match im Verwendungszweck (Priorität 3)
    vzweck_bereinigt = _bereinige_text(vzweck)
    for regel in regeln:
        muster = _bereinige_text(regel["muster"])
        if muster and muster in vzweck_bereinigt:
            return regel["kategorie"] or "", regel["typ"] or "Einnahme", regel["konto_typ"] or "Wohngeldkonto"

    return "", "Einnahme", "Wohngeldkonto"

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
        conn.close()

        kpis = [
            ("🏠", "Mieter",        str(mieter_count),    ACCENT2),
            ("💰", "Einnahmen",     fmt_euro(einnahmen),   SUCCESS),
            ("🔧", "Offene Aufgaben", str(offene_wartung), WARNING),
            ("✉️",  "Ungelesen",    str(ungelesen),        ACCENT),
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

# ── Mieter-Seite ──────────────────────────────────────────────────────────────

class MieterPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_CARD)
        self._build()

    def _build(self):
        section_header(self, "Mieter", "＋ Mieter", self._new)
        cols = ("Name", "Wohnung", "Kaltmiete", "NK-Voraus.", "Einzug", "Telefon", "IBAN")
        f, self.tree = make_table(self, cols, height=16)
        f.pack(fill="both", expand=True, padx=20, pady=10)
        for c, w in zip(cols, [160, 130, 110, 110, 110, 130, 180]):
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
                r["telefon"] or "–",
                r["iban"] or "–"
            ))
        conn.close()

    def _new(self):
        if not hat_recht("Mieter", "schreiben"):
            messagebox.showwarning("Berechtigung", "Sie haben keine Schreibberechtigung.", parent=self); return
        d = MieterDialog(self)
        self.wait_window(d)
        if d.result:
            v = d.result
            conn = get_db()
            conn.execute("INSERT INTO mieter (vorname,name,strasse,ort,land,telefon,email,iban,wohnung_id,einzug,kaltmiete,nebenkosten_vorauszahlung,kaution,notizen) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (v["vorname"], v["name"], v["strasse"], v["ort"], v["land"], v["telefon"], v["email"], v["iban"],
                 v["wohnung_id"], v["einzug"], v["kaltmiete"] or 0, v["nk"] or 0, v["kaution"] or 0, v["notizen"]))
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
            conn.execute("UPDATE mieter SET vorname=?,name=?,strasse=?,ort=?,land=?,telefon=?,email=?,iban=?,wohnung_id=?,einzug=?,kaltmiete=?,nebenkosten_vorauszahlung=?,kaution=?,notizen=? WHERE id=?",
                (v["vorname"], v["name"], v["strasse"], v["ort"], v["land"], v["telefon"], v["email"], v["iban"],
                 v["wohnung_id"], v["einzug"], v["kaltmiete"] or 0, v["nk"] or 0, v["kaution"] or 0, v["notizen"], mid))
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
        # Row 2: Straße + Ort
        two = tk.Frame(self._body, bg=BG_CARD); two.pack(fill="x", padx=20); two.columnconfigure((0,1), weight=1)
        l = tk.Frame(two, bg=BG_CARD); l.grid(row=0, column=0, padx=(0,6), sticky="ew")
        ri = tk.Frame(two, bg=BG_CARD); ri.grid(row=0, column=1, padx=(6,0), sticky="ew")
        self._add_field("Straße", "strasse", r.get("strasse",""), row=l)
        self._add_field("Ort", "ort", r.get("ort",""), row=ri)
        # Row 3: Land + Telefon
        two = tk.Frame(self._body, bg=BG_CARD); two.pack(fill="x", padx=20); two.columnconfigure((0,1), weight=1)
        l = tk.Frame(two, bg=BG_CARD); l.grid(row=0, column=0, padx=(0,6), sticky="ew")
        ri = tk.Frame(two, bg=BG_CARD); ri.grid(row=0, column=1, padx=(6,0), sticky="ew")
        self._add_field("Land", "land", r.get("land","Deutschland"), row=l)
        self._add_field("Telefon", "telefon", r.get("telefon",""), row=ri)
        # Row 4: E-Mail + IBAN
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
        self._add_field("Kaltmiete €", "kaltmiete", r.get("kaltmiete",""), row=ri)

        two = tk.Frame(self._body, bg=BG_CARD); two.pack(fill="x", padx=20); two.columnconfigure((0,1), weight=1)
        l = tk.Frame(two, bg=BG_CARD); l.grid(row=0, column=0, padx=(0,6), sticky="ew")
        ri = tk.Frame(two, bg=BG_CARD); ri.grid(row=0, column=1, padx=(6,0), sticky="ew")
        self._add_field("NK-Vorausz. €", "nk", r.get("nebenkosten_vorauszahlung",""), row=l)
        self._add_field("Kaution €", "kaution", r.get("kaution",""), row=ri)

        self._add_field("Notizen", "notizen", r.get("notizen",""), widget_type="text")

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
            mea_str = f"{mea:.1f}" if mea else "–"
            self.tree.insert("", "end", iid=r["id"], values=(
                full_name, r["ort"] or "–",
                r["telefon"] or "–",
                r["email"] or "–", r["iban"] or "–", mea_str))
        conn.close()

    def _new(self):
        if not hat_recht("Eigentümer", "schreiben"):
            messagebox.showwarning("Berechtigung", "Sie haben keine Schreibberechtigung.", parent=self); return
        d = EigentuemerDialog(self)
        self.wait_window(d)
        if d.result:
            v = d.result
            conn = get_db()
            conn.execute("INSERT INTO eigentuemer (vorname,name,strasse,ort,land,telefon,email,iban,anteil_prozent,einheit,notizen) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (v["vorname"], v["name"], v["strasse"], v["ort"], v["land"], v["telefon"], v["email"], v["iban"], v["anteil"] or 33.33, v["einheit"], v["notizen"]))
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
            conn.execute("UPDATE eigentuemer SET vorname=?,name=?,strasse=?,ort=?,land=?,telefon=?,email=?,iban=?,anteil_prozent=?,einheit=?,notizen=? WHERE id=?",
                (v["vorname"], v["name"], v["strasse"], v["ort"], v["land"], v["telefon"], v["email"], v["iban"], v["anteil"] or 33.33, v["einheit"], v["notizen"], int(sel[0])))
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
        # Row 2: Straße + Ort
        two = tk.Frame(self._body, bg=BG_CARD); two.pack(fill="x", padx=20); two.columnconfigure((0,1), weight=1)
        l = tk.Frame(two, bg=BG_CARD); l.grid(row=0, column=0, padx=(0,6), sticky="ew")
        ri = tk.Frame(two, bg=BG_CARD); ri.grid(row=0, column=1, padx=(6,0), sticky="ew")
        self._add_field("Straße", "strasse", r.get("strasse",""), row=l)
        self._add_field("Ort", "ort", r.get("ort",""), row=ri)
        # Row 3: Land + Telefon
        two = tk.Frame(self._body, bg=BG_CARD); two.pack(fill="x", padx=20); two.columnconfigure((0,1), weight=1)
        l = tk.Frame(two, bg=BG_CARD); l.grid(row=0, column=0, padx=(0,6), sticky="ew")
        ri = tk.Frame(two, bg=BG_CARD); ri.grid(row=0, column=1, padx=(6,0), sticky="ew")
        self._add_field("Land", "land", r.get("land","Deutschland"), row=l)
        self._add_field("Telefon", "telefon", r.get("telefon",""), row=ri)
        # Row 4: E-Mail + IBAN
        two = tk.Frame(self._body, bg=BG_CARD); two.pack(fill="x", padx=20); two.columnconfigure((0,1), weight=1)
        l = tk.Frame(two, bg=BG_CARD); l.grid(row=0, column=0, padx=(0,6), sticky="ew")
        ri = tk.Frame(two, bg=BG_CARD); ri.grid(row=0, column=1, padx=(6,0), sticky="ew")
        self._add_field("E-Mail", "email", r.get("email",""), row=l)
        self._add_field("IBAN", "iban", r.get("iban",""), row=ri)
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
            conn.close()
            if wohnungen:
                for w in wohnungen:
                    wrow = tk.Frame(woh_frame, bg=BG_INPUT)
                    wrow.pack(fill="x", pady=2, ipady=4)
                    mea = f"{w['mea_tausendstel']:.1f} ‰" if w["mea_tausendstel"] else "–"
                    flaeche = f"{w['nutzflaeche_qm']:.1f} m²" if w["nutzflaeche_qm"] else ""
                    info = f"  {w['bezeichnung']}  ·  {w['typ'] or '–'}  ·  {w['lage'] or '–'}  ·  {mea}"
                    if flaeche:
                        info += f"  ·  {flaeche}"
                    tk.Label(wrow, text=info, bg=BG_INPUT, fg=TEXT,
                             font=FONT_SMALL, anchor="w").pack(fill="x", padx=8)
            else:
                tk.Label(woh_frame, text="  Keine Wohnungen zugeordnet",
                         bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w")

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
            mea = f"{r['mea_tausendstel']:.1f}" if r["mea_tausendstel"] else "–"
            self.tree.insert("", "end", iid=r["id"], values=(
                r["bezeichnung"], r["typ"] or "–", r["lage"] or "–",
                f"{r['nutzflaeche_qm']:.1f}" if r["nutzflaeche_qm"] else "–",
                r["zimmer"] or "–", mea,
                ename, mname))
        conn.close()

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
        self._add_field("MEA Tausendstel", "mea_tausendstel", r.get("mea_tausendstel",""))
        self._add_field("MEA (Miteigentumsanteil)", "miteigentumsanteil", r.get("miteigentumsanteil",""))
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

    # Kostenkategorien gemäß WEG-Verwaltung (Notion: Kostenkategorie/Kostenart)
    KATEGORIEN = [
        # Laufende Betriebskosten
        "Heizung", "Wasser/Abwasser", "Allgemeinstrom",
        "Gebäudereinigung", "Hausmeister", "Winterdienst", "Gartenpflege",
        "Müllabfuhr", "Straßenreinigung",
        # Verwaltungskosten
        "Verwaltervergütung", "Bankgebühren", "Porto/Telefon",
        "Rechts-/Prozesskosten",
        # Instandhaltung & Wartung
        "Reparaturen", "Wartungsverträge", "Sanierung",
        # Versicherungen
        "Wohngebäudeversicherung", "Haftpflichtversicherung",
        "Elementar-/Glasversicherung",
        # Finanzplanung & Rücklagen
        "Erhaltungsrücklage", "Sonderumlage",
        # Einnahmen
        "Hausgeld", "Miete", "Nebenkosten-Vorauszahlung",
        # Sonstiges
        "Sonstiges",
        # Offen / Unkategorisiert
        "Kategorie offen",
    ]
    # Kostenkategorie-Zuordnung mit Metadaten
    KOSTENARTEN = {
        # Laufende Betriebskosten (umlagefähig)
        "Heizung":              {"kategorie": "Laufende Betriebskosten", "umlagefaehig": True,  "schluessel": "Verbrauch/Wohnfläche"},
        "Wasser/Abwasser":      {"kategorie": "Laufende Betriebskosten", "umlagefaehig": True,  "schluessel": "Verbrauch/Wohnfläche"},
        "Allgemeinstrom":       {"kategorie": "Laufende Betriebskosten", "umlagefaehig": True,  "schluessel": "MEA"},
        "Gebäudereinigung":     {"kategorie": "Laufende Betriebskosten", "umlagefaehig": True,  "schluessel": "MEA/Fläche"},
        "Hausmeister":          {"kategorie": "Laufende Betriebskosten", "umlagefaehig": True,  "schluessel": "MEA/Fläche"},
        "Winterdienst":         {"kategorie": "Laufende Betriebskosten", "umlagefaehig": True,  "schluessel": "MEA/Fläche"},
        "Gartenpflege":         {"kategorie": "Laufende Betriebskosten", "umlagefaehig": True,  "schluessel": "MEA/Fläche"},
        "Müllabfuhr":           {"kategorie": "Laufende Betriebskosten", "umlagefaehig": True,  "schluessel": "MEA/Wohneinheiten"},
        "Straßenreinigung":     {"kategorie": "Laufende Betriebskosten", "umlagefaehig": True,  "schluessel": "MEA/Wohneinheiten"},
        # Verwaltungskosten (nicht umlagefähig)
        "Verwaltervergütung":   {"kategorie": "Verwaltungskosten",       "umlagefaehig": False, "schluessel": "Wohneinheiten/MEA"},
        "Bankgebühren":         {"kategorie": "Verwaltungskosten",       "umlagefaehig": False, "schluessel": "MEA/Wohneinheiten"},
        "Porto/Telefon":        {"kategorie": "Verwaltungskosten",       "umlagefaehig": False, "schluessel": "MEA/Wohneinheiten"},
        "Rechts-/Prozesskosten":{"kategorie": "Verwaltungskosten",       "umlagefaehig": False, "schluessel": "MEA"},
        # Instandhaltung & Wartung
        "Reparaturen":          {"kategorie": "Instandhaltung & Wartung","umlagefaehig": False, "schluessel": "MEA"},
        "Wartungsverträge":     {"kategorie": "Instandhaltung & Wartung","umlagefaehig": "Teilweise", "schluessel": "MEA/Wohneinheiten"},
        "Sanierung":            {"kategorie": "Instandhaltung & Wartung","umlagefaehig": False, "schluessel": "MEA"},
        # Versicherungen (umlagefähig)
        "Wohngebäudeversicherung":  {"kategorie": "Versicherungen",      "umlagefaehig": True,  "schluessel": "MEA"},
        "Haftpflichtversicherung":  {"kategorie": "Versicherungen",      "umlagefaehig": True,  "schluessel": "MEA"},
        "Elementar-/Glasversicherung":{"kategorie": "Versicherungen",    "umlagefaehig": True,  "schluessel": "MEA"},
        # Finanzplanung & Rücklagen
        "Erhaltungsrücklage":   {"kategorie": "Finanzplanung & Rücklagen","umlagefaehig": False,"schluessel": "MEA"},
        "Sonderumlage":         {"kategorie": "Finanzplanung & Rücklagen","umlagefaehig": False,"schluessel": "MEA"},
        # Einnahmen
        "Hausgeld":             {"kategorie": "Einnahmen",               "umlagefaehig": False, "schluessel": "–"},
        "Miete":                {"kategorie": "Einnahmen",               "umlagefaehig": False, "schluessel": "–"},
        "Nebenkosten-Vorauszahlung":{"kategorie": "Einnahmen",           "umlagefaehig": False, "schluessel": "–"},
        # Sonstiges
        "Sonstiges":            {"kategorie": "Sonstiges",               "umlagefaehig": False, "schluessel": "–"},
        "Kategorie offen":      {"kategorie": "Offen",                   "umlagefaehig": False, "schluessel": "–"},
    }

    def __init__(self, parent):
        super().__init__(parent, bg=BG_CARD)
        self._active_tab = "buchungen"
        self._build()

    # ── Aufbau ────────────────────────────────────────────────────────────────

    def _build(self):
        # ── Kopfzeile ─────────────────────────────────────────────────────────
        top = tk.Frame(self, bg=BG_CARD)
        top.pack(fill="x", padx=20, pady=(16, 0))
        self._saldo_label = tk.Label(top, text="", bg=BG_CARD, fg=TEXT, font=FONT_H2)
        self._saldo_label.pack(side="left")
        make_btn(top, "＋ Buchung",    self._new_zahlung).pack(side="right")
        make_btn(top, "📊 Export CSV", self._export_csv,
                 color=BG_INPUT, fg=TEXT).pack(side="right", padx=(0, 8))

        # ── Sub-Tab-Leiste ─────────────────────────────────────────────────────
        self._tab_btns = {}
        tab_bar = tk.Frame(self, bg=BG_CARD)
        tab_bar.pack(fill="x", padx=20, pady=(8, 0))
        for tid, label in [("buchungen",  "📒  Buchungen"),
                            ("vorschlaege","🔔  Kontoauszug Vorschläge"),
                            ("regeln",    "⚙  Buchungsregeln"),
                            ("kostenarten","📋  Kostenarten")]:
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
        cols_b = ("Datum", "Beschreibung", "Kategorie", "Betrag", "Typ", "Status", "Belegnr.")
        fb, self.tree_b = make_table(self._view_buchungen, cols_b, height=13)
        fb.pack(fill="both", expand=True, padx=20, pady=6)
        for c, w in zip(cols_b, [90, 210, 110, 100, 80, 80, 80]):
            self.tree_b.heading(c, text=c); self.tree_b.column(c, width=w, anchor="w")
        self.tree_b.tag_configure("einnahme", foreground=SUCCESS)
        self.tree_b.tag_configure("ausgabe",  foreground=DANGER)
        self.tree_b.tag_configure("neu", foreground=ACCENT2, font=("Segoe UI Semibold", 10))
        self.tree_b.bind("<Double-1>", self._edit_buchung)
        btn_b = tk.Frame(self._view_buchungen, bg=BG_CARD)
        btn_b.pack(fill="x", padx=20, pady=(0, 8))
        make_btn(btn_b, "✏ Bearbeiten",       self._edit_buchung, color=BG_INPUT, fg=TEXT).pack(side="left", padx=(0,6))
        make_btn(btn_b, "🗑 Löschen",         self._delete_buchung, color=DANGER).pack(side="left")

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
        for v in [self._view_buchungen, self._view_vorschlaege, self._view_regeln, self._view_kostenarten]:
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

    # ── Tab 1: Buchungen ──────────────────────────────────────────────────────

    def _load_buchungen(self):
        for i in self.tree_b.get_children(): self.tree_b.delete(i)
        conn = get_db()
        typ = self._typ_var.get()
        q = "SELECT * FROM zahlungen"
        if typ != "Alle":
            q += f" WHERE typ='{typ}'"
        q += " ORDER BY datum DESC, erstellt_am DESC"
        einnahmen = ausgaben = 0.0
        for r in conn.execute(q):
            rd = dict(r)
            status = rd.get("status") or "Geprüft"
            tags_list = ["einnahme" if rd["typ"] == "Einnahme" else "ausgabe"]
            if status == "Neu":
                tags_list.append("neu")
            self.tree_b.insert("", "end", iid=rd["id"], values=(
                fmt_date(rd["datum"]), rd["beschreibung"] or "–",
                rd["kategorie"] or "–", fmt_euro(rd["betrag"]),
                rd["typ"], status, rd["belegnr"] or "–"), tags=tuple(tags_list))
            if rd["typ"] == "Einnahme": einnahmen += rd["betrag"] or 0
            else:                       ausgaben  += abs(rd["betrag"] or 0)
        conn.close()
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
                "INSERT INTO zahlungen (datum,betrag,typ,kategorie,beschreibung,belegnr,status) "
                "VALUES (?,?,?,?,?,?,?)",
                (v["datum"], betrag, v["typ"], v["kategorie"], v["beschreibung"], v["belegnr"],
                 v.get("status", "Geprüft")))
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
                "UPDATE zahlungen SET datum=?,betrag=?,typ=?,kategorie=?,beschreibung=?,belegnr=?,status=? "
                "WHERE id=?",
                (v["datum"], betrag, v["typ"], v["kategorie"],
                 v["beschreibung"], v["belegnr"], v.get("status", "Geprüft"), int(sel[0])))
            conn.commit(); conn.close()
            self._load_buchungen()

    def _delete_buchung(self):
        if not hat_recht("Buchhaltung", "loeschen"):
            messagebox.showwarning("Berechtigung", "Keine Löschberechtigung.", parent=self); return
        sel = self.tree_b.selection()
        if not sel: return
        if messagebox.askyesno("Löschen", "Buchung unwiderruflich löschen?"):
            conn = get_db()
            conn.execute("DELETE FROM zahlungen WHERE id=?", (int(sel[0]),))
            conn.commit(); conn.close()
            self._load_buchungen()

    def _export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv",
            filetypes=[("CSV", "*.csv")], title="Buchungen exportieren")
        if not path: return
        conn = get_db()
        rows = conn.execute(
            "SELECT datum,beschreibung,kategorie,betrag,typ,belegnr "
            "FROM zahlungen ORDER BY datum DESC").fetchall()
        conn.close()
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["Datum", "Beschreibung", "Kategorie", "Betrag", "Typ", "Belegnr."])
            for r in rows:
                w.writerow([fmt_date(r[0]), r[1], r[2],
                             str(r[3]).replace(".", ","), r[4], r[5]])
        messagebox.showinfo("Export", f"Exportiert: {os.path.basename(path)}")

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
            vorschlag  = r.get("kategorie_vorschlag") or vorschlag_kategorie(raw)[0]
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
        kat_v, typ_v, kto_v = vorschlag_kategorie(raw)
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
        """Alle grün markierten Vorschläge (mit Kategorie-Vorschlag) automatisch übernehmen."""
        if not hat_recht("Buchhaltung", "schreiben"):
            messagebox.showwarning("Berechtigung", "Keine Schreibberechtigung.", parent=self)
            return
        conn = get_db()
        # Alle nicht übernommenen Einträge MIT Kategorie-Vorschlag
        q = ("SELECT * FROM kontoauszug "
             "WHERE (als_buchung_uebernommen IS NULL OR als_buchung_uebernommen=0) "
             "AND (falsch_zugeordnet IS NULL OR falsch_zugeordnet=0) ")
        params = []
        selected_iban = self._vs_iban_map.get(self._vs_konto_var.get())
        if selected_iban:
            q += "AND iban=? "
            params.append(selected_iban)
        q += "ORDER BY datum"
        rows = conn.execute(q, params).fetchall()
        count = 0
        for row_raw in rows:
            row = dict(row_raw)
            raw = row["buchungstext"] or ""
            kat = row.get("kategorie_vorschlag") or vorschlag_kategorie(raw)[0]
            if not kat:
                continue  # Kein Vorschlag → überspringen
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
            lerne_buchung(raw, kat, typ, kt)
            count += 1
        conn.commit()
        conn.close()
        if count:
            messagebox.showinfo("Batch-Übernahme", f"{count} Vorschläge automatisch übernommen.")
        else:
            messagebox.showinfo("Batch-Übernahme", "Keine Vorschläge mit Kategorie-Zuordnung vorhanden.")
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
        kat_v = row.get("kategorie_vorschlag") or vorschlag_kategorie(raw)[0]
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
        super().__init__(parent, "Buchung", 480, 480)
        r = dict(row) if row else {}
        self._add_field("Datum (JJJJ-MM-TT) *", "datum",
                        r.get("datum", date.today().isoformat()))
        self._add_field("Typ *", "typ", r.get("typ", "Einnahme"),
                        widget_type="combo", options=["Einnahme", "Ausgabe"])
        self._add_field("Betrag € *", "betrag", abs(r.get("betrag", 0) or 0))
        self._add_field("Kategorie", "kategorie", r.get("kategorie", ""),
                        widget_type="combo",
                        options=BuchhaltungPage.aktive_kategorien())
        self._add_field("Beschreibung", "beschreibung", r.get("beschreibung", ""))
        self._add_field("Belegnummer",  "belegnr",      r.get("belegnr", ""))
        self._add_field("Status", "status", r.get("status", "Neu"),
                        widget_type="combo", options=["Neu", "Geprüft", "Freigegeben"])

    def _on_save(self):
        v = self._get_values()
        if not v.get("datum") or not v.get("betrag"):
            messagebox.showwarning("Pflichtfelder", "Datum und Betrag sind erforderlich.", parent=self); return
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
        if s != "Alle": q += f" WHERE status='{s}'"
        q += " ORDER BY CASE prioritaet WHEN 'Hoch' THEN 1 WHEN 'Mittel' THEN 2 ELSE 3 END, erstellt_am DESC"
        for r in conn.execute(q):
            self.tree.insert("", "end", iid=r["id"], values=(
                r["titel"], r["einheit"] or "–", r["prioritaet"],
                r["status"], fmt_date(r["erstellt_am"]),
                fmt_euro(r["kosten"]) if r["kosten"] else "–"))
        conn.close()

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
        self.tree.bind("<Double-1>", self._read)

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

    def _read(self, event=None):
        sel = self.tree.selection()
        if not sel: return
        conn = get_db()
        conn.execute("UPDATE nachrichten SET gelesen=1 WHERE id=?", (int(sel[0]),))
        conn.commit(); conn.close(); self._load()

    def _mark_read(self):
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
        path = filedialog.askopenfilename(title="Datei auswählen")
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
    def __init__(self, parent):
        super().__init__(parent, bg=BG_CARD)
        self._build()

    def _build(self):
        top = tk.Frame(self, bg=BG_CARD)
        top.pack(fill="x", padx=20, pady=(18, 0))
        tk.Label(top, text="Nebenkostenabrechnung", bg=BG_CARD, fg=TEXT, font=FONT_H2).pack(side="left")
        make_btn(top, "＋ Eintrag", self._new).pack(side="right")
        make_btn(top, "📊 Jahresauswertung", self._jahresauswertung,
                 color=BG_INPUT, fg=TEXT).pack(side="right", padx=(0, 8))
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=20)

        cols = ("Jahr", "Monat", "Kategorie", "Betrag", "Umlage", "Notizen")
        f, self.tree = make_table(self, cols, height=16)
        f.pack(fill="both", expand=True, padx=20, pady=8)
        for c, w in zip(cols, [60, 60, 160, 100, 140, 200]):
            self.tree.heading(c, text=c); self.tree.column(c, width=w, anchor="w")

        self.tree.bind("<Double-1>", self._edit)
        btn_row = tk.Frame(self, bg=BG_CARD)
        btn_row.pack(fill="x", padx=20, pady=(0, 10))
        if hat_recht("Nebenkosten", "schreiben"):
            make_btn(btn_row, "✏ Bearbeiten", self._edit, color=BG_INPUT, fg=TEXT).pack(side="left", padx=(0, 8))
        if hat_recht("Nebenkosten", "loeschen"):
            make_btn(btn_row, "🗑 Löschen", self._delete, color=DANGER).pack(side="left")
        self._load()

    def _load(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = get_db()
        for r in conn.execute("SELECT * FROM nebenkosten ORDER BY jahr DESC, monat DESC"):
            self.tree.insert("", "end", iid=r["id"], values=(
                r["jahr"], r["monat"] or "–", r["kategorie"],
                fmt_euro(r["betrag"]), r["umlageschluessel"] or "–",
                r["notizen"] or "–"))
        conn.close()

    def _new(self):
        if not hat_recht("Nebenkosten", "schreiben"):
            messagebox.showwarning("Berechtigung", "Keine Schreibberechtigung.", parent=self); return
        d = NebenkostenDialog(self)
        self.wait_window(d)
        if d.result:
            v = d.result
            conn = get_db()
            conn.execute("INSERT INTO nebenkosten (jahr,monat,kategorie,betrag,umlageschluessel,notizen) VALUES (?,?,?,?,?,?)",
                (v["jahr"] or date.today().year, v["monat"] or "",
                 v["kategorie"], v["betrag"] or 0,
                 v["umlage"], v["notizen"]))
            conn.commit(); conn.close(); self._load()

    def _edit(self, event=None):
        if not hat_recht("Nebenkosten", "schreiben"):
            messagebox.showwarning("Berechtigung", "Keine Schreibberechtigung.", parent=self); return
        sel = self.tree.selection()
        if not sel: return
        conn = get_db()
        row = conn.execute("SELECT * FROM nebenkosten WHERE id=?", (int(sel[0]),)).fetchone()
        conn.close()
        d = NebenkostenDialog(self, row)
        self.wait_window(d)
        if d.result:
            v = d.result
            conn = get_db()
            conn.execute("UPDATE nebenkosten SET jahr=?,monat=?,kategorie=?,betrag=?,umlageschluessel=?,notizen=? WHERE id=?",
                (v["jahr"] or date.today().year, v["monat"] or "",
                 v["kategorie"], v["betrag"] or 0,
                 v["umlage"], v["notizen"], int(sel[0])))
            conn.commit(); conn.close(); self._load()

    def _delete(self):
        if not hat_recht("Nebenkosten", "loeschen"):
            messagebox.showwarning("Berechtigung", "Keine Löschberechtigung.", parent=self); return
        sel = self.tree.selection()
        if not sel: return
        if messagebox.askyesno("Löschen", "Eintrag löschen?"):
            conn = get_db()
            conn.execute("DELETE FROM nebenkosten WHERE id=?", (int(sel[0]),))
            conn.commit(); conn.close(); self._load()

    def _jahresauswertung(self):
        jahr = simpledialog.askinteger("Jahr", "Auswertungsjahr:", initialvalue=date.today().year, parent=self)
        if not jahr: return
        conn = get_db()
        rows   = conn.execute(
            "SELECT kategorie, SUM(betrag) as gesamt FROM nebenkosten WHERE jahr=? GROUP BY kategorie ORDER BY gesamt DESC",
            (jahr,)).fetchall()
        mieter = conn.execute("SELECT name, nebenkosten_vorauszahlung FROM mieter").fetchall()
        conn.close()

        win = tk.Toplevel(self)
        win.title(f"Nebenkostenauswertung {jahr}")
        win.geometry("520x500")
        win.configure(bg=BG_CARD)

        tk.Frame(win, bg=BG_SIDEBAR, height=46).pack(fill="x")
        tk.Label(win, text=f"  Jahresauswertung {jahr}", bg=BG_SIDEBAR, fg=TEXT_WHITE,
                 font=FONT_H3).place(x=0, y=8, width=520)

        body = tk.Frame(win, bg=BG_CARD)
        body.pack(fill="both", expand=True, padx=20, pady=14)

        total_kosten      = sum(r["gesamt"] for r in rows)
        total_vorauszahl  = sum((m["nebenkosten_vorauszahlung"] or 0) * 12 for m in mieter)
        differenz         = total_vorauszahl - total_kosten

        tk.Label(body, text="Gesamtkosten:", bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w")
        tk.Label(body, text=fmt_euro(total_kosten), bg=BG_CARD, fg=TEXT, font=FONT_H2).pack(anchor="w")
        tk.Label(body, text="Vorauszahlungen gesamt:", bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w", pady=(8, 0))
        tk.Label(body, text=fmt_euro(total_vorauszahl), bg=BG_CARD, fg=TEXT, font=FONT_H2).pack(anchor="w")

        color = SUCCESS if differenz >= 0 else DANGER
        label = "Guthaben für Mieter:" if differenz >= 0 else "Nachzahlung Mieter:"
        tk.Label(body, text=label, bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w", pady=(8, 0))
        tk.Label(body, text=fmt_euro(abs(differenz)), bg=BG_CARD, fg=color, font=FONT_H2).pack(anchor="w")

        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=10)
        tk.Label(body, text="Kosten nach Kategorie:", bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w")
        for r in rows:
            row = tk.Frame(body, bg=BG_CARD)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=r["kategorie"], bg=BG_CARD, fg=TEXT,       font=FONT_BODY).pack(side="left")
            tk.Label(row, text=fmt_euro(r["gesamt"]), bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_MONO).pack(side="right")


class NebenkostenDialog(BaseDialog):
    def __init__(self, parent, row=None):
        super().__init__(parent, "Nebenkosteneintrag", 460, 420)
        r = dict(row) if row else {}
        # Row 1: Jahr + Monat
        two = tk.Frame(self._body, bg=BG_CARD)
        two.pack(fill="x", padx=20)
        two.columnconfigure((0, 1), weight=1)
        l  = tk.Frame(two, bg=BG_CARD); l.grid(row=0, column=0, padx=(0, 6), sticky="ew")
        ri = tk.Frame(two, bg=BG_CARD); ri.grid(row=0, column=1, padx=(6, 0), sticky="ew")
        self._add_field("Jahr",          "jahr",  r.get("jahr", date.today().year), row=l)
        self._add_field("Monat (1-12)",  "monat", r.get("monat", ""),                row=ri)
        # Single fields
        self._add_field("Kategorie *",   "kategorie", r.get("kategorie", "Heizung"),
                        widget_type="combo",
                        options=["Heizung", "Wasser", "Müll", "Versicherung", "Hausmeister", "Strom", "Sonstiges"])
        self._add_field("Betrag €",      "betrag",  r.get("betrag", ""))
        self._add_field("Umlageschlüssel","umlage", r.get("umlageschluessel", "Wohnfläche"),
                        widget_type="combo",
                        options=["Wohnfläche", "Personenanzahl", "Einheiten gleich", "Verbrauch"])
        self._add_field("Notizen",       "notizen", r.get("notizen", ""))

    def _on_save(self):
        v = self._get_values()
        if not v.get("kategorie"):
            messagebox.showwarning("Pflichtfeld", "Kategorie ist erforderlich.", parent=self); return
        self.result = v; self.destroy()

# ── Kontoauszug-Seite ─────────────────────────────────────────────────────────



class AufteilungenPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_CARD)
        self._build()

    def _build(self):
        section_header(self, "Aufteilungen", "＋ Aufteilung", self._new)
        tk.Label(self, text="Umlageschlüssel und Verteilungsregeln für Nebenkosten",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w", padx=20, pady=(0,8))
        cols = ("Name", "Typ", "Bezug / Einheit", "Wert", "Notizen")
        f, self.tree = make_table(self, cols, height=16)
        f.pack(fill="both", expand=True, padx=20, pady=8)
        for c, w in zip(cols, [180, 140, 160, 100, 220]):
            self.tree.heading(c, text=c); self.tree.column(c, width=w, anchor="w")
        self.tree.bind("<Double-1>", self._edit)
        btn_row = tk.Frame(self, bg=BG_CARD)
        btn_row.pack(fill="x", padx=20, pady=(0,10))
        if hat_recht("Aufteilungen", "schreiben"):
            make_btn(btn_row, "✏ Bearbeiten", self._edit, color=BG_INPUT, fg=TEXT).pack(side="left", padx=(0,8))
        if hat_recht("Aufteilungen", "loeschen"):
            make_btn(btn_row, "🗑 Löschen", self._delete, color=DANGER).pack(side="left")
        self._load()

    def _load(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = get_db()
        for r in conn.execute("SELECT * FROM aufteilungen ORDER BY name"):
            self.tree.insert("", "end", iid=r["id"], values=(
                r["name"], r["typ"] or "–", r["bezug"] or "–",
                r["wert"] or "–", r["notizen"] or "–"))
        conn.close()

    def _new(self):
        if not hat_recht("Aufteilungen", "schreiben"):
            messagebox.showwarning("Berechtigung", "Keine Schreibberechtigung.", parent=self); return
        d = AufteilungDialog(self)
        self.wait_window(d)
        if d.result:
            v = d.result
            conn = get_db()
            conn.execute("INSERT INTO aufteilungen (name,beschreibung,typ,bezug,wert,notizen) VALUES (?,?,?,?,?,?)",
                (v["name"], v["beschreibung"], v["typ"], v["bezug"], v["wert"] or None, v["notizen"]))
            conn.commit(); conn.close(); self._load()

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
            conn.execute("UPDATE aufteilungen SET name=?,beschreibung=?,typ=?,bezug=?,wert=?,notizen=? WHERE id=?",
                (v["name"], v["beschreibung"], v["typ"], v["bezug"], v["wert"] or None, v["notizen"], int(sel[0])))
            conn.commit(); conn.close(); self._load()

    def _delete(self):
        if not hat_recht("Aufteilungen", "loeschen"):
            messagebox.showwarning("Berechtigung", "Keine Löschberechtigung.", parent=self); return
        sel = self.tree.selection()
        if not sel: return
        if messagebox.askyesno("Löschen", "Aufteilung löschen?"):
            conn = get_db()
            conn.execute("DELETE FROM aufteilungen WHERE id=?", (int(sel[0]),))
            conn.commit(); conn.close(); self._load()


class AufteilungDialog(BaseDialog):
    def __init__(self, parent, row=None):
        super().__init__(parent, "Aufteilung " + ("bearbeiten" if row else "hinzufügen"), 480, 560)
        r = dict(row) if row else {}
        self._add_field("Name *", "name", r.get("name",""))
        self._add_field("Typ", "typ", r.get("typ","Wohnfläche"),
                        widget_type="combo",
                        options=["Wohnfläche", "Personenanzahl", "Einheiten gleich", "Verbrauch", "MEA", "Sonstiges"])
        self._add_field("Bezug / Einheit", "bezug", r.get("bezug",""))
        self._add_field("Wert", "wert", r.get("wert",""))
        self._add_field("Beschreibung", "beschreibung", r.get("beschreibung",""))
        self._add_field("Notizen", "notizen", r.get("notizen",""), widget_type="text")

    def _on_save(self):
        v = self._get_values()
        if not v.get("name"):
            messagebox.showwarning("Pflichtfeld", "Name ist erforderlich.", parent=self); return
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
        """Gibt den Standard-Importpfad aus den Einstellungen zurück."""
        cfg = load_config()
        d = cfg.get("pfad_kontoauszug_import", "")
        if d and os.path.isdir(d):
            return d
        return None

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
                for datum, buchungstext, betrag in buchungen:
                    # Dublettenprüfung: gleiche Buchung bereits vorhanden?
                    existing = conn.execute(
                        "SELECT COUNT(*) FROM kontoauszug WHERE datum=? AND buchungstext=? AND betrag=? AND iban=?",
                        (datum, buchungstext, betrag, iban)).fetchone()[0]
                    if existing:
                        dup_count += 1
                        continue

                    # Kategorie-Vorschlag ermitteln
                    kat, typ, kt = vorschlag_kategorie(buchungstext)
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
                        conn.execute(
                            "INSERT INTO zahlungen (datum,betrag,typ,kategorie,beschreibung,konto_typ,status) "
                            "VALUES (?,?,?,?,?,?,?)",
                            (datum, betrag, typ, kat, beschr[:200], kt, "Neu"))
                        zahlung_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                        conn.execute(
                            "UPDATE kontoauszug SET als_buchung_uebernommen=1, zugeordnet=1, zahlung_id=? WHERE id=?",
                            (zahlung_id, ka_id))
                        lerne_buchung(buchungstext, kat, typ, kt)
                        auto_count += 1
                conn.commit()
                gesamt_buchungen += imp_count
                gesamt_auto += auto_count
                gesamt_duplikate += dup_count
                letzte_bank = bank
                letzte_iban = iban
                letzte_saldo = saldo
            except Exception as exc:
                fehler_dateien.append(f"{os.path.basename(path)}: {exc}")
        conn.close()

        # Ergebnis-Meldung
        saldo_str = fmt_euro(letzte_saldo) if letzte_saldo is not None else "–"
        msg = f"{gesamt_buchungen} Buchung(en) aus {len(paths)} Datei(en) importiert"
        if gesamt_duplikate:
            msg += f"\n{gesamt_duplikate} Duplikat(e) übersprungen"
        if gesamt_auto:
            msg += f"\nDavon automatisch gebucht: {gesamt_auto}"
        if fehler_dateien:
            msg += f"\n\n⚠ Fehler in {len(fehler_dateien)} Datei(en):\n" + "\n".join(fehler_dateien[:5])
        messagebox.showinfo("CAMT.052 Import", msg)
        if letzte_iban:
            self._info_var.set(
                f"Zuletzt importiert: {letzte_bank} · ···{letzte_iban[-8:]} · Saldo {saldo_str}")
        self._load()

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



class EinstellungenPage(tk.Frame):
    """Einstellungen-Seite: Speicherpfade und Konfiguration."""

    def __init__(self, parent):
        super().__init__(parent, bg=BG_CARD)
        self._cfg = load_config()
        self._vars = {}
        self._build()

    def _build(self):
        # Scrollbarer Inhalt
        canvas = tk.Canvas(self, bg=BG_CARD, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        self._inner = tk.Frame(canvas, bg=BG_CARD)
        canvas_window = canvas.create_window((0,0), window=self._inner, anchor="nw")
        self._inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))

        body = self._inner
        
        # Header
        tk.Label(body, text="Einstellungen", bg=BG_CARD, fg=TEXT,
                 font=FONT_H2).pack(anchor="w", padx=20, pady=(18,6))
        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", padx=20)
        
        cfg_path_text = str(CONFIG_PATH)
        tk.Label(body, text=f"Konfigurationsdatei: {cfg_path_text}",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w", padx=20, pady=(6,12))

        # Section: WEG-Stammdaten
        self._section(body, "WEG-Stammdaten")
        self._path_field(body, "WEG-Name", "weg_name", is_path=False)
        self._path_field(body, "Adresse (Straße, PLZ Ort)", "weg_adresse", is_path=False)

        # Section: Konten (nur Wohngeld + Rücklage)
        self._section(body, "Konten")
        self._path_field(body, "Bezeichnung Wohngeldkonto", "bez_wohngeld", is_path=False)
        self._iban_field(body, "IBAN Wohngeldkonto", "iban_wohngeld")
        self._path_field(body, "Bezeichnung Rücklagenkonto", "bez_ruecklage", is_path=False)
        self._iban_field(body, "IBAN Rücklagenkonto", "iban_ruecklage")

        # Section: Speicherpfade Kontoauszüge
        self._section(body, "Speicherpfade Kontoauszüge")
        self._path_field(body, "Standard-Importordner Kontoauszüge", "pfad_kontoauszug_import", is_path=True, is_dir=True)

        # Section: Weitere Speicherpfade
        self._section(body, "Weitere Speicherpfade")
        self._path_field(body, "Ordner Dokumente / Belege", "pfad_dokumente", is_path=True, is_dir=True)
        self._path_field(body, "Ordner Datenbank-Backup", "pfad_backup", is_path=True, is_dir=True)
        self._path_field(body, "Datenbankdatei (hausverwaltung.db)", "pfad_datenbank", is_path=True, is_dir=False)

        # Speichern-Button
        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(20,0))
        btn_row = tk.Frame(body, bg=BG_CARD)
        btn_row.pack(fill="x", padx=20, pady=12)
        make_btn(btn_row, "💾 Einstellungen speichern", self._save, color=SUCCESS).pack(side="left")

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
        save_config(self._cfg)
        messagebox.showinfo("Gespeichert", "Einstellungen wurden gespeichert.\n" + str(CONFIG_PATH))

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
                "Nachrichten", "Dokumente", "Benutzer", "Rollen & Rechte", "Einstellungen"]

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
        ("⚖",  "Aufteilungen",   AufteilungenPage),
        ("✉️",  "Nachrichten",    NachrichtenPage),
        ("📁", "Dokumente",      DokumentePage),
        ("👤", "Benutzer",       BenutzerverwaltungPage),
        ("🔐", "Rollen & Rechte",RollenverwaltungPage),
        ("⚙",  "Einstellungen",  EinstellungenPage),
    ]

    def __init__(self):
        super().__init__()
        self.withdraw()
        init_db()
        login = LoginDialog(self)
        self.wait_window(login)
        if not login.result:
            self.destroy()
            return
        global _CURRENT_USER
        self._current_user = login.result
        _CURRENT_USER = login.result
        self.deiconify()
        self.title(f"Hausverwaltung v{APP_VERSION} – {login.result['benutzername']}")
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
        tk.Label(info, text="Hausverwaltung", bg=BG_SIDEBAR, fg=TEXT_WHITE,
                 font=("Segoe UI Semibold", 10)).pack(anchor="w")
        tk.Label(info, text="Musterstraße 12", bg=BG_SIDEBAR, fg=SIDEBAR_FG,
                 font=FONT_SMALL).pack(anchor="w")

        tk.Frame(sidebar, bg="#2C3E50", height=1).pack(fill="x", padx=12)

        self._nav_btns = []
        nav_frame = tk.Frame(sidebar, bg=BG_SIDEBAR)
        nav_frame.pack(fill="x", pady=8)

        for i, (icon, label, _) in enumerate(self.PAGES):
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


if __name__ == "__main__":
    app = HausverwaltungApp()
    app.mainloop()
