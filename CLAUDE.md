# Hausverwaltung – WEG Eigentümergemeinschaft

## Projektübersicht

Desktop-App zur Verwaltung einer **Wohnungseigentümergemeinschaft (WEG)** nach deutschem Recht.
Stack: **Python · Tkinter · SQLite** — alles in der Standardbibliothek, keine externen Abhängigkeiten.

**Aktuelle Version:** Siehe `APP_VERSION` in `hausverwaltung.py` und `VERSION`-Datei.

**Echte WEG:** Welte Rapp Bilgery · Sparkasse Bodensee
**Konten:**
- Rücklagenkonto: IBAN DE14 6905 0001 1007 2120 85 (BIC SOLADES1KNZ)
- Wohngeldkonto:  IBAN DE11 6905 0001 0000 0817 03 (BIC SOLADES1KNZ)

---

## Wie die App gestartet wird

```bash
# Virtuelles Environment aktivieren (Windows)
venv\Scripts\activate

# App starten
python hausverwaltung.py
```

Die SQLite-Datenbank liegt unter `~/hausverwaltung.db` (Heimverzeichnis des Benutzers).

---

## Architektur

Die gesamte App befindet sich in **einer einzigen Datei: `hausverwaltung.py`** (ca. 3400 Zeilen).
Das ist bewusst so — einfach zu deployen, kein Build-System nötig.

### Seitenstruktur (Navigation)
| Icon | Seite          | Klasse              | Funktion                              |
|------|----------------|---------------------|---------------------------------------|
| 🏠   | Übersicht      | `DashboardPage`     | KPIs, Schnellübersicht                |
| 👥   | Mieter         | `MieterPage`        | Mieter verwalten (CRUD)               |
| 🏛   | Eigentümer     | `EigentuemerPage`   | Eigentümer mit Miteigentumsanteilen   |
| 💰   | Buchhaltung    | `BuchhaltungPage`   | Zahlungen, Einnahmen/Ausgaben         |
| 🔧   | Wartung        | `WartungPage`       | Wartungsaufgaben & Reparaturen        |
| 🏦   | Kontoauszug    | `KontoauszugPage`   | Bankbuchungen importieren             |
| 📋   | Nebenkosten    | `NebenkostenPage`   | Nebenkostenabrechnung                 |
| ✉️   | Nachrichten    | `NachrichtenPage`   | Interne Kommunikation                 |
| 📁   | Dokumente      | `DokumentePage`     | Dokumentenverwaltung                  |

### Klassen-Hierarchie
```
HausverwaltungApp (tk.Tk)          ← Hauptfenster + Navigation
├── DashboardPage (tk.Frame)
├── MieterPage + MieterDialog
├── EigentuemerPage + EigentuemerDialog
├── BuchhaltungPage + ZahlungDialog
├── WartungPage + WartungDialog
├── KontoauszugPage
├── NebenkostenPage + NebenkostenDialog
├── NachrichtenPage + NachtrichtDialog
└── DokumentePage + DokumentDialog

BaseDialog (tk.Toplevel)           ← Basis für alle Eingabe-Dialoge
```

---

## Datenbank-Schema (SQLite)

```sql
eigentuemer  -- Wohnungseigentümer mit Miteigentumsanteilen (MEA in %)
mieter       -- Mieter mit Mietvertragsdaten
zahlungen    -- Alle Buchungen (Einnahmen + Ausgaben)
kontoauszug  -- Importierte Bankbuchungen (CSV oder CAMT.052 XML)
wartung      -- Wartungsaufgaben und Reparaturen
dokumente    -- Dokumentenverweise (Dateipfade)
nachrichten  -- Interne Nachrichten zwischen Eigentümern/Verwaltung
nebenkosten  -- Nebenkostenpositionen für Jahresabrechnung
```

---

## Design-System (Farben & Fonts)

