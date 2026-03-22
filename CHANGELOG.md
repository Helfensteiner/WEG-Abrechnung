# Changelog

Alle wesentlichen Änderungen an der Hausverwaltung-App werden hier dokumentiert.

Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/).
Versionierung folgt [Semantic Versioning](https://semver.org/lang/de/) — Major-Version 0 während der Entwicklungsphase.

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
