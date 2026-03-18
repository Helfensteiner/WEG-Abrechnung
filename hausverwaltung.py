"""
Hausverwaltung – Eigentümergemeinschaft
Desktop-App mit Tkinter · SQLite-Datenbank
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import sqlite3
import json
import os
import csv
import re
from datetime import datetime, date
from pathlib import Path

DB_PATH = Path.home() / "hausverwaltung.db"

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
""")
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

class BaseDialog(tk.Toplevel):
    def __init__(self, parent, title, width=500, height=520):
        super().__init__(parent)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.configure(bg=BG_CARD)
        self.resizable(False, False)
        self.grab_set()
        self.result = None
        self._fields = {}

        header = tk.Frame(self, bg=BG_SIDEBAR, height=48)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=title, bg=BG_SIDEBAR, fg=TEXT_WHITE,
                 font=FONT_H3).pack(side="left", padx=16, pady=12)

        self._body = tk.Frame(self, bg=BG_CARD)
        self._body.pack(fill="both", expand=True, padx=20, pady=12)

        self._btn_row = tk.Frame(self, bg=BG_CARD)
        self._btn_row.pack(fill="x", padx=20, pady=(0, 16))
        make_btn(self._btn_row, "Abbrechen", self.destroy,
                 color=BG_INPUT, fg=TEXT).pack(side="right", padx=(8, 0))
        make_btn(self._btn_row, "Speichern", self._on_save,
                 color=ACCENT2).pack(side="right")

    def _add_field(self, label, key, default="", widget_type="entry", options=None, row=None):
        frame = self._body if row is None else row
        tk.Label(frame, text=label, bg=BG_CARD, fg=TEXT_LIGHT,
                 font=FONT_SMALL).pack(anchor="w", pady=(8, 1))
        if widget_type == "entry":
            var = tk.StringVar(value=str(default) if default else "")
            w   = make_entry(frame, textvariable=var)
            w.pack(fill="x", ipady=6)
            self._fields[key] = var
        elif widget_type == "text":
            w = tk.Text(frame, height=3, bg=BG_INPUT, fg=TEXT,
                        relief="flat", font=FONT_BODY, bd=0, padx=6, pady=4)
            w.pack(fill="x")
            if default:
                w.insert("1.0", str(default))
            self._fields[key] = w
        elif widget_type == "combo":
            var = tk.StringVar(value=str(default) if default else "")
            w   = ttk.Combobox(frame, textvariable=var, values=options or [],
                               state="readonly", font=FONT_BODY)
            w.pack(fill="x", ipady=4)
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
        cols = ("Name", "Einheit", "Kaltmiete", "NK-Voraus.", "Einzug", "Kaution", "Tel.")
        f, self.tree = make_table(self, cols, height=16)
        f.pack(fill="both", expand=True, padx=20, pady=10)
        for c, w in zip(cols, [160, 130, 100, 100, 100, 100, 130]):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="w")
        self.tree.bind("<Double-1>", self._edit)
        self._load()
        btn_row = tk.Frame(self, bg=BG_CARD)
        btn_row.pack(fill="x", padx=20, pady=(0, 10))
        make_btn(btn_row, "✏ Bearbeiten", self._edit, color=BG_INPUT, fg=TEXT).pack(side="left", padx=(0, 8))
        make_btn(btn_row, "🗑 Löschen",   self._delete, color=DANGER).pack(side="left")

    def _load(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = get_db()
        for r in conn.execute("SELECT * FROM mieter ORDER BY name"):
            self.tree.insert("", "end", iid=r["id"], values=(
                r["name"], r["einheit"] or "–",
                fmt_euro(r["kaltmiete"]),
                fmt_euro(r["nebenkosten_vorauszahlung"]),
                fmt_date(r["einzug"]),
                fmt_euro(r["kaution"]),
                r["telefon"] or "–"
            ))
        conn.close()

    def _new(self):
        d = MieterDialog(self)
        self.wait_window(d)
        if d.result:
            v = d.result
            conn = get_db()
            conn.execute("INSERT INTO mieter (name,email,telefon,einheit,einzug,kaltmiete,nebenkosten_vorauszahlung,kaution,notizen) VALUES (?,?,?,?,?,?,?,?,?)",
                (v["name"], v["email"], v["telefon"], v["einheit"], v["einzug"],
                 v["kaltmiete"] or 0, v["nk"] or 0, v["kaution"] or 0, v["notizen"]))
            conn.commit(); conn.close()
            self._load()

    def _edit(self, event=None):
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
            conn.execute("UPDATE mieter SET name=?,email=?,telefon=?,einheit=?,einzug=?,kaltmiete=?,nebenkosten_vorauszahlung=?,kaution=?,notizen=? WHERE id=?",
                (v["name"], v["email"], v["telefon"], v["einheit"], v["einzug"],
                 v["kaltmiete"] or 0, v["nk"] or 0, v["kaution"] or 0, v["notizen"], mid))
            conn.commit(); conn.close()
            self._load()

    def _delete(self):
        sel = self.tree.selection()
        if not sel: return
        if messagebox.askyesno("Löschen", "Mieter wirklich löschen?"):
            conn = get_db()
            conn.execute("DELETE FROM mieter WHERE id=?", (int(sel[0]),))
            conn.commit(); conn.close()
            self._load()


class MieterDialog(BaseDialog):
    def __init__(self, parent, row=None):
        super().__init__(parent, "Mieter" + (" bearbeiten" if row else " hinzufügen"), 500, 580)
        r  = row or {}
        two = tk.Frame(self._body, bg=BG_CARD)
        two.pack(fill="x")
        two.columnconfigure((0, 1), weight=1)
        l  = tk.Frame(two, bg=BG_CARD); l.grid(row=0, column=0, padx=(0, 6), sticky="ew")
        ri = tk.Frame(two, bg=BG_CARD); ri.grid(row=0, column=1, padx=(6, 0), sticky="ew")
        self._add_field("Name *",              "name",      r.get("name", ""),      row=l)
        self._add_field("E-Mail",              "email",     r.get("email", ""),     row=ri)
        self._add_field("Telefon",             "telefon",   r.get("telefon", ""),   row=l)
        self._add_field("Einheit",             "einheit",   r.get("einheit", ""),   row=ri)
        self._add_field("Einzug (JJJJ-MM-TT)","einzug",    r.get("einzug", ""),    row=l)
        self._add_field("Kaltmiete €",         "kaltmiete", r.get("kaltmiete", ""), row=ri)
        self._add_field("NK-Vorausz. €",       "nk",        r.get("nebenkosten_vorauszahlung", ""))
        self._add_field("Kaution €",           "kaution",   r.get("kaution", ""))
        self._add_field("Notizen",             "notizen",   r.get("notizen", ""),   widget_type="text")

    def _on_save(self):
        v = self._get_values()
        if not v.get("name"):
            messagebox.showwarning("Pflichtfeld", "Name ist erforderlich.", parent=self); return
        self.result = v; self.destroy()

# ── Eigentümer-Seite ──────────────────────────────────────────────────────────

class EigentuemerPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_CARD)
        self._build()

    def _build(self):
        section_header(self, "Eigentümer", "＋ Eigentümer", self._new)
        cols = ("Name", "Einheit", "Anteil %", "E-Mail", "Telefon")
        f, self.tree = make_table(self, cols, height=8)
        f.pack(fill="both", expand=True, padx=20, pady=10)
        for c, w in zip(cols, [180, 130, 80, 200, 130]):
            self.tree.heading(c, text=c); self.tree.column(c, width=w, anchor="w")
        self.tree.bind("<Double-1>", self._edit)
        self._load()
        btn_row = tk.Frame(self, bg=BG_CARD)
        btn_row.pack(fill="x", padx=20, pady=(0, 10))
        make_btn(btn_row, "✏ Bearbeiten", self._edit, color=BG_INPUT, fg=TEXT).pack(side="left", padx=(0, 8))
        make_btn(btn_row, "🗑 Löschen",   self._delete, color=DANGER).pack(side="left")

    def _load(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = get_db()
        for r in conn.execute("SELECT * FROM eigentuemer ORDER BY name"):
            self.tree.insert("", "end", iid=r["id"], values=(
                r["name"], r["einheit"] or "–",
                f"{r['anteil_prozent']:.1f} %",
                r["email"] or "–", r["telefon"] or "–"))
        conn.close()

    def _new(self):
        d = EigentuemerDialog(self)
        self.wait_window(d)
        if d.result:
            v = d.result
            conn = get_db()
            conn.execute("INSERT INTO eigentuemer (name,email,telefon,anteil_prozent,einheit,notizen) VALUES (?,?,?,?,?,?)",
                (v["name"], v["email"], v["telefon"], v["anteil"] or 33.33, v["einheit"], v["notizen"]))
            conn.commit(); conn.close(); self._load()

    def _edit(self, event=None):
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
            conn.execute("UPDATE eigentuemer SET name=?,email=?,telefon=?,anteil_prozent=?,einheit=?,notizen=? WHERE id=?",
                (v["name"], v["email"], v["telefon"], v["anteil"] or 33.33, v["einheit"], v["notizen"], int(sel[0])))
            conn.commit(); conn.close(); self._load()

    def _delete(self):
        sel = self.tree.selection()
        if not sel: return
        if messagebox.askyesno("Löschen", "Eigentümer löschen?"):
            conn = get_db()
            conn.execute("DELETE FROM eigentuemer WHERE id=?", (int(sel[0]),))
            conn.commit(); conn.close(); self._load()


class EigentuemerDialog(BaseDialog):
    def __init__(self, parent, row=None):
        super().__init__(parent, "Eigentümer", 480, 440)
        r = row or {}
        self._add_field("Name *",    "name",    r.get("name", ""))
        self._add_field("E-Mail",    "email",   r.get("email", ""))
        self._add_field("Telefon",   "telefon", r.get("telefon", ""))
        self._add_field("Einheit",   "einheit", r.get("einheit", ""))
        self._add_field("Anteil % *","anteil",  r.get("anteil_prozent", "33.33"))
        self._add_field("Notizen",   "notizen", r.get("notizen", ""), widget_type="text")

    def _on_save(self):
        v = self._get_values()
        if not v.get("name"):
            messagebox.showwarning("Pflichtfeld", "Name ist erforderlich.", parent=self); return
        self.result = v; self.destroy()

# ── Buchhaltung-Seite ─────────────────────────────────────────────────────────

class BuchhaltungPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_CARD)
        self._build()

    def _build(self):
        top = tk.Frame(self, bg=BG_CARD)
        top.pack(fill="x", padx=20, pady=(18, 0))
        self._saldo_label = tk.Label(top, text="", bg=BG_CARD, fg=TEXT, font=FONT_H2)
        self._saldo_label.pack(side="left")
        make_btn(top, "＋ Buchung", self._new_zahlung).pack(side="right")
        make_btn(top, "📥 Kontoauszug importieren", self._import_csv,
                 color=BG_INPUT, fg=TEXT).pack(side="right", padx=(0, 8))

        filter_row = tk.Frame(self, bg=BG_CARD)
        filter_row.pack(fill="x", padx=20, pady=8)
        tk.Label(filter_row, text="Typ:", bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(side="left")
        self._typ_var = tk.StringVar(value="Alle")
        for t in ("Alle", "Einnahme", "Ausgabe"):
            tk.Radiobutton(filter_row, text=t, variable=self._typ_var, value=t,
                           bg=BG_CARD, fg=TEXT, font=FONT_SMALL,
                           activebackground=BG_CARD, selectcolor=BG_CARD,
                           command=self._load).pack(side="left", padx=6)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=20)
        cols = ("Datum", "Beschreibung", "Kategorie", "Betrag", "Typ", "Belegnr.")
        f, self.tree = make_table(self, cols, height=16)
        f.pack(fill="both", expand=True, padx=20, pady=8)
        for c, w in zip(cols, [90, 240, 120, 100, 80, 90]):
            self.tree.heading(c, text=c); self.tree.column(c, width=w, anchor="w")
        self.tree.bind("<Double-1>", self._edit)

        btn_row = tk.Frame(self, bg=BG_CARD)
        btn_row.pack(fill="x", padx=20, pady=(0, 10))
        make_btn(btn_row, "✏ Bearbeiten", self._edit, color=BG_INPUT, fg=TEXT).pack(side="left", padx=(0, 8))
        make_btn(btn_row, "🗑 Löschen",   self._delete, color=DANGER).pack(side="left")
        make_btn(btn_row, "📊 Export CSV", self._export_csv, color=BG_INPUT, fg=TEXT).pack(side="right")
        self._load()

    def _load(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = get_db()
        typ = self._typ_var.get()
        q = "SELECT * FROM zahlungen"
        if typ != "Alle": q += f" WHERE typ='{typ}'"
        q += " ORDER BY datum DESC, erstellt_am DESC"
        einnahmen = ausgaben = 0
        for r in conn.execute(q):
            self.tree.insert("", "end", iid=r["id"], values=(
                fmt_date(r["datum"]), r["beschreibung"] or "–",
                r["kategorie"] or "–", fmt_euro(r["betrag"]),
                r["typ"], r["belegnr"] or "–"))
            if r["typ"] == "Einnahme": einnahmen += r["betrag"] or 0
            else: ausgaben += abs(r["betrag"] or 0)
        conn.close()
        saldo = einnahmen - ausgaben
        color = SUCCESS if saldo >= 0 else DANGER
        self._saldo_label.config(
            text=f"Saldo: {fmt_euro(saldo)}   |   Einnahmen: {fmt_euro(einnahmen)}   Ausgaben: {fmt_euro(ausgaben)}",
            fg=color)

    def _new_zahlung(self):
        d = ZahlungDialog(self)
        self.wait_window(d)
        if d.result:
            v = d.result
            betrag = float(v["betrag"] or 0)
            if v["typ"] == "Ausgabe": betrag = -abs(betrag)
            conn = get_db()
            conn.execute("INSERT INTO zahlungen (datum,betrag,typ,kategorie,beschreibung,belegnr) VALUES (?,?,?,?,?,?)",
                (v["datum"], betrag, v["typ"], v["kategorie"], v["beschreibung"], v["belegnr"]))
            conn.commit(); conn.close(); self._load()

    def _edit(self, event=None):
        sel = self.tree.selection()
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
            conn.execute("UPDATE zahlungen SET datum=?,betrag=?,typ=?,kategorie=?,beschreibung=?,belegnr=? WHERE id=?",
                (v["datum"], betrag, v["typ"], v["kategorie"], v["beschreibung"], v["belegnr"], int(sel[0])))
            conn.commit(); conn.close(); self._load()

    def _delete(self):
        sel = self.tree.selection()
        if not sel: return
        if messagebox.askyesno("Löschen", "Buchung löschen?"):
            conn = get_db()
            conn.execute("DELETE FROM zahlungen WHERE id=?", (int(sel[0]),))
            conn.commit(); conn.close(); self._load()

    def _import_csv(self):
        path = filedialog.askopenfilename(
            filetypes=[("CSV Dateien", "*.csv"), ("Alle Dateien", "*.*")],
            title="Kontoauszug (CSV) importieren")
        if not path: return
        imported = 0
        conn = get_db()
        try:
            with open(path, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f, delimiter=";")
                for row in reader:
                    datum       = row.get("Datum", "").strip()
                    buchungstext = row.get("Buchungstext", row.get("Verwendungszweck", "")).strip()
                    betrag_str  = row.get("Betrag", "0").replace(".", "").replace(",", ".").strip()
                    saldo_str   = row.get("Saldo",  "0").replace(".", "").replace(",", ".").strip()
                    try:
                        betrag = float(betrag_str)
                        saldo  = float(saldo_str) if saldo_str else None
                    except:
                        continue
                    try:
                        datum = datetime.strptime(datum, "%d.%m.%Y").strftime("%Y-%m-%d")
                    except: pass
                    conn.execute("INSERT INTO kontoauszug (datum,buchungstext,betrag,saldo) VALUES (?,?,?,?)",
                        (datum, buchungstext, betrag, saldo))
                    imported += 1
            conn.commit()
            messagebox.showinfo("Import", f"{imported} Zeilen importiert.\nKontoauszug unter 'Kontoauszug' einsehbar.")
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Import:\n{e}")
        conn.close()

    def _export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv",
            filetypes=[("CSV", "*.csv")], title="Buchungen exportieren")
        if not path: return
        conn = get_db()
        rows = conn.execute("SELECT datum,beschreibung,kategorie,betrag,typ,belegnr FROM zahlungen ORDER BY datum DESC").fetchall()
        conn.close()
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["Datum", "Beschreibung", "Kategorie", "Betrag", "Typ", "Belegnr."])
            for r in rows:
                w.writerow([fmt_date(r[0]), r[1], r[2], str(r[3]).replace(".", ","), r[4], r[5]])
        messagebox.showinfo("Export", f"Exportiert: {os.path.basename(path)}")


