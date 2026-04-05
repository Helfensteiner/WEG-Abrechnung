# Changelog

Alle wesentlichen Änderungen an der Hausverwaltung-App werden hier dokumentiert.

Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/).
Versionierung folgt [Semantic Versioning](https://semver.org/lang/de/) — Major-Version 0 während der Entwicklungsphase.

---

## [0.16.0] — 2026-04-05

### Default-Pfade, Aufteilungstypen, Keywords, Wirtschaftsplan-Vorschläge

#### Neue Features

- **#38 Default Speicherpfade**: Neue Funktion `get_pfad(schluessel, standard_unterordner)` legt automatisch Unterordner im Programmverzeichnis an, wenn kein Pfad konfiguriert ist; wird in den Einstellungen gespeichert; angewendet auf Kontoauszüge, Dokumente, Belege, Backup

- **#39 Benutzerdefinierte Aufteilungstypen**: Neue Spalten `aktiv` und `ist_benutzerdefiniert` in `aufteilungen`; neue Tabelle `aufteilung_wohnungen` für Typ „Ausgewählte Wohnungen"; AufteilungDialog zeigt Listbox mit Multi-Select; nur Super-Admin kann löschen (mit Verwendungs-Prüfung); De/Aktivieren-Button für alle

- **#40 Buchungsregeln-Keywords**: Neue Spalte `keywords` in `buchungsregeln`; `vorschlag_kategorie()` durchsucht Keywords mit 0.65 Konfidenz (zwischen Muster 0.85 und Auftraggeber 0.70); Keyword-Suche als Stufe 1b eingefügt

- **#41 Wirtschaftsplan-Vorschläge**: Neuer Button „📊 Vorschlag aus Vorjahr" in Wirtschaftsplan-Tab; WirtschaftsplanVorschlagDialog generiert Vorschläge aus Vorjahres-Istdaten; Preisanpassung pro Position + globale Anpassung möglich; bereits vorhandene Kategorien werden gekennzeichnet (grün deaktiviert)

#### Neue DB-Tabellen
- `aufteilung_wohnungen` — Wohnungen-Zuordnung für Typ „Ausgewählte Wohnungen" (#39)

#### Neue DB-Spalten
- `aufteilungen.aktiv` (DEFAULT 1), `aufteilungen.ist_benutzerdefiniert` (DEFAULT 0) — #39
- `buchungsregeln.keywords` — #40

---

## [0.15.0] — 2026-04-05

### Smart Workflow: Kontoauszug → Buchung → Nebenkosten (Komplettimplementierung)

#### Neue Features

- **Konfidenz-Scoring**: `vorschlag_kategorie()` gibt jetzt einen Konfidenz-Score 0.0–1.0 zurück; 5 Stufen (95%=Exakt+Betrag, 85%=Exakter Text, 70%=Auftraggeber, 50%=Keyword, 0%=kein Treffer); Betrag-Min/Max-Filter in Buchungsregeln
- **Status-Pipeline Kontoauszug**: Neues Feld `buchung_status` mit den Werten `importiert → vorschlag → uebernommen → abgerechnet`; farbkodierte Legende (grau/orange/grün/blau) in KontoauszugPage
- **Abrechnungsrelevanz-Flag**: Neue Checkbox "Abrechnungsrelevant" im ZahlungDialog; Buchungen können explizit aus der Nebenkostenabrechnung ausgeschlossen werden; Nebenkosten-SQL-Queries filtern danach
- **Drill-Down Einzelbuchungen**: Doppelklick auf Kategorie im §28-WEG-Tab öffnet Dialog mit allen Einzelbuchungen inkl. Abrechnungsrelevanz-Status
- **Echte Umlageschlüssel**: `_berechne_umlageanteil()` berechnet Anteile nach Wohnfläche, MEA (Miteigentumsanteil in ‰), Kopfanzahl, Verbrauch oder HeizKV (70/30 §7 HeizKV); §556 BGB-Abrechnung nutzt jetzt den richtigen Schlüssel pro Kategorie aus `KOSTENARTEN`
- **Verbrauchsdaten-Tab**: Neuer Tab "🔢 Verbrauch" in NebenkostenPage; Zählerstände (Anfang/Ende) pro Wohnung, Kategorie und Jahr eintragbar; Basis für verbrauchsabhängige Umlageschlüssel und HeizKV
- **Pro-Rata-Temporis**: `pro_rata_temporis(einzug, auszug, jahr)` berechnet den zeitanteiligen Mieteranteil; §556-BGB-Abrechnung multipliziert Kosten- und Vorauszahlungsanteil mit dem Zeitfaktor
- **Abrechnungs-Snapshot**: Button "🔒 Abrechnung feststellen" friert alle relevanten Buchungen in `abrechnung_positionen` ein; festgestellte Abrechnungen können nicht mehr geändert werden; Buchungen im Kontoauszug werden auf `abgerechnet` gesetzt; Übersicht aller Abrechnungen via "📋 Festgestellte Abrechnungen"
- **Dashboard KPI Buchungs-Status**: Neue Kacheln zeigen Zugeordnet/Vorschläge offen/Ungeklärt/Abrechnung-Status in Echtzeit

#### Neue DB-Tabellen
- `verbrauchsdaten` — Zählerstände für verbrauchsabhängige Umlageschlüssel
- `abrechnungen` — Festgestellte Jahresabrechnungs-Snapshots (WEG/BGB)
- `abrechnung_positionen` — Eingefrorene Buchungspositionen pro Abrechnung
- `abrechnung_anteile` — Berechnete Eigentümer-/Mieter-Anteile

#### Neue DB-Spalten
- `zahlungen.abrechnungsrelevant` (DEFAULT 1), `zahlungen.abrechnungsjahr`, `zahlungen.kommentar_abrechnung`
- `buchungsregeln.betrag_min`, `buchungsregeln.betrag_max`, `buchungsregeln.konfidenz`
- `kontoauszug.buchung_status` (importiert/vorschlag/uebernommen/abgerechnet)
- `wohnungen.bewohner_anzahl` (für Kopfanzahl-Umlageschlüssel)

---

## [0.14.1] — 2026-04-04

### Behoben

- **#37 NameError `KiAssistentPage`**: `_ki_analyse_starten` referenzierte fälschlicherweise `KiAssistentPage._parse_modell_auswahl` statt `KIAssistentPage._parse_modell_auswahl`; der KI-Analyse-Button im Buchungsdialog war dadurch vollständig unbrauchbar

- **#37 KI-Modell-Dropdown im Buchungsdialog**: Neues Combobox-Widget neben dem KI-Analyse-Button erlaubt die Modellauswahl direkt im Dialog (Anthropic-Modelle und Ollama); Auswahl hat Vorrang vor der globalen KI-Einstellung

- **#37 Beschreibungsfeld nicht überschreiben**: `_ki_felder_befuellen` überschreibt das Feld „Beschreibung" jetzt nur noch wenn es leer ist; bereits eingetragene Beschreibungen bleiben erhalten

---

## [0.14.0] — 2026-04-04

### Neu

- **#35 KI-Rechnungsanalyse in Buchungen**: Neuer Button „🤖 KI-Analyse starten" im ZahlungDialog öffnet eine automatische Extraktion aus der Beleg-Datei (PDF oder Bild); das KI-Modell extrahiert Rechnungsdatum, Belegnummer, Beschreibung, Kategorie, Rechnungssteller und Betrag und befüllt die Formularfelder; Dateiname wird automatisch als `YYYY-MM-DD_Rechnungssteller_N` generiert; Lernfunktion schreibt erkannte Buchungsregeln; Schaltfläche nur aktiviert wenn Berechtigung `KI-Assistent: Lesen` vorhanden; Dateigrößenprüfung max. 20 MB

- **#35 Rechnungssteller-Feld**: Neues Datenbankfeld `zahlungen.rechnungssteller` und entsprechendes Eingabefeld im ZahlungDialog

- **#33 KI-Modell-Dropdown zeigt alle konfigurierten Modelle**: Der KI-Assistent zeigt jetzt beide Anbieter gleichzeitig — Anthropic-Modelle (`[Anthropic]`) und Ollama-Modell (`[Ollama]`) — sofern konfiguriert; Auswahl bestimmt welche API aufgerufen wird; Config-Key `ki_aktives_modell` speichert die letzte Wahl

- **#34 KI-Zugriffssteuerung in Rollen & Rechte**: Neuer Bereich „KI-Administration" in der Berechtigungsmatrix; steuert wer die KI-Einstellungen sehen und ändern darf; Standardrolle Benutzer hat keinen Zugriff

### Geändert

- **#34 „Zugriff nach Rollen"-Feld entfernt**: Der einfache Rollen-Text-Filter in Einstellungen → KI-Administration wurde entfernt; Zugriffssteuerung erfolgt jetzt über Rollen & Rechte (Bereich `KI-Administration`)

- **#34 KI-Admin-Tab mit Zugriffsschutz**: Tab-Inhalt wird nur angezeigt wenn `hat_recht("KI-Administration", "lesen")` gilt

### Behoben

- **#36 Custom-Kategorien in Buchung-Dialog**: Benutzerdefinierte Kategorien aus dem Kostenarten-Tab erscheinen jetzt auch im Buchung-Dialog; `_sync_kategorien_from_config()` lädt `custom_kategorien` aus der Config beim App-Start

- **SQL-Injection in WartungPage**: Status-Filter im Wartungsmodul verwendete f-String statt parametrisiertes Query — behoben

---

## [0.13.1] — 2026-04-04

### Behoben

- **KI-Assistent: Ollama-Integration komplett verdrahtet**: `_api_call_thread()` liest jetzt `ki_anbieter` aus Einstellungen und routet zu `_anthropic_call_thread()` (Anthropic API) oder `_ollama_call_thread()` (Ollama `POST /api/chat`, `stream: false`); Ollama-Anfragen senden System-Prompt korrekt als erstes `messages`-Element; Timeout 60 s (statt 30 s für langsamere lokale Modelle)

- **KI-Assistent: Modell-Dropdown dynamisch**: Bei Ollama-Anbieter zeigt das Dropdown das konfigurierte `ollama_modell` (z.B. `gemma3:4b`); bei Anthropic die drei Claude-Modelle; Auswahl wird in der richtigen Config-Einstellung gespeichert

- **KI-Assistent: Provider-Status-Widget**: Neuer Button „🔄 Provider neu laden" synchronisiert UI mit aktuellen Einstellungen; bei Ollama wird automatisch `GET /api/tags` aufgerufen und verfügbare Modelle werden im Statusfeld angezeigt; Header-Label und Warte-Text wechseln je nach Anbieter

---

## [0.13.0] — 2026-03-29

### Neu

- **#19 Wohngeld Soll/Ist-Übersicht**: Neuer Tab „💰 Wohngeld Soll/Ist" in der Buchhaltungsseite; zeigt je Eigentümer MEA-Anteil, Soll-Kostenanteil (aus Gesamtausgaben × MEA%), tatsächlich gezahltes Hausgeld (Ist), Saldo und Status (✔ ausgeglichen / ⚠ Rückstand); KPI-Leiste mit Gesamtausgaben, Hausgeld-Einnahmen und Jahressaldo; Jahres-Dropdown

- **#22 Jahresabschluss-PDF**: Neuer Button „📄 Jahresabschluss" im Buchungskopf; generiert vollständige A4-PDF-Abrechnung: Gesamtübersicht mit Saldo, Einnahmen nach Kategorie (grüner Header), Ausgaben nach Kategorie (roter Header), monatliche Übersicht; Jahreseingabe per Dialog; nutzt reportlab

- **#30 Datenbank Backup/Restore**: Neuer Abschnitt „Backup & Wiederherstellung" im Einstellungen-Tab „📁 Speicherpfade"; **💾 Backup erstellen** kopiert DB mit Zeitstempel in konfigurierten Backup-Ordner; **♻ Datenbank wiederherstellen** ersetzt aktuelle DB nach Warnung, legt automatisch Sicherheits-Backup der alten DB an

- **#32 Dashboard-Erweiterung**: Sechs KPI-Kacheln (vorher vier); neu: **Jahressaldo** (Einnahmen − Ausgaben laufendes Jahr, grün/rot) und **Rücklagen (kumuliert)** (Summe aller Erhaltungsrücklage-Buchungen, blau)

### Verbessert

- **#31 CSV-Export mit Filtern**: CSV-Export fragt jetzt nach Jahr (leer = alle); berücksichtigt den aktiven Typfilter (Einnahme/Ausgabe/Alle); Dateiname enthält Jahr und Typ; Info-Dialog zeigt Anzahl exportierter Buchungen

### Behoben

- **#20 MEA-Felder vereinheitlichen**: Neue Funktion `sync_mea_eigentuemer()` berechnet `eigentuemer.anteil_prozent` immer aus `SUM(wohnungen.mea_tausendstel) / 10`; wird nach jedem Wohnungs-Speichern (neu + bearbeiten) und beim Datenbankstart (`init_db()`) aufgerufen — veraltete MEA-Werte werden automatisch korrigiert

### Behoben (4-Rollen-Review)

- **Python-Entwickler**: `sync_mea_eigentuemer()` nutzt optionale `conn`-Übergabe um Connection-Leaks zu vermeiden; `_db_restore()` legt immer Auto-Backup an vor dem Überschreiben
- **Buchhalter**: Jahresabschluss zeigt Einnahmen und Ausgaben farblich getrennt; Saldo wird als Überschuss/Fehlbetrag korrekt benannt
- **UX-Tester**: Dashboard-Kachel Jahressaldo wechselt Farbe (grün ↔ rot); Wohngeld-Tab zeigt Rückstand mit konkretem Betrag in Statustext
- **Datenbankexperte**: CSV-Export verwendet parametrisierte Queries (kein SQL-Injection-Risiko durch Jahres-String)

---

## [0.12.0] — 2026-03-29

### Neu

- **#25 PDF-Export (reportlab)**: Drei neue `📄 PDF Export`-Buttons in der Nebenkostenabrechnung — für **§28 WEG Jahresabrechnung**, **§556 BGB Betriebskostenabrechnung** und **Wirtschaftsplan Soll/Ist-Vergleich**; professionelles A4-Layout mit WEG-Kopfzeile, farbigen Tabellen-Headern, Summenzeilen und Ampel-Farbgebung; Datei-Speichern-Dialog mit Vorschlagsnamen; optionales Öffnen nach Export (plattformübergreifend)

- **#23 §28 WEG: Rücklage-Einlage separat ausweisen**: Neues `WEG_EINLAGE_KATEGORIEN`-Set (`Erhaltungsrücklage`, `Sonderumlage`); KPI-Zeile zeigt jetzt **Bewirtschaftungskosten** und **Rücklage-Einlage** getrennt statt einem Gesamtbetrag; neue Spalte „Typ" in der Ausgaben-Tabelle (`Betriebskosten` / `Rücklage-Einlage`); Einlage-Zeilen blau hervorgehoben (#2E6DA4)

- **#24 §556 BGB: Leerstand-Wohnungen einbeziehen**: SQL-Abfrage auf LEFT JOIN mit Bedingung im ON-Teil umgestellt — alle Wohnungen (auch ohne aktiven Mieter) fließen in die Flächenberechnung ein; Leerstand-Wohnungen erscheinen als `⚠ Leerstand (Eigentümer)` (goldfarben) in der Mieter-Tabelle; neue KPI-Kachel zeigt Anzahl Leerstände; Leerstand-Kosten trägt der Eigentümer (Vorauszahlung = 0 €)

### Behoben (4-Rollen-Review)

- **Python-Entwickler**: `_export_pdf_*`-Methoden fangen `ImportError` (reportlab nicht installiert) und allgemeine Exceptions ab — kein unkontrollierter Absturz möglich
- **Buchhalter (WEG)**: Rücklage-Einlagen werden nach §28 WEG korrekt separat ausgewiesen, nicht mit Betriebskosten vermengt
- **UX-Tester**: Leerstand goldfarben (#C8A96E) statt rot/grün — eindeutig andere Bedeutung als Nachzahlung/Guthaben
- **Datenbankexperte**: LEFT JOIN-Bedingung im ON-Teil verhindert fehlerhafte NULL-Filterung bei Leerstand-Wohnungen

---

## [0.11.0] — 2026-03-29

### Neu

- **#27 Mietende (Auszugsdatum)**: `auszug`-Feld in `MieterDialog` hinzugefügt (neben Einzug); Datum wird normalisiert und in `NULL`/ISO-Format gespeichert; Spalte „Auszug" in der Mieter-Tabelle sichtbar; INSERT/UPDATE aktualisiert; §556 BGB Mieter-Abrechnung berücksichtigt jetzt nur Mieter, die im gewählten Jahr aktiv waren (`auszug IS NULL OR auszug >= JJJJ-01-01`)

- **#21 Leere Tabellen mit Hinweistext**: Neue Hilfsfunktion `tree_empty_hint()` zeigt „(Keine Einträge vorhanden)" in allen leeren Treeview-Tabellen (grauer Hinweistext); betrifft Mieter, Eigentümer, Wohnungen, Buchhaltung, Wartung, Nachrichten, Dokumente, Aufteilungen, Benutzer, Kontoauszug

- **#29 Rechnungs-Upload (Beleg-Dateipfad)**: Neue Spalte `beleg_dateipfad TEXT` in `zahlungen` (Migration automatisch); `ZahlungDialog` hat Datei-Picker-Zeile (📂 Durchsuchen) für PDF/Bild-Dateien; Buchungstabelle zeigt 📎-Indikator bei hinterlegtem Beleg; neuer Button „📎 Beleg öffnen" öffnet hinterlegte Datei plattformübergreifend (Windows/Mac/Linux)

- **#28 Einstellungen: 4-Tab-Layout**: `EinstellungenPage` vollständig neu gestaltet mit `ttk.Notebook`; 4 Tabs: **🏛 Stammdaten** (WEG-Name, Anschrift, Kontakt), **🏦 Bankdaten** (Wohngeld- + Rücklagenkonto mit IBAN), **📁 Speicherpfade** (Kontoauszüge, Belege, Dokumente, Datenbank), **🤖 KI-Administration** (Anbieter-Auswahl Anthropic/Ollama, API-Key, Modell, Rollenzugriff); Speichern-Button im Header

### Behoben

- **#26 Wirtschaftsplan leer**: `_wp_soll_ist()` zeigt jetzt Fehlermeldung anstatt leeres Fenster, wenn keine Wirtschaftsplan-Einträge für das Jahr vorhanden sind

---

## [0.10.1] — 2026-03-29

### Behoben (4-Rollen-Review: Python · Buchhalter · UX · Datenbank)

- **parse_float() None-sicher** (Python-Entwickler): `parse_float(None)` lieferte `ValueError` — trat auf wenn `flaeche_qm` oder `nebenkosten_vorauszahlung` in der DB `NULL` waren; Fix: frühe Rückgabe `0.0` bei `None` und leerem String
- **try/finally in `_wp_delete`** (Python-Entwickler): DB-Connection-Leak bei Fehler in `conn.commit()` behoben
- **Index `wirtschaftsplan(jahr)`** (Datenbankexperte): Fehlender Performance-Index in `init_db` ergänzt
- **Soll/Ist-Status „– kein Soll"** (UX-Tester): Wenn kein Soll-Wert geplant (Soll = 0), wird jetzt „– kein Soll" (grau) statt „⚠ Überzogen" (rot) angezeigt

### Neue GitHub Issues (aus 4-Rollen-Review)
- **#23** 📊 §28 WEG: Erhaltungsrücklage als Einlage kennzeichnen
- **#24** 👤 §556 BGB: Wohnungen ohne aktiven Mieter in Flächenberechnung
- **#25** 📄 Export-Funktion für Jahresabrechnung PDF/CSV
- **#26** 📋 Wirtschaftsplan Soll/Ist: Hinweis wenn kein Plan vorhanden

---

## [0.10.0] — 2026-03-29

### Neu

- **Einheitliches Kategoriensystem (§2 BetrKV / WEG)**: Globale `WEG_KATEGORIEN`-Konstante mit 34 Kategorien ersetzt die getrennten Listen in Buchhaltung und Nebenkosten; Metadaten (Obergruppe, Umlagefähigkeit nach §556 BGB, empfohlener Umlageschlüssel) direkt eingebettet; `WEG_KATEGORIEN_UMLAGE` enthält automatisch nur umlagefähige Kategorien

- **§28 WEG – Eigentümer-Jahresabrechnung**: Neuer Tab in Nebenkostenabrechnung; liest Ausgaben direkt aus der Buchhaltung (Tabelle `zahlungen`), kein manuelles Nebenkosten-Befüllen mehr; Anteil pro Eigentümer wird nach `anteil_prozent` (MEA) berechnet; zeigt Hausgeld-Einnahmen-Soll vs. tatsächlichen Kostenanteil → Saldo pro Eigentümer

- **§556 BGB – Mieter-Betriebskostenabrechnung**: Neuer Tab; nur umlagefähige Ausgaben aus Buchhaltung; Anteil nach Wohnfläche (m²) berechnet; zeigt geleistete Vorauszahlungen × 12 vs. tatsächlichen Anteil → Nachzahlung / Guthaben pro Mieter

- **Wirtschaftsplan (§28 Abs. 1 WEG)**: Neuer Tab + neue DB-Tabelle `wirtschaftsplan` (Jahr, Kategorie, Soll-Betrag, Notizen); CRUD-Dialoge; Soll/Ist-Vergleich gegen tatsächliche Ausgaben aus Buchhaltung mit Ampelfarben

- **Neuer Dialog `WirtschaftsplanDialog`**: Erstellt und bearbeitet Wirtschaftsplan-Einträge; Kategorie-Dropdown aus globalem WEG_KATEGORIEN-System

### Geändert

- `BuchhaltungPage.KATEGORIEN` und `KOSTENARTEN` werden jetzt aus `WEG_KATEGORIEN` abgeleitet (keine Duplikate mehr)
- `NebenkostenDialog`-Kategorie-Dropdown nutzt jetzt die vollständige einheitliche Liste (`WEG_KATEGORIEN_LISTE`)
- `NebenkostenPage` hat jetzt 3 Sub-Tabs statt einfacher Tabelle + Button

---

## [0.9.4] — 2026-03-28

### Behoben (Profi-Review: Python · Buchhalter · UX · Datenbank)
- **SQL-Injection** in `BuchhaltungPage._load_buchungen()`: String-Formatierung durch parametrisierte SQLite-Abfrage ersetzt
- **Duplikat-Code** in `NachrichtenPage`: `_read()` und `_mark_read()` zusammengeführt (identische Funktion)
- **Typo UX**: „Loeschen" → „🗑 Löschen" in Wasserkosten-Punktetabelle
- **FOREIGN KEY Pragma**: `PRAGMA foreign_keys = ON` in `get_db()` — referentielle Integrität jetzt erzwungen
- **DB-Indizes**: 8 neue Indizes für häufig abgefragte Spalten (`zahlungen`, `kontoauszug`, `nachrichten`, `wohnungen`, `mieter`)

### Neue GitHub Issues (aus Profi-Review)
- **#18** 🔐 Passwort-Hashing SHA256 → PBKDF2
- **#19** 📊 Wohngeld-Übersicht Soll/Ist-Vergleich
- **#20** 🗄️ MEA-Felder vereinheitlichen
- **#21** 🖥️ Leere Tabellen mit Hinweistext
- **#22** 📋 Jahresabschluss-Bericht PDF §28 WEG

---

## [0.9.3] — 2026-03-28

### Behoben
- **AufteilungDialog – Eingaben erschienen nicht in Tabelle**: `_on_typ_change()` rief `.configure()` und `.bind()` auf `tk.StringVar`-Objekte auf (statt auf die echten Widget-Referenzen), was einen `AttributeError` verursachte; jetzt werden `self._typ_combo` und `self._bezug_entry` direkt als Widget-Referenzen gespeichert
- **Wasserkosten-Navigation erscheint nicht**: Bedingung `_wk_aktiv` wurde nur beim App-Start geprüft; 💧 Wasserkosten ist jetzt immer in der Navigation sichtbar (kein nachträglicher Neustart nötig)

---

## [0.9.2] — 2026-03-28

### Behoben
- **#17 WEG-Stammdaten – Felder getrennt**: Einstellungen → WEG-Stammdaten zeigt jetzt einzelne Felder: WEG-Name, Straße, PLZ, Ort, E-Mail, Telefon (statt einem kombinierten Adressfeld); Sidebar kombiniert PLZ + Ort automatisch; Rückwärtskompatibilität mit altem `weg_adresse`-Feld

---

## [0.9.1] — 2026-03-28

### Behoben (Issues #10–#16)
- **#16 KI-Assistent – Keine Eingabe möglich**: Schnell-Aktionen-Buttons durch echte `make_btn`-Buttons ersetzt; Entry-Feld erhält automatisch Fokus
- **#16 KI-Assistent – Modell-Dropdown**: Combobox für Modellauswahl (Opus/Sonnet/Haiku), wird in Einstellungen gespeichert
- **#16 KI-Assistent – Einstellungen-Button**: Navigiert zur Einstellungen-Seite
- **#15 Fenstertitel**: Sidebar-Logo und Fenstertitel zeigen WEG-Name/Adresse aus Einstellungen; Fallback auf "Hausverwaltung"/"Musterstraße 12"
- **#12 Wohnung – MEA doppelt**: Redundantes Feld "MEA (Miteigentumsanteil)" entfernt; "MEA Tausendstel" → "MEA Tausendstel (Miteigentumsanteil)"
- **#11 Buchhaltung – Mehrfach-Löschen**: Alle per SHIFT markierten Buchungen werden gemeinsam gelöscht
- **#10 Doppelimport**: Belt-and-Suspenders-Dublettencheck für `zahlungen` beim CAMT.052-Import verhindert doppelte Einträge bei Re-Import
- **#13 Aufteilungen – Typ "Wasserkosten nach Punkten"**: Neuer Typ im Aufteilung-Dialog; Bezug wird automatisch gesetzt; Hinweistext eingeblendet
- **#14 Wasserkosten – Bedingte Navigation**: 💧 Wasserkosten-Seite erscheint nur wenn eine Aufteilung vom Typ "Wasserkosten nach Punkten" existiert

---

## [0.9.0] — 2026-03-28

### Hinzugefügt
- **🤖 KI-Assistent** (neue Seite): Chat-Interface mit Claude (Anthropic API) direkt in der App
  - Fragen in natürlicher Sprache: „Welche Eigentümer haben nicht bezahlt?", „Ausgaben Q1 2026?"
  - KI generiert SQL-Abfragen und führt sie direkt auf der DB aus, Ergebnis wird im Chat angezeigt
  - **Auto-Kategorisierung**: Unkategorisierte Bankbuchungen werden per KI kategorisiert
  - **Anomalie-Check**: Fehlende Wohngeld-Zahlungen und ungewöhnliche Beträge werden erkannt
  - **Monats-Bericht**: Automatische Zusammenfassung der Finanzen des aktuellen Monats
  - **Offene Forderungen**: Wer hat diesen Monat noch nicht bezahlt?
- **Anthropic API-Key** in Einstellungen: Schlüssel und Modell konfigurierbar

### Behoben
- **parse_float()** Hilfsfunktion: SQLite gibt REAL-Spalten manchmal als deutschen Komma-String zurück (`'334,69'`) — `float()` scheiterte daran, `parse_float()` normiert korrekt
- Alle `mea_tausendstel`- und `nutzflaeche_qm`-Formatierungen verwenden jetzt `parse_float()`

---

## [0.8.0] — 2026-03-22

### Hinzugefügt
- **Mieter – Wasserkosten-Stammdaten** (Issue #9): Neue Felder im Mieter-Dialog: Personen, Spülmaschinen, Waschmaschinen, Trockner (Wasserkühlung) — werden beim Klick auf „Aus Stammdaten" in der Wasserkosten-Punktetabelle automatisch übernommen
- **Datum-Normalisierung** (Issue #8): Alle Datumsfelder akzeptieren jetzt drei Formate: `JJJJ-MM-TT`, `TT.MM.JJJJ` und `TT/MM/JJJJ` — Anzeige immer als ISO `JJJJ-MM-TT`. Gilt für Einzug, Buchungsdatum, Wartungsdaten, Nebenkosten.
- **Enter = Speichern** (Issue #8): In allen Dialogen (BaseDialog) löst die Enter-Taste das Speichern aus

### Geändert
- **Eigentümer – MEA-Anteile** (Issue #6): „Anteil %" umbenannt in „MEA-Anteile gesamt" — Wert wird automatisch als Summe aus den zugeordneten Wohnungen (`mea_tausendstel`) berechnet, kein manueller Eingriff mehr nötig
- **Eigentümer – NK-Vorauszahlung** (Issue #7): Im Eigentümer-Dialog wird die Gesamtsumme der NK-Vorauszahlungen aller aktiven Mieter in den zugeordneten Wohnungen angezeigt

---

## [0.7.4] — 2026-03-22

### Bugfixes
- **Wasserkosten – Speichern-Button nicht sichtbar** (Issue #5): Im Dialog „Wohnung Punktedaten" war der Speichern-Button durch das expandierende Body-Frame verdrängt worden. Fix: Button-Zeile wird jetzt zuerst mit `side="bottom"` gepackt — immer sichtbar. Fensterhöhe auf 480px erhöht, Größenveränderung aktiviert.

---

## [0.7.3] — 2026-03-22

### Bugfixes
- **Eigentümer – KeyError 'anteil'**: Felder „Anteil %" und „Einheit" fehlten komplett im Eigentümer-Dialog — Speichern schlug mit KeyError fehl. Beide Felder sind jetzt als eigene Zeile im Dialog vorhanden.
- **Robustheit INSERT/UPDATE**: Alle Datenzugriffe in den SQL-Statements für Eigentümer und Mieter auf `v.get(...)` mit Fallback-Werten umgestellt — verhindert KeyErrors bei fehlenden Feldern.

---

## [0.7.2] — 2026-03-22

### Bugfixes
- **Kontoauszug – „database is locked" beim Ordner-Import** (Issue #3): `lerne_buchung()` wird jetzt erst nach `conn.commit()` aufgerufen — verhindert SQLite-Lock bei Ordner-Imports mit vielen Dateien
- **Kontoauszug – Import-Ergebnismeldung** (Issue #3): Ergebnis-Dialog ist jetzt 700 px breit und scrollbar — alle Dateinamen und Fehler vollständig lesbar
- **Eigentümer – PLZ fehlt** (Issue #4): PLZ-Feld ist jetzt im Eigentümer-Dialog zwischen Straße und Ort vorhanden
- **Mieter – PLZ fehlt** (Issue #4): PLZ-Feld ist jetzt im Mieter-Dialog zwischen Straße und Ort vorhanden
- **DB-Migration**: Neue Spalte `plz TEXT` in `eigentuemer` und `mieter` (automatische Migration beim Start)

---

## [0.7.0] — 2026-03-22

### Hinzugefügt
- **Wasserkosten-Seite**: Neue Seite „💧 Wasserkosten" zur Berechnung der Wasserkostenverteilung nach Punkteschlüssel
  - Tab 1 „Jahreskosten": Erfassung von Frischwasser, Abwasser und Niederschlagswasser (je Verbrauch m³, Kosten €, Ablesedatum) sowie Gutschrift/Erstattung
  - Tab 2 „Punktetabelle": Wohnungsdaten mit Personen, Spülmaschinen, Waschmaschinen, Trockner (Wasserkühlung), Monate; automatischer Import aus Stammdaten-Wohnungen
  - Tab 3 „Auswertung": Berechnung Kosten je Punkt (Gesamtkosten netto / Gesamtpunkte gewichtet), Aufschlüsselung je Wohneinheit und je Eigentümer, Plausibilitätscheck (Toleranz < 0,10 €), Vorjahresvergleich
  - Daten werden je Abrechnungsjahr in drei neuen DB-Tabellen gespeichert: `wasserkosten_positionen`, `wasserkosten_wohnungsdaten`, `wasserkosten_vorjahr`

### Bugfixes
- **Buchhaltung – „Alle grünen übernehmen"** (Issue #2): Batch-Übernahme funktioniert jetzt korrekt bei mehreren markierten Einträgen
  - Einträge selektiert → nur die markierten grünen Einträge werden verarbeitet
  - Nichts selektiert → alle grünen Einträge des aktiven Kontos werden verarbeitet
  - Keine Rückfrage pro Buchung im Bulk-Modus

---

## [0.6.0] — 2026-03-21

### Bugfixes
- **Kontoauszug – „database is locked"**: XML-Import verwendet jetzt eine einzige DB-Verbindung für alle Dateien (statt je Datei eine neue Verbindung) — löst SQLite-Locking-Fehler bei Multi-Datei-Import
- **Buchhaltung – Übernehmen**: Eintrag-Übernahme aus Vorschläge speichert jetzt korrekt `konto_typ`, `zahlung_id` und setzt `zugeordnet=1` in `kontoauszug`
- **Buchhaltung – Batch-Übernahme**: Konto-Typ-Fallback von „Girokonto" auf „Wohngeldkonto" korrigiert
- **Einstellungen**: Girokonto- und Tagesgeldkonto-Felder entfernt; nur Wohngeldkonto und Rücklagenkonto verbleiben (inkl. Bezeichnungsfelder)
- **Kategorie-Erkennung**: Fallback-Konto-Typ in `vorschlag_kategorie()` und `lerne_buchung()` von „Girokonto" auf „Wohngeldkonto" korrigiert

### Hinzugefügt
- **Kontoauszug – Importfortschritt**: Statuszeile zeigt während des Imports „Importiere Datei X von Y…"
- **Buchhaltung – Kostenarten-Tab**: Neuer Sub-Tab „Kostenarten" zur Verwaltung der WEG-Kostenkategorien (CRUD)
  - Neue Kategorie anlegen (Name, Oberkategorie, Schlüssel, Umlagefähig)
  - Kategorie bearbeiten (Oberkategorie, Schlüssel, Umlagefähig ändern)
  - Kategorie deaktivieren/aktivieren (Toggle) — deaktivierte Kategorien erscheinen nicht mehr in Dropdowns
  - Kategorie löschen — geschützt wenn in Buchungen verwendet (zeigt Anzahl der Verwendungen)
  - Tabellenübersicht mit Kategorie, Oberkategorie, Umlagefähigkeit, Schlüssel, Status und Verwendungsanzahl
- **Buchhaltung – „Kategorie offen"**: Neue Kategorie für nicht erkannte Buchungen; erscheint in allen Kategorie-Dropdowns
- **Buchungsregeln – Verbessertes Matching**: Dreistufige Matching-Strategie
  1. Exakter Muster-Match im gesamten Buchungstext
  2. Auftraggeber/Empfänger-Match (vor dem `||`-Trennzeichen)
  3. Keyword-Match im Verwendungszweck (nach dem `||`)
- **Buchungsregeln – Füllwörter**: Globale Liste mit ~50 Füllwörtern (Artikel, Präpositionen, Rechtsformen wie GmbH/AG/KG) wird beim Matching ignoriert
- **Buchungsregeln – Muster-Extraktion**: Bei Buchungstexten mit `||` wird der Auftraggeber/Empfänger (bis 60 Zeichen) als primäres Muster gespeichert statt der ersten 40 Zeichen des Gesamttexts
- **Kategorie-Dropdowns**: Verwenden jetzt `aktive_kategorien()` statt der vollständigen KATEGORIEN-Liste

### Geändert
- **Einstellungen – Speicherpfade**: „Ordner Girokonto XML-Dateien" und „Ordner Tagesgeldkonto XML-Dateien" entfernt; nur Standard-Importordner bleibt
- **IBAN-Mapping in Import**: Konto-Typ-Erkennung prüft nur noch Wohngeldkonto und Rücklagenkonto (keine Girokonto/Tagesgeld-Fallbacks mehr)

---

## [0.5.0] — 2026-03-21

### Hinzugefügt
- **WEG-Kostenkategorien**: 27 Kategorien mit Metadaten (Umlagefähigkeit, Verteilerschlüssel) gemäß Notion-Spezifikation „Kostenkategorie/Kostenart" — gruppiert in: Laufende Betriebskosten, Verwaltungskosten, Instandhaltung & Wartung, Versicherungen, Finanzplanung & Rücklagen, Einnahmen, Sonstiges
- **Einstellungen – Kontobezeichnungen**: Jedes Konto (Wohngeld, Rücklage, Giro, Tagesgeld) hat ein eigenes Bezeichnungsfeld
- **Einstellungen – IBAN-Formatierung**: IBAN wird beim Eingeben automatisch im Format `DE## #### #### …` angezeigt und ohne Leerzeichen gespeichert
- **Einstellungen – Standard-Importordner**: Neues Feld für den Standard-Importpfad für Kontoauszüge — wird beim Import automatisch als Startverzeichnis geöffnet
- **Kontoauszug – Konto-Filter**: Dropdown-Filter zum Anzeigen einzelner Konten oder aller Konten
- **Kontoauszug – Fett-Markierung**: Neue Buchungen werden fett angezeigt; Klick auf eine Zeile entfernt die Markierung
- **Kontoauszug – Erweiterte Kacheln**: Jede Konto-Kachel zeigt Bezeichnung (aus Einstellungen), IBAN formatiert, Kontostand, Gesamtbuchungen und neue Buchungen. Klick auf Kachel filtert auf dieses Konto
- **Buchhaltung – Konto-Filter für Vorschläge**: Dropdown zur Filterung der Kontoauszug-Vorschläge nach Konto
- **Buchhaltung – Batch-Übernahme**: Button „Alle grünen übernehmen" übernimmt alle Vorschläge mit erkannter Kategorie automatisch in einem Schritt
- **Rollen – Passwort-Skip pro Rolle**: Checkbox in der Rollenverwaltung, um die Passwortabfrage für alle Benutzer einer Rolle zu deaktivieren (Login prüft sowohl User- als auch Rollen-Einstellung)

### Geändert
- **Kategorie-Dropdowns**: ZahlungDialog und Korrigieren-Dialog verwenden jetzt die erweiterte Kategorienliste
- **Einstellungen-Seite**: Neu organisiert in Abschnitte „WEG-Stammdaten", „Konten", „Speicherpfade Kontoauszüge", „Weitere Speicherpfade"

---

## [0.4.1] — 2026-03-21

### Hinzugefügt
- **Passwort generieren**: Automatische Passwort-Generierung (12 Zeichen) beim Anlegen neuer Benutzer und beim Passwort-Ändern
- **Passwortabfrage abschaltbar**: Pro Benutzer kann die Passwortabfrage beim Login deaktiviert werden (Checkbox im BenutzerDialog, neue Spalte in der Benutzerliste)
- **Passwort-Ändern-Dialog**: Wahl zwischen automatisch generiertem und manuell eingegebenem Passwort

### Behoben
- **Buchhaltung Vorschläge**: Kontoauszug-Vorschläge konnten nicht geladen oder übernommen werden — `sqlite3.Row` hat keine `.get()`-Methode, Rows werden jetzt korrekt zu `dict()` konvertiert
- **Kategorie korrigieren**: Gleiches Problem beim Korrigieren von Vorschlägen behoben

---

## [0.4.0] — 2026-03-21

### Hinzugefügt
- **Multi-Datei-Import**: Kontoauszug-Import (CAMT.052 XML und CSV) unterstützt jetzt mehrere Dateien gleichzeitig
- **Ordner-Import**: Kompletten Ordner mit XML- oder CSV-Dateien auf einmal importieren
- **Dublettenprüfung**: Bereits vorhandene Buchungen werden beim Import automatisch erkannt und übersprungen (anhand Datum, Betrag, Buchungstext)
- **Buchungsstatus**: Neues Status-Feld in der Buchhaltung mit Werten „Neu", „Geprüft", „Freigegeben"
- **Visuelle Hervorhebung**: Neue Buchungen (Status „Neu") werden in der Buchungsliste farblich hervorgehoben (blau, fett)
- **Status im ZahlungDialog**: Buchungsstatus kann beim Erstellen und Bearbeiten gesetzt werden

### Geändert
- **Kontoauszug-Import**: Dialog fragt jetzt Dateien vs. Ordner-Auswahl ab
- **Auto-Transfer**: Automatisch aus Kontoauszug übernommene Buchungen erhalten Status „Neu"
- **Buchhaltung-Tabelle**: Neue Spalte „Status" in der Buchungsliste

---

## [0.3.0] — 2026-03-19

### Hinzugefügt
- **Scrollbare Dialoge**: Alle Bearbeitungsdialoge sind jetzt scrollbar bei Überlauf
- **Größenveränderbare Fenster**: Dialoge können in der Größe angepasst werden
- **Größenpersistenz**: Angepasste Fenstergrößen werden in `einstellungen.json` gespeichert
- **Rollenverwaltung-UI**: Neue Seite "Rollen & Rechte" mit Berechtigungsmatrix
- **Eigentümer-Wohnungszuordnung**: Im Eigentümer-Dialog werden zugeordnete Wohnungen angezeigt
- **Eigentümer als Bewohner**: Neuer Button "Eigentümer als Bewohner" auf der Mieterseite für Eigennutzung
- **Versionierung**: App-Version im Sidebar, klickbarer Versions-Info-Dialog mit Git-Informationen
- **Berechtigungsprüfung**: `hat_recht()` checks auf allen Seiten (Buchhaltung, Wartung, Nebenkosten, Aufteilungen, Nachrichten, Dokumente, Benutzerverwaltung)
- **Superadmin-Schutz**: Superadmin-Benutzer können nicht gelöscht werden

### Geändert
- **Menüreihenfolge**: Kontoauszug steht jetzt vor Buchhaltung
- **BenutzerDialog**: Verwendet jetzt Rollen-Dropdown aus DB statt fest codierter Liste
- **BaseDialog**: Komplett neu geschrieben mit Canvas-Scrollbar und Größenverwaltung
- **Benutzerverwaltung**: Zeigt jetzt Rollenname aus rollen-Tabelle statt fest codiertem Wert

### Behoben
- **Speichern/Abbrechen-Buttons**: Sind jetzt immer sichtbar (fixiert am unteren Rand)
- **hat_recht() sqlite3.Row-Bug**: Konvertierung zu dict vor `.get()`-Aufruf

---

## [0.2.0] — 2026-03-19

### Hinzugefügt
- **RBAC-System**: Rollen- und Rechte-Tabellen, `hat_recht()` Berechtigungsfunktion
- **Lernfähiges Buchungssystem**: Automatische Kategorisierung mit Musterlernung (`buchungsregeln`)
- **Erweiterte Eigentümer-Stammdaten**: Straße, Ort, Land, IBAN, MEA ‰ aus Wohnungen
- **Erweiterte Wohnungsdaten**: Typ, Lage, Nutzfläche, Balkon, Keller, Stellplatz, Heizungsart, MEA Tausendstel
- **Erweiterte Mieter-Stammdaten**: Straße, Ort, Land, IBAN, Wohnung-Dropdown
- **Benutzerverwaltung**: Login-Dialog, Benutzer-CRUD, Passwort-Änderung
- **Kontoauszug Auto-Transfer**: Beim CAMT.052-Import automatische Übernahme in Buchhaltung bei erkannter Kategorie
- **Standardrollen**: Superadmin, Administrator, Benutzer mit Default-Rechten
- **Berechtigungsprüfung**: `hat_recht()` in Eigentümer, Wohnungen, Mieter Pages

### Geändert
- **Buchhaltung**: 3 Sub-Tabs (Buchungen, Vorschläge, Regeln)
- **Kontoauszug**: Speichert IBAN, Konto-Typ, Kategorie-Vorschlag

---

## [0.1.0] — 2026-03-18

### Hinzugefügt
- **Initiale App**: Tkinter-GUI mit Sidebar-Navigation und Seitenwechsel
- **SQLite-Datenbank**: Automatische Erstellung und Schema-Migration
- **Dashboard**: KPI-Kacheln (Mieter, Einnahmen, Offene Aufgaben, Ungelesen)
- **Mieter-Verwaltung**: CRUD mit Mietvertragsdaten
- **Eigentümer-Verwaltung**: CRUD mit Miteigentumsanteilen
- **Buchhaltung**: Einnahmen/Ausgaben, Typ-Filter, CSV-Export
- **Wartung**: Aufträge mit Priorität und Status-Tracking
- **Kontoauszug**: CAMT.052 XML-Import (Sparkasse Bodensee) und CSV-Import
- **Nebenkosten**: Nebenkostenpositionen mit Jahresauswertung
- **Nachrichten**: Interne Kommunikation mit Gelesen-Status
- **Dokumente**: Dokumentenverwaltung mit Dateiverknüpfung
- **Aufteilungen**: Umlageschlüssel für Nebenkostenverteilung
- **Einstellungen**: Konfigurierbare Dateipfade (JSON-basiert)
- **Design-System**: Professionelles Farbschema und Typography
- **Demo-Daten**: Automatische Befüllung bei erster Nutzung