```python
# Farben — NICHT ändern ohne Absprache
BG_SIDEBAR  = "#1C2B3A"   # Dunkelblau Sidebar
ACCENT      = "#C8A96E"   # Gold (aktiver Nav-Eintrag, Hover)
ACCENT2     = "#2E6DA4"   # Blau (primäre Buttons)
SUCCESS     = "#3A7D44"   # Grün
DANGER      = "#C0392B"   # Rot
BG_CARD     = "#FFFFFF"   # Kartenhintergrund
BG          = "#F7F5F0"   # Seiten-Hintergrund

# Fonts (Windows: Segoe UI / Georgia)
FONT_H1  = ("Georgia", 18, "bold")
FONT_H2  = ("Georgia", 13, "bold")
FONT_NAV = ("Segoe UI Semibold", 10)
FONT_BODY = ("Segoe UI", 10)
```

---

## Coding-Konventionen

### Allgemein
- **Sprache:** Variablen, Kommentare, UI-Texte **auf Deutsch** (Fachbegriffe WEG-Recht)
- **Datei:** Eine Datei `hausverwaltung.py` — neue Features werden in diese Datei integriert
- **Encoding:** UTF-8, deutsche Umlaute direkt (nicht escaped)

### Tkinter-Muster
```python
# Neue Seite hinzufügen:
class MeineNeuePage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG_CARD)
        self._build()

    def _build(self):
        section_header(self, "Titel", "➕ Neu", self._neu)
        # ... Inhalt ...
        self._load()

    def _load(self):
        # Daten aus DB laden und anzeigen
        ...
```

### Dialog-Muster
```python
class MeinDialog(BaseDialog):
    def __init__(self, parent, data=None):
        super().__init__(parent, "Titel", width=500, height=450)
        self._add_field("Label", "key", data.get("key","") if data else "")
        # widget_type: "entry" | "text" | "combo"

    def _on_save(self):
        # Felder lesen: self._fields["key"].get()
        # Validierung + DB-Speicherung
        self.result = {...}
        self.destroy()
```

### Datenbank-Muster
```python
# Immer with-Statement oder manuelles conn.close() verwenden
conn = get_db()
try:
    conn.execute("INSERT INTO ...", (...))
    conn.commit()
finally:
    conn.close()
```

### Formatierung
```python
fmt_euro(wert)    # → "1.234,56 €"
fmt_date(datum)   # ISO → "31.12.2025"
```

---

## Bankdaten-Import: CAMT.052 XML

Die Sparkasse Bodensee liefert Kontoauszüge als **CAMT.052 XML** (nicht CSV!).
Format: ISO 20022 `camt.052.001.08`

**Wichtig:** Die aktuelle `KontoauszugPage` importiert nur CSV.
**Nächste Priorität:** CAMT.052 XML-Import implementieren.

### CAMT.052 Struktur (relevante Felder)
```xml
<Document>
  <BkToCstmrAcctRpt>
    <Rpt>
      <Acct>
        <Id><IBAN>DE14690500011007212085</IBAN></Id>
      </Acct>
      <Bal>  <!-- Kontosaldo: OPBD=Eröffnung, CLBD=Schluss -->
        <Cd>CLBD</Cd>
        <Amt Ccy="EUR">9922.83</Amt>
      </Bal>
      <Ntry>  <!-- Eine Buchung -->
        <Amt Ccy="EUR">190.20</Amt>
        <CdtDbtInd>CRDT</CdtDbtInd>  <!-- CRDT=Gutschrift, DBIT=Lastschrift -->
        <BookgDt><Dt>2026-02-02</Dt></BookgDt>
        <NtryDtls>
          <TxDtls>
            <RltdPties>
              <Dbtr><Pty><Nm>Bettina Bilgery</Nm></Pty></Dbtr>
            </RltdPties>
            <RmtInf><Ustrd>Rücklage WEG Reutestr. 50</Ustrd></RmtInf>
          </TxDtls>
        </NtryDtls>
      </Ntry>
    </Rpt>
  </BkToCstmrAcctRpt>
</Document>
```

### XML-Namespace
```python
NS = {"ns": "urn:iso:std:iso:20022:tech:xsd:camt.052.001.08"}
# Verwendung: tree.findall("ns:Ntry", NS)
```

---

## WEG-Fachbegriffe (wichtig für korrekten Code)