class ZahlungDialog(BaseDialog):
    def __init__(self, parent, row=None):
        super().__init__(parent, "Buchung", 480, 480)
        r = row or {}
        self._add_field("Datum (JJJJ-MM-TT) *", "datum",
                        r.get("datum", date.today().isoformat()))
        self._add_field("Typ *", "typ", r.get("typ", "Einnahme"),
                        widget_type="combo", options=["Einnahme", "Ausgabe"])
        self._add_field("Betrag € *", "betrag", abs(r.get("betrag", 0) or 0))
        self._add_field("Kategorie", "kategorie", r.get("kategorie", ""),
                        widget_type="combo",
                        options=["Miete", "Nebenkosten", "Wartung", "Verwaltung", "Versicherung", "Sonstiges"])
        self._add_field("Beschreibung", "beschreibung", r.get("beschreibung", ""))
        self._add_field("Belegnummer",  "belegnr",      r.get("belegnr", ""))

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
        make_btn(btn_row, "✏ Bearbeiten",   self._edit,      color=BG_INPUT, fg=TEXT).pack(side="left", padx=(0, 8))
        make_btn(btn_row, "✔ Als erledigt", self._mark_done, color=SUCCESS).pack(side="left", padx=(0, 8))
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
        sel = self.tree.selection()
        if not sel: return
        conn = get_db()
        conn.execute("UPDATE wartung SET status='Erledigt',erledigt_am=? WHERE id=?",
            (date.today().isoformat(), int(sel[0])))
        conn.commit(); conn.close(); self._load()

    def _delete(self):
        sel = self.tree.selection()
        if not sel: return
        if messagebox.askyesno("Löschen", "Auftrag löschen?"):
            conn = get_db()
            conn.execute("DELETE FROM wartung WHERE id=?", (int(sel[0]),))
            conn.commit(); conn.close(); self._load()


