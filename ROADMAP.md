# WEG-App · Roadmap

## ✅ Version 1.0 – Fertig
- Dashboard mit KPI-Karten
- Mieter-Verwaltung (CRUD)
- Eigentümer-Verwaltung mit Miteigentumsanteilen
- Buchhaltung: Einnahmen/Ausgaben
- Wartungsaufgaben
- Nachrichten-System
- Dokumentenverwaltung
- Nebenkostenerfassung
- Kontoauszug-Import (CSV)

---

## 🚧 Version 1.1 – Nächste Schritte

### 1. CAMT.052 XML-Import (Hochprioritär)
Die Sparkasse Bodensee liefert Kontoauszüge als CAMT.052 XML (ISO 20022).
Aktuell wird nur CSV unterstützt.

**Aufgabe:** `KontoauszugPage._import()` erweitern:
- Dateiauswahl: `*.xml` hinzufügen
- XML mit `xml.etree.ElementTree` parsen
- Namespace: `urn:iso:std:iso:20022:tech:xsd:camt.052.001.08`
- Felder: BookgDt/Dt, Amt, CdtDbtInd (CRDT/DBIT → +/-), RmtInf/Ustrd, RltdPties/Dbtr/Nm
- Kontosaldo (CLBD) anzeigen

### 2. Automatische Buchungszuordnung
- Bankbuchungen automatisch den Zahlungen zuordnen
- Fuzzy-Match: Betrag + Datum + Verwendungszweck

### 3. Echte Eigentümerdaten
- Demo-Daten durch echte WEG "Welte Rapp Bilgery" ersetzen
- Eigentümer: Welte, Rapp, Bilgery

---

## 📋 Version 1.2 – Berichte & Export

### PDF-Abrechnung
- Jahres-Nebenkostenabrechnung pro Mieter/Eigentümer
- Einnahmen/Ausgaben-Übersicht
- Eigentümerversammlungs-Protokoll-Vorlage

### Jahresabschluss
- Einnahmen/Ausgaben-Rechnung (kein doppelte Buchführung nötig)
- Kontenübersicht: Wohngeldkonto + Rücklagenkonto
- Rücklagenentwicklung über Zeit

---

## 🔮 Version 2.0 – Zukunft

- Windows-EXE via PyInstaller (kein Python nötig)
- Automatisches Datenbank-Backup (täglich, ins OneDrive)
- Mehrere WEG-Objekte verwalten
- E-Mail-Versand aus der App (SMTP)

---

## Technische Schulden

- [ ] Datenbankfehler abfangen (try/except in allen DB-Funktionen)
- [ ] Eingabevalidierung verbessern (Betrag, IBAN, Datum)
- [ ] Bestätigungsdialog beim Löschen einheitlich machen
- [ ] Kontoauszug: Saldo-Verlauf anzeigen
