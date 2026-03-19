# Changelog

Alle wesentlichen Änderungen an der Hausverwaltung-App werden hier dokumentiert.

Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/).
Versionierung folgt [Semantic Versioning](https://semver.org/lang/de/) — Major-Version 0 während der Entwicklungsphase.

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