class WartungDialog(BaseDialog):
    def __init__(self, parent, row=None):
        super().__init__(parent, "Wartungsauftrag", 480, 520)
        r = row or {}
        self._add_field("Titel *", "titel", r.get("titel", ""))
        two = tk.Frame(self._body, bg=BG_CARD)
        two.pack(fill="x")
        two.columnconfigure((0, 1), weight=1)
        l  = tk.Frame(two, bg=BG_CARD); l.grid(row=0, column=0, padx=(0, 6), sticky="ew")
        ri = tk.Frame(two, bg=BG_CARD); ri.grid(row=0, column=1, padx=(6, 0), sticky="ew")
        self._add_field("Priorität", "prioritaet", r.get("prioritaet", "Mittel"),
                        widget_type="combo", options=["Hoch", "Mittel", "Niedrig"], row=l)
        self._add_field("Status", "status", r.get("status", "Offen"),
                        widget_type="combo", options=["Offen", "In Arbeit", "Erledigt"], row=ri)
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
        make_btn(btn_row, "✔ Als gelesen markieren", self._mark_read, color=SUCCESS).pack(side="left", padx=(0, 8))
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

    def _delete(self):
        sel = self.tree.selection()
        if not sel: return
        if messagebox.askyesno("Löschen", "Dokument löschen?"):
            conn = get_db()
            conn.execute("DELETE FROM dokumente WHERE id=?", (int(sel[0]),))
            conn.commit(); conn.close(); self._load()