| Begriff | Bedeutung |
|---------|-----------|
| WEG | Wohnungseigentümergemeinschaft |
| MEA | Miteigentumsanteil (in Tausendstel oder Prozent) |
| Wohngeld | Monatliche Vorauszahlung der Eigentümer |
| Hausgeld | = Wohngeld (alternativer Begriff) |
| Rücklage | Instandhaltungsrücklage (Sparkonto für Reparaturen) |
| Nebenkosten | Betriebskosten (Heizung, Wasser, Müll, etc.) |
| Eigentümerversammlung | Jährliche Pflichtversammlung der Eigentümer |
| WEG-Verwalter | Professioneller Verwalter (hier: Selbstverwaltung) |
| SEPA | Zahlungsverkehr (CAMT.052 = SEPA-Kontoauszugsformat) |

---

## Aktuelle Eigentümer (echte Daten)

```
Wohnanlage: Reutestraße 50 (aus Buchungstext ersichtlich)
WEG-Name:   Welte Rapp Bilgery
Bank:       Sparkasse Bodensee (BIC SOLADES1KNZ)
```

Demo-Daten in der DB verwenden fiktive Namen — diese können gelöscht werden.

---

## Bekannte Einschränkungen & TODOs

### Hochprioritär
- [ ] **CAMT.052 XML-Import** (statt CSV) für Sparkasse Bodensee
- [ ] **Automatische Zuordnung** von Bankbuchungen zu Zahlungen
- [ ] Eigentümer-Stammdaten mit echten WEG-Daten befüllen

### Mittelfristig
- [ ] PDF-Export: Nebenkostenabrechnung, Eigentumsnachweis
- [ ] Jahresabschluss-Bericht (Einnahmen/Ausgaben-Übersicht)
- [ ] E-Mail-Versand von Nachrichten
- [ ] Backup/Restore der SQLite-Datenbank
- [ ] Windows-EXE erstellen (PyInstaller)

### Langfristig
- [ ] Mehrere Objekte/WEGs verwalten
- [ ] Mieter-Portal (Web-Interface)
- [ ] DATEV-Export für Steuerberater

---

## Projektdateien

```
WEG-Abrechnung/
├── hausverwaltung.py    ← GESAMTE App (Hauptdatei, ~3400 Zeilen)
├── VERSION              ← Aktuelle Versionsnummer (z.B. "0.3.0")
├── CHANGELOG.md         ← Änderungshistorie aller Versionen
├── CLAUDE.md            ← Diese Datei (Projektkontext für Claude)
├── ROADMAP.md           ← Feature-Roadmap
├── requirements.txt     ← Python-Abhängigkeiten (nur stdlib)
├── einstellungen.json   ← Laufzeit-Konfiguration (Pfade, Fenstergrößen)
├── .gitignore
└── venv/                ← Virtuelles Environment (nicht im Git)
```

---

## Versionierung

Semantic Versioning: `MAJOR.MINOR.PATCH` — Major-Version **0** während der Entwicklungsphase.

### Versionspflege bei Änderungen

1. **`APP_VERSION`** in `hausverwaltung.py` aktualisieren
2. **`VERSION`**-Datei aktualisieren (gleicher Wert)
3. **`CHANGELOG.md`** mit Änderungen ergänzen
4. **Versionshistorie-Kommentar** im Header von `hausverwaltung.py` ergänzen
5. Git-Commit erstellen und **Tag setzen**: `git tag v0.X.Y`

### Wann hochzählen?

| Änderung | Beispiel | Version |
|----------|----------|---------|
| Neues Feature, neue Seite | Rollenverwaltung | MINOR+1, PATCH=0 |
| Bugfix, kleine Anpassung | Dialog-Fix | PATCH+1 |
| Breaking Change (nach v1.0) | DB-Schema-Umbau | MAJOR+1 |

### Git-Tag-Konvention

```bash
git tag v0.3.0
git push origin v0.3.0
```

Tags sind immer `v` + Versionsnummer und synchron mit `APP_VERSION`.

---

## Git-Workflow

```bash
git add hausverwaltung.py VERSION CHANGELOG.md
git commit -m "feat: kurze Beschreibung"
git tag v0.X.Y
git push && git push --tags
```

Commit-Typen: `feat:` | `fix:` | `refactor:` | `docs:` | `test:`