class DokumentDialog(BaseDialog):
    def __init__(self, parent):
        super().__init__(parent, "Dokument hinzufügen", 480, 440)
        self._add_field("Titel *",     "titel",       "")
        self._add_field("Kategorie",   "kategorie",   "Vertrag",
                        widget_type="combo",
                        options=["Vertrag", "Beschluss", "Abrechnung", "Protokoll", "Versicherung", "Sonstiges"])
        self._add_field("Beschreibung","beschreibung","")
        self._path_var = tk.StringVar()
        tk.Label(self._body, text="Datei", bg=BG_CARD, fg=TEXT_LIGHT,
                 font=FONT_SMALL).pack(anchor="w", pady=(8, 1))
        row = tk.Frame(self._body, bg=BG_CARD)
        row.pack(fill="x")
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

        btn_row = tk.Frame(self, bg=BG_CARD)
        btn_row.pack(fill="x", padx=20, pady=(0, 10))
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

    def _delete(self):
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
    def __init__(self, parent):
        super().__init__(parent, "Nebenkosteneintrag", 460, 420)
        two = tk.Frame(self._body, bg=BG_CARD)
        two.pack(fill="x")
        two.columnconfigure((0, 1), weight=1)
        l  = tk.Frame(two, bg=BG_CARD); l.grid(row=0, column=0, padx=(0, 6), sticky="ew")
        ri = tk.Frame(two, bg=BG_CARD); ri.grid(row=0, column=1, padx=(6, 0), sticky="ew")
        self._add_field("Jahr",          "jahr",  date.today().year, row=l)
        self._add_field("Monat (1-12)",  "monat", "",                row=ri)
        self._add_field("Kategorie *",   "kategorie", "Heizung",
                        widget_type="combo",
                        options=["Heizung", "Wasser", "Müll", "Versicherung", "Hausmeister", "Strom", "Sonstiges"])
        self._add_field("Betrag €",      "betrag",  "")
        self._add_field("Umlageschlüssel","umlage", "Wohnfläche",
                        widget_type="combo",
                        options=["Wohnfläche", "Personenanzahl", "Einheiten gleich", "Verbrauch"])
        self._add_field("Notizen",       "notizen", "")

    def _on_save(self):
        v = self._get_values()
        if not v.get("kategorie"):
            messagebox.showwarning("Pflichtfeld", "Kategorie ist erforderlich.", parent=self); return
        self.result = v; self.destroy()

# ── Kontoauszug-Seite ─────────────────────────────────────────────────────────

class KontoauszugPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_CARD)
        self._build()

    def _build(self):
        section_header(self, "Kontoauszug", "📥 CSV importieren", self._import)
        tk.Label(self, text="Importierte Kontoauszugsbuchungen (CSV-Format der Bank)",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w", padx=20, pady=(0, 8))

        cols = ("Datum", "Buchungstext", "Betrag", "Saldo", "Zugeordnet")
        f, self.tree = make_table(self, cols, height=18)
        f.pack(fill="both", expand=True, padx=20, pady=8)
        for c, w in zip(cols, [90, 320, 100, 100, 80]):
            self.tree.heading(c, text=c); self.tree.column(c, width=w, anchor="w")

        btn_row = tk.Frame(self, bg=BG_CARD)
        btn_row.pack(fill="x", padx=20, pady=(0, 10))
        make_btn(btn_row, "🗑 Alle löschen", self._clear, color=DANGER).pack(side="left")
        self._load()

    def _load(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = get_db()
        for r in conn.execute("SELECT * FROM kontoauszug ORDER BY datum DESC, id DESC"):
            self.tree.insert("", "end", values=(
                fmt_date(r["datum"]),
                r["buchungstext"] or "–",
                fmt_euro(r["betrag"]),
                fmt_euro(r["saldo"]) if r["saldo"] is not None else "–",
                "✔" if r["zugeordnet"] else ""))
        conn.close()

    def _import(self):
        path = filedialog.askopenfilename(
            filetypes=[("CSV", "*.csv"), ("Alle", "*.*")],
            title="Kontoauszug importieren")
        if not path: return
        imported = 0
        conn = get_db()
        try:
            with open(path, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f, delimiter=";")
                for row in reader:
                    datum = row.get("Datum", "").strip()
                    text  = row.get("Buchungstext", row.get("Verwendungszweck", "")).strip()
                    bstr  = row.get("Betrag", "0").replace(".", "").replace(",", ".").strip()
                    sstr  = row.get("Saldo",  "").replace(".", "").replace(",", ".").strip()
                    try: betrag = float(bstr)
                    except: continue
                    try: saldo = float(sstr)
                    except: saldo = None
                    try: datum = datetime.strptime(datum, "%d.%m.%Y").strftime("%Y-%m-%d")
                    except: pass
                    conn.execute("INSERT INTO kontoauszug (datum,buchungstext,betrag,saldo) VALUES (?,?,?,?)",
                        (datum, text, betrag, saldo))
                    imported += 1
            conn.commit()
            messagebox.showinfo("Import", f"{imported} Buchungen importiert.")
        except Exception as e:
            messagebox.showerror("Fehler", str(e))
        conn.close()
        self._load()

    def _clear(self):
        if messagebox.askyesno("Löschen", "Alle importierten Kontoauszüge löschen?"):
            conn = get_db()
            conn.execute("DELETE FROM kontoauszug")
            conn.commit(); conn.close(); self._load()


# ══════════════════════════════════════════════════════════════════════════════
# HAUPT-FENSTER
# ══════════════════════════════════════════════════════════════════════════════

class HausverwaltungApp(tk.Tk):
    PAGES = [
        ("🏠", "Übersicht",   DashboardPage),
        ("👥", "Mieter",      MieterPage),
        ("🏛", "Eigentümer",  EigentuemerPage),
        ("💰", "Buchhaltung", BuchhaltungPage),
        ("🔧", "Wartung",     WartungPage),
        ("🏦", "Kontoauszug", KontoauszugPage),
        ("📋", "Nebenkosten", NebenkostenPage),
        ("✉️",  "Nachrichten", NachrichtenPage),
        ("📁", "Dokumente",   DokumentePage),
    ]

    def __init__(self):
        super().__init__()
        self.title("Hausverwaltung – Eigentümergemeinschaft")
        self.geometry("1280x800")
        self.minsize(1024, 680)
        self.configure(bg=BG_SIDEBAR)
        init_db()
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

        tk.Label(sidebar, text="v1.0  •  SQLite", bg=BG_SIDEBAR, fg="#2C3E50",
                 font=("Segoe UI", 8)).pack(side="bottom", pady=8)

        self._content = tk.Frame(self, bg=BG_CARD)
        self._content.pack(side="left", fill="both", expand=True)

    def _switch(self, idx: int):
        if self._active == idx:
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


if __name__ == "__main__":
    app = HausverwaltungApp()
    app.mainloop()
