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
#   0.23.0 — Issues #64, #65, #66: Doppelte Buchführung (GoB) + Rechnungsverwaltung:
#             #64 Wasserkosten Mietzeiträume: Pro-Rata-Monatsberechnung bei Mieterwechsel;
#                 _calc_monate_im_jahr(), _import_wohnungen() neu, von_datum/bis_datum in Dialog;
#             #65 Mehrere Buchungen auf Rechnung: rechnung_id FK in zahlungen; Rechnungen-Tab
#                 zeigt Soll/Haben/Differenz farbkodiert; BuchungZuordnenDialog;
#             #66 Rechnungsverwaltung: neue RechnungenPage + RechnungDialog; ZUGFeRD (CII XML)
#                 und xRechnung (UBL 2.1) Import; KI-OCR Fallback; Navigation "🧾 Rechnungen"
#   0.24.0 — Issues #69/#70/#71/#72/#74: Auto-Matching Engine (Kontoauszug ↔ Rechnung):
#             _score_kontoauszug_gegen_rechnung() Weighted Fuzzy Score (Betrag 40%,
#             Datum 30%, Text 30%); _auto_match_alle() + _auto_log_match() (GoB Audit Trail);
#             MatchingReviewDialog: Vorschläge visuell bestätigen/ablehnen/überspringen;
#             kontoauszug_match_log DB-Tabelle (#71); Button „🔗 Auto-Matching" in KontoauszugPage;
#             Einstellungen-Tab „🔗 Matching" mit konfigurierbaren Schwellwerten (#74);
#             Matching-Log-Viewer in Einstellungen; Dashboard KPI: Auto-Matches +
#             Rechnungen offen + Teilbezahlt (#72).
#   0.23.1 — AC-Review + Bugfixes + neue Issues #67/#68:
#             Bug: zugferd_format ging beim UPDATE verloren (RechnungDialog + _edit_rechnung);
#             Bug: ZahlungDialog Rechnung-Dropdown zeigte Bezahlt-Rechnungen nicht;
#             #67 Auto-Status Rechnung (Offen→Teilbezahlt→Bezahlt) bei Zahlungszuordnung:
#                 _auto_update_rechnung_status() in _new_zahlung, _edit_buchung, BuchungZuordnenDialog;
#             #68 KI-OCR Fallback in _extrahiere_und_parse: Anthropic PDF-Vision wenn
#                 kein ZUGFeRD erkannt (claude-haiku-4-5-20251001 mit PDFs-Beta)
#   0.29.0 — GitHub Issues GH#76/GH#77/GH#79 (BuchungZuordnen-UX + Kostenart-Fix):
#             GH#76 Suchfeld "Nicht zugeordnete Buchungen": BuchungZuordnenDialog
#                 hat jetzt ein Live-Suchfeld (StringVar.trace) über dem unteren
#                 Treeview; filtert nach Datum, Beschreibung, Betrag, Belegnr;
#                 Cache self._alle_offen bleibt nach Reload erhalten.
#             GH#77 Click-to-Sort in beiden Treeviews: _setup_sort() richtet
#                 Spalten-Header mit ▲/▼-Pfeil ein; _sort_tree() sortiert
#                 numerisch (Betrag €) oder alphabetisch; toggle per zweitem Klick.
#             GH#78 Differenzbeträge: Konzept dokumentiert in konzept_workflow.html;
#                 Implementierung zurückgestellt (Needs Refinement).
#             GH#79 Umlageschlüssel zeigt Name statt Typ: _umlageschluessel_aus_aufteilungen()
#                 gibt jetzt (namen, name_zu_typ, typ_zu_name, tooltips) zurück;
#                 Combobox zeigt aufteilungen.name; intern wird Typ gespeichert;
#                 make_tooltip() zeigt Typ + Beschreibung bei Hover.
#   0.30.0 — GH Issues #83–#88: BuchhaltungPage Refactoring — Tabs auf andere Seiten verteilt:
#             #83 Vorschläge-Tab → KontoauszugPage (2-Tab-Struktur: Kontoauszug + Vorschläge)
#             #84 Buchungsregeln-Tab → EinstellungenPage Tab 5
#             #85 Kostenarten-Tab → EinstellungenPage Tab 6; KATEGORIEN/KOSTENARTEN
#                 bleiben als Klassenvariablen auf BuchhaltungPage
#             #86 Wohngeld Soll/Ist-Tab → NebenkostenPage als "💰 Hausgeld-Kontrolle" Tab 5
#             #87 _jahresabschluss_pdf() (reportlab) → _jahresabschluss_html() (Browser-HTML)
#             #88 Leere _import_csv()-Methode (pass) entfernt
#   0.28.0 — GH Issues #80/#81/#82:
#             #80 Dashboard Backup-KPI: Timestamp nach ZIP-Backup in
#                 einstellungen.json speichern (cfg["letztes_backup"]);
#                 DashboardPage Zeile 3 "Datensicherung" mit Datum (grün) oder
#                 "Kein Backup" (orange) als KPI-Kachel.
#             #81 CAMT.052 XML-Import: bereits vollständig implementiert
#                 (_import_xml + _parse_camt); nur Konzept-Aktualisierung.
#             #82 HTML-Jahresabrechnung: neuer Button "🌐 HTML Export" in
#                 NebenkostenPage §28-Tab; _export_html_weg() generiert
#                 druckfertiges HTML (kein reportlab nötig) mit KPI-Grid,
#                 Ausgaben- und Eigentümer-Tabelle; speichert nach
#                 Dokumente/Abrechnungen/; öffnet automatisch im Browser.
#   0.27.0 — GH Issues #76/#77/#78/#79:
#             #76 DB-Cleanup: 6 Waisen-Spalten aus zahlungen entfernt
#                 (rechnungssteller, rechnungsdatum, rechnungsnummer,
#                 gesamtrechnungsbetrag, lohnanteil, handwerker_steuerlich);
#                 NebenkostenPage-Query auf LEFT JOIN rechnungen umgestellt;
#                 Ista-INSERT vereinfacht.
#             #77 ZahlungDialog: Beleg-Datei-Feld + KI-Analyse entfernt;
#                 INSERT/UPDATE zahlungen ohne beleg_dateipfad.
#             #78 Kategorie-Sync: _sync_kategorie_von_rechnung() kopiert Kategorie
#                 der Rechnung in die Zahlung wenn Zahlung keine Kategorie hat
#                 (aufgerufen aus _new_zahlung, _edit_buchung, BuchungZuordnenDialog).
#             #79 Backup v2: ZIP-Archiv mit DB + einstellungen.json + backup_meta.json
#                 (SHA256-Prüfsumme); _db_restore liest .zip und .db (abwaertskompatibel).
#   0.26.0 — GH Issues #72/#73/#74/#75:
#             #72 Dialog-Größen persistent: BaseDialog.destroy() überschrieben →
#                 _persist_size() wird immer aufgerufen (auch bei Speichern/Abbrechen,
#                 nicht nur X-Button); _on_close() ruft jetzt destroy() auf.
#             #73 Beleg-Archivierung: neue Funktion _beleg_archivieren(); nach jedem
#                 Rechnung-Speichern wird Beleg-Kopie unter <app-dir>/Belege/<Jahr>/
#                 abgelegt; Ordner wird automatisch erstellt.
#             #74 §35a-Checkbox aus RechnungDialog entfernt: handwerker_steuerlich
#                 wird auto. auf 1 gesetzt wenn lohnanteil > 0, sonst 0.
#             #75 Duplikat-Erkennung Belegablage: bei gleichem Dateinamen in Ablage →
#                 Hinweisfenster mit Speichern/Abbrechen; bei Speichern: Versionierung
#                 als <basis>_duplikat_v<n><ext>; Original bleibt erhalten.
#   0.25.0 — GH Issues #68/#69/#70/#71:
#             #68 §35a EStG in RechnungDialog verschoben: handwerker_steuerlich
#                 Checkbox jetzt in RechnungDialog (Beträge-Abschnitt), nicht mehr
#                 in ZahlungDialog; DB-Migration rechnungen.handwerker_steuerlich;
#                 INSERT/UPDATE rechnungen um handwerker_steuerlich ergänzt.
#             #69 ZahlungDialog bereinigt: Rechnungsinformationen-Sektion entfernt
#                 (rechnungsdatum, rechnungsnummer, rechnungssteller,
#                 gesamtrechnungsbetrag, lohnanteil, §35a); INSERT/UPDATE zahlungen
#                 vereinfacht (11 statt 17 Spalten); Dialoghöhe 680→520.
#             #70 Nebenkosten-Unterkategorien in Sidebar ein-/ausklappbar:
#                 Ista-Wärme, Wasserkosten, Aufteilungen als eingerückte Sub-Buttons
#                 unter Nebenkosten; sub_frame wird beim Wechsel ein-/ausgeblendet.
#             #71 Dialog-Größen & Layout: BaseDialog minsize dynamisch (½ Defaultgröße,
#                 mind. 380×300); RechnungDialog 720→660, 2-Spalten-Layout für
#                 Grunddaten und Beträge; ZahlungDialog 680→520 (s. #69).
APP_VERSION = "0.30.0"
APP_NAME    = "Hausverwaltung"
APP_AUTHOR  = "WEG Welte Rapp Bilgery"
#   0.22.0 — Issues #58–#63:
#             #58 Buchung Rechnungsinformationen: rechnungsnummer, gesamtrechnungsbetrag,
#                 lohnanteil, handwerker_steuerlich (§35a EStG) als neue DB-Spalten;
#                 ZahlungDialog um diese Felder erweitert; Auto-Status „Geprüft" wenn
#                 Betrag == Gesamtrechnungsbetrag UND Belegnr == Rechnungsnummer;
#                 _ki_felder_befuellen: datum + betrag nur überschreiben wenn noch leer.
#             #59 Mieter NK-Vorauszahlung mit Zeiträumen: neue Tabelle
#                 nk_vorauszahlung_zeitraeume; NKZeitraumDialog für Verwaltung;
#                 nk_vorauszahlung_fuer_jahr() Hilfsfunktion (Pro-Rata-Temporis);
#                 §556 BGB Berechnung nutzt Zeitraum-basierte Vorauszahlungen.
#             #60 Ista-Abrechnungsjahr: Trace auf Abrechnungsjahr-Feld aktualisiert
#                 Zeitraum-von/bis automatisch auf 01-01 / 12-31.
#             #61 Ista-Auftragsnummer → Liegenschaftsnummer (Label + KI-Prompts).
#             #62 „Alle Wohnungen laden" filtert Mieter nach Abrechnungsjahr;
#                 separate Zeile je Mieter bei Mieterwechsel im Jahr.
#             #63 Wasserkosten „Aus Stamm": UPDATE bestehende Zeilen statt nur INSERT;
#                 _jahr_var trace_add für automatische Aktualisierung bei Jahreswechsel.
#   0.21.0 — Issues #56, #57:
#             #56 Buchungsdatum + Rechnungsdatum: zahlungen.rechnungsdatum (ALTER TABLE),
#                 ZahlungDialog umstrukturiert — Buchungsdatum oben, Sektion
#                 „Rechnungsinformationen" mit Rechnungsdatum + Rechnungssteller (#35/#56).
#                 BuchhaltungPage Spalte „Datum" → „Buchungsdatum".
#             #57 Aufteilung ↔ Kostenarten: _umlageschluessel_aus_aufteilungen() liest
#                 aktive aufteilungen.typ aus DB; _new_kostenart/_edit_kostenart nutzen
#                 dynamische Liste statt hardcodierter Werte.
#   0.20.1 — Issue #55: Ista-Werte manuell erfassen (_manuell_erfassen_komplett):
#             Gesamtwerte + Positionen pro Wohnung, „Alle Wohnungen laden"-Button,
#             Plausibilitätsprüfung (Summe Positionen vs. Gesamtwerte) mit Farbstatus.
#   0.20.0 — Issues #51–#54:
#             #51 WohnungDialog: Balkon/Terrasse/Garten/Stellplatz/Carport als Dropdown 0-5
#                 statt Ja/Nein + separate Anzahlfelder; vereinfachte Eingabe.
#             #52 ISTA PDF-Import: Bild-/Scan-PDFs per Anthropic Vision API (base64 Document-Block)
#                 analysieren; automatische Erkennung von gescannten vs. Text-PDFs.
#             #53 KI-Protokoll: Detail-Dialog (Doppelklick/Button), Kopieren-Funktion,
#                 versteckte ID-Spalte für eindeutige Selektion.
#             #54 Buchungsregeln: Spalte „Muster" → „Auftraggeber / Empfänger" für Klarheit.
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


# ── Pfad-Setup ──────────────────────────────────────────────────────────────
# v0.20.0: DB + Konfiguration liegen standardmäßig im Unterordner "daten"
# neben der hausverwaltung.py. Der DB-Pfad ist über die Einstellungen
# anpassbar (z. B. auf ein Netzlaufwerk).

APP_DIR = Path(__file__).parent                # Verzeichnis der Programmdatei (#38)
DATA_DIR = APP_DIR / "daten"                   # Standard-Datenverzeichnis

DEFAULT_DB_PATH = DATA_DIR / "hausverwaltung.db"
CONFIG_PATH = DATA_DIR / "einstellungen.json"

def _init_data_dir():
    """Erstellt daten/-Verzeichnis, migriert alte Dateien und legt eine
    Standard-einstellungen.json an falls noch keine existiert."""
    import shutil as _sh
    # 1. Verzeichnis sicherstellen
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 2. Alte Dateien migrieren (v0.19.0 und früher)
    _old_config = APP_DIR / "einstellungen.json"
    _old_db_home = Path.home() / "hausverwaltung.db"

    if _old_config.exists() and not CONFIG_PATH.exists():
        _sh.copy2(str(_old_config), str(CONFIG_PATH))
        print(f"[Migration] {_old_config} → {CONFIG_PATH}")

    if _old_db_home.exists() and not DEFAULT_DB_PATH.exists():
        _sh.copy2(str(_old_db_home), str(DEFAULT_DB_PATH))
        print(f"[Migration] {_old_db_home} → {DEFAULT_DB_PATH}")

    # 3. Garantiert eine einstellungen.json anlegen (Standardwerte)
    if not CONFIG_PATH.exists():
        default_cfg = {
            "pfad_datenbank": str(DEFAULT_DB_PATH),
            "pfad_belege": str(APP_DIR / "Belege"),
            "pfad_dokumente": str(APP_DIR / "Dokumente"),
            "pfad_backup": str(DATA_DIR / "backups"),
        }
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(default_cfg, indent=2, ensure_ascii=False, fp=f)
        print(f"[Init] Standardkonfiguration angelegt: {CONFIG_PATH}")

try:
    _init_data_dir()
except Exception as _e:
    print(f"[Warnung] daten/-Verzeichnis konnte nicht initialisiert werden: {_e}")

def load_config():
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_config(cfg: dict):
    try:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

def get_db_path() -> Path:
    """Liefert aktuellen DB-Pfad: Config 'pfad_datenbank' oder Standard (daten/hausverwaltung.db)."""
    try:
        cfg = load_config()
        p = cfg.get("pfad_datenbank", "")
        if p:
            pp = Path(p).expanduser()
            # Falls nur ein Verzeichnis angegeben wurde → Dateiname anhängen
            if pp.is_dir():
                pp = pp / "hausverwaltung.db"
            try:
                pp.parent.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
            return pp
    except Exception:
        pass
    return DEFAULT_DB_PATH

# DB_PATH wird initial ausgewertet; zur Laufzeit wird stets get_db_path()
# verwendet, damit Änderungen in den Einstellungen (z. B. Netzlaufwerk)
# ohne Neustart wirksam werden.
DB_PATH = get_db_path()

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

def ki_log(bereich: str, aktion: str, eingabe: str = "", ergebnis: str = "",
           modell: str = "", anbieter: str = "", dauer_ms: int = 0, fehler: str = ""):
    """Schreibt einen KI-Protokoll-Eintrag in die Datenbank (#44)."""
    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO ki_protokoll (bereich, aktion, eingabe_kurz, ergebnis_kurz, "
            "modell, anbieter, benutzer_id, dauer_ms, fehler) VALUES (?,?,?,?,?,?,?,?,?)",
            (bereich, aktion,
             (eingabe[:300] if eingabe else ""),
             (ergebnis[:500] if ergebnis else ""),
             modell, anbieter,
             _CURRENT_USER["id"] if _CURRENT_USER else None,
             dauer_ms, fehler))
        conn.commit()
        conn.close()
    except Exception:
        pass  # Protokollierung darf nie die App blockieren

def _lade_ki_training(bereich: str) -> tuple:
    """Gibt (feld_hinweise, system_zusatz) aus der ki_training-Tabelle zurück (#46)."""
    try:
        conn = get_db()
        r = conn.execute(
            "SELECT feld_hinweise, system_zusatz FROM ki_training WHERE bereich=?",
            (bereich,)).fetchone()
        conn.close()
        if r:
            return r["feld_hinweise"] or "", r["system_zusatz"] or ""
    except Exception:
        pass
    return "", ""

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
    conn = sqlite3.connect(str(get_db_path()))
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
CREATE TABLE IF NOT EXISTS ki_protokoll (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zeitpunkt DATETIME DEFAULT CURRENT_TIMESTAMP,
    bereich TEXT,
    aktion TEXT,
    eingabe_kurz TEXT,
    ergebnis_kurz TEXT,
    modell TEXT,
    anbieter TEXT,
    benutzer_id INTEGER,
    dauer_ms INTEGER,
    fehler TEXT
);
CREATE TABLE IF NOT EXISTS ki_training (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bereich TEXT NOT NULL UNIQUE,
    feld_hinweise TEXT,
    system_zusatz TEXT,
    geaendert_am DATETIME DEFAULT CURRENT_TIMESTAMP,
    geaendert_von INTEGER
);
CREATE TABLE IF NOT EXISTS nk_vorauszahlung_zeitraeume (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mieter_id INTEGER NOT NULL,
    beginn_datum DATE NOT NULL,
    ende_datum DATE,
    betrag REAL NOT NULL,
    FOREIGN KEY (mieter_id) REFERENCES mieter(id) ON DELETE CASCADE
);
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
        "ALTER TABLE zahlungen ADD COLUMN rechnungsdatum DATE",  # #56 Rechnungsdatum
        "CREATE TABLE IF NOT EXISTS nk_vorauszahlung_zeitraeume (id INTEGER PRIMARY KEY AUTOINCREMENT, mieter_id INTEGER NOT NULL, beginn_datum DATE NOT NULL, ende_datum DATE, betrag REAL NOT NULL)",  # #59
        "ALTER TABLE zahlungen ADD COLUMN rechnungsnummer TEXT",  # #58
        "ALTER TABLE zahlungen ADD COLUMN gesamtrechnungsbetrag REAL",  # #58
        "ALTER TABLE zahlungen ADD COLUMN lohnanteil REAL",  # #58
        "ALTER TABLE zahlungen ADD COLUMN handwerker_steuerlich INTEGER DEFAULT 0",  # #58 §35a EStG
        "ALTER TABLE zahlungen ADD COLUMN rechnung_id INTEGER",  # #65 Mehrere Buchungen auf eine Rechnung
        "CREATE TABLE IF NOT EXISTS rechnungen (id INTEGER PRIMARY KEY AUTOINCREMENT, rechnungsnummer TEXT, rechnungssteller TEXT NOT NULL, rechnungsdatum DATE, faelligkeitsdatum DATE, betrag_brutto REAL NOT NULL DEFAULT 0, betrag_netto REAL, mwst_satz REAL DEFAULT 19.0, mwst_betrag REAL, lohnanteil REAL, kategorie TEXT, beschreibung TEXT, beleg_dateipfad TEXT, status TEXT DEFAULT 'Offen', zugferd_format TEXT, erstellt_am DATETIME DEFAULT CURRENT_TIMESTAMP)",  # #66
        "ALTER TABLE rechnungen ADD COLUMN handwerker_steuerlich INTEGER DEFAULT 0",  # #68 §35a EStG
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
        # v0.19.0 – #48 Wohnfläche/Nutzfläche
        "ALTER TABLE wohnungen ADD COLUMN wohnflaeche_qm REAL",
        # v0.19.0 – #49 Balkon/Terrasse/Garten/Stellplatz/Carport mit Anzahl
        "ALTER TABLE wohnungen ADD COLUMN balkon_anzahl INTEGER DEFAULT 0",
        "ALTER TABLE wohnungen ADD COLUMN terrasse INTEGER DEFAULT 0",
        "ALTER TABLE wohnungen ADD COLUMN terrasse_anzahl INTEGER DEFAULT 0",
        "ALTER TABLE wohnungen ADD COLUMN garten INTEGER DEFAULT 0",
        "ALTER TABLE wohnungen ADD COLUMN garten_anzahl INTEGER DEFAULT 0",
        "ALTER TABLE wohnungen ADD COLUMN stellplatz_anzahl INTEGER DEFAULT 0",
        "ALTER TABLE wohnungen ADD COLUMN carport INTEGER DEFAULT 0",
        "ALTER TABLE wohnungen ADD COLUMN carport_anzahl INTEGER DEFAULT 0",
        # v0.19.0 – #50 Soft-Delete Wohnung
        "ALTER TABLE wohnungen ADD COLUMN aktiv INTEGER DEFAULT 1",
        # v0.24.0 – #71 Auto-Matching Audit Trail
        """CREATE TABLE IF NOT EXISTS kontoauszug_match_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            kontoauszug_id  INTEGER NOT NULL REFERENCES kontoauszug(id),
            rechnung_id     INTEGER REFERENCES rechnungen(id),
            zahlung_id      INTEGER REFERENCES zahlungen(id),
            score           REAL,
            methode         TEXT,
            benutzer        TEXT,
            erstellt_am     TEXT DEFAULT (datetime('now')),
            bestaetigt_am   TEXT,
            abgelehnt       INTEGER DEFAULT 0
        )""",
        # v0.27.0 – #76 DB-Cleanup: Waisen-Spalten aus zahlungen entfernen
        # (Felder existieren jetzt korrekt in rechnungen; in zahlungen nie mehr befüllt seit v0.25)
        "ALTER TABLE zahlungen DROP COLUMN rechnungssteller",
        "ALTER TABLE zahlungen DROP COLUMN rechnungsdatum",
        "ALTER TABLE zahlungen DROP COLUMN rechnungsnummer",
        "ALTER TABLE zahlungen DROP COLUMN gesamtrechnungsbetrag",
        "ALTER TABLE zahlungen DROP COLUMN lohnanteil",
        "ALTER TABLE zahlungen DROP COLUMN handwerker_steuerlich",
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


def make_tooltip(widget, text_oder_func):
    """GH#79 – Einfaches Tooltip-Popup (gelbes Label) für beliebige Tkinter-Widgets.

    text_oder_func: str oder callable → wird bei <Enter> ausgewertet.
    """
    _tip = [None]

    def _show(event):
        txt = text_oder_func() if callable(text_oder_func) else text_oder_func
        if not txt:
            return
        if _tip[0]:
            return
        tw = tk.Toplevel(widget)
        tw.wm_overrideredirect(True)
        x = widget.winfo_rootx() + 20
        y = widget.winfo_rooty() + widget.winfo_height() + 4
        tw.wm_geometry(f"+{x}+{y}")
        tk.Label(tw, text=txt, bg="#FFFBE6", fg=TEXT, relief="solid", bd=1,
                 font=FONT_SMALL, justify="left", padx=8, pady=5).pack()
        _tip[0] = tw

    def _hide(event):
        if _tip[0]:
            try:
                _tip[0].destroy()
            except Exception:
                pass
            _tip[0] = None

    widget.bind("<Enter>", _show, add="+")
    widget.bind("<Leave>", _hide, add="+")
    widget.bind("<FocusOut>", _hide, add="+")


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

    regeln = [dict(r) for r in regeln]

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

    def __init__(self, parent, title, width=500, height=520, min_w=None, min_h=None):
        super().__init__(parent)
        self._dialog_key = title  # key for size persistence
        self.title(title)
        self.configure(bg=BG_CARD)
        self.resizable(True, True)
        # #71 – Mindestgröße: mindestens die Hälfte der Standardgröße, min. 380×300
        self.minsize(max(380, min_w or width // 2), max(300, min_h or height // 2))
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
        self.destroy()  # destroy() ruft _persist_size() auf (#72)

    def destroy(self):
        """#72 – Größe immer speichern: bei X-Button, Speichern UND Abbrechen."""
        self._persist_size()
        super().destroy()

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
        """#72 – KPI-Kacheln für Buchungs-/Abrechnungsstatus inkl. Auto-Match-Rate."""
        conn = get_db()
        try:
            total   = conn.execute("SELECT COUNT(*) FROM kontoauszug").fetchone()[0]
            zugeord = conn.execute("SELECT COUNT(*) FROM kontoauszug WHERE buchung_status='uebernommen' OR buchung_status='abgerechnet'").fetchone()[0]
            offen   = conn.execute("SELECT COUNT(*) FROM kontoauszug WHERE als_buchung_uebernommen=0 AND kategorie_vorschlag IS NOT NULL AND kategorie_vorschlag!=''").fetchone()[0]
            ungekl  = conn.execute("SELECT COUNT(*) FROM kontoauszug WHERE als_buchung_uebernommen=0 AND (kategorie_vorschlag IS NULL OR kategorie_vorschlag='')").fetchone()[0]
            abr_status = conn.execute("SELECT status, jahr FROM abrechnungen WHERE typ='WEG' ORDER BY jahr DESC LIMIT 1").fetchone()
            # #72 – Matching-Rate: Automatisch gebuchte Matches
            auto_matches = conn.execute(
                "SELECT COUNT(*) FROM kontoauszug_match_log WHERE methode='auto' AND abgelehnt=0"
            ).fetchone()[0]
            # Offene Rechnungen
            rg_offen = conn.execute(
                "SELECT COUNT(*) FROM rechnungen WHERE status='Offen'"
            ).fetchone()[0]
            rg_teilbez = conn.execute(
                "SELECT COUNT(*) FROM rechnungen WHERE status='Teilbezahlt'"
            ).fetchone()[0]
        finally:
            conn.close()

        abr_text = "Keine Abrechnung" if not abr_status else f"{abr_status['status']} {abr_status['jahr']}"
        abr_farbe = SUCCESS if (abr_status and abr_status["status"] == "Festgestellt") else ACCENT

        # Zeile 1: bestehende KPIs
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

        # Zeile 2: #72 Matching + Rechnungs-KPIs
        frame2 = tk.Frame(parent, bg=BG_CARD)
        frame2.grid(row=2, column=0, columnspan=2, sticky="ew", padx=(0, 8), pady=(4, 0), ipady=6)
        tk.Label(frame2, text="Rechnungen & Matching", bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w", padx=12)

        kpis2_frame = tk.Frame(frame2, bg=BG_CARD)
        kpis2_frame.pack(fill="x", padx=12)

        for text, wert, farbe in [
            ("🔗 Auto-Matches",      str(auto_matches),  ACCENT2),
            ("🧾 Rechnungen offen",  str(rg_offen),      DANGER if rg_offen > 0 else TEXT_LIGHT),
            ("⏳ Teilbezahlt",       str(rg_teilbez),    ACCENT if rg_teilbez > 0 else TEXT_LIGHT),
        ]:
            card2 = tk.Frame(kpis2_frame, bg=BG_INPUT, bd=0, relief="flat")
            card2.pack(side="left", padx=(0, 8), pady=4, ipadx=12, ipady=8)
            tk.Label(card2, text=wert, bg=BG_INPUT, fg=farbe, font=FONT_H2).pack()
            tk.Label(card2, text=text, bg=BG_INPUT, fg=TEXT_LIGHT, font=FONT_SMALL).pack()

        # Zeile 3: #80 Backup-KPI
        letztes_backup_raw = load_config().get("letztes_backup")
        if letztes_backup_raw:
            try:
                from datetime import datetime as _dt
                backup_dt = _dt.fromisoformat(letztes_backup_raw)
                backup_text = backup_dt.strftime("%d.%m.%Y %H:%M")
                backup_farbe = SUCCESS
                backup_icon = "💾"
            except Exception:
                backup_text = "Fehler"
                backup_farbe = DANGER
                backup_icon = "⚠️"
        else:
            backup_text = "Kein Backup!"
            backup_farbe = WARNING
            backup_icon = "⚠️"

        frame3 = tk.Frame(parent, bg=BG_CARD)
        frame3.grid(row=3, column=0, columnspan=2, sticky="ew", padx=(0, 8), pady=(4, 0), ipady=6)
        tk.Label(frame3, text="Datensicherung", bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w", padx=12)
        kpis3_frame = tk.Frame(frame3, bg=BG_CARD)
        kpis3_frame.pack(fill="x", padx=12)
        card3 = tk.Frame(kpis3_frame, bg=BG_INPUT, bd=0, relief="flat")
        card3.pack(side="left", padx=(0, 8), pady=4, ipadx=12, ipady=8)
        tk.Label(card3, text=f"{backup_icon} {backup_text}", bg=BG_INPUT, fg=backup_farbe, font=FONT_H2).pack()
        tk.Label(card3, text="Letztes Backup", bg=BG_INPUT, fg=TEXT_LIGHT, font=FONT_SMALL).pack()  # #80

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


# ── #59 Hilfsfunktion: NK-Vorauszahlung aus Zeiträumen ───────────────────────

def nk_vorauszahlung_fuer_jahr(mieter_id: int, jahr: int,
                                fallback_monatlich: float = 0.0) -> float:
    """Berechnet die gewichtete NK-Vorauszahlung für ein Abrechnungsjahr.

    Für jeden Zeitraum, der das Jahr überlappt, wird der tagesgenaue Anteil
    berechnet (Pro-Rata-Temporis). Wenn keine Zeiträume vorhanden sind,
    wird der Fallback-Wert × 12 verwendet.
    """
    from datetime import date as _date
    try:
        conn = get_db()
        try:
            reihen = conn.execute(
                "SELECT beginn_datum, ende_datum, betrag "
                "FROM nk_vorauszahlung_zeitraeume "
                "WHERE mieter_id=? ORDER BY beginn_datum",
                (mieter_id,)
            ).fetchall()
        finally:
            conn.close()
        if not reihen:
            return fallback_monatlich * 12
        jahr_von = _date(jahr, 1, 1)
        jahr_bis = _date(jahr, 12, 31)
        tage_jahr = 366 if jahr % 4 == 0 and (jahr % 100 != 0 or jahr % 400 == 0) else 365
        total = 0.0
        for r in reihen:
            b = r["beginn_datum"]
            e = r["ende_datum"]
            betrag = float(r["betrag"] or 0)
            try:
                zr_von = _date.fromisoformat(b) if b else _date(1900, 1, 1)
                zr_bis = _date.fromisoformat(e) if e else _date(9999, 12, 31)
            except (ValueError, TypeError):
                continue
            # Überschneidung mit Abrechnungsjahr
            overlap_von = max(zr_von, jahr_von)
            overlap_bis = min(zr_bis, jahr_bis)
            if overlap_von > overlap_bis:
                continue
            tage = (overlap_bis - overlap_von).days + 1
            # Jahresanteil × Jahresbetrag (= betrag_monatlich × 12)
            total += betrag * 12 * (tage / tage_jahr)
        return total
    except Exception:
        return fallback_monatlich * 12


class NKZeitraumDialog(tk.Toplevel):
    """#59 – Verwaltung der NK-Vorauszahlungs-Zeiträume für einen Mieter."""

    def __init__(self, parent, mieter_id: int, mieter_name: str):
        super().__init__(parent)
        self.title(f"NK-Vorauszahlungs-Zeiträume – {mieter_name}")
        self.configure(bg=BG_CARD)
        self.geometry("580x460")
        self.resizable(False, False)
        self.grab_set()
        self._mieter_id = mieter_id
        self._build()
        self._load()

    def _build(self):
        tk.Label(self, text="NK-Vorauszahlungs-Zeiträume",
                 bg=BG_CARD, fg=TEXT, font=FONT_H2).pack(padx=20, pady=(16, 2), anchor="w")
        tk.Label(self,
                 text="Kein Ende-Datum = unbefristet. Zeiträume dürfen sich nicht überschneiden.",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(padx=20, anchor="w")

        # Tabelle
        f, self._tree = make_table(self,
            ("Von (JJJJ-MM-TT)", "Bis (JJJJ-MM-TT)", "Betrag €/Monat"), height=8)
        f.pack(fill="both", expand=True, padx=20, pady=8)
        for col, w in zip(("Von (JJJJ-MM-TT)", "Bis (JJJJ-MM-TT)", "Betrag €/Monat"),
                           [170, 170, 130]):
            self._tree.heading(col, text=col)
            self._tree.column(col, width=w, anchor="w")

        # Formular für neue Zeile
        frm = tk.Frame(self, bg=BG_INPUT, padx=12, pady=10)
        frm.pack(fill="x", padx=20, pady=(0, 8))
        tk.Label(frm, text="Von:", bg=BG_INPUT, fg=TEXT_LIGHT, font=FONT_SMALL,
                 width=6, anchor="w").grid(row=0, column=0)
        self._von_var = tk.StringVar()
        tk.Entry(frm, textvariable=self._von_var, bg=BG_CARD, fg=TEXT, font=FONT_BODY,
                 relief="flat", bd=0, width=14).grid(row=0, column=1, padx=(4, 12))
        tk.Label(frm, text="Bis:", bg=BG_INPUT, fg=TEXT_LIGHT, font=FONT_SMALL,
                 width=4, anchor="w").grid(row=0, column=2)
        self._bis_var = tk.StringVar()
        tk.Entry(frm, textvariable=self._bis_var, bg=BG_CARD, fg=TEXT, font=FONT_BODY,
                 relief="flat", bd=0, width=14).grid(row=0, column=3, padx=(4, 12))
        tk.Label(frm, text="Betrag €:", bg=BG_INPUT, fg=TEXT_LIGHT, font=FONT_SMALL,
                 width=8, anchor="w").grid(row=0, column=4)
        self._betrag_var = tk.StringVar()
        tk.Entry(frm, textvariable=self._betrag_var, bg=BG_CARD, fg=TEXT, font=FONT_BODY,
                 relief="flat", bd=0, width=10).grid(row=0, column=5, padx=(4, 12))
        make_btn(frm, "➕ Hinzufügen", self._add).grid(row=0, column=6)

        # Buttons
        btn_row = tk.Frame(self, bg=BG_CARD)
        btn_row.pack(fill="x", padx=20, pady=(0, 12))
        make_btn(btn_row, "🗑 Ausgewählten löschen", self._delete, color=DANGER).pack(side="left")
        make_btn(btn_row, "Schließen", self.destroy, color=ACCENT2).pack(side="right")

    def _load(self):
        for i in self._tree.get_children():
            self._tree.delete(i)
        conn = get_db()
        try:
            rows = conn.execute(
                "SELECT id, beginn_datum, ende_datum, betrag "
                "FROM nk_vorauszahlung_zeitraeume "
                "WHERE mieter_id=? ORDER BY beginn_datum",
                (self._mieter_id,)
            ).fetchall()
        finally:
            conn.close()
        for r in rows:
            self._tree.insert("", "end", iid=r["id"], values=(
                r["beginn_datum"] or "–",
                r["ende_datum"] or "unbefristet",
                fmt_euro(r["betrag"])
            ))
        tree_empty_hint(self._tree)

    def _add(self):
        von = self._von_var.get().strip()
        bis = self._bis_var.get().strip() or None
        betrag_str = self._betrag_var.get().strip().replace(",", ".")
        # Validierung
        if not von:
            messagebox.showwarning("Pflichtfeld", "Von-Datum ist erforderlich.", parent=self)
            return
        try:
            from datetime import date as _date
            _date.fromisoformat(von)
            if bis:
                bis_d = _date.fromisoformat(bis)
                von_d = _date.fromisoformat(von)
                if bis_d < von_d:
                    messagebox.showwarning("Datum", "Bis-Datum darf nicht vor Von-Datum liegen.", parent=self)
                    return
        except ValueError:
            messagebox.showwarning("Datum", "Datum im Format JJJJ-MM-TT eingeben.", parent=self)
            return
        try:
            betrag = float(betrag_str)
            if betrag < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Betrag", "Betrag muss eine positive Zahl sein.", parent=self)
            return
        # Überschneidungs-Check
        if self._hat_ueberschneidung(von, bis):
            messagebox.showwarning("Überschneidung",
                "Dieser Zeitraum überschneidet sich mit einem bestehenden Eintrag.\n"
                "Bitte Zeiträume lückenlos und überschneidungsfrei anlegen.", parent=self)
            return
        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO nk_vorauszahlung_zeitraeume (mieter_id, beginn_datum, ende_datum, betrag) "
                "VALUES (?,?,?,?)",
                (self._mieter_id, von, bis, betrag)
            )
            conn.commit()
        finally:
            conn.close()
        self._von_var.set("")
        self._bis_var.set("")
        self._betrag_var.set("")
        self._load()

    def _delete(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showwarning("Auswahl", "Bitte einen Eintrag auswählen.", parent=self)
            return
        if not messagebox.askyesno("Löschen", "Ausgewählten Zeitraum löschen?", parent=self):
            return
        conn = get_db()
        try:
            conn.execute("DELETE FROM nk_vorauszahlung_zeitraeume WHERE id=?", (int(sel[0]),))
            conn.commit()
        finally:
            conn.close()
        self._load()

    def _hat_ueberschneidung(self, von: str, bis) -> bool:
        """Prüft ob der neue Zeitraum einen bestehenden überlappt."""
        from datetime import date as _date
        conn = get_db()
        try:
            rows = conn.execute(
                "SELECT beginn_datum, ende_datum FROM nk_vorauszahlung_zeitraeume "
                "WHERE mieter_id=?",
                (self._mieter_id,)
            ).fetchall()
        finally:
            conn.close()
        try:
            von_d = _date.fromisoformat(von)
            bis_d = _date.fromisoformat(bis) if bis else _date(9999, 12, 31)
        except (ValueError, TypeError):
            return False
        for r in rows:
            try:
                ex_von = _date.fromisoformat(r["beginn_datum"]) if r["beginn_datum"] else _date(1900, 1, 1)
                ex_bis = _date.fromisoformat(r["ende_datum"]) if r["ende_datum"] else _date(9999, 12, 31)
            except (ValueError, TypeError):
                continue
            if von_d <= ex_bis and bis_d >= ex_von:
                return True
        return False


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
        self._add_field("NK-Vorausz. € (aktuell)", "nk", r.get("nebenkosten_vorauszahlung",""), row=ri)
        # #59 – Zeiträume-Button (nur für vorhandene Mieter)
        self._mieter_id = r.get("id")
        self._mieter_row = r
        if self._mieter_id:
            nk_btn_row = tk.Frame(self._body, bg=BG_CARD)
            nk_btn_row.pack(fill="x", padx=20, pady=(0, 4))
            mieter_name = f"{r.get('vorname','')} {r.get('name','')}".strip()
            make_btn(nk_btn_row, "📅 NK-Zeiträume verwalten",
                     lambda: NKZeitraumDialog(self, self._mieter_id, mieter_name),
                     color=BG_INPUT, fg=TEXT).pack(side="left")
            tk.Label(nk_btn_row,
                     text="(Zeitraum-basierte Vorauszahlungen für §556 BGB Abrechnung)",
                     bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(side="left", padx=(8, 0))

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

    # Spalten die im INSERT/UPDATE der Wohnungen verwendet werden (#50 Bug-Fix +
    # #48/#49 neue Felder).  Eine zentrale Liste verhindert, dass Spalten und
    # Werte sich auseinander entwickeln.
    _COLS = (
        "bezeichnung", "typ", "etage", "lage",
        "wohnflaeche_qm", "nutzflaeche_qm", "zimmer",
        "balkon", "balkon_anzahl",
        "terrasse", "terrasse_anzahl",
        "garten", "garten_anzahl",
        "stellplatz", "stellplatz_anzahl",
        "carport", "carport_anzahl",
        "keller", "heizungsart",
        "mea_tausendstel", "eigentuemer_id", "mieter_id",
        "baujahr", "bewohner_anzahl", "notizen", "aktiv",
    )

    def _build(self):
        section_header(self, "Wohnungen", "＋ Wohnung", self._new)
        cols = ("Bezeichnung", "Typ", "Lage", "Wohnfl. m²", "Nutzfl. m²", "Zimmer",
                "MEA ‰", "MEA-Kontr. ‰", "Eigentümer", "Mieter", "Status")
        f, self.tree = make_table(self, cols, height=16)
        f.pack(fill="both", expand=True, padx=20, pady=10)
        for c, w in zip(cols, [110, 70, 90, 75, 75, 60, 70, 90, 130, 130, 70]):
            self.tree.heading(c, text=c); self.tree.column(c, width=w, anchor="w")
        self.tree.bind("<Double-1>", self._edit)
        btn_row = tk.Frame(self, bg=BG_CARD)
        btn_row.pack(fill="x", padx=20, pady=(0, 10))
        if hat_recht("Wohnungen", "schreiben"):
            make_btn(btn_row, "✏ Bearbeiten", self._edit, color=BG_INPUT, fg=TEXT).pack(side="left", padx=(0, 8))
            make_btn(btn_row, "⊘ Deaktivieren", self._deaktivieren, color=BG_INPUT, fg=TEXT).pack(side="left", padx=(0, 8))
            if hat_recht("Wohnungen", "loeschen"):
                make_btn(btn_row, "↺ Reaktivieren", self._reaktivieren, color=BG_INPUT, fg=TEXT).pack(side="left", padx=(0, 8))
        if hat_recht("Wohnungen", "loeschen"):
            make_btn(btn_row, "🗑 Löschen", self._delete, color=DANGER).pack(side="left")
        # Anzeige inaktiver Wohnungen erfordert Löschrecht (#50)
        self._zeige_inaktive = hat_recht("Wohnungen", "loeschen")
        self._load()

    def _load(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        conn = get_db()
        where = "" if self._zeige_inaktive else "WHERE COALESCE(w.aktiv,1)=1"
        rows = conn.execute(
            "SELECT w.*, e.name as ename, e.vorname as evname, m.name as mname, m.vorname as mvname "
            "FROM wohnungen w "
            "LEFT JOIN eigentuemer e ON w.eigentuemer_id=e.id "
            "LEFT JOIN mieter m ON w.mieter_id=m.id "
            f"{where} ORDER BY w.bezeichnung").fetchall()
        # Summe der Wohnflächen für MEA-Kontrollberechnung (#48)
        total_wfl = conn.execute(
            "SELECT COALESCE(SUM(wohnflaeche_qm),0) FROM wohnungen WHERE COALESCE(aktiv,1)=1"
        ).fetchone()[0] or 0.0
        for r in rows:
            d = dict(r)
            ename = f"{d.get('evname') or ''} {d.get('ename') or ''}".strip() if d.get('ename') else "–"
            mname = f"{d.get('mvname') or ''} {d.get('mname') or ''}".strip() if d.get('mname') else "–"
            mea = f"{parse_float(d.get('mea_tausendstel')):.1f}" if d.get("mea_tausendstel") else "–"
            wfl = parse_float(d.get("wohnflaeche_qm"))
            # MEA-Kontrolle nach Wohnfläche: 1000 * (Wohnfläche / Gesamt-Wohnfläche)
            mea_ctrl = f"{(1000.0 * wfl / total_wfl):.1f}" if (wfl and total_wfl) else "–"
            status = "aktiv" if (d.get("aktiv") in (None, 1)) else "inaktiv"
            self.tree.insert("", "end", iid=d["id"], values=(
                d["bezeichnung"], d.get("typ") or "–", d.get("lage") or "–",
                f"{wfl:.1f}" if wfl else "–",
                f"{parse_float(d.get('nutzflaeche_qm')):.1f}" if d.get("nutzflaeche_qm") else "–",
                d.get("zimmer") or "–", mea, mea_ctrl,
                ename, mname, status))
        conn.close()
        tree_empty_hint(self.tree)

    def _save_values(self, v: dict, where_id: int = None):
        """Zentrales INSERT/UPDATE für Wohnungen (#50 Bug-Fix).
        Verwendet self._COLS damit Spalten und Werte synchron bleiben.
        Fehler werden dem Benutzer als Messagebox angezeigt."""
        try:
            conn = get_db()
            try:
                vals = [v.get(c) if v.get(c) not in ("", None) else (0 if c in (
                    "balkon","balkon_anzahl","terrasse","terrasse_anzahl",
                    "garten","garten_anzahl","stellplatz_anzahl","carport","carport_anzahl"
                ) else (1 if c == "aktiv" else None)) for c in self._COLS]
                if where_id is None:
                    cols_sql = ",".join(self._COLS)
                    placeholders = ",".join(["?"] * len(self._COLS))
                    conn.execute(f"INSERT INTO wohnungen ({cols_sql}) VALUES ({placeholders})", vals)
                else:
                    set_sql = ",".join(f"{c}=?" for c in self._COLS)
                    conn.execute(f"UPDATE wohnungen SET {set_sql} WHERE id=?", vals + [int(where_id)])
                conn.commit()
                sync_mea_eigentuemer(conn)
                conn.commit()
            finally:
                conn.close()
            return True
        except Exception as ex:
            messagebox.showerror("Fehler beim Speichern",
                                 f"Wohnung konnte nicht gespeichert werden:\n{ex}",
                                 parent=self)
            return False

    def _new(self):
        if not hat_recht("Wohnungen", "schreiben"):
            messagebox.showwarning("Berechtigung", "Sie haben keine Schreibberechtigung.", parent=self); return
        d = WohnungDialog(self)
        self.wait_window(d)
        if d.result:
            if self._save_values(d.result):
                self._load()

    def _edit(self, event=None):
        if not hat_recht("Wohnungen", "schreiben"):
            messagebox.showwarning("Berechtigung", "Sie haben keine Schreibberechtigung.", parent=self); return
        sel = self.tree.selection()
        if not sel: return
        conn = get_db()
        row = conn.execute("SELECT * FROM wohnungen WHERE id=?", (int(sel[0]),)).fetchone()
        conn.close()
        if not row: return
        d = WohnungDialog(self, row)
        self.wait_window(d)
        if d.result:
            if self._save_values(d.result, where_id=int(sel[0])):
                self._load()

    def _deaktivieren(self):
        if not hat_recht("Wohnungen", "schreiben"):
            messagebox.showwarning("Berechtigung", "Sie haben keine Schreibberechtigung.", parent=self); return
        sel = self.tree.selection()
        if not sel: return
        if messagebox.askyesno("Deaktivieren", "Wohnung deaktivieren?", parent=self):
            conn = get_db()
            conn.execute("UPDATE wohnungen SET aktiv=0 WHERE id=?", (int(sel[0]),))
            conn.commit(); sync_mea_eigentuemer(conn); conn.commit(); conn.close()
            self._load()

    def _reaktivieren(self):
        if not hat_recht("Wohnungen", "loeschen"):
            messagebox.showwarning("Berechtigung", "Reaktivieren erfordert Löschrecht.", parent=self); return
        sel = self.tree.selection()
        if not sel: return
        conn = get_db()
        conn.execute("UPDATE wohnungen SET aktiv=1 WHERE id=?", (int(sel[0]),))
        conn.commit(); sync_mea_eigentuemer(conn); conn.commit(); conn.close()
        self._load()

    def _delete(self):
        if not hat_recht("Wohnungen", "loeschen"):
            messagebox.showwarning("Berechtigung", "Sie haben keine Löschberechtigung.", parent=self); return
        sel = self.tree.selection()
        if not sel: return
        if messagebox.askyesno("Löschen", "Wohnung endgültig löschen?", parent=self):
            try:
                conn = get_db()
                conn.execute("DELETE FROM wohnungen WHERE id=?", (int(sel[0]),))
                conn.commit(); conn.close()
            except Exception as ex:
                messagebox.showerror("Fehler", str(ex), parent=self)
            self._load()


class WohnungDialog(BaseDialog):
    def __init__(self, parent, row=None):
        super().__init__(parent, "Wohnung " + ("bearbeiten" if row else "hinzufügen"), 600, 780)
        r = dict(row) if row else {}
        self._row = r

        def _two():
            f = tk.Frame(self._body, bg=BG_CARD); f.pack(fill="x", padx=20)
            f.columnconfigure((0,1), weight=1)
            l = tk.Frame(f, bg=BG_CARD); l.grid(row=0, column=0, padx=(0,6), sticky="ew")
            ri = tk.Frame(f, bg=BG_CARD); ri.grid(row=0, column=1, padx=(6,0), sticky="ew")
            return l, ri

        self._add_field("Bezeichnung *", "bezeichnung", r.get("bezeichnung",""))
        l, ri = _two()
        self._add_field("Typ", "typ", r.get("typ","Wohnung"), row=l)
        self._add_field("Etage", "etage", r.get("etage",""), row=ri)
        l, ri = _two()
        self._add_field("Lage", "lage", r.get("lage",""), row=l)
        self._add_field("Zimmer", "zimmer", r.get("zimmer",""), row=ri)

        # #48 Wohnfläche / Nutzfläche laut Aufteilungsplan
        l, ri = _two()
        self._add_field("Wohnfläche m² (laut Aufteilungsplan)", "wohnflaeche_qm",
                        r.get("wohnflaeche_qm",""), row=l)
        self._add_field("Nutzfläche m² (z. B. Keller, ohne MEA-Einfluss)", "nutzflaeche_qm",
                        r.get("nutzflaeche_qm",""), row=ri)

        # #51 Balkon / Terrasse / Garten / Stellplatz / Carport — einheitlich als
        # Dropdown 0-5 (Anzahl).  Das ersetzt die bisherigen Ja/Nein + separate
        # Anzahl-Felder.  Die DB-Spalten "balkon", "terrasse" etc. speichern jetzt
        # direkt die Anzahl (0 = keiner, 1-5 = Stück).
        anzahl_opt = ["0", "1", "2", "3", "4", "5"]
        l, ri = _two()
        self._add_field("Balkone", "balkon", str(r.get("balkon") or 0),
                        widget_type="combo", options=anzahl_opt, row=l)
        self._add_field("Terrassen", "terrasse", str(r.get("terrasse") or 0),
                        widget_type="combo", options=anzahl_opt, row=ri)
        l, ri = _two()
        self._add_field("Gärten", "garten", str(r.get("garten") or 0),
                        widget_type="combo", options=anzahl_opt, row=l)
        self._add_field("Stellplätze", "stellplatz_anzahl", str(r.get("stellplatz_anzahl") or 0),
                        widget_type="combo", options=anzahl_opt, row=ri)
        l, ri = _two()
        self._add_field("Carports", "carport", str(r.get("carport") or 0),
                        widget_type="combo", options=anzahl_opt, row=l)
        self._add_field("Stellplatz-Typ", "stellplatz", r.get("stellplatz","") or "",
                        widget_type="combo", options=["", "Außen", "Tiefgarage", "Doppelparker"], row=ri)

        l, ri = _two()
        self._add_field("Keller", "keller", r.get("keller",""), row=l)
        self._add_field("Heizungsart", "heizungsart", r.get("heizungsart","Zentralheizung"), row=ri)

        l, ri = _two()
        self._add_field("MEA Tausendstel (Miteigentumsanteil)", "mea_tausendstel",
                        r.get("mea_tausendstel",""), row=l)
        self._add_field("Baujahr", "baujahr", r.get("baujahr",""), row=ri)

        # #48 MEA-Kontrollwert (live berechnet aus Wohnfläche / Σ Wohnflächen)
        self._mea_ctrl_var = tk.StringVar(value="")
        ctl = tk.Frame(self._body, bg=BG_CARD); ctl.pack(fill="x", padx=20, pady=(8,0))
        tk.Label(ctl, text="MEA-Kontrollwert (1000 × Wohnfläche / Σ aktive Wohnflächen):",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w")
        tk.Label(ctl, textvariable=self._mea_ctrl_var, bg=BG_CARD, fg=ACCENT2,
                 font=FONT_BODY).pack(anchor="w")
        # Bei jeder Änderung des Wohnflächen-Feldes neu berechnen
        try:
            self._fields["wohnflaeche_qm"].trace_add("write", lambda *a: self._update_mea_kontrolle())
        except Exception:
            pass
        self._update_mea_kontrolle()

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

    def _update_mea_kontrolle(self):
        """#48 – Live-Anzeige des MEA-Kontrollwerts beim Bearbeiten."""
        try:
            wfl = parse_float(self._fields["wohnflaeche_qm"].get())
        except Exception:
            wfl = 0.0
        try:
            conn = get_db()
            row_id = self._row.get("id")
            if row_id:
                total = conn.execute(
                    "SELECT COALESCE(SUM(wohnflaeche_qm),0) FROM wohnungen "
                    "WHERE COALESCE(aktiv,1)=1 AND id<>?", (row_id,)).fetchone()[0] or 0.0
            else:
                total = conn.execute(
                    "SELECT COALESCE(SUM(wohnflaeche_qm),0) FROM wohnungen "
                    "WHERE COALESCE(aktiv,1)=1").fetchone()[0] or 0.0
            conn.close()
        except Exception:
            total = 0.0
        gesamt = total + (wfl or 0.0)
        if wfl and gesamt:
            self._mea_ctrl_var.set(f"{(1000.0 * wfl / gesamt):.2f} ‰  (von gesamt {gesamt:.1f} m²)")
        else:
            self._mea_ctrl_var.set("– (Wohnfläche eintragen)")

    def _on_save(self):
        v = self._get_values()
        if not v.get("bezeichnung"):
            messagebox.showwarning("Pflichtfeld", "Bezeichnung ist erforderlich.", parent=self); return

        # #51 Dropdown-Werte → int (Balkone, Terrassen etc. jetzt direkt als Anzahl 0-5)
        for key in ("balkon", "terrasse", "garten", "carport",
                    "stellplatz_anzahl", "zimmer", "baujahr"):
            try:
                v[key] = int(parse_float(v.get(key))) if v.get(key) not in ("", None) else 0
            except Exception:
                v[key] = 0
        # Nicht mehr genutzte separate Anzahl-Felder synchronisieren (Abwärtskompatibilität)
        v["balkon_anzahl"] = v.get("balkon", 0)
        v["terrasse_anzahl"] = v.get("terrasse", 0)
        v["garten_anzahl"] = v.get("garten", 0)
        v["carport_anzahl"] = v.get("carport", 0)

        # Float-Felder
        for key in ("wohnflaeche_qm", "nutzflaeche_qm", "mea_tausendstel"):
            v[key] = parse_float(v.get(key)) if v.get(key) not in ("", None) else None

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

        # Felder die im Dialog nicht editierbar sind beim Bearbeiten erhalten
        v.setdefault("bewohner_anzahl", self._row.get("bewohner_anzahl") or 1)
        # Beim Bearbeiten Aktiv-Status erhalten, beim Neu-Anlegen aktiv=1 (#50)
        v["aktiv"] = self._row.get("aktiv", 1)
        if v["aktiv"] is None:
            v["aktiv"] = 1

        self.result = v; self.destroy()

# ── Buchhaltung-Seite ─────────────────────────────────────────────────────────

class BuchhaltungPage(tk.Frame):
    """Buchhaltung: Buchungen verwalten, Jahresabschluss-Export."""

    # Kostenkategorien – zentral aus WEG_KATEGORIEN (einheitliches System)
    KATEGORIEN = WEG_KATEGORIEN_LISTE[:]
    # Metadaten für Kostenarten aus dem globalen System ableiten
    KOSTENARTEN = {
        k: {"kategorie": v[0], "umlagefaehig": v[1], "schluessel": v[2]}
        for k, v in WEG_KATEGORIEN.items()
    }

    def __init__(self, parent):
        super().__init__(parent, bg=BG_CARD)
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
        make_btn(top, "🌐 Jahresabschluss", self._jahresabschluss_html,
                 color=BG_INPUT, fg=TEXT).pack(side="right", padx=(0, 8))
        make_btn(top, "📊 Export CSV",  self._export_csv,
                 color=BG_INPUT, fg=TEXT).pack(side="right", padx=(0, 8))
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(6, 0))

        # ── Filter-Zeile ──────────────────────────────────────────────────────
        filter_frame = tk.Frame(self, bg=BG_CARD)
        filter_frame.pack(fill="x", padx=20, pady=(4, 0))
        tk.Label(filter_frame, text="Typ:", bg=BG_CARD,
                 fg=TEXT_LIGHT, font=FONT_SMALL).pack(side="left")
        self._typ_var = tk.StringVar(value="Alle")
        for t in ("Alle", "Einnahme", "Ausgabe"):
            tk.Radiobutton(filter_frame, text=t, variable=self._typ_var, value=t,
                           bg=BG_CARD, fg=TEXT, font=FONT_SMALL,
                           activebackground=BG_CARD, selectcolor=BG_CARD,
                           command=self._load_buchungen).pack(side="left", padx=6)

        # ── Buchungen-Tabelle ──────────────────────────────────────────────────
        cols_b = ("Buchungsdatum", "Beschreibung", "Kategorie", "Betrag", "Typ", "Status", "Belegnr.", "📎")  # #56
        fb, self.tree_b = make_table(self, cols_b, height=16)
        fb.pack(fill="both", expand=True, padx=20, pady=6)
        for c, w in zip(cols_b, [100, 200, 110, 100, 80, 80, 80, 28]):
            self.tree_b.heading(c, text=c); self.tree_b.column(c, width=w, anchor="w")
        self.tree_b.tag_configure("einnahme", foreground=SUCCESS)
        self.tree_b.tag_configure("ausgabe",  foreground=DANGER)
        self.tree_b.tag_configure("neu", foreground=ACCENT2, font=("Segoe UI Semibold", 10))
        self.tree_b.bind("<Double-1>", self._edit_buchung)

        btn_b = tk.Frame(self, bg=BG_CARD)
        btn_b.pack(fill="x", padx=20, pady=(0, 8))
        make_btn(btn_b, "✏ Bearbeiten",       self._edit_buchung, color=BG_INPUT, fg=TEXT).pack(side="left", padx=(0,6))
        make_btn(btn_b, "🗑 Löschen",         self._delete_buchung, color=DANGER).pack(side="left", padx=(0,6))
        make_btn(btn_b, "📎 Beleg öffnen",    self._beleg_oeffnen, color=BG_INPUT, fg=TEXT).pack(side="left")

        self._load_buchungen()

    # ── Buchungen ──────────────────────────────────────────────────────────────

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
                "INSERT INTO zahlungen (datum,betrag,typ,kategorie,beschreibung,belegnr,status,abrechnungsrelevant,abrechnungsjahr,rechnung_id) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                (v["datum"], betrag, v["typ"], v["kategorie"], v["beschreibung"], v["belegnr"],
                 v.get("status", "Geprüft"),
                 v.get("abrechnungsrelevant", 1),
                 v.get("abrechnungsjahr") or None,
                 v.get("rechnung_id") or None))  # #65 | #77 beleg_dateipfad entfernt
            zahlung_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            _sync_kategorie_von_rechnung(conn, zahlung_id, v.get("rechnung_id"))  # #78
            _auto_update_rechnung_status(conn, v.get("rechnung_id"))  # #67
            conn.commit(); conn.close()
            self._load_buchungen()

    def _edit_buchung(self, event=None):
        if not hat_recht("Buchhaltung", "schreiben"):
            messagebox.showwarning("Berechtigung", "Keine Schreibberechtigung.", parent=self); return
        sel = self.tree_b.selection()
        if not sel: return
        conn = get_db()
        row = conn.execute("SELECT * FROM zahlungen WHERE id=?", (int(sel[0]),)).fetchone()
        conn.close()
        _alte_rechnung_id = row["rechnung_id"] if row else None  # #67 – alte Zuordnung merken
        d = ZahlungDialog(self, row)
        self.wait_window(d)
        if d.result:
            v = d.result
            betrag = float(v["betrag"] or 0)
            if v["typ"] == "Ausgabe": betrag = -abs(betrag)
            conn = get_db()
            conn.execute(
                "UPDATE zahlungen SET datum=?,betrag=?,typ=?,kategorie=?,beschreibung=?,belegnr=?,status=?,abrechnungsrelevant=?,abrechnungsjahr=?,rechnung_id=? "
                "WHERE id=?",
                (v["datum"], betrag, v["typ"], v["kategorie"],
                 v["beschreibung"], v["belegnr"], v.get("status", "Geprüft"),
                 v.get("abrechnungsrelevant", 1), v.get("abrechnungsjahr") or None,
                 v.get("rechnung_id") or None,  # #65 | #77 beleg_dateipfad entfernt
                 int(sel[0])))
            # #67 – Status beider Rechnungen aktualisieren (alt + neu)
            _neue_rechnung_id = v.get("rechnung_id") or None
            _sync_kategorie_von_rechnung(conn, int(sel[0]), _neue_rechnung_id)  # #78
            _auto_update_rechnung_status(conn, _neue_rechnung_id)
            if _alte_rechnung_id and _alte_rechnung_id != _neue_rechnung_id:
                _auto_update_rechnung_status(conn, _alte_rechnung_id)
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

    def _jahresabschluss_html(self):
        """#87 Jahresabschluss-HTML: Vollständige Einnahmen/Ausgaben-Übersicht, öffnet im Browser."""
        import webbrowser

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
        ein_rows = conn.execute(
            "SELECT kategorie, SUM(betrag) as s FROM zahlungen "
            "WHERE typ='Einnahme' AND strftime('%Y',datum)=? GROUP BY kategorie ORDER BY s DESC",
            (str(jahr),)).fetchall()
        aus_rows = conn.execute(
            "SELECT kategorie, SUM(betrag) as s FROM zahlungen "
            "WHERE typ='Ausgabe' AND strftime('%Y',datum)=? GROUP BY kategorie ORDER BY s DESC",
            (str(jahr),)).fetchall()
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
        cfg = load_config()
        weg_name = cfg.get("weg_name") or "WEG Hausverwaltung"
        erstellt_am = date.today().strftime("%d.%m.%Y")

        def td(text, align="left", bold=False, color=""):
            style = f"text-align:{align};"
            if bold:  style += "font-weight:bold;"
            if color: style += f"color:{color};"
            return f'<td style="{style}">{text}</td>'

        # Einnahmen-Tabelle
        ein_html = ""
        for r in ein_rows:
            ein_html += f"<tr>{td(r['kategorie'] or '–')}{td(fmt_euro(r['s'] or 0), 'right')}</tr>\n"
        ein_html += (f"<tr style='background:#D4EDDA;font-weight:bold'>"
                     f"{td('Gesamt Einnahmen', bold=True)}"
                     f"{td(fmt_euro(total_ein), 'right', bold=True, color='#3A7D44')}</tr>")

        # Ausgaben-Tabelle
        aus_html = ""
        for r in aus_rows:
            aus_html += f"<tr>{td(r['kategorie'] or '–')}{td(fmt_euro(r['s'] or 0), 'right')}</tr>\n"
        aus_html += (f"<tr style='background:#FADADD;font-weight:bold'>"
                     f"{td('Gesamt Ausgaben', bold=True)}"
                     f"{td(fmt_euro(total_aus), 'right', bold=True, color='#C0392B')}</tr>")

        # Monatsübersicht
        monate = ["Jan","Feb","Mär","Apr","Mai","Jun","Jul","Aug","Sep","Okt","Nov","Dez"]
        mon_html = ""
        for r in monat_rows:
            mi = int(r["m"]) - 1
            mon = monate[mi] if 0 <= mi < 12 else r["m"]
            ein_m = r["ein"] or 0
            aus_m = r["aus"] or 0
            saldo_m = ein_m - aus_m
            farbe = "#3A7D44" if saldo_m >= 0 else "#C0392B"
            mon_html += (f"<tr>{td(f'{mon} {jahr}')}{td(fmt_euro(ein_m),'right')}"
                         f"{td(fmt_euro(aus_m),'right')}"
                         f"{td(fmt_euro(saldo_m),'right',color=farbe)}</tr>\n")

        saldo_farbe = "#3A7D44" if jahres_saldo >= 0 else "#C0392B"
        saldo_bg    = "#D4EDDA" if jahres_saldo >= 0 else "#FADADD"
        saldo_label = "Jahresüberschuss" if jahres_saldo >= 0 else "Jahresfehlbetrag"

        html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<title>{weg_name} – Jahresabschluss {jahr}</title>
<style>
  @page {{ size: A4; margin: 2cm; }}
  body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 11pt;
          color: #2C2C2C; background: #fff; max-width: 900px; margin: 0 auto; padding: 20px; }}
  h1 {{ font-size: 18pt; color: #1C2B3A; margin-bottom: 4px; }}
  h2 {{ font-size: 13pt; color: #1C2B3A; margin-top: 24px; margin-bottom: 6px; }}
  .meta {{ color: #888; font-size: 9pt; margin-bottom: 16px; }}
  table {{ border-collapse: collapse; width: 100%; margin-bottom: 16px; }}
  th {{ background: #1C2B3A; color: #fff; padding: 6px 10px; text-align: left; font-size: 10pt; }}
  td {{ padding: 5px 10px; border-bottom: 1px solid #E0E0E0; font-size: 10pt; }}
  tr:nth-child(even) {{ background: #F7F5F0; }}
  .kpi-row {{ display: flex; gap: 16px; margin-bottom: 20px; }}
  .kpi {{ background: #F7F5F0; border-radius: 6px; padding: 12px 20px; flex: 1; }}
  .kpi-label {{ color: #666; font-size: 9pt; }}
  .kpi-val {{ font-size: 14pt; font-weight: bold; margin-top: 2px; }}
  .ein-head {{ background: #3A7D44 !important; }}
  .aus-head {{ background: #C0392B !important; }}
  .mon-head {{ background: #1C2B3A !important; }}
  @media print {{ body {{ padding: 0; }} }}
</style>
</head>
<body>
<h1>{weg_name}</h1>
<div class="meta">Jahresabschluss {jahr} – Einnahmen &amp; Ausgaben | Erstellt am {erstellt_am}</div>

<div class="kpi-row">
  <div class="kpi">
    <div class="kpi-label">Gesamteinnahmen</div>
    <div class="kpi-val" style="color:#3A7D44">{fmt_euro(total_ein)}</div>
  </div>
  <div class="kpi">
    <div class="kpi-label">Gesamtausgaben</div>
    <div class="kpi-val" style="color:#C0392B">{fmt_euro(total_aus)}</div>
  </div>
  <div class="kpi" style="background:{saldo_bg}">
    <div class="kpi-label">{saldo_label}</div>
    <div class="kpi-val" style="color:{saldo_farbe}">{fmt_euro(jahres_saldo)}</div>
  </div>
</div>

<h2>Einnahmen nach Kategorie</h2>
<table>
  <tr><th class="ein-head">Kategorie</th><th class="ein-head" style="text-align:right">Betrag</th></tr>
  {ein_html}
</table>

<h2>Ausgaben nach Kategorie</h2>
<table>
  <tr><th class="aus-head">Kategorie</th><th class="aus-head" style="text-align:right">Betrag</th></tr>
  {aus_html}
</table>
""" + (f"""
<h2>Monatliche Übersicht</h2>
<table>
  <tr>
    <th class="mon-head">Monat</th>
    <th class="mon-head" style="text-align:right">Einnahmen</th>
    <th class="mon-head" style="text-align:right">Ausgaben</th>
    <th class="mon-head" style="text-align:right">Monatssaldo</th>
  </tr>
  {mon_html}
</table>
""" if monat_rows else "") + """
</body>
</html>"""

        # Speichern
        ziel_dir = Path(get_pfad("pfad_dokumente", "Dokumente")) / "Abrechnungen"
        try:
            ziel_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        pfad = ziel_dir / f"WEG_Jahresabschluss_{jahr}.html"
        try:
            pfad.write_text(html, encoding="utf-8")
            webbrowser.open(pfad.as_uri())
            messagebox.showinfo("Jahresabschluss",
                f"Jahresabschluss {jahr} geöffnet:\n{pfad}\n\nIm Browser: Strg+P → Als PDF speichern",
                parent=self)
        except Exception as exc:
            messagebox.showerror("Fehler", f"Konnte HTML nicht speichern:\n{exc}", parent=self)

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

    # ── Kategorien-Verwaltung (Klassenvariablen bleiben hier — genutzt von ZahlungDialog etc.) ──

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

    # Compat: alter Name → neuer Name
    def _load(self):
        self._load_buchungen()


class ZahlungDialog(BaseDialog):
    def __init__(self, parent, row=None):
        super().__init__(parent, "Buchung", 560, 520)
        r = dict(row) if row else {}

        # ── Buchungsdaten (#56: Buchungsdatum klar als solches kennzeichnen) ──
        self._add_field("Buchungsdatum (JJJJ-MM-TT) *", "datum",
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
        self._add_field("Abrechnungsjahr", "abrechnungsjahr",
                        r.get("abrechnungsjahr", "") or "")

        # #65 – Rechnung zuordnen
        tk.Frame(self._body, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(10, 4))
        rechnung_lbl = tk.Label(self._body, text="Rechnung zuordnen (optional)",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=("Segoe UI Semibold", 9))
        rechnung_lbl.pack(padx=20, anchor="w")
        rechnung_row = tk.Frame(self._body, bg=BG_CARD)
        rechnung_row.pack(fill="x", padx=20, pady=(2, 4))
        # Lade Rechnungen für Dropdown
        _cur_rid = r.get("rechnung_id")
        try:
            _conn_r = get_db()
            _rech_rows = _conn_r.execute(
                "SELECT id, rechnungsnummer, rechnungssteller, betrag_brutto "
                "FROM rechnungen WHERE status IN ('Offen','Teilbezahlt') "
                "ORDER BY rechnungsdatum DESC LIMIT 50"
            ).fetchall()
            # #65 Fix: Falls aktuelle Rechnung nicht in der Liste (z.B. Bezahlt), nachladen
            if _cur_rid and not any(_rr["id"] == _cur_rid for _rr in _rech_rows):
                _cur_row = _conn_r.execute(
                    "SELECT id, rechnungsnummer, rechnungssteller, betrag_brutto FROM rechnungen WHERE id=?",
                    (_cur_rid,)).fetchone()
                if _cur_row:
                    _rech_rows = list(_rech_rows) + [_cur_row]
            _conn_r.close()
        except Exception:
            _rech_rows = []
        self._rechnung_map = {0: "– keine –"}
        rech_options = ["– keine –"]
        for _rr in _rech_rows:
            label = f"{_rr['rechnungsnummer'] or _rr['id']} – {_rr['rechnungssteller']} ({fmt_euro(_rr['betrag_brutto'])})"
            self._rechnung_map[_rr["id"]] = label
            rech_options.append(label)
        # Aktuell zugeordnet?
        _cur_label = self._rechnung_map.get(_cur_rid, "– keine –") if _cur_rid else "– keine –"
        self._rechnung_var = tk.StringVar(value=_cur_label)
        self._rechnung_id_val = _cur_rid
        rech_combo = ttk.Combobox(rechnung_row, textvariable=self._rechnung_var,
                                  values=rech_options, state="readonly", width=40, font=FONT_BODY)
        rech_combo.pack(side="left", fill="x", expand=True)
        def _on_rech_selected(e=None):
            sel_lbl = self._rechnung_var.get()
            for rid, lbl in self._rechnung_map.items():
                if lbl == sel_lbl:
                    self._rechnung_id_val = rid if rid != 0 else None
                    break
        rech_combo.bind("<<ComboboxSelected>>", _on_rech_selected)

        # Abrechnungsrelevanz-Checkbox
        abr_frame = tk.Frame(self._body, bg=BG_CARD)
        abr_frame.pack(fill="x", padx=20, pady=(2, 4))
        self._abr_var = tk.BooleanVar(value=bool(r.get("abrechnungsrelevant", 1)))
        tk.Checkbutton(abr_frame, text="✅ Abrechnungsrelevant (in Nebenkostenabrechnung einbeziehen)",
                       variable=self._abr_var, bg=BG_CARD, fg=TEXT, font=FONT_BODY,
                       activebackground=BG_CARD, selectcolor=BG_CARD).pack(anchor="w")

        # #77 – Beleg-Feld + KI-Analyse entfernt: Beleg lebt jetzt ausschließlich in
        # RechnungDialog (rechnungen.beleg_dateipfad). Zahlung hat keinen eigenen Beleg mehr.

    def _on_save(self):
        v = self._get_values()
        if not v.get("datum") or not v.get("betrag"):
            messagebox.showwarning("Pflichtfelder", "Datum und Betrag sind erforderlich.", parent=self); return
        # Normalisiere Datum
        if v.get("datum"):
            v["datum"] = parse_datum(v["datum"])
        # Abrechnungsrelevanz speichern
        v["abrechnungsrelevant"] = 1 if self._abr_var.get() else 0
        # #65 – Rechnung-Zuordnung
        v["rechnung_id"] = self._rechnung_id_val if hasattr(self, "_rechnung_id_val") else None
        self.result = v; self.destroy()

# ── Rechnungen-Hilfsfunktionen ───────────────────────────────────────────────

def _beleg_archivieren(parent_win, beleg_pfad: str, rechnungsdatum: str) -> str | None:
    """#73/#75 – Archiviert Beleg-Datei unter <app-dir>/Belege/<Jahr>/.

    Bei Duplikat (#75): Hinweisfenster mit Entscheidung Speichern/Abbrechen.
    Bei Speichern-Entscheid: Versionierung als <basis>_duplikat_v<n><ext>.
    Vorhandene Datei wird niemals überschrieben.
    Gibt den Zielpfad zurück, oder None bei Abbruch / Fehler.
    """
    if not beleg_pfad or not os.path.isfile(beleg_pfad):
        return None
    try:
        import shutil as _shutil
        # Jahr aus Rechnungsdatum ableiten
        jahr = str((rechnungsdatum or "")[:4]).strip() or str(date.today().year)
        if not jahr.isdigit() or not (2000 <= int(jahr) <= 2100):
            jahr = str(date.today().year)
        # Zielordner: <app-dir>/Belege/<Jahr>/
        app_dir = os.path.dirname(os.path.abspath(__file__))
        ziel_dir = os.path.join(app_dir, "Belege", jahr)
        os.makedirs(ziel_dir, exist_ok=True)
        dateiname = os.path.basename(beleg_pfad)
        basis, ext = os.path.splitext(dateiname)
        ziel_pfad = os.path.join(ziel_dir, dateiname)

        if os.path.exists(ziel_pfad):
            # #75 – Duplikat: Benutzer fragen
            antwort = messagebox.askyesno(
                "Duplikat erkannt",
                f"Ein Beleg '{dateiname}' ist bereits in der Jahresablage {jahr} vorhanden.\n\n"
                f"Soll der Beleg trotzdem gespeichert werden?\n"
                f"(Vorhandene Datei bleibt unverändert; der neue Beleg wird\n"
                f"als Duplikat mit Versionsnummer abgelegt.)",
                parent=parent_win
            )
            if not antwort:
                return None  # Abbrechen
            # Nächste freie Versionsnummer finden
            version = 2
            while True:
                versionierter_name = f"{basis}_duplikat_v{version}{ext}"
                ziel_pfad = os.path.join(ziel_dir, versionierter_name)
                if not os.path.exists(ziel_pfad):
                    break
                version += 1

        _shutil.copy2(beleg_pfad, ziel_pfad)
        return ziel_pfad
    except Exception:
        return None


# ── Rechnungen-Hilfsfunktion (#67 – Auto-Status) ─────────────────────────────

def _auto_update_rechnung_status(conn, rechnung_id):
    """#67 – Aktualisiert den Status einer Rechnung nach GoB-Differenzprinzip.

    Soll = betrag_brutto, Haben = SUM(ABS(zahlungen.betrag) WHERE rechnung_id=?)
    Status: Bezahlt | Teilbezahlt | Offen  (Storniert wird NICHT überschrieben)
    """
    if not rechnung_id:
        return
    try:
        row = conn.execute(
            "SELECT betrag_brutto, status FROM rechnungen WHERE id=?",
            (rechnung_id,)).fetchone()
        if not row or row["status"] == "Storniert":
            return
        brutto = row["betrag_brutto"] or 0
        gebucht = conn.execute(
            "SELECT COALESCE(SUM(ABS(betrag)), 0) FROM zahlungen WHERE rechnung_id=?",
            (rechnung_id,)).fetchone()[0] or 0
        differenz = brutto - gebucht
        if abs(differenz) < 0.01:
            neuer_status = "Bezahlt"
        elif gebucht > 0.009:
            neuer_status = "Teilbezahlt"
        else:
            neuer_status = "Offen"
        conn.execute("UPDATE rechnungen SET status=? WHERE id=?",
                     (neuer_status, rechnung_id))
    except Exception:
        pass  # Fehler beim Status-Update sollen die Hauptoperation nicht blockieren


def _sync_kategorie_von_rechnung(conn, zahlung_id, rechnung_id):
    """#78 – Übernimmt die Kategorie der Rechnung in die Zahlung, falls die Zahlung
    noch keine eigene Kategorie hat.

    Wird aufgerufen nach INSERT/UPDATE von zahlungen.rechnung_id, damit Buchungen
    die Kostenart der verknüpften Rechnung erben (GoB-Konformität: gleiche Konten).
    """
    if not zahlung_id or not rechnung_id:
        return
    try:
        z_row = conn.execute(
            "SELECT kategorie FROM zahlungen WHERE id=?", (zahlung_id,)).fetchone()
        r_row = conn.execute(
            "SELECT kategorie FROM rechnungen WHERE id=?", (rechnung_id,)).fetchone()
        if not z_row or not r_row:
            return
        if not (z_row["kategorie"] or "").strip() and (r_row["kategorie"] or "").strip():
            conn.execute("UPDATE zahlungen SET kategorie=? WHERE id=?",
                         (r_row["kategorie"], zahlung_id))
    except Exception:
        pass  # Kategorie-Sync soll die Hauptoperation nie blockieren


# ── Auto-Matching (#69/#70/#71) ───────────────────────────────────────────────

def _score_kontoauszug_gegen_rechnung(kb: dict, rechnung: dict) -> float:
    """Gewichteter Fuzzy-Score (0–100): Kontoauszugsbuchung vs. Rechnung.

    Gewichte:  Betrag 40 pt | Datum 30 pt | Text/Rechnungsnummer 30 pt
    Quellen:   SWIFT CGI-MP Best Practices v1.1; Rillion 3-Way-Matching Guide
    """
    from difflib import SequenceMatcher
    score = 0.0

    # ── 1. Betrag-Match (max. 40 Punkte) ─────────────────────────────────────
    kb_betrag = abs(kb["betrag"] or 0)
    rg_betrag = abs(rechnung["betrag_brutto"] or 0)
    if rg_betrag > 0:
        differenz = abs(kb_betrag - rg_betrag)
        toleranz_1pct = rg_betrag * 0.01
        toleranz_5pct = rg_betrag * 0.05
        if differenz < 0.005:          # exakter Treffer (Cent-genau)
            score += 40
        elif differenz <= toleranz_1pct:  # ±1 % (Skonto, Bankgebühren)
            score += 35
        elif differenz <= toleranz_5pct:  # ±5 % (Teilzahlung?)
            score += 20
        # > 5 % → kein Betrag-Score

    # ── 2. Datum-Match (max. 30 Punkte) ──────────────────────────────────────
    # Vergleich: Buchungsdatum des Kontoauszugs vs. Fälligkeitsdatum der Rechnung
    try:
        from datetime import date as _date
        def _to_date(s):
            if not s:
                return None
            if isinstance(s, _date):
                return s
            for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d.%m.%y"):
                try:
                    return _date.fromisoformat(str(s)) if fmt == "%Y-%m-%d" else \
                           __import__('datetime').datetime.strptime(str(s), fmt).date()
                except ValueError:
                    continue
            return None
        kb_dat = _to_date(kb.get("datum"))
        rg_dat = _to_date(rechnung.get("faelligkeitsdatum")) or _to_date(rechnung.get("rechnungsdatum"))
        if kb_dat and rg_dat:
            tage = abs((kb_dat - rg_dat).days)
            if tage == 0:    score += 30
            elif tage <= 3:  score += 25
            elif tage <= 7:  score += 15
            elif tage <= 30: score += 5
    except Exception:
        pass

    # ── 3. Text-Match (max. 30 Punkte) ────────────────────────────────────────
    # Rechnungsnummer oder Rechnungssteller im Verwendungszweck des Kontoauszugs?
    try:
        vzweck = (kb.get("buchungstext") or "").upper()
        rgnr   = (rechnung.get("rechnungsnummer") or "").upper().strip()
        steller = (rechnung.get("rechnungssteller") or "").upper().strip()

        if rgnr and rgnr in vzweck:
            score += 30     # Rechnungsnummer exakt im Verwendungszweck
        elif rgnr and len(rgnr) >= 4:
            ratio = SequenceMatcher(None, rgnr, vzweck).ratio()
            if ratio >= 0.80:
                score += 20
            elif ratio >= 0.60:
                score += 10
        elif steller:
            # Rechnungssteller-Wörter (≥4 Buchstaben) im Verwendungszweck suchen
            woerter = [w for w in steller.split() if len(w) >= 4]
            treffer = sum(1 for w in woerter if w in vzweck)
            if woerter and treffer >= max(1, len(woerter) // 2):
                score += 15
    except Exception:
        pass

    return min(100.0, score)


def _auto_log_match(conn, kontoauszug_id: int, rechnung_id, zahlung_id,
                    score: float, methode: str):
    """GoB-konformer Audit-Trail: jeden Match-Vorgang in kontoauszug_match_log speichern."""
    try:
        conn.execute(
            "INSERT INTO kontoauszug_match_log "
            "(kontoauszug_id, rechnung_id, zahlung_id, score, methode) "
            "VALUES (?,?,?,?,?)",
            (kontoauszug_id, rechnung_id, zahlung_id, score, methode))
    except Exception:
        pass


def _auto_match_alle(conn, schwelle_auto: float = 80.0,
                     schwelle_vorschlag: float = 60.0) -> dict:
    """Führt automatisches Matching für nicht zugeordnete Kontoauszugsbuchungen durch.

    Rückgabe: {"auto": int, "vorschlaege": list[dict], "offen": int}
    Jedes Vorschlag-dict: {kb, kandidaten: [{rechnung, score}]}
    """
    # Alle Ausgaben (betrag < 0) ohne Rechnung-Zuordnung
    ka_rows = conn.execute(
        "SELECT * FROM kontoauszug WHERE betrag < 0 AND zugeordnet=0 "
        "ORDER BY datum DESC"
    ).fetchall()

    # Offene + Teilbezahlte Rechnungen
    rg_rows = conn.execute(
        "SELECT * FROM rechnungen WHERE status IN ('Offen','Teilbezahlt')"
    ).fetchall()

    auto_count = 0
    vorschlaege = []
    offen_count = 0

    for kb in ka_rows:
        kandidaten = []
        for r in rg_rows:
            s = _score_kontoauszug_gegen_rechnung(dict(kb), dict(r))
            if s >= schwelle_vorschlag:
                kandidaten.append({"rechnung": dict(r), "score": s})
        kandidaten.sort(key=lambda x: x["score"], reverse=True)

        if not kandidaten:
            offen_count += 1
            continue

        bester = kandidaten[0]
        if bester["score"] >= schwelle_auto:
            # Auto-Buchung: Zahlung anlegen + Rechnung verknüpfen
            try:
                kb_dict = dict(kb)
                buchungstext = kb_dict.get("buchungstext", "")
                # Verwendungszweck aufbereiten
                if "||" in buchungstext:
                    gegenkonto, vzweck = buchungstext.split("||", 1)
                    beschr = f"{gegenkonto.strip()} – {vzweck.strip()}"[:200]
                else:
                    beschr = buchungstext[:200]

                rechnung = bester["rechnung"]
                # Prüfen ob für diesen Kontoauszugseintrag schon eine Zahlung existiert
                existing_z = conn.execute(
                    "SELECT id FROM zahlungen WHERE datum=? AND betrag=? AND konto_typ=?",
                    (kb_dict.get("datum"), kb_dict.get("betrag"),
                     kb_dict.get("konto_typ", ""))).fetchone()

                if existing_z:
                    zahlung_id = existing_z["id"]
                    # Rechnung-Verknüpfung setzen falls noch nicht gesetzt
                    conn.execute("UPDATE zahlungen SET rechnung_id=? WHERE id=? AND rechnung_id IS NULL",
                                 (rechnung["id"], zahlung_id))
                else:
                    kat = kb_dict.get("kategorie_vorschlag") or rechnung.get("kategorie") or "Sonstiges"
                    conn.execute(
                        "INSERT INTO zahlungen "
                        "(datum,betrag,typ,kategorie,beschreibung,konto_typ,status,rechnung_id) "
                        "VALUES (?,?,?,?,?,?,?,?)",
                        (kb_dict.get("datum"), kb_dict.get("betrag"), "Ausgabe",
                         kat, beschr,
                         kb_dict.get("konto_typ", ""),
                         "Neu", rechnung["id"]))
                    zahlung_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

                conn.execute(
                    "UPDATE kontoauszug SET zugeordnet=1, als_buchung_uebernommen=1, "
                    "zahlung_id=? WHERE id=?",
                    (zahlung_id, kb_dict["id"]))
                _auto_update_rechnung_status(conn, rechnung["id"])
                _auto_log_match(conn, kb_dict["id"], rechnung["id"], zahlung_id,
                                bester["score"], "auto")
                auto_count += 1
            except Exception:
                offen_count += 1
        else:
            vorschlaege.append({"kb": dict(kb), "kandidaten": kandidaten[:3]})

    conn.commit()
    return {"auto": auto_count, "vorschlaege": vorschlaege, "offen": offen_count}


# ── Rechnungen-Seite (#65 / #66 – Doppelte Buchführung) ──────────────────────

class RechnungenPage(tk.Frame):
    """#65/#66 – Rechnungsverwaltung mit Doppelter-Buchführungs-Prinzip.

    Jede Rechnung ist eine Verbindlichkeit. Buchungen (zahlungen) werden
    per rechnung_id zugeordnet. Anzeige: Rechnungsbetrag, gebucht, Differenz.
    ZUGFeRD/xRechnung XML-Import, KI-OCR Fallback, manuelle Eingabe.
    """

    STATI = ["Offen", "Teilbezahlt", "Bezahlt", "Storniert"]

    def __init__(self, parent):
        super().__init__(parent, bg=BG_CARD)
        self._build()

    # ── Aufbau ────────────────────────────────────────────────────────────────

    def _build(self):
        section_header(self, "Rechnungen", "＋ Rechnung", self._new_rechnung)

        # Filter-Leiste
        fr = tk.Frame(self, bg=BG_CARD)
        fr.pack(fill="x", padx=20, pady=4)
        tk.Label(fr, text="Status:", bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(side="left")
        self._status_var = tk.StringVar(value="Alle")
        for s in ("Alle", "Offen", "Teilbezahlt", "Bezahlt", "Storniert"):
            tk.Radiobutton(fr, text=s, variable=self._status_var, value=s,
                           bg=BG_CARD, fg=TEXT, font=FONT_SMALL,
                           activebackground=BG_CARD, selectcolor=BG_CARD,
                           command=self._load).pack(side="left", padx=6)

        # Rechnungstabelle
        cols = ("Nr.", "Steller", "Datum", "Brutto €", "Gebucht €", "Differenz €", "Status", "Kategorie")
        f, self.tree = make_table(self, cols, height=14)
        f.pack(fill="both", expand=True, padx=20, pady=4)
        for c, w in zip(cols, [90, 160, 90, 90, 90, 100, 90, 120]):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="w")
        self.tree.column("Brutto €",    anchor="e")
        self.tree.column("Gebucht €",   anchor="e")
        self.tree.column("Differenz €", anchor="e")
        self.tree.bind("<Double-1>", self._edit_rechnung)
        self.tree.tag_configure("bezahlt",     foreground=SUCCESS)
        self.tree.tag_configure("offen",       foreground=TEXT)
        self.tree.tag_configure("ueberzahlt",  foreground=DANGER)
        self.tree.tag_configure("teilbezahlt", foreground=ACCENT2)

        # Button-Leiste
        btn_row = tk.Frame(self, bg=BG_CARD)
        btn_row.pack(fill="x", padx=20, pady=(0, 8))
        if hat_recht("Buchhaltung", "schreiben"):
            make_btn(btn_row, "✏ Bearbeiten",    self._edit_rechnung,  color=BG_INPUT, fg=TEXT).pack(side="left", padx=(0, 6))
            make_btn(btn_row, "📎 Buchung zuordnen", self._buchung_zuordnen, color=BG_INPUT, fg=TEXT).pack(side="left", padx=(0, 6))
            make_btn(btn_row, "📄 Buchungen anzeigen", self._show_buchungen, color=BG_INPUT, fg=TEXT).pack(side="left", padx=(0, 6))
        if hat_recht("Buchhaltung", "loeschen"):
            make_btn(btn_row, "🗑 Löschen", self._delete_rechnung, color=DANGER).pack(side="left")

        # KPI-Leiste
        self._kpi_frame = tk.Frame(self, bg=BG_CARD)
        self._kpi_frame.pack(fill="x", padx=20, pady=(0, 8))

        self._load()

    # ── Daten laden ───────────────────────────────────────────────────────────

    def _load(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        conn = get_db()
        try:
            s = self._status_var.get()
            where = "WHERE r.status=?" if s != "Alle" else ""
            params = (s,) if s != "Alle" else ()
            rechnungen = conn.execute(
                f"SELECT r.*, "
                f"  COALESCE((SELECT SUM(ABS(z.betrag)) FROM zahlungen z "
                f"            WHERE z.rechnung_id=r.id), 0) AS gebucht "
                f"FROM rechnungen r {where} ORDER BY r.rechnungsdatum DESC, r.id DESC",
                params
            ).fetchall()
        finally:
            conn.close()

        total_brutto = total_gebucht = 0.0
        offen_count = 0
        for r in rechnungen:
            rd = dict(r)
            brutto   = rd["betrag_brutto"] or 0
            gebucht  = rd["gebucht"] or 0
            differenz = brutto - gebucht
            total_brutto  += brutto
            total_gebucht += gebucht
            if rd["status"] in ("Offen", "Teilbezahlt"):
                offen_count += 1
            # Farbtag
            if abs(differenz) < 0.01:
                tag = "bezahlt"
            elif differenz < -0.01:
                tag = "ueberzahlt"
            elif gebucht > 0:
                tag = "teilbezahlt"
            else:
                tag = "offen"
            # Differenz-Farbe: zu wenig = grün (noch offen), zu viel = rot, genau = schwarz
            diff_str = fmt_euro(differenz)
            self.tree.insert("", "end", iid=rd["id"], values=(
                rd["rechnungsnummer"] or "–",
                rd["rechnungssteller"] or "–",
                fmt_date(rd["rechnungsdatum"]) if rd["rechnungsdatum"] else "–",
                fmt_euro(brutto),
                fmt_euro(gebucht),
                diff_str,
                rd["status"] or "–",
                rd["kategorie"] or "–"
            ), tags=(tag,))
        tree_empty_hint(self.tree)
        self._update_kpi(total_brutto, total_gebucht, offen_count)

    def _update_kpi(self, total_brutto, total_gebucht, offen_count):
        for w in self._kpi_frame.winfo_children():
            w.destroy()
        differenz = total_brutto - total_gebucht
        items = [
            ("Rechnungen gesamt", fmt_euro(total_brutto), DANGER),
            ("Bezahlt", fmt_euro(total_gebucht), SUCCESS),
            ("Noch offen", fmt_euro(differenz), WARNING if differenz > 0.01 else TEXT),
            ("Offene Rechnungen", str(offen_count), ACCENT2),
        ]
        for lbl, wert, color in items:
            karte = tk.Frame(self._kpi_frame, bg=BG_INPUT, padx=12, pady=6)
            karte.pack(side="left", padx=(0, 10))
            tk.Label(karte, text=lbl, bg=BG_INPUT, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w")
            tk.Label(karte, text=wert, bg=BG_INPUT, fg=color, font=FONT_H3).pack(anchor="w")

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def _new_rechnung(self):
        if not hat_recht("Buchhaltung", "schreiben"):
            messagebox.showwarning("Berechtigung", "Keine Schreibberechtigung.", parent=self); return
        d = RechnungDialog(self)
        self.wait_window(d)
        if d.result:
            v = d.result
            conn = get_db()
            try:
                conn.execute(
                    "INSERT INTO rechnungen (rechnungsnummer, rechnungssteller, rechnungsdatum, "
                    "faelligkeitsdatum, betrag_brutto, betrag_netto, mwst_satz, mwst_betrag, "
                    "lohnanteil, handwerker_steuerlich, kategorie, beschreibung, beleg_dateipfad, status, zugferd_format) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (v.get("rechnungsnummer"), v.get("rechnungssteller"),
                     v.get("rechnungsdatum"), v.get("faelligkeitsdatum"),
                     float(v.get("betrag_brutto") or 0),
                     float(v.get("betrag_netto") or 0) or None,
                     float(v.get("mwst_satz") or 19),
                     float(v.get("mwst_betrag") or 0) or None,
                     float(v.get("lohnanteil") or 0) or None,
                     v.get("handwerker_steuerlich", 0),  # #68 §35a EStG
                     v.get("kategorie"), v.get("beschreibung"),
                     v.get("beleg_dateipfad"), v.get("status", "Offen"),
                     v.get("zugferd_format")))
                conn.commit()
            finally:
                conn.close()
            # #73/#75 – Beleg automatisch in Jahresablage archivieren
            if v.get("beleg_dateipfad"):
                _beleg_archivieren(self, v.get("beleg_dateipfad"), v.get("rechnungsdatum", ""))
            self._load()

    def _edit_rechnung(self, event=None):
        if not hat_recht("Buchhaltung", "schreiben"):
            messagebox.showwarning("Berechtigung", "Keine Schreibberechtigung.", parent=self); return
        sel = self.tree.selection()
        if not sel: return
        conn = get_db()
        try:
            row = conn.execute("SELECT * FROM rechnungen WHERE id=?", (int(sel[0]),)).fetchone()
        finally:
            conn.close()
        if not row: return
        d = RechnungDialog(self, dict(row))
        self.wait_window(d)
        if d.result:
            v = d.result
            conn = get_db()
            try:
                conn.execute(
                    "UPDATE rechnungen SET rechnungsnummer=?, rechnungssteller=?, "
                    "rechnungsdatum=?, faelligkeitsdatum=?, betrag_brutto=?, betrag_netto=?, "
                    "mwst_satz=?, mwst_betrag=?, lohnanteil=?, handwerker_steuerlich=?, "
                    "kategorie=?, beschreibung=?, beleg_dateipfad=?, status=?, zugferd_format=? "
                    "WHERE id=?",
                    (v.get("rechnungsnummer"), v.get("rechnungssteller"),
                     v.get("rechnungsdatum"), v.get("faelligkeitsdatum"),
                     float(v.get("betrag_brutto") or 0),
                     float(v.get("betrag_netto") or 0) or None,
                     float(v.get("mwst_satz") or 19),
                     float(v.get("mwst_betrag") or 0) or None,
                     float(v.get("lohnanteil") or 0) or None,
                     v.get("handwerker_steuerlich", 0),  # #68 §35a EStG
                     v.get("kategorie"), v.get("beschreibung"),
                     v.get("beleg_dateipfad"), v.get("status", "Offen"),
                     v.get("zugferd_format"),  # #66 – bewahrt das Import-Format
                     int(sel[0])))
                conn.commit()
            finally:
                conn.close()
            # #73/#75 – Beleg automatisch in Jahresablage archivieren
            if v.get("beleg_dateipfad"):
                _beleg_archivieren(self, v.get("beleg_dateipfad"), v.get("rechnungsdatum", ""))
            self._load()

    def _delete_rechnung(self):
        if not hat_recht("Buchhaltung", "loeschen"):
            messagebox.showwarning("Berechtigung", "Keine Löschberechtigung.", parent=self); return
        sel = self.tree.selection()
        if not sel: return
        conn = get_db()
        try:
            cnt = conn.execute(
                "SELECT COUNT(*) FROM zahlungen WHERE rechnung_id=?", (int(sel[0]),)
            ).fetchone()[0]
        finally:
            conn.close()
        hinweis = f"\n\n⚠ {cnt} Buchung(en) sind dieser Rechnung zugeordnet." if cnt else ""
        if not messagebox.askyesno("Löschen",
            f"Rechnung wirklich löschen?{hinweis}", parent=self):
            return
        conn = get_db()
        try:
            # Zuordnungen aufheben
            conn.execute("UPDATE zahlungen SET rechnung_id=NULL WHERE rechnung_id=?", (int(sel[0]),))
            conn.execute("DELETE FROM rechnungen WHERE id=?", (int(sel[0]),))
            conn.commit()
        finally:
            conn.close()
        self._load()

    def _buchung_zuordnen(self):
        """Öffnet Dialog um bestehende Buchung einer Rechnung zuzuordnen."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Auswahl", "Bitte eine Rechnung auswählen.", parent=self); return
        rechnung_id = int(sel[0])
        conn = get_db()
        try:
            r = conn.execute("SELECT * FROM rechnungen WHERE id=?", (rechnung_id,)).fetchone()
        finally:
            conn.close()
        if not r: return
        BuchungZuordnenDialog(self, rechnung_id, r["rechnungssteller"],
                              r["betrag_brutto"] or 0, self._load)

    def _show_buchungen(self):
        """Zeigt alle Buchungen zu einer Rechnung."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Auswahl", "Bitte eine Rechnung auswählen.", parent=self); return
        rechnung_id = int(sel[0])
        conn = get_db()
        try:
            r = conn.execute("SELECT * FROM rechnungen WHERE id=?", (rechnung_id,)).fetchone()
            buchungen = conn.execute(
                "SELECT datum, beschreibung, betrag, belegnr, status "
                "FROM zahlungen WHERE rechnung_id=? ORDER BY datum",
                (rechnung_id,)).fetchall()
        finally:
            conn.close()
        if not r: return
        win = tk.Toplevel(self)
        win.title(f"Buchungen zu Rechnung {r['rechnungsnummer'] or r['id']}")
        win.geometry("700x400")
        win.configure(bg=BG_CARD)
        win.grab_set()
        tk.Label(win, text=f"Rechnung: {r['rechnungssteller']} – {fmt_euro(r['betrag_brutto'])}",
                 bg=BG_CARD, fg=TEXT, font=FONT_H2).pack(padx=20, pady=(14, 4), anchor="w")
        cols = ("Datum", "Beschreibung", "Betrag €", "Beleg", "Status")
        f, tree = make_table(win, cols, height=10)
        f.pack(fill="both", expand=True, padx=20, pady=8)
        for c, w in zip(cols, [90, 220, 100, 90, 90]):
            tree.heading(c, text=c); tree.column(c, width=w, anchor="w")
        tree.column("Betrag €", anchor="e")
        total = 0.0
        for b in buchungen:
            betrag = b["betrag"] or 0
            total += abs(betrag)
            tree.insert("", "end", values=(
                fmt_date(b["datum"]) if b["datum"] else "–",
                b["beschreibung"] or "–",
                fmt_euro(abs(betrag)),
                b["belegnr"] or "–",
                b["status"] or "–"
            ))
        tree_empty_hint(tree)
        differenz = (r["betrag_brutto"] or 0) - total
        diff_color = SUCCESS if abs(differenz) < 0.01 else (DANGER if differenz < -0.01 else ACCENT2)
        sum_fr = tk.Frame(win, bg=BG_CARD)
        sum_fr.pack(fill="x", padx=20, pady=(0, 12))
        tk.Label(sum_fr, text=f"Gebucht: {fmt_euro(total)}   Differenz: {fmt_euro(differenz)}",
                 bg=BG_CARD, fg=diff_color, font=FONT_H3).pack(side="left")
        make_btn(win, "Schließen", win.destroy, color=BG_INPUT, fg=TEXT).pack(
            side="bottom", anchor="e", padx=20, pady=8)

    # ── ZUGFeRD / xRechnung Parser ────────────────────────────────────────────

    @staticmethod
    def _parse_zugferd_cii(xml_bytes: bytes) -> dict:
        """Parst ZUGFeRD / Factur-X / xRechnung CII XML."""
        import xml.etree.ElementTree as ET
        NS = {
            "rsm": "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100",
            "ram": "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100",
            "udt": "urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100",
        }
        try:
            root = ET.fromstring(xml_bytes)
        except ET.ParseError:
            return {}
        def _txt(path, ns=NS):
            el = root.find(path, ns)
            return el.text.strip() if el is not None and el.text else ""
        # Rechnungsnummer
        rnr = _txt(".//rsm:ExchangedDocument/ram:ID")
        # Datum (YYYYMMDD → YYYY-MM-DD)
        datum_raw = _txt(".//rsm:ExchangedDocument/ram:IssueDateTime/udt:DateTimeString")
        rechnungsdatum = f"{datum_raw[:4]}-{datum_raw[4:6]}-{datum_raw[6:8]}" \
            if len(datum_raw) >= 8 else datum_raw
        # Steller
        steller = _txt(".//ram:SellerTradeParty/ram:Name")
        # Beträge
        try:
            brutto = float(_txt(".//ram:GrandTotalAmount") or 0)
        except ValueError:
            brutto = 0.0
        try:
            netto = float(_txt(".//ram:TaxBasisTotalAmount") or 0)
        except ValueError:
            netto = 0.0
        try:
            mwst = float(_txt(".//ram:TaxTotalAmount") or 0)
        except ValueError:
            mwst = 0.0
        # Fälligkeit
        faellig_raw = _txt(".//ram:DueDateDateTime/udt:DateTimeString")
        faelligkeitsdatum = f"{faellig_raw[:4]}-{faellig_raw[4:6]}-{faellig_raw[6:8]}" \
            if len(faellig_raw) >= 8 else ""
        return {
            "rechnungsnummer": rnr,
            "rechnungssteller": steller,
            "rechnungsdatum": rechnungsdatum,
            "faelligkeitsdatum": faelligkeitsdatum,
            "betrag_brutto": brutto,
            "betrag_netto": netto,
            "mwst_betrag": mwst,
            "mwst_satz": round(mwst / netto * 100, 1) if netto else 19.0,
            "zugferd_format": "ZUGFeRD/CII",
        }

    @staticmethod
    def _parse_xrechnung_ubl(xml_bytes: bytes) -> dict:
        """Parst xRechnung UBL 2.1 XML."""
        import xml.etree.ElementTree as ET
        NS = {
            "ubl": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
            "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
            "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
        }
        try:
            root = ET.fromstring(xml_bytes)
        except ET.ParseError:
            return {}
        def _txt(path):
            el = root.find(path, NS)
            return el.text.strip() if el is not None and el.text else ""
        try:
            brutto = float(_txt(".//cac:LegalMonetaryTotal/cbc:PayableAmount") or 0)
        except ValueError:
            brutto = 0.0
        try:
            netto = float(_txt(".//cac:LegalMonetaryTotal/cbc:TaxExclusiveAmount") or 0)
        except ValueError:
            netto = 0.0
        return {
            "rechnungsnummer": _txt("cbc:ID"),
            "rechnungssteller": _txt(".//cac:AccountingSupplierParty/cac:Party/cac:PartyName/cbc:Name"),
            "rechnungsdatum": _txt("cbc:IssueDate"),
            "faelligkeitsdatum": _txt(".//cac:PaymentMeans/cbc:PaymentDueDate"),
            "betrag_brutto": brutto,
            "betrag_netto": netto,
            "zugferd_format": "xRechnung-UBL",
        }

    @staticmethod
    def _extrahiere_zugferd_aus_pdf(pdf_pfad: str) -> bytes:
        """Versucht ZUGFeRD-XML aus PDF-Anhang zu extrahieren (ohne externe Libs)."""
        try:
            with open(pdf_pfad, "rb") as f:
                data = f.read()
            # Suche nach eingebettetem XML (ZUGFeRD/Factur-X)
            markers = [b"<?xml version", b"<?XML VERSION"]
            for marker in markers:
                idx = data.find(marker)
                while idx != -1:
                    # Suche Ende des XML-Dokuments
                    for end_tag in [b"</rsm:CrossIndustryInvoice>",
                                    b"</CrossIndustryInvoice>",
                                    b"</Invoice>"]:
                        end_idx = data.find(end_tag, idx)
                        if end_idx != -1:
                            xml_bytes = data[idx:end_idx + len(end_tag)]
                            if b"CrossIndustryInvoice" in xml_bytes or b"Invoice" in xml_bytes:
                                return xml_bytes
                    idx = data.find(marker, idx + 1)
        except Exception:
            pass
        return b""

    def _import_rechnung_aus_datei(self, pfad: str) -> dict:
        """Liest Rechnungsdaten aus Datei: ZUGFeRD XML, xRechnung, oder KI-OCR."""
        import os
        ext = os.path.splitext(pfad)[1].lower()
        # 1. Direkte XML-Datei
        if ext == ".xml":
            try:
                with open(pfad, "rb") as f:
                    xml_bytes = f.read()
                # Versuche CII zuerst, dann UBL
                if b"CrossIndustryInvoice" in xml_bytes:
                    return self._parse_zugferd_cii(xml_bytes)
                elif b"Invoice-2" in xml_bytes or b"urn:oasis:names:specification:ubl" in xml_bytes:
                    return self._parse_xrechnung_ubl(xml_bytes)
            except Exception:
                pass
        # 2. PDF mit eingebettetem ZUGFeRD-XML
        if ext == ".pdf":
            xml_bytes = self._extrahiere_zugferd_aus_pdf(pfad)
            if xml_bytes:
                result = self._parse_zugferd_cii(xml_bytes)
                if result.get("rechnungssteller") or result.get("betrag_brutto"):
                    return result
        # 3. KI-OCR Fallback
        return {}


class BuchungZuordnenDialog(tk.Toplevel):
    """#65 – Dialog um Buchungen einer Rechnung zuzuordnen.

    GH#76: Suchfeld für „Nicht zugeordnete Buchungen" (Filter nach Datum/Beschreibung/Betrag/Belegnr).
    GH#77: Click-to-Sort (▲/▼) in beiden Treeviews.
    """

    _COLS = ("Datum", "Beschreibung", "Betrag €", "Belegnr.")
    _COL_W = (90, 220, 100, 90)

    def __init__(self, parent, rechnung_id: int, steller: str,
                 betrag_gesamt: float, callback=None):
        super().__init__(parent)
        self.title(f"Buchung zuordnen – {steller}")
        self.configure(bg=BG_CARD)
        self.geometry("780x560")
        self.grab_set()
        self._rechnung_id = rechnung_id
        self._betrag_gesamt = betrag_gesamt
        self._callback = callback
        self._alle_offen: list = []          # #GH76: Cache für Suchfilter
        self._such_var = tk.StringVar()      # #GH76: Suchtext
        self._build()
        self._load()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build(self):
        tk.Label(self, text="Buchungen der Rechnung zuordnen",
                 bg=BG_CARD, fg=TEXT, font=FONT_H2).pack(padx=20, pady=(14, 2), anchor="w")
        tk.Label(self,
                 text="Doppelklick auf eine Buchung um sie dieser Rechnung zuzuordnen "
                      "(oder Zuordnung aufzuheben).",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(padx=20, anchor="w")

        # ── Bereits zugeordnet ────────────────────────────────────────────────
        tk.Label(self, text="✅ Bereits zugeordnete Buchungen:",
                 bg=BG_CARD, fg=SUCCESS, font=("Segoe UI Semibold", 9)).pack(
                     padx=20, pady=(10, 2), anchor="w")
        f1, self._tree_zugeord = make_table(self, self._COLS, height=4)
        f1.pack(fill="x", padx=20)
        for c, w in zip(self._COLS, self._COL_W):
            self._tree_zugeord.column(c, width=w)
        self._tree_zugeord.column("Betrag €", anchor="e")
        self._tree_zugeord.bind("<Double-1>",
                                lambda e: self._toggle(self._tree_zugeord, False))
        # #GH77: Sortierung für zugeordnete Tabelle einrichten
        self._setup_sort(self._tree_zugeord)

        # ── Suchfeld (GH#76) ──────────────────────────────────────────────────
        such_row = tk.Frame(self, bg=BG_CARD)
        such_row.pack(fill="x", padx=20, pady=(8, 0))
        tk.Label(such_row, text="⬜ Nicht zugeordnete Buchungen (Doppelklick zum Zuordnen):",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=("Segoe UI Semibold", 9)).pack(side="left")
        tk.Frame(such_row, bg=BG_CARD).pack(side="left", expand=True, fill="x")
        tk.Label(such_row, text="🔍", bg=BG_CARD, fg=TEXT_LIGHT,
                 font=FONT_BODY).pack(side="left", padx=(0, 2))
        such_entry = tk.Entry(such_row, textvariable=self._such_var,
                              width=20, font=FONT_BODY, relief="solid", bd=1)
        such_entry.pack(side="left", pady=2)
        self._such_var.trace("w", lambda *_: self._filter_offen())  # #GH76

        # ── Nicht zugeordnet ──────────────────────────────────────────────────
        f2, self._tree_offen = make_table(self, self._COLS, height=6)
        f2.pack(fill="both", expand=True, padx=20, pady=(2, 0))
        for c, w in zip(self._COLS, self._COL_W):
            self._tree_offen.column(c, width=w)
        self._tree_offen.column("Betrag €", anchor="e")
        self._tree_offen.bind("<Double-1>",
                              lambda e: self._toggle(self._tree_offen, True))
        # #GH77: Sortierung für offene Tabelle einrichten
        self._setup_sort(self._tree_offen)

        # ── Summen & Buttons ──────────────────────────────────────────────────
        self._sum_lbl = tk.Label(self, text="", bg=BG_CARD, fg=TEXT, font=FONT_H3)
        self._sum_lbl.pack(padx=20, pady=(6, 2), anchor="w")

        btn_row = tk.Frame(self, bg=BG_CARD)
        btn_row.pack(fill="x", padx=20, pady=(0, 12))
        make_btn(btn_row, "Schließen", self._close, color=ACCENT2).pack(side="right")

    # ── GH#77: Sortierung einrichten ──────────────────────────────────────────

    def _setup_sort(self, tv):
        """GH#77 – Richtet Click-to-Sort-Handler für alle Spalten des Treeviews ein."""
        for col in self._COLS:
            tv.heading(col, text=col,
                       command=lambda c=col, t=tv: self._sort_tree(t, c, False))

    def _sort_tree(self, tv, col, reverse):
        """GH#77 – Sortiert den Treeview nach Spalte col (asc/desc toggle)."""
        children = tv.get_children("")
        # Leere-Hinweis-Zeile herausfiltern
        data = [(tv.set(k, col), k) for k in children if k != "__empty__"]
        if not data:
            return
        if col == "Betrag €":
            def _num_key(t):
                try:
                    return float(
                        t[0].replace(".", "").replace(",", ".").replace("€", "").strip()
                    )
                except ValueError:
                    return 0.0
            data.sort(key=_num_key, reverse=reverse)
        else:
            data.sort(key=lambda t: t[0].lower(), reverse=reverse)
        for idx, (_, k) in enumerate(data):
            tv.move(k, "", idx)
        # Headings: aktive Spalte mit Pfeil, andere zurücksetzen
        arrow_up = " ▲"
        arrow_down = " ▼"
        for c in self._COLS:
            if c == col:
                tv.heading(c, text=c + (arrow_up if not reverse else arrow_down),
                           command=lambda c2=c, t2=tv: self._sort_tree(t2, c2, not reverse))
            else:
                tv.heading(c, text=c,
                           command=lambda c2=c, t2=tv: self._sort_tree(t2, c2, False))

    # ── GH#76: Suchfilter ─────────────────────────────────────────────────────

    def _filter_offen(self):
        """GH#76 – Filtert den 'Nicht zugeordnet'-Treeview nach Suchtext."""
        for k in self._tree_offen.get_children():
            self._tree_offen.delete(k)
        suchtext = self._such_var.get().strip().lower()
        for b in self._alle_offen:
            betrag = abs(b["betrag"] or 0)
            datum_str = fmt_date(b["datum"]) if b["datum"] else "–"
            desc_str = b["beschreibung"] or "–"
            belegnr_str = b["belegnr"] or "–"
            betrag_str = fmt_euro(betrag)
            if suchtext and not any(
                suchtext in s.lower()
                for s in (datum_str, desc_str, belegnr_str, betrag_str)
            ):
                continue
            self._tree_offen.insert("", "end", iid=b["id"], values=(
                datum_str, desc_str, betrag_str, belegnr_str))
        tree_empty_hint(self._tree_offen,
                        "(Keine Buchungen)" if not suchtext else "(Keine Treffer)")
        self._setup_sort(self._tree_offen)  # Sort-Handler nach Neubefüllung neu einrichten

    # ── Daten laden ───────────────────────────────────────────────────────────

    def _load(self):
        for t in (self._tree_zugeord, self._tree_offen):
            for i in t.get_children(): t.delete(i)
        conn = get_db()
        try:
            zugeordnet = conn.execute(
                "SELECT id, datum, beschreibung, betrag, belegnr FROM zahlungen "
                "WHERE rechnung_id=? ORDER BY datum", (self._rechnung_id,)).fetchall()
            offen_raw = conn.execute(
                "SELECT id, datum, beschreibung, betrag, belegnr FROM zahlungen "
                "WHERE rechnung_id IS NULL AND typ='Ausgabe' ORDER BY datum DESC LIMIT 100"
            ).fetchall()
        finally:
            conn.close()
        # #GH76: Cache für Suchfilter
        self._alle_offen = [dict(r) for r in offen_raw]
        total = 0.0
        for b in zugeordnet:
            betrag = abs(b["betrag"] or 0)
            total += betrag
            self._tree_zugeord.insert("", "end", iid=b["id"], values=(
                fmt_date(b["datum"]) if b["datum"] else "–",
                b["beschreibung"] or "–", fmt_euro(betrag), b["belegnr"] or "–"))
        tree_empty_hint(self._tree_zugeord)
        self._setup_sort(self._tree_zugeord)  # #GH77: Sort-Handler nach Laden
        self._filter_offen()  # #GH76: gefiltert (re-)laden (behält Suchtext nach Reload)
        diff = self._betrag_gesamt - total
        diff_color = SUCCESS if abs(diff) < 0.01 else (DANGER if diff < -0.01 else ACCENT2)
        self._sum_lbl.config(
            text=f"Rechnungsbetrag: {fmt_euro(self._betrag_gesamt)}  "
                 f"Gebucht: {fmt_euro(total)}  "
                 f"Differenz: {fmt_euro(diff)}",
            fg=diff_color)

    def _toggle(self, tree, zuordnen: bool):
        sel = tree.selection()
        if not sel: return
        zahlung_id = int(sel[0])
        conn = get_db()
        try:
            if zuordnen:
                conn.execute("UPDATE zahlungen SET rechnung_id=? WHERE id=?",
                             (self._rechnung_id, zahlung_id))
                _sync_kategorie_von_rechnung(conn, zahlung_id, self._rechnung_id)  # #78
            else:
                conn.execute("UPDATE zahlungen SET rechnung_id=NULL WHERE id=?",
                             (zahlung_id,))
            _auto_update_rechnung_status(conn, self._rechnung_id)  # #67
            conn.commit()
        finally:
            conn.close()
        self._load()
        if self._callback:
            self._callback()

    def _close(self):
        if self._callback:
            self._callback()
        self.destroy()


class MatchingReviewDialog(tk.Toplevel):
    """#70 – Vorschläge des Auto-Matchings visuell bestätigen oder ablehnen.

    Zeigt Kontoauszugsbuchung und den besten Rechnungs-Kandidaten nebeneinander.
    Benutzer kann bestätigen (Zahlung wird angelegt), ablehnen (nächster Vorschlag)
    oder die Rechnung manuell wählen.
    """

    def __init__(self, parent, vorschlaege: list, conn_factory, callback=None):
        super().__init__(parent)
        self.title("Auto-Matching – Vorschläge prüfen")
        self.geometry("900x600")
        self.configure(bg=BG_CARD)
        self.resizable(True, True)
        self.grab_set()
        self._vorschlaege = vorschlaege
        self._idx = 0
        self._conn_factory = conn_factory
        self._callback = callback
        self._bestaetigt = 0
        self._abgelehnt = 0
        self._build()
        self._show_current()

    # ── UI aufbauen ────────────────────────────────────────────────────────────

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=BG_SIDEBAR)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🔗 Auto-Matching – Vorschläge prüfen",
                 bg=BG_SIDEBAR, fg=ACCENT, font=FONT_H2).pack(side="left", padx=16, pady=10)
        self._fortschritt_lbl = tk.Label(hdr, text="", bg=BG_SIDEBAR, fg=TEXT_WHITE, font=FONT_SMALL)
        self._fortschritt_lbl.pack(side="right", padx=16)

        # Score-Balken
        self._score_frame = tk.Frame(self, bg=BG_CARD)
        self._score_frame.pack(fill="x", padx=20, pady=(10, 0))

        # Haupt-Inhalt: Kontoauszug links | Rechnung rechts
        content = tk.Frame(self, bg=BG_CARD)
        content.pack(fill="both", expand=True, padx=20, pady=8)
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=1)

        # Linke Seite: Kontoauszug
        self._ka_frame = tk.LabelFrame(content, text="🏦 Kontoauszugsbuchung",
                                        bg=BG_CARD, fg=ACCENT2, font=FONT_BODY, bd=1, relief="groove")
        self._ka_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=4)

        # Rechte Seite: Rechnungs-Kandidat
        self._rg_frame = tk.LabelFrame(content, text="🧾 Rechnungs-Kandidat",
                                        bg=BG_CARD, fg=DARKBLUE if hasattr(__builtins__, 'DARKBLUE') else "#1A5276",
                                        font=FONT_BODY, bd=1, relief="groove")
        self._rg_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=4)

        # Kandidaten-Auswahl (wenn mehrere)
        self._kandidat_frame = tk.Frame(content, bg=BG_CARD)
        self._kandidat_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        self._kandidat_var = tk.IntVar(value=0)

        # Status-Leiste
        self._status_lbl = tk.Label(self, text="", bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL)
        self._status_lbl.pack(pady=(0, 4))

        # Button-Leiste
        btn_row = tk.Frame(self, bg=BG_CARD)
        btn_row.pack(fill="x", padx=20, pady=(0, 14))
        make_btn(btn_row, "✅ Bestätigen",  self._bestaetigen, color=SUCCESS).pack(side="left", padx=(0, 8))
        make_btn(btn_row, "❌ Ablehnen",    self._ablehnen,    color=DANGER).pack(side="left", padx=(0, 8))
        make_btn(btn_row, "⏭ Überspringen", self._ueberspringen, color=BG_INPUT, fg=TEXT).pack(side="left", padx=(0, 8))
        make_btn(btn_row, "🏁 Fertig",      self._fertig,      color=ACCENT2).pack(side="right")

    # ── Aktuellen Vorschlag anzeigen ──────────────────────────────────────────

    def _show_current(self):
        """Zeigt den aktuellen Vorschlag (self._idx) an."""
        # Score-Balken leeren
        for w in self._score_frame.winfo_children():
            w.destroy()
        for w in self._ka_frame.winfo_children():
            w.destroy()
        for w in self._rg_frame.winfo_children():
            w.destroy()
        for w in self._kandidat_frame.winfo_children():
            w.destroy()

        if self._idx >= len(self._vorschlaege):
            self._fertig()
            return

        v = self._vorschlaege[self._idx]
        kb = v["kb"]
        kandidaten = v["kandidaten"]
        self._kandidat_var.set(0)

        total = len(self._vorschlaege)
        self._fortschritt_lbl.config(text=f"Vorschlag {self._idx + 1} von {total}  "
                                          f"(✅ {self._bestaetigt}  ❌ {self._abgelehnt})")

        # Score-Balken
        bester_score = kandidaten[0]["score"] if kandidaten else 0
        farbe = SUCCESS if bester_score >= 80 else (ACCENT if bester_score >= 60 else WARNING)
        tk.Label(self._score_frame, text=f"Confidence Score: {bester_score:.0f} / 100",
                 bg=BG_CARD, fg=farbe, font=FONT_H2).pack(side="left")
        if bester_score >= 80:
            tk.Label(self._score_frame, text="  → Auto-Match-Grenze erreicht",
                     bg=BG_CARD, fg=SUCCESS, font=FONT_SMALL).pack(side="left", padx=8)
        bar_outer = tk.Frame(self._score_frame, bg=BG_INPUT, width=200, height=12)
        bar_outer.pack(side="left", padx=16, pady=4)
        bar_outer.pack_propagate(False)
        bar_w = max(4, int(bester_score * 2))
        tk.Frame(bar_outer, bg=farbe, width=bar_w, height=12).pack(side="left")

        # Kontoauszug-Felder (linke Seite)
        def lbl_row(parent, key, val):
            r = tk.Frame(parent, bg=BG_CARD)
            r.pack(fill="x", padx=10, pady=2)
            tk.Label(r, text=key + ":", bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL,
                     width=16, anchor="w").pack(side="left")
            tk.Label(r, text=str(val or "–"), bg=BG_CARD, fg=TEXT, font=FONT_BODY,
                     anchor="w", wraplength=280).pack(side="left", fill="x", expand=True)

        lbl_row(self._ka_frame, "Datum",   fmt_date(kb.get("datum")))
        lbl_row(self._ka_frame, "Betrag",  fmt_euro(kb.get("betrag")))
        lbl_row(self._ka_frame, "IBAN",    kb.get("iban", "–"))
        lbl_row(self._ka_frame, "Konto",   kb.get("konto_typ", "–"))
        bt = kb.get("buchungstext", "")
        if "||" in bt:
            gk, vzw = bt.split("||", 1)
            lbl_row(self._ka_frame, "Gegenkonto", gk.strip())
            lbl_row(self._ka_frame, "Verwendungszweck", vzw.strip())
        else:
            lbl_row(self._ka_frame, "Buchungstext", bt)

        # Rechts: bester Kandidat (oder gewählter via Radio)
        def _show_rechnung(ridx):
            for w in self._rg_frame.winfo_children():
                w.destroy()
            if ridx >= len(kandidaten):
                return
            rg = kandidaten[ridx]["rechnung"]
            lbl_row(self._rg_frame, "Rechnungs-Nr.", rg.get("rechnungsnummer"))
            lbl_row(self._rg_frame, "Rechnungssteller", rg.get("rechnungssteller"))
            lbl_row(self._rg_frame, "Datum", fmt_date(rg.get("rechnungsdatum")))
            lbl_row(self._rg_frame, "Fälligkeit", fmt_date(rg.get("faelligkeitsdatum")))
            lbl_row(self._rg_frame, "Brutto", fmt_euro(rg.get("betrag_brutto")))
            lbl_row(self._rg_frame, "Status", rg.get("status", "–"))
            lbl_row(self._rg_frame, "Kategorie", rg.get("kategorie", "–"))

        self._show_rechnung_fn = _show_rechnung
        _show_rechnung(0)

        # Kandidaten-Auswahl (wenn > 1 Kandidat)
        if len(kandidaten) > 1:
            tk.Label(self._kandidat_frame, text="Andere Kandidaten:",
                     bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(side="left", padx=(0, 8))
            for i, k in enumerate(kandidaten):
                rg = k["rechnung"]
                txt = f"#{i+1}: {rg.get('rechnungssteller','?')} {fmt_euro(rg.get('betrag_brutto'))} (Score {k['score']:.0f})"
                tk.Radiobutton(
                    self._kandidat_frame, text=txt,
                    variable=self._kandidat_var, value=i,
                    bg=BG_CARD, fg=TEXT, font=FONT_SMALL,
                    activebackground=BG_CARD, selectcolor=BG_CARD,
                    command=lambda i=i: _show_rechnung(i)
                ).pack(side="left", padx=4)

    # ── Aktionen ──────────────────────────────────────────────────────────────

    def _bestaetigen(self):
        """Bestätigter Vorschlag: Zahlung anlegen, Rechnung verknüpfen, Log-Eintrag."""
        if self._idx >= len(self._vorschlaege):
            return
        v = self._vorschlaege[self._idx]
        kb = v["kb"]
        ridx = self._kandidat_var.get()
        if ridx >= len(v["kandidaten"]):
            return
        rechnung = v["kandidaten"][ridx]["rechnung"]
        score = v["kandidaten"][ridx]["score"]

        conn = self._conn_factory()
        try:
            bt = kb.get("buchungstext", "")
            if "||" in bt:
                gk, vzw = bt.split("||", 1)
                beschr = f"{gk.strip()} – {vzw.strip()}"[:200]
            else:
                beschr = bt[:200]

            existing_z = conn.execute(
                "SELECT id FROM zahlungen WHERE datum=? AND betrag=? AND konto_typ=?",
                (kb.get("datum"), kb.get("betrag"), kb.get("konto_typ", ""))
            ).fetchone()

            if existing_z:
                zahlung_id = existing_z["id"]
                conn.execute("UPDATE zahlungen SET rechnung_id=? WHERE id=? AND rechnung_id IS NULL",
                             (rechnung["id"], zahlung_id))
            else:
                kat = kb.get("kategorie_vorschlag") or rechnung.get("kategorie") or "Sonstiges"
                conn.execute(
                    "INSERT INTO zahlungen "
                    "(datum,betrag,typ,kategorie,beschreibung,konto_typ,status,rechnung_id) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (kb.get("datum"), kb.get("betrag"), "Ausgabe",
                     kat, beschr,
                     kb.get("konto_typ", ""), "Neu", rechnung["id"]))
                zahlung_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

            conn.execute(
                "UPDATE kontoauszug SET zugeordnet=1, als_buchung_uebernommen=1, "
                "zahlung_id=? WHERE id=?",
                (zahlung_id, kb["id"]))
            _auto_update_rechnung_status(conn, rechnung["id"])

            # Match-Log: bestätigt
            conn.execute(
                "UPDATE kontoauszug_match_log SET bestaetigt_am=datetime('now') "
                "WHERE kontoauszug_id=? AND rechnung_id=? AND abgelehnt=0",
                (kb["id"], rechnung["id"]))
            _auto_log_match(conn, kb["id"], rechnung["id"], zahlung_id, score, "manuell_bestaetigt")
            conn.commit()
            self._bestaetigt += 1
        except Exception as e:
            messagebox.showerror("Fehler", f"Buchung konnte nicht gespeichert werden:\n{e}", parent=self)
        finally:
            conn.close()

        self._idx += 1
        self._show_current()

    def _ablehnen(self):
        """Ablehnen: Match als abgelehnt markieren, Buchung bleibt offen."""
        if self._idx >= len(self._vorschlaege):
            return
        v = self._vorschlaege[self._idx]
        kb = v["kb"]
        ridx = self._kandidat_var.get()
        rechnung_id = v["kandidaten"][ridx]["rechnung"]["id"] if ridx < len(v["kandidaten"]) else None
        score = v["kandidaten"][ridx]["score"] if ridx < len(v["kandidaten"]) else 0

        conn = self._conn_factory()
        try:
            _auto_log_match(conn, kb["id"], rechnung_id, None, score, "abgelehnt")
            conn.execute(
                "UPDATE kontoauszug_match_log SET abgelehnt=1 WHERE kontoauszug_id=? AND bestaetigt_am IS NULL",
                (kb["id"],))
            conn.commit()
            self._abgelehnt += 1
        finally:
            conn.close()

        self._idx += 1
        self._show_current()

    def _ueberspringen(self):
        """Überspringen: kein Log-Eintrag, nächster Vorschlag."""
        self._idx += 1
        self._show_current()

    def _fertig(self):
        """Alle Vorschläge bearbeitet: Zusammenfassung anzeigen + Dialog schließen."""
        rest = len(self._vorschlaege) - self._idx
        messagebox.showinfo(
            "Matching abgeschlossen",
            f"✅ Bestätigt:    {self._bestaetigt}\n"
            f"❌ Abgelehnt:   {self._abgelehnt}\n"
            f"⏭ Übersprungen: {rest}\n\n"
            "Alle offenen Positionen können in der Rechnungsverwaltung\n"
            "per ›Buchung zuordnen‹ manuell verknüpft werden.",
            parent=self)
        if self._callback:
            self._callback()
        self.destroy()


class RechnungDialog(BaseDialog):
    """Dialog zum Anlegen/Bearbeiten einer Rechnung (#66)."""

    def __init__(self, parent, row=None):
        super().__init__(parent, "Rechnung" + (" bearbeiten" if row else " erfassen"), 600, 660)
        r = row or {}

        # Grunddaten – zweispaltig: Rechnungsnummer + Rechnungssteller
        def _two_col():
            """Hilfsfunktion: Gibt zwei gleichbreite Spalten-Frames zurück."""
            f = tk.Frame(self._body, bg=BG_CARD); f.pack(fill="x", padx=20)
            f.columnconfigure((0, 1), weight=1)
            l = tk.Frame(f, bg=BG_CARD); l.grid(row=0, column=0, padx=(0, 6), sticky="ew")
            ri = tk.Frame(f, bg=BG_CARD); ri.grid(row=0, column=1, padx=(6, 0), sticky="ew")
            return l, ri

        l, ri = _two_col()
        self._add_field("Rechnungsnummer", "rechnungsnummer", r.get("rechnungsnummer", "") or "", row=l)
        self._add_field("Rechnungssteller *", "rechnungssteller", r.get("rechnungssteller", "") or "", row=ri)
        l, ri = _two_col()
        self._add_field("Rechnungsdatum (JJJJ-MM-TT)", "rechnungsdatum",
                        r.get("rechnungsdatum", date.today().isoformat()) or "", row=l)
        self._add_field("Fälligkeitsdatum (JJJJ-MM-TT)", "faelligkeitsdatum",
                        r.get("faelligkeitsdatum", "") or "", row=ri)

        # Beträge – zweispaltig: Brutto/Netto und MwSt-Satz/Betrag #71
        tk.Frame(self._body, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(10, 4))
        tk.Label(self._body, text="Beträge",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=("Segoe UI Semibold", 9)).pack(padx=20, anchor="w")
        l, ri = _two_col()
        self._add_field("Betrag Brutto € *", "betrag_brutto",
                        r.get("betrag_brutto", "") or "", row=l)
        self._add_field("Betrag Netto €", "betrag_netto",
                        r.get("betrag_netto", "") or "", row=ri)
        l, ri = _two_col()
        self._add_field("MwSt. %", "mwst_satz", r.get("mwst_satz", "19") or "19", row=l)
        self._add_field("MwSt. Betrag €", "mwst_betrag", r.get("mwst_betrag", "") or "", row=ri)
        # #74 – Lohnanteil: §35a EStG wird automatisch erkannt (kein Checkbox mehr)
        self._add_field("Lohnanteil € (§35a EStG – Handwerkerleistung)", "lohnanteil",
                        r.get("lohnanteil", "") or "")

        # Kategorie & Status
        tk.Frame(self._body, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(10, 4))
        self._add_field("Kategorie", "kategorie", r.get("kategorie", "") or "",
                        widget_type="combo", options=BuchhaltungPage.aktive_kategorien())
        self._add_field("Status", "status", r.get("status", "Offen") or "Offen",
                        widget_type="combo", options=RechnungenPage.STATI)
        self._add_field("Beschreibung", "beschreibung", r.get("beschreibung", "") or "",
                        widget_type="text")

        # Beleg-Datei
        tk.Frame(self._body, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(10, 4))
        tk.Label(self._body, text="Beleg / Rechnung (PDF, XML)",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(padx=20, anchor="w")
        beleg_row = tk.Frame(self._body, bg=BG_CARD)
        beleg_row.pack(fill="x", padx=20)
        self._beleg_var = tk.StringVar(value=r.get("beleg_dateipfad", "") or "")
        beleg_entry = tk.Entry(beleg_row, textvariable=self._beleg_var,
                               bg=BG_INPUT, fg=TEXT, font=FONT_BODY,
                               relief="flat", bd=0, highlightthickness=1,
                               highlightbackground=BORDER)
        beleg_entry.pack(side="left", fill="x", expand=True, ipady=5)
        make_btn(beleg_row, "📂 Durchsuchen", self._browse_und_import,
                 color=BG_INPUT, fg=TEXT).pack(side="left", padx=(6, 0))
        self._zugferd_format_val = r.get("zugferd_format") or None  # #66 – gespeichertes Format
        self._import_lbl = tk.Label(self._body,
            text=f"Format: {r.get('zugferd_format','–')}" if r.get("zugferd_format") else "",
            bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL)
        self._import_lbl.pack(padx=20, anchor="w")

    def _browse_und_import(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            parent=self,
            title="Rechnung auswählen (PDF, XML)",
            filetypes=[("Rechnungen", "*.pdf *.xml"), ("Alle", "*.*")]
        )
        if not path:
            return
        self._beleg_var.set(path)
        # Versuche automatischen Import
        try:
            daten = RechnungenPage._extrahiere_und_parse(path)
            if daten:
                self._felder_befuellen(daten)
                fmt = daten.get("zugferd_format", "Unbekannt")
                self._zugferd_format_val = fmt  # #66 – Format merken
                self._import_lbl.config(text=f"✅ Importiert ({fmt})", fg=SUCCESS)
            else:
                self._import_lbl.config(
                    text="ℹ Kein ZUGFeRD/xRechnung erkannt – bitte manuell ausfüllen",
                    fg=TEXT_LIGHT)
        except Exception as ex:
            self._import_lbl.config(text=f"⚠ Fehler: {ex}", fg=DANGER)

    def _felder_befuellen(self, daten: dict):
        """Befüllt Formularfelder aus importierten Rechnungsdaten."""
        def _set(key, val):
            if not val:
                return
            w = self._fields.get(key)
            if not w: return
            if hasattr(w, "set"): w.set(str(val))
            elif hasattr(w, "delete"): w.delete(0, "end"); w.insert(0, str(val))
        for key in ("rechnungsnummer", "rechnungssteller", "rechnungsdatum",
                    "faelligkeitsdatum", "betrag_brutto", "betrag_netto",
                    "mwst_satz", "mwst_betrag", "lohnanteil"):
            _set(key, daten.get(key))

    def _on_save(self):
        v = self._get_values()
        if not v.get("rechnungssteller"):
            messagebox.showwarning("Pflichtfeld", "Rechnungssteller ist erforderlich.", parent=self)
            return
        if not v.get("betrag_brutto"):
            messagebox.showwarning("Pflichtfeld", "Betrag Brutto ist erforderlich.", parent=self)
            return
        v["beleg_dateipfad"] = self._beleg_var.get().strip() or None
        v["zugferd_format"] = getattr(self, "_zugferd_format_val", None)  # #66
        # #74 – handwerker_steuerlich auto: 1 wenn Lohnanteil > 0 (keine Checkbox)
        try:
            v["handwerker_steuerlich"] = 1 if float(v.get("lohnanteil") or 0) > 0 else 0
        except (ValueError, TypeError):
            v["handwerker_steuerlich"] = 0
        self.result = v
        self.destroy()


# ── Hilfsmethode als Klassenmethode von RechnungenPage ───────────────────────

def _ki_ocr_rechnung_static(pdf_pfad: str) -> dict:
    """#68 – KI-OCR Fallback: Sendet PDF an Anthropic API um Rechnungsdaten zu extrahieren."""
    import base64
    cfg = load_config()
    api_key = cfg.get("anthropic_api_key", "").strip() or cfg.get("ki_api_key", "").strip()
    if not api_key:
        return {}
    modell = "claude-haiku-4-5-20251001"  # Schnelles Modell für OCR
    try:
        with open(pdf_pfad, "rb") as fh:
            pdf_b64 = base64.standard_b64encode(fh.read()).decode("ascii")
    except Exception:
        return {}

    prompt = (
        "Analysiere diese Rechnung (PDF). Führe OCR durch und extrahiere die Daten.\n"
        "Antworte NUR mit einem gültigen JSON-Objekt ohne Markdown-Formatierung.\n\n"
        "Felder:\n"
        '  "rechnungsnummer": Rechnungsnummer als Text\n'
        '  "rechnungssteller": Name des Rechnungsausstellers\n'
        '  "rechnungsdatum": Rechnungsdatum als YYYY-MM-DD\n'
        '  "faelligkeitsdatum": Fälligkeitsdatum als YYYY-MM-DD (oder null)\n'
        '  "betrag_brutto": Gesamtbetrag inkl. MwSt als Dezimalzahl\n'
        '  "betrag_netto": Nettobetrag als Dezimalzahl (oder null)\n'
        '  "mwst_satz": MwSt-Satz in Prozent (z.B. 19.0 oder null)\n'
        '  "mwst_betrag": MwSt-Betrag als Dezimalzahl (oder null)\n'
        '  "lohnanteil": Lohnanteil (§35a EStG) als Dezimalzahl (oder null)\n'
        '  "beschreibung": Kurze Leistungsbeschreibung'
    )
    try:
        import json as _json
        body = _json.dumps({
            "model": modell,
            "max_tokens": 512,
            "system": "Du bist ein Experte für Rechnungsanalyse. Extrahiere Daten präzise.",
            "messages": [{"role": "user", "content": [
                {"type": "document", "source": {
                    "type": "base64", "media_type": "application/pdf", "data": pdf_b64}},
                {"type": "text", "text": prompt}
            ]}]
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=body,
            headers={"Content-Type": "application/json",
                     "x-api-key": api_key,
                     "anthropic-version": "2023-06-01",
                     "anthropic-beta": "pdfs-2024-09-25"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = _json.loads(resp.read().decode())
        text = result.get("content", [{}])[0].get("text", "")
        # JSON aus Antwort extrahieren
        start = text.find("{")
        end   = text.rfind("}") + 1
        if start >= 0 and end > start:
            daten = _json.loads(text[start:end])
            daten["zugferd_format"] = "PDF-KI-OCR"
            return daten
    except Exception:
        pass
    return {}


@staticmethod
def _extrahiere_und_parse_static(pfad: str) -> dict:
    """#66/#68 – Extrahiert und parst Rechnungsdaten: ZUGFeRD → xRechnung → KI-OCR."""
    import os
    ext = os.path.splitext(pfad)[1].lower()
    if ext == ".xml":
        try:
            with open(pfad, "rb") as f:
                xml_bytes = f.read()
            if b"CrossIndustryInvoice" in xml_bytes:
                return RechnungenPage._parse_zugferd_cii(xml_bytes)
            elif b"Invoice-2" in xml_bytes or b"urn:oasis:names:specification:ubl" in xml_bytes:
                return RechnungenPage._parse_xrechnung_ubl(xml_bytes)
        except Exception:
            pass
    elif ext == ".pdf":
        # 1. ZUGFeRD aus PDF extrahieren
        xml_bytes = RechnungenPage._extrahiere_zugferd_aus_pdf(pfad)
        if xml_bytes:
            result = RechnungenPage._parse_zugferd_cii(xml_bytes)
            if result.get("rechnungssteller") or result.get("betrag_brutto"):
                return result
        # 2. KI-OCR Fallback (#68)
        return _ki_ocr_rechnung_static(pfad)
    return {}


RechnungenPage._extrahiere_und_parse = staticmethod(_extrahiere_und_parse_static)
RechnungenPage._ki_ocr_rechnung = staticmethod(_ki_ocr_rechnung_static)


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
        import shutil, os
        dok_ordner = get_pfad("pfad_dokumente", "Dokumente")  # #38
        path = filedialog.askopenfilename(title="Datei auswählen", initialdir=str(dok_ordner))
        if path:
            # Datei in den Dokumente-Ordner kopieren, falls sie nicht schon dort liegt (#47)
            if os.path.normpath(os.path.dirname(path)) != os.path.normpath(str(dok_ordner)):
                ziel = os.path.join(str(dok_ordner), os.path.basename(path))
                try:
                    if not os.path.exists(ziel):
                        shutil.copy2(path, ziel)
                    path = ziel
                except Exception:
                    pass  # Original-Pfad beibehalten wenn Kopieren fehlschlägt
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
                            ("verbrauch", "🔢 Verbrauch"),
                            ("wohngeld", "💰 Hausgeld-Kontrolle")]:
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
        make_btn(yr_row, "🌐 HTML Export", self._export_html_weg,  # #82
                 color=BG_INPUT, fg=TEXT).pack(side="left", padx=(4, 0))
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

        # ── Tab Hausgeld-Kontrolle (#86) ────────────────────────────────────────
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
                 text="Hausgeld-Einnahmen pro Eigentümer (Ist) vs. Kostenpflicht (Soll nach MEA)",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w", padx=20)
        cols_wg = ("Eigentümer", "MEA %", "Soll (Kostenanteil)", "Ist (gezahlt)", "Saldo", "Status")
        fwg, self._tree_wg = make_table(self._view_wohngeld, cols_wg, height=12)
        fwg.pack(fill="both", expand=True, padx=20, pady=(2, 8))
        for c, w in zip(cols_wg, [180, 60, 140, 140, 110, 100]):
            self._tree_wg.heading(c, text=c)
            self._tree_wg.column(c, width=w, anchor="w")

        self._switch_tab("weg")

    # ── Tab-Wechsel ────────────────────────────────────────────────────────────

    def _switch_tab(self, tid):
        self._active_tab = tid
        for t, btn in self._tab_btns.items():
            btn.configure(bg=ACCENT if t == tid else BG_CARD,
                          fg=TEXT_WHITE if t == tid else TEXT)
        for frame in (self._view_weg, self._view_bgb, self._view_wp,
                      self._view_verbrauch, self._view_wohngeld):
            frame.pack_forget()
        view_map = {"weg": self._view_weg, "bgb": self._view_bgb,
                    "wp": self._view_wp, "verbrauch": self._view_verbrauch,
                    "wohngeld": self._view_wohngeld}
        load_map = {"weg": self._load_weg, "bgb": self._load_bgb,
                    "wp": self._load_wp, "verbrauch": self._load_verbrauch_tab,
                    "wohngeld": self._load_wohngeld}
        view_map[tid].pack(fill="both", expand=True)
        load_map[tid]()

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

    # ── Hausgeld-Kontrolle (#86) ──────────────────────────────────────────────

    def _load_wohngeld(self):
        """Wohngeld Soll/Ist: Vergleich geleisteter vs. erwarteter Hausgeld-Zahlungen."""
        try:
            jahr = int(self._wg_jahr.get())
        except ValueError:
            return
        conn = get_db()
        total_ausgaben = conn.execute(
            "SELECT COALESCE(SUM(betrag),0) FROM zahlungen "
            "WHERE typ='Ausgabe' AND strftime('%Y',datum)=?", (str(jahr),)
        ).fetchone()[0]
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
        # KPI-Karten
        for w in self._wg_kpi.winfo_children():
            w.destroy()
        saldo_gesamt = hg_gesamt_ist - total_ausgaben
        for label, wert, color in [
            ("Gesamtausgaben (Soll)", fmt_euro(total_ausgaben), DANGER),
            ("Hausgeld-Einnahmen (Ist)", fmt_euro(hg_gesamt_ist), SUCCESS),
            ("Jahressaldo", fmt_euro(saldo_gesamt), SUCCESS if saldo_gesamt >= 0 else DANGER),
        ]:
            karte = tk.Frame(self._wg_kpi, bg=BG_INPUT, padx=14, pady=8)
            karte.pack(side="left", padx=(0, 10))
            tk.Label(karte, text=label, bg=BG_INPUT, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w")
            tk.Label(karte, text=wert,  bg=BG_INPUT, fg=color,      font=FONT_H3).pack(anchor="w")
        # Pro-Eigentümer-Tabelle
        for i in self._tree_wg.get_children():
            self._tree_wg.delete(i)
        for e in eigentuemer:
            anteil_pct = parse_float(e["anteil_prozent"]) or 0
            soll       = total_ausgaben * anteil_pct / 100
            ist        = hg_map.get(e["id"], 0)
            saldo      = ist - soll
            name       = f"{e['vorname'] or ''} {e['name']}".strip()
            if saldo >= 0:
                status    = "✔ ausgeglichen"
                color_tag = "wg_plus"
            else:
                status    = f"⚠ Rückstand {fmt_euro(abs(saldo))}"
                color_tag = "wg_minus"
            self._tree_wg.insert("", "end", values=(
                name, f"{anteil_pct:.2f}%",
                fmt_euro(soll), fmt_euro(ist),
                fmt_euro(saldo), status), tags=(color_tag,))
        self._tree_wg.tag_configure("wg_plus",  foreground=SUCCESS)
        self._tree_wg.tag_configure("wg_minus", foreground=DANGER)

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
                # #59: Zeitraum-basierte NK-Vorauszahlung (Fallback: statischer Wert × 12)
                fallback_monatlich = parse_float(w["nebenkosten_vorauszahlung"]) or 0
                vorauszahlung = nk_vorauszahlung_fuer_jahr(
                    w["mieter_id"], int(jahr), fallback_monatlich) * zeitfaktor
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
                "SELECT z.datum, z.beschreibung, "
                "  COALESCE(r.rechnungssteller, '') AS rechnungssteller, "
                "  z.betrag, z.abrechnungsrelevant "
                "FROM zahlungen z LEFT JOIN rechnungen r ON z.rechnung_id = r.id "
                "WHERE z.typ='Ausgabe' AND z.kategorie=? AND strftime('%Y',z.datum)=? "
                "ORDER BY z.datum",
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

    def _export_html_weg(self):
        """#82 – HTML-Export §28 WEG Jahresabrechnung (kein reportlab nötig).
        Erstellt eine druckfertige HTML-Datei → Browser → Strg+P → Als PDF speichern.
        """
        import webbrowser, tempfile

        try:
            jahr = int(self._weg_jahr.get())
        except (ValueError, AttributeError):
            messagebox.showwarning("Jahr", "Bitte zuerst eine Auswertung laden.", parent=self)
            return

        conn = get_db()
        try:
            ausgaben_rows = conn.execute(
                "SELECT kategorie, SUM(betrag) as s FROM zahlungen "
                "WHERE typ='Ausgabe' AND strftime('%Y', datum)=? "
                "GROUP BY kategorie ORDER BY s DESC", (str(jahr),)).fetchall()
            hausgeld_rows = conn.execute(
                "SELECT eigentuemer_id, SUM(betrag) as s FROM zahlungen "
                "WHERE typ='Einnahme' AND kategorie='Hausgeld' AND strftime('%Y', datum)=? "
                "GROUP BY eigentuemer_id", (str(jahr),)).fetchall()
            hausgeld_gesamt = conn.execute(
                "SELECT COALESCE(SUM(betrag),0) FROM zahlungen "
                "WHERE typ='Einnahme' AND kategorie='Hausgeld' AND strftime('%Y', datum)=?",
                (str(jahr),)).fetchone()[0] or 0
            eigentuemer = conn.execute(
                "SELECT id, vorname, name, anteil_prozent FROM eigentuemer ORDER BY name"
            ).fetchall()
        finally:
            conn.close()

        weg_name = self._get_weg_name()
        hg_map = {r["eigentuemer_id"]: (r["s"] or 0) for r in hausgeld_rows}
        total_ausgaben = sum(r["s"] or 0 for r in ausgaben_rows)
        total_einlagen = sum(r["s"] or 0 for r in ausgaben_rows
                             if (r["kategorie"] or "") in WEG_EINLAGE_KATEGORIEN)
        total_betrieb  = total_ausgaben - total_einlagen
        saldo_gesamt   = hausgeld_gesamt - total_ausgaben
        erstellt_am    = date.today().strftime("%d.%m.%Y")

        def td(t, align="left", bold=False, color=""):
            style = f"text-align:{align};"
            if bold:   style += "font-weight:bold;"
            if color:  style += f"color:{color};"
            return f'<td style="{style}">{t}</td>'

        # ── Ausgaben-Tabelle ──────────────────────────────────────────────────
        ausgaben_html = ""
        for r in ausgaben_rows:
            kat  = r["kategorie"] or "Kategorie offen"
            meta = WEG_KATEGORIEN.get(kat, ("Sonstiges", False, "–"))
            typ  = "Rücklage-Einlage" if kat in WEG_EINLAGE_KATEGORIEN else "Betriebskosten"
            ausgaben_html += f"<tr>{td(kat)}{td(meta[0])}{td(fmt_euro(r['s'] or 0), 'right')}{td(typ)}</tr>\n"
        ausgaben_html += (f"<tr style='background:#EEEAE3;font-weight:bold'>"
                          f"{td('Gesamt')}{td('')}{td(fmt_euro(total_ausgaben),'right',True)}{td('')}</tr>")

        # ── Eigentümer-Tabelle ────────────────────────────────────────────────
        eig_html = ""
        for e in eigentuemer:
            anteil_pct   = parse_float(e["anteil_prozent"]) or 0
            kostenanteil = total_ausgaben * anteil_pct / 100
            hg_ist       = hg_map.get(e["id"], 0)
            saldo        = hg_ist - kostenanteil
            name         = f"{e['vorname'] or ''} {e['name']}".strip()
            farbe        = "#3A7D44" if saldo >= 0 else "#C0392B"
            eig_html += (f"<tr>{td(name)}{td(f'{anteil_pct:.1f}%','right')}"
                         f"{td(fmt_euro(kostenanteil),'right')}{td(fmt_euro(hg_ist),'right')}"
                         f"{td(fmt_euro(saldo),'right',color=farbe)}</tr>\n")

        html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<title>{weg_name} – §28 WEG Jahresabrechnung {jahr}</title>
<style>
  @page {{ size: A4; margin: 2cm; }}
  body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 11pt;
          color: #2C2C2C; background: #fff; }}
  h1 {{ font-size: 18pt; color: #1C2B3A; margin-bottom: 4px; }}
  h2 {{ font-size: 13pt; color: #1C2B3A; margin-top: 24px; margin-bottom: 8px;
        border-bottom: 2px solid #C8A96E; padding-bottom: 4px; }}
  .meta {{ color: #777; font-size: 9pt; margin-bottom: 20px; }}
  table {{ width: 100%; border-collapse: collapse; margin-bottom: 16px; }}
  th {{ background: #1C2B3A; color: #fff; padding: 6px 10px; text-align: left; font-size: 10pt; }}
  td {{ padding: 5px 10px; border-bottom: 1px solid #E0DDD7; font-size: 10pt; }}
  tr:nth-child(even) td {{ background: #F7F5F0; }}
  .kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }}
  .kpi {{ background: #F7F5F0; border-left: 4px solid #C8A96E; padding: 10px 14px; }}
  .kpi .val {{ font-size: 14pt; font-weight: bold; color: #1C2B3A; }}
  .kpi .lbl {{ font-size: 9pt; color: #777; margin-top: 2px; }}
  .saldo-pos {{ color: #3A7D44; }}
  .saldo-neg {{ color: #C0392B; }}
  @media print {{
    .no-print {{ display: none; }}
    body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  }}
  .print-btn {{ position: fixed; bottom: 24px; right: 24px; background: #2E6DA4;
                color: #fff; border: none; padding: 10px 20px; border-radius: 6px;
                cursor: pointer; font-size: 12pt; box-shadow: 0 2px 8px rgba(0,0,0,.2); }}
</style>
</head>
<body>
<h1>{weg_name}</h1>
<h2 style="border-bottom:3px solid #C8A96E;margin-top:8px;">§28 WEG – Jahresabrechnung {jahr}</h2>
<p class="meta">Erstellt am {erstellt_am} · Alle Beträge in Euro inkl. MwSt.</p>

<div class="kpi-grid">
  <div class="kpi"><div class="val">{fmt_euro(total_betrieb)}</div><div class="lbl">Bewirtschaftungskosten</div></div>
  <div class="kpi"><div class="val">{fmt_euro(total_einlagen)}</div><div class="lbl">Rücklage-Einlagen</div></div>
  <div class="kpi"><div class="val">{fmt_euro(hausgeld_gesamt)}</div><div class="lbl">Hausgeld-Einnahmen</div></div>
  <div class="kpi"><div class="val {'saldo-pos' if saldo_gesamt >= 0 else 'saldo-neg'}">{fmt_euro(saldo_gesamt)}</div><div class="lbl">Saldo</div></div>
</div>

<h2>Ausgaben nach Kategorie</h2>
<table>
  <tr><th>Kategorie</th><th>Gruppe</th><th style="text-align:right">Betrag</th><th>Typ</th></tr>
  {ausgaben_html}
</table>

<h2>Anteil pro Eigentümer (nach MEA)</h2>
<table>
  <tr><th>Eigentümer</th><th style="text-align:right">MEA %</th>
      <th style="text-align:right">Kostenanteil</th>
      <th style="text-align:right">Hausgeld (Ist)</th>
      <th style="text-align:right">Saldo</th></tr>
  {eig_html}
</table>

<button class="print-btn no-print" onclick="window.print()">🖨 Drucken / Als PDF speichern</button>
</body>
</html>"""

        # Ziel-Ordner: Dokumente/Abrechnungen/
        try:
            abr_dir = get_pfad("pfad_dokumente", "Dokumente") / "Abrechnungen"
            abr_dir.mkdir(parents=True, exist_ok=True)
            pfad = abr_dir / f"WEG_§28_Jahresabrechnung_{jahr}.html"
        except Exception:
            # Fallback: temporäre Datei
            tf = tempfile.NamedTemporaryFile(suffix=".html", delete=False,
                                             prefix=f"WEG_{jahr}_")
            pfad = Path(tf.name)
            tf.close()

        pfad.write_text(html, encoding="utf-8")
        webbrowser.open(pfad.as_uri())
        messagebox.showinfo("HTML Export",
            f"Jahresabrechnung {jahr} geöffnet im Browser:\n{pfad}\n\n"
            "Zum Speichern als PDF: Strg+P → Drucker = 'Als PDF speichern'",
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
            aktiv_str = "✅" if (r["aktiv"] if "aktiv" in r.keys() else 1) else "❌"  # #39
            wohn_str = ", ".join(wohn_names) if wohn_names else ((r["bezug"] if "bezug" in r.keys() else None) or "–")  # #39
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
    """Kontoauszug-Seite: Import von CAMT.052 XML (Sparkasse) und CSV.
    Tab 1: 🏦 Kontoauszug – importierte Buchungen
    Tab 2: 🔔 Vorschläge – neue Einträge auf Zuordnung warten (#83)
    """

    CAMT_NS = "urn:iso:std:iso:20022:tech:xsd:camt.052.001.08"

    def __init__(self, parent):
        super().__init__(parent, bg=BG_CARD)
        self._build()

    # ── UI aufbauen ───────────────────────────────────────────────────────────

    def _build(self):
        # ── Kopfzeile ────────────────────────────────────────────────────────
        hdr_row = tk.Frame(self, bg=BG_CARD)
        hdr_row.pack(fill="x", padx=20, pady=(18, 6))
        tk.Label(hdr_row, text="Kontoauszug", bg=BG_CARD, fg=TEXT,
                 font=FONT_H2).pack(side="left")
        make_btn(hdr_row, "📥 CAMT.052 XML", self._import_xml,
                 color=ACCENT2).pack(side="right")
        make_btn(hdr_row, "📄 CSV", self._import_csv_action,
                 color=BG_INPUT, fg=TEXT).pack(side="right", padx=(0, 8))
        make_btn(hdr_row, "🔗 Auto-Matching", self._auto_matching_starten,
                 color="#1A5276").pack(side="right", padx=(0, 8))  # #69

        # ── Sub-Tab-Leiste ────────────────────────────────────────────────────
        self._ka_tab_btns = {}
        tab_bar = tk.Frame(self, bg=BG_CARD)
        tab_bar.pack(fill="x", padx=20, pady=(4, 0))
        for tid, label in [("kontoauszug", "🏦  Kontoauszug"),
                            ("vorschlaege", "🔔  Vorschläge")]:
            btn = tk.Button(tab_bar, text=label, font=FONT_NAV, relief="flat", bd=0,
                            padx=14, pady=7, cursor="hand2",
                            command=lambda t=tid: self._switch_ka_tab(t))
            btn.pack(side="left", padx=2)
            self._ka_tab_btns[tid] = btn
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(4, 0))

        # ── Content-Bereich ───────────────────────────────────────────────────
        self._ka_content = tk.Frame(self, bg=BG_CARD)
        self._ka_content.pack(fill="both", expand=True)

        # ── View 1: Kontoauszug ───────────────────────────────────────────────
        self._view_kontoauszug = tk.Frame(self._ka_content, bg=BG_CARD)

        # Konto-Filter-Zeile
        filter_row = tk.Frame(self._view_kontoauszug, bg=BG_CARD)
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
        tk.Label(self._view_kontoauszug, textvariable=self._info_var,
                 bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(
                 anchor="w", padx=20, pady=(4, 0))

        # Status-Legende
        legende_frame = tk.Frame(self._view_kontoauszug, bg=BG_CARD)
        legende_frame.pack(fill="x", padx=20, pady=(4, 0))
        for text, farbe in [
            ("● Importiert", TEXT_LIGHT),
            ("● Vorschlag", "#E67E22"),
            ("● Übernommen", SUCCESS),
            ("● Abgerechnet", ACCENT2),
        ]:
            tk.Label(legende_frame, text=text, bg=BG_CARD, fg=farbe, font=FONT_SMALL).pack(side="left", padx=6)

        # Saldo-Kacheln (pro Konto)
        self._saldo_frame = tk.Frame(self._view_kontoauszug, bg=BG_CARD)
        self._saldo_frame.pack(fill="x", padx=20, pady=(4, 0))

        # Buchungstabelle
        cols = ("Datum", "Auftraggeber / Empfänger", "Verwendungszweck", "Betrag", "✔")
        f, self.tree = make_table(self._view_kontoauszug, cols, height=12)
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
        btn_row = tk.Frame(self._view_kontoauszug, bg=BG_CARD)
        btn_row.pack(fill="x", padx=20, pady=(0, 10))
        make_btn(btn_row, "🗑 Alle löschen", self._clear,
                 color=DANGER).pack(side="left")

        # ── View 2: Vorschläge (#83) ──────────────────────────────────────────
        self._view_vorschlaege = tk.Frame(self._ka_content, bg=BG_CARD)

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

        self._switch_ka_tab("kontoauszug")

    # ── Tab-Umschalten ────────────────────────────────────────────────────────

    def _switch_ka_tab(self, tab: str):
        for tid, btn in self._ka_tab_btns.items():
            btn.config(bg=ACCENT2 if tid == tab else BG_CARD,
                       fg=TEXT_WHITE if tid == tab else TEXT_LIGHT)
        for v in [self._view_kontoauszug, self._view_vorschlaege]:
            v.pack_forget()
        if tab == "kontoauszug":
            self._view_kontoauszug.pack(fill="both", expand=True)
            self._load()
        elif tab == "vorschlaege":
            self._view_vorschlaege.pack(fill="both", expand=True)
            self._load_vorschlaege()

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

    # ── Tab 2: Vorschläge (#83) ───────────────────────────────────────────────

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
            label = self._konto_bezeichnung(iban, cfg)
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
        kat_v, typ_v, kto_v, _ = vorschlag_kategorie(raw)
        kat_v = row.get("kategorie_vorschlag") or kat_v
        kt = row.get("konto_typ") or kto_v or "Wohngeldkonto"
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

    def _batch_uebernehmen(self):
        """Grün markierte Vorschläge automatisch übernehmen."""
        if not hat_recht("Buchhaltung", "schreiben"):
            messagebox.showwarning("Berechtigung", "Keine Schreibberechtigung.", parent=self)
            return
        selected_ids = [int(iid) for iid in self.tree_v.selection()]
        use_selection = bool(selected_ids)
        selected_iban = self._vs_iban_map.get(self._vs_konto_var.get())
        conn = get_db()
        if use_selection:
            placeholders = ",".join("?" * len(selected_ids))
            q = (f"SELECT * FROM kontoauszug "
                 f"WHERE id IN ({placeholders}) "
                 f"AND (als_buchung_uebernommen IS NULL OR als_buchung_uebernommen=0) "
                 f"AND (falsch_zugeordnet IS NULL OR falsch_zugeordnet=0) "
                 f"ORDER BY datum")
            rows = conn.execute(q, selected_ids).fetchall()
            quelle = f"{len(selected_ids)} ausgewählte Einträge"
        else:
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
        lern_queue = []
        for row_raw in rows:
            row = dict(row_raw)
            raw = row["buchungstext"] or ""
            kat = row.get("kategorie_vorschlag") or vorschlag_kategorie(raw)[0]
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
        cb = ttk.Combobox(body, textvariable=kat_var, values=BuchhaltungPage.aktive_kategorien(),
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

    # ── Import ────────────────────────────────────────────────────────────────

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

    def _auto_matching_starten(self):
        """#69/#70 – Automatisches Matching: Kontoauszugsbuchungen gegen offene Rechnungen abgleichen."""
        # Schwellwerte aus Einstellungen laden (#74)
        cfg = load_config()
        schwelle_auto     = float(cfg.get("matching_schwelle_auto",     80))
        schwelle_vorschlag = float(cfg.get("matching_schwelle_vorschlag", 60))

        # Vorab-Zählung: wie viele unzugeordnete Ausgaben gibt es?
        conn = get_db()
        try:
            ka_anzahl = conn.execute(
                "SELECT COUNT(*) FROM kontoauszug WHERE betrag < 0 AND zugeordnet=0"
            ).fetchone()[0]
            rg_anzahl = conn.execute(
                "SELECT COUNT(*) FROM rechnungen WHERE status IN ('Offen','Teilbezahlt')"
            ).fetchone()[0]
        finally:
            conn.close()

        if ka_anzahl == 0:
            messagebox.showinfo(
                "Auto-Matching",
                "Keine offenen Kontoauszugsbuchungen vorhanden.\n"
                "Alle Ausgaben sind bereits zugeordnet.",
                parent=self)
            return
        if rg_anzahl == 0:
            messagebox.showinfo(
                "Auto-Matching",
                "Keine offenen Rechnungen vorhanden.\n"
                "Bitte zuerst Rechnungen in der Rechnungsverwaltung erfassen.",
                parent=self)
            return

        antwort = messagebox.askyesno(
            "Auto-Matching starten",
            f"Kontoauszug-Buchungen (Ausgaben, unzugeordnet): {ka_anzahl}\n"
            f"Offene / Teilbezahlte Rechnungen: {rg_anzahl}\n\n"
            f"Schwellwert Auto-Buchung: {schwelle_auto:.0f}  |  Vorschlag: {schwelle_vorschlag:.0f}\n\n"
            f"Auto-Matching jetzt starten?",
            parent=self)
        if not antwort:
            return

        self._info_var.set("🔗 Auto-Matching läuft …")
        self.update_idletasks()

        conn = get_db()
        try:
            ergebnis = _auto_match_alle(conn, schwelle_auto, schwelle_vorschlag)
        finally:
            conn.close()

        self._load()

        auto = ergebnis["auto"]
        vorschlaege = ergebnis["vorschlaege"]
        offen = ergebnis["offen"]

        self._info_var.set(
            f"✅ Auto-Matching: {auto} automatisch gebucht  |  "
            f"{len(vorschlaege)} Vorschläge zur Prüfung  |  {offen} ungeklärt")

        if vorschlaege:
            # Review-Dialog öffnen
            MatchingReviewDialog(self, vorschlaege, get_db, callback=self._load)
        else:
            messagebox.showinfo(
                "Auto-Matching abgeschlossen",
                f"✅ Automatisch gebucht: {auto}\n"
                f"📋 Vorschläge zur Prüfung: 0\n"
                f"❓ Ungeklärt (kein Treffer): {offen}\n\n"
                f"Ungeklärte Buchungen können in der Rechnungsverwaltung\n"
                f"per ›Buchung zuordnen‹ manuell verknüpft werden.",
                parent=self)

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
        self._jahr_var.trace_add("write", lambda *_: self._refresh())  # #63
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
            # #64: Wohnungsbezeichnung + Mietername (aus bemerkung) + Zeitraum anzeigen
            von_str = (rd.get("von_datum") or "")[:10] if rd.get("von_datum") else ""
            bis_str = (rd.get("bis_datum") or "")[:10] if rd.get("bis_datum") else ""
            zeitraum = f" [{von_str}→{bis_str}]" if (von_str or bis_str) else ""
            bez = rd["wohnung_bezeichnung"] + zeitraum
            self.tree_p.insert("", "end", iid=rd["id"], values=(
                bez, rd["eigentuemer"] or "",
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
        # #64 – Von/Bis-Datum für Mietzeitraum
        von_v   = lf("Von (JJJJ-MM-TT im Jahr)",       r.get("von_datum", f"{jahr}-01-01") or f"{jahr}-01-01")
        bis_v   = lf("Bis (JJJJ-MM-TT im Jahr)",       r.get("bis_datum", f"{jahr}-12-31") or f"{jahr}-12-31")
        pers_v  = lf("Personen",                        r.get("personen", 1))
        spuel_v = lf("Spuelmaschinen (je 1 Pkt)",       r.get("spuelmaschinen", 0))
        wasch_v = lf("Waschmaschinen (je 1 Pkt)",       r.get("waschmaschinen", 1))
        trock_v = lf("Trockner Wasserkuehlung (1 Pkt)", r.get("trockner_wasserkuehlung", 0))
        mon_v   = lf("Monate (auto aus Von/Bis)",       r.get("monate", 12))
        # Auto-Berechnung Monate aus Von/Bis
        def _auto_monate(*_):
            mon = WasserkostenPage._calc_monate_im_jahr(
                von_v.get().strip(), bis_v.get().strip(), jahr)
            if mon > 0:
                mon_v.set(str(mon))
        von_v.trace_add("write", _auto_monate)
        bis_v.trace_add("write", _auto_monate)

        def _save():
            wohn = wohn_v.get().strip()
            if not wohn:
                messagebox.showwarning("Pflichtfeld", "Wohnung ist erforderlich.", parent=win)
                return
            von_str = von_v.get().strip() or None
            bis_str = bis_v.get().strip() or None
            monate = max(0.0, min(12.0, self._flt(mon_v.get()) or 12.0))
            conn = get_db()
            if row:
                conn.execute(
                    "UPDATE wasserkosten_wohnungsdaten SET "
                    "wohnung_bezeichnung=?, eigentuemer=?, von_datum=?, bis_datum=?, "
                    "personen=?, spuelmaschinen=?, waschmaschinen=?, "
                    "trockner_wasserkuehlung=?, monate=? WHERE id=?",
                    (wohn, eig_v.get().strip(), von_str, bis_str,
                     self._int(pers_v.get()), self._int(spuel_v.get()),
                     self._int(wasch_v.get()), self._int(trock_v.get()),
                     monate, row["id"]))
            else:
                conn.execute(
                    "INSERT INTO wasserkosten_wohnungsdaten "
                    "(jahr, wohnung_bezeichnung, eigentuemer, von_datum, bis_datum, "
                    "personen, spuelmaschinen, waschmaschinen, "
                    "trockner_wasserkuehlung, monate) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (jahr, wohn, eig_v.get().strip(), von_str, bis_str,
                     self._int(pers_v.get()), self._int(spuel_v.get()),
                     self._int(wasch_v.get()), self._int(trock_v.get()),
                     monate))
            conn.commit()
            conn.close()
            win.destroy()
            self._load_punkte()

        make_btn(br, "Speichern", _save, color=SUCCESS).pack(side="right")

    @staticmethod
    def _calc_monate_im_jahr(einzug: str, auszug: str, jahr: int) -> float:
        """#64 – Berechnet anteilige Monate eines Mieters im Abrechnungsjahr (Pro-Rata)."""
        from datetime import date as _date
        j_von = _date(jahr, 1, 1)
        j_bis = _date(jahr, 12, 31)
        tage_jahr = 366 if (jahr % 4 == 0 and (jahr % 100 != 0 or jahr % 400 == 0)) else 365
        try:
            von_d = max(_date.fromisoformat(einzug), j_von) if einzug else j_von
        except (ValueError, TypeError):
            von_d = j_von
        try:
            bis_d = min(_date.fromisoformat(auszug), j_bis) if auszug else j_bis
        except (ValueError, TypeError):
            bis_d = j_bis
        if bis_d < von_d:
            return 0.0
        tage = (bis_d - von_d).days + 1
        return round(tage / tage_jahr * 12, 2)

    def _import_wohnungen(self):
        """#64 – Übernimmt Wohnungen aus Stammdaten mit Mietzeitraum-Berücksichtigung."""
        from datetime import date as _date
        jahr = self._jahr_int()
        if not jahr:
            return
        j_von = _date(jahr, 1, 1)
        j_bis = _date(jahr, 12, 31)
        conn = get_db()
        try:
            wohnungen_db = conn.execute(
                "SELECT w.id, w.bezeichnung, COALESCE(e.name,'') AS eig "
                "FROM wohnungen w "
                "LEFT JOIN eigentuemer e ON w.eigentuemer_id=e.id "
                "WHERE w.aktiv=1 ORDER BY w.bezeichnung"
            ).fetchall()
            if not wohnungen_db:
                messagebox.showinfo("Keine Wohnungen",
                    "Keine aktiven Wohnungen in den Stammdaten.", parent=self)
                return
            added = updated = 0
            for w in wohnungen_db:
                # Alle Mieter laden, die im Abrechnungsjahr in dieser Wohnung waren
                mieter_rows = conn.execute(
                    "SELECT m.vorname, m.name, m.einzug, m.auszug, "
                    "  COALESCE(m.personen,1) AS personen, "
                    "  COALESCE(m.spuelmaschinen,0) AS spuel, "
                    "  COALESCE(m.waschmaschinen,1) AS wasch, "
                    "  COALESCE(m.trockner_wasserkuehlung,0) AS trockner "
                    "FROM mieter m "
                    "WHERE m.wohnung_id=? "
                    "  AND m.einzug <= ? "
                    "  AND (m.auszug IS NULL OR m.auszug='' OR m.auszug >= ?) "
                    "ORDER BY m.einzug",
                    (w["id"], j_bis.isoformat(), j_von.isoformat())
                ).fetchall()

                if mieter_rows:
                    for m in mieter_rows:
                        monate = self._calc_monate_im_jahr(
                            m["einzug"], m["auszug"] or None, jahr)
                        if monate <= 0:
                            continue
                        mname = f"{m['vorname'] or ''} {m['name']}".strip()
                        # Von/Bis im Jahr berechnen
                        try:
                            von_d = max(_date.fromisoformat(m["einzug"]), j_von)
                        except (ValueError, TypeError):
                            von_d = j_von
                        try:
                            bis_d = min(_date.fromisoformat(m["auszug"]), j_bis) \
                                if m["auszug"] else j_bis
                        except (ValueError, TypeError):
                            bis_d = j_bis
                        # Eindeutigkeitsschlüssel: (jahr, bez, von_datum)
                        existing = conn.execute(
                            "SELECT id FROM wasserkosten_wohnungsdaten "
                            "WHERE jahr=? AND wohnung_bezeichnung=? AND von_datum=?",
                            (jahr, w["bezeichnung"], von_d.isoformat())
                        ).fetchone()
                        if existing:
                            conn.execute(
                                "UPDATE wasserkosten_wohnungsdaten SET "
                                "eigentuemer=?, personen=?, spuelmaschinen=?, "
                                "waschmaschinen=?, trockner_wasserkuehlung=?, "
                                "bis_datum=?, monate=?, bemerkung=? WHERE id=?",
                                (w["eig"], m["personen"], m["spuel"], m["wasch"], m["trockner"],
                                 bis_d.isoformat(), monate, mname, existing["id"]))
                            updated += 1
                        else:
                            conn.execute(
                                "INSERT INTO wasserkosten_wohnungsdaten "
                                "(jahr, wohnung_bezeichnung, eigentuemer, von_datum, bis_datum, "
                                "personen, spuelmaschinen, waschmaschinen, "
                                "trockner_wasserkuehlung, monate, bemerkung) "
                                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                                (jahr, w["bezeichnung"], w["eig"],
                                 von_d.isoformat(), bis_d.isoformat(),
                                 m["personen"], m["spuel"], m["wasch"], m["trockner"],
                                 monate, mname))
                            added += 1
                else:
                    # Keine Mieter → Eigentümer als Leerstand, 12 Monate
                    existing = conn.execute(
                        "SELECT id FROM wasserkosten_wohnungsdaten "
                        "WHERE jahr=? AND wohnung_bezeichnung=? AND "
                        "(von_datum IS NULL OR von_datum=?)",
                        (jahr, w["bezeichnung"], j_von.isoformat())
                    ).fetchone()
                    if existing:
                        conn.execute(
                            "UPDATE wasserkosten_wohnungsdaten SET "
                            "eigentuemer=?, monate=12 WHERE id=?",
                            (w["eig"], existing["id"]))
                        updated += 1
                    else:
                        conn.execute(
                            "INSERT INTO wasserkosten_wohnungsdaten "
                            "(jahr, wohnung_bezeichnung, eigentuemer, von_datum, bis_datum, "
                            "personen, spuelmaschinen, waschmaschinen, "
                            "trockner_wasserkuehlung, monate) VALUES (?,?,?,?,?,1,0,1,0,12)",
                            (jahr, w["bezeichnung"], w["eig"],
                             j_von.isoformat(), j_bis.isoformat()))
                        added += 1
            conn.commit()
        finally:
            conn.close()
        teile = []
        if added:
            teile.append(f"{added} neu hinzugefügt")
        if updated:
            teile.append(f"{updated} aktualisiert")
        if teile:
            messagebox.showinfo("Aus Stamm übernommen",
                ", ".join(teile) + ".\nBei Mieterwechsel wurden separate Zeilen angelegt.",
                parent=self)
        else:
            messagebox.showinfo("Keine Änderungen",
                "Alle Einträge bereits aktuell.", parent=self)
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
            self.after(0, lambda i=info: self._api_status.winfo_exists() and self._api_status.config(text=i, fg=SUCCESS))
        except Exception as ex:
            info = f"❌ Ollama nicht erreichbar:\n{ex}"
            self.after(0, lambda i=info: self._api_status.winfo_exists() and self._api_status.config(text=i, fg=DANGER))

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
        import time as _time
        _t0 = _time.time()
        key = cfg.get("anthropic_api_key", "").strip()
        if not key:
            self.after(0, lambda: self._append_chat("error_msg",
                "❌ Kein Anthropic API-Key. Bitte in Einstellungen → KI-Administration eintragen."))
            return
        # KI-Training laden (#46)
        _feld_hinweise, _system_zusatz = _lade_ki_training("KI-Assistent")
        system_text = self._SCHEMA_KONTEXT
        if _system_zusatz:
            system_text = system_text + "\n\n" + _system_zusatz
        try:
            modell = modell_override or cfg.get("ki_modell", "claude-opus-4-6")
            payload = json.dumps({
                "model": modell,
                "max_tokens": 1024,
                "system": system_text,
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
            # KI-Protokoll (#45)
            eingabe_kurz = messages[-1]["content"][:200] if messages else ""
            ki_log("KI-Assistent", "Chat", eingabe_kurz, antwort[:300],
                   modell, "anthropic", int((_time.time() - _t0) * 1000))
            if "SQL:" in antwort:
                self.after(0, lambda a=antwort: self._handle_sql_response(a))
            else:
                self.after(0, lambda a=antwort: self._append_chat("ki_bubble", f"🤖 Claude: {a}"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            ki_log("KI-Assistent", "Fehler", "", "", modell_override or "", "anthropic",
                   int((_time.time() - _t0) * 1000), body[:200])
            self.after(0, lambda b=body: self._append_chat("error_msg", f"❌ API-Fehler: {b[:200]}"))
        except Exception as ex:
            ki_log("KI-Assistent", "Fehler", "", "", modell_override or "", "anthropic",
                   int((_time.time() - _t0) * 1000), str(ex))
            self.after(0, lambda x=str(ex): self._append_chat("error_msg", f"❌ Fehler: {x}"))

    def _ollama_call_thread(self, messages, cfg, modell_override=None):
        """API-Call an lokales Ollama (POST /api/chat)."""
        import time as _time
        _t0 = _time.time()
        base_url = cfg.get("ollama_url", "http://localhost:11434").strip().rstrip("/")
        modell   = modell_override or cfg.get("ollama_modell", "llama3.2").strip() or "llama3.2"
        # KI-Training laden (#46)
        _feld_hinweise, _system_zusatz = _lade_ki_training("KI-Assistent")
        system_text = self._SCHEMA_KONTEXT
        if _system_zusatz:
            system_text = system_text + "\n\n" + _system_zusatz
        # System-Nachricht als erstes Element in messages-Liste (Ollama-Format)
        ollama_msgs = [{"role": "system", "content": system_text}] + messages
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
            # KI-Protokoll (#45)
            eingabe_kurz = messages[-1]["content"][:200] if messages else ""
            ki_log("KI-Assistent", "Chat", eingabe_kurz, antwort[:300],
                   modell, "ollama", int((_time.time() - _t0) * 1000))
            label = f"🤖 {modell}"
            if "SQL:" in antwort:
                self.after(0, lambda a=antwort: self._handle_sql_response(a))
            else:
                self.after(0, lambda a=antwort, l=label:
                           self._append_chat("ki_bubble", f"{l}: {a}"))
        except urllib.error.URLError as e:
            ki_log("KI-Assistent", "Fehler", "", "", modell, "ollama",
                   int((_time.time() - _t0) * 1000), str(e))
            self.after(0, lambda x=str(e): self._append_chat("error_msg",
                f"❌ Ollama nicht erreichbar ({base_url}):\n{x}\n"
                "Bitte sicherstellen dass Ollama läuft: ollama serve"))
        except Exception as ex:
            ki_log("KI-Assistent", "Fehler", "", "", modell, "ollama",
                   int((_time.time() - _t0) * 1000), str(ex))
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


class KiProtokollPage(tk.Frame):
    """KI-Protokoll und Training – nur für Admin/Superadmin (#44)."""

    def __init__(self, parent):
        super().__init__(parent, bg=BG_CARD)
        self._build()

    def _build(self):
        section_header(self, "KI-Protokoll & Training", None, None)

        if not hat_recht("KI-Administration", "lesen"):
            tk.Label(self, text="🔒  Kein Zugriff.\nNur für Admin und Super-Admin.",
                     bg=BG_CARD, fg=DANGER, font=FONT_BODY,
                     justify="center").pack(expand=True)
            return

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=16, pady=(8, 16))

        # Tab 1: Protokoll
        t1 = tk.Frame(nb, bg=BG_CARD)
        nb.add(t1, text="📋 KI-Protokoll")
        self._build_protokoll_tab(t1)

        # Tab 2: Training (nur schreiben-Recht)
        t2 = tk.Frame(nb, bg=BG_CARD)
        nb.add(t2, text="🎓 KI-Training")
        self._build_training_tab(t2)

    def _build_protokoll_tab(self, parent):
        # Filter-Zeile
        flt = tk.Frame(parent, bg=BG_CARD)
        flt.pack(fill="x", padx=16, pady=(10, 4))
        tk.Label(flt, text="Bereich:", bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(side="left")
        self._bereich_var = tk.StringVar(value="Alle")
        bereiche = ["Alle", "Beleg-Analyse", "Ista-Extraktion", "KI-Assistent"]
        ttk.Combobox(flt, textvariable=self._bereich_var, values=bereiche,
                     state="readonly", width=18, font=FONT_SMALL).pack(side="left", padx=(4, 16))
        make_btn(flt, "🔄 Laden", self._load_protokoll, color=ACCENT2).pack(side="left")
        make_btn(flt, "🗑 Protokoll leeren", self._protokoll_leeren,
                 color=DANGER).pack(side="right")

        cols = ("ID", "Zeitpunkt", "Bereich", "Aktion", "Modell", "Eingabe (Auszug)", "Ergebnis (Auszug)", "Fehler")
        f, self._tree_log = make_table(parent, cols, height=14)
        f.pack(fill="both", expand=True, padx=16, pady=4)
        for c, w in zip(cols, [0, 140, 100, 100, 140, 200, 200, 120]):
            self._tree_log.heading(c, text=c)
            self._tree_log.column(c, width=w, anchor="w")
        # ID-Spalte unsichtbar (#53)
        self._tree_log.column("ID", width=0, minwidth=0, stretch=False)

        # #53 Doppelklick für Detail-Ansicht
        self._tree_log.bind("<Double-1>", self._show_detail)

        # Buttons unter dem Tree
        btn_proto = tk.Frame(parent, bg=BG_CARD)
        btn_proto.pack(fill="x", padx=16, pady=(0, 4))
        make_btn(btn_proto, "🔍 Details anzeigen", self._show_detail,
                 color=BG_INPUT, fg=TEXT).pack(side="left", padx=(0, 6))
        make_btn(btn_proto, "📋 Kopieren", self._copy_detail,
                 color=BG_INPUT, fg=TEXT).pack(side="left", padx=(0, 6))

        self._load_protokoll()

    def _load_protokoll(self):
        for i in self._tree_log.get_children(): self._tree_log.delete(i)
        conn = get_db()
        bereich = self._bereich_var.get()
        if bereich == "Alle":
            rows = conn.execute(
                "SELECT * FROM ki_protokoll ORDER BY zeitpunkt DESC LIMIT 200").fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM ki_protokoll WHERE bereich=? ORDER BY zeitpunkt DESC LIMIT 200",
                (bereich,)).fetchall()
        conn.close()
        for r in rows:
            self._tree_log.insert("", "end", values=(
                r["id"],
                (r["zeitpunkt"] or "")[:16],
                r["bereich"] or "",
                r["aktion"] or "",
                r["modell"] or "",
                (r["eingabe_kurz"] or "")[:60],
                (r["ergebnis_kurz"] or "")[:60],
                r["fehler"] or ""))
        tree_empty_hint(self._tree_log)

    def _protokoll_leeren(self):
        if not hat_recht("KI-Administration", "loeschen"):
            messagebox.showwarning("Berechtigung", "Keine Lösch-Berechtigung.", parent=self)
            return
        if messagebox.askyesno("Protokoll leeren",
                               "Alle KI-Protokoll-Einträge löschen?", parent=self):
            conn = get_db()
            conn.execute("DELETE FROM ki_protokoll")
            conn.commit()
            conn.close()
            self._load_protokoll()

    def _get_selected_protokoll(self):
        """Gibt den vollständigen DB-Row des ausgewählten Protokolleintrags zurück (#53)."""
        sel = self._tree_log.selection()
        if not sel:
            messagebox.showinfo("Hinweis", "Bitte einen Eintrag auswählen.", parent=self)
            return None
        vals = self._tree_log.item(sel[0], "values")
        if not vals:
            return None
        row_id = vals[0]
        try:
            conn = get_db()
            r = conn.execute("SELECT * FROM ki_protokoll WHERE id=?", (int(row_id),)).fetchone()
            conn.close()
            return dict(r) if r else None
        except Exception:
            return None

    def _show_detail(self, event=None):
        """#53 – Detail-Ansicht eines KI-Protokolleintrags per Doppelklick oder Button."""
        r = self._get_selected_protokoll()
        if not r:
            return
        # Detail-Dialog
        dlg = tk.Toplevel(self)
        dlg.title(f"KI-Protokoll – {r.get('bereich','')} – {r.get('aktion','')}")
        dlg.geometry("700x550")
        dlg.configure(bg=BG_CARD)
        dlg.grab_set()

        header = tk.Frame(dlg, bg=BG_SIDEBAR, height=40)
        header.pack(fill="x"); header.pack_propagate(False)
        tk.Label(header, text=f"Protokoll #{r['id']}", bg=BG_SIDEBAR, fg=TEXT_WHITE,
                 font=FONT_H3).pack(side="left", padx=14, pady=8)

        body = tk.Frame(dlg, bg=BG_CARD)
        body.pack(fill="both", expand=True, padx=16, pady=8)

        def _row(lbl, val):
            f = tk.Frame(body, bg=BG_CARD); f.pack(fill="x", pady=2)
            tk.Label(f, text=lbl, bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL,
                     width=14, anchor="e").pack(side="left")
            tk.Label(f, text=str(val or "–"), bg=BG_CARD, fg=TEXT, font=FONT_BODY,
                     anchor="w", wraplength=520).pack(side="left", padx=(6,0), fill="x", expand=True)

        _row("Zeitpunkt:", r.get("zeitpunkt",""))
        _row("Bereich:", r.get("bereich",""))
        _row("Aktion:", r.get("aktion",""))
        _row("Modell:", r.get("modell",""))
        _row("Anbieter:", r.get("anbieter",""))
        _row("Dauer (ms):", r.get("dauer_ms",""))
        _row("Fehler:", r.get("fehler",""))

        # Eingabe (vollständig)
        tk.Label(body, text="Eingabe:", bg=BG_CARD, fg=TEXT_LIGHT,
                 font=FONT_SMALL).pack(anchor="w", pady=(8,2))
        t_in = tk.Text(body, height=5, font=FONT_BODY, bg=BG_INPUT, fg=TEXT,
                       relief="flat", wrap="word", padx=6, pady=4)
        t_in.pack(fill="x")
        t_in.insert("1.0", r.get("eingabe_kurz","") or "")
        t_in.configure(state="disabled")

        # Ergebnis (vollständig)
        tk.Label(body, text="Ergebnis:", bg=BG_CARD, fg=TEXT_LIGHT,
                 font=FONT_SMALL).pack(anchor="w", pady=(8,2))
        t_out = tk.Text(body, height=8, font=FONT_BODY, bg=BG_INPUT, fg=TEXT,
                        relief="flat", wrap="word", padx=6, pady=4)
        t_out.pack(fill="both", expand=True)
        t_out.insert("1.0", r.get("ergebnis_kurz","") or "")
        t_out.configure(state="disabled")

        # Buttons
        btn_f = tk.Frame(dlg, bg=BG_CARD)
        btn_f.pack(fill="x", padx=16, pady=(4,12))
        make_btn(btn_f, "📋 Alles kopieren",
                 lambda: self._copy_row_to_clipboard(r), color=BG_INPUT, fg=TEXT).pack(side="left", padx=(0,8))
        make_btn(btn_f, "Schließen", dlg.destroy, color=BG_INPUT, fg=TEXT).pack(side="right")

    def _copy_row_to_clipboard(self, r: dict):
        """Kopiert alle Felder eines Protokolleintrags in die Zwischenablage (#53)."""
        text = "\n".join(f"{k}: {v}" for k, v in r.items() if v)
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("Kopiert", "Protokolleintrag wurde in die Zwischenablage kopiert.", parent=self)

    def _copy_detail(self):
        """#53 – Kopiert den ausgewählten Eintrag in die Zwischenablage."""
        r = self._get_selected_protokoll()
        if r:
            self._copy_row_to_clipboard(r)

    def _build_training_tab(self, parent):
        if not hat_recht("KI-Administration", "schreiben"):
            tk.Label(parent, text="🔒  Schreibzugriff auf KI-Training benötigt.",
                     bg=BG_CARD, fg=DANGER, font=FONT_BODY).pack(expand=True)
            return

        tk.Label(parent,
                 text="Hier können Sie der KI für jeden Bereich zusätzliche Hinweise und Beispiele geben.\n"
                      "Diese werden automatisch in alle KI-Anfragen des jeweiligen Bereichs eingebettet.\n"
                      "  • KI-Assistent → Chat-Assistent auf der KI-Seite\n"
                      "  • Beleg-Analyse → KI-Analyse von Rechnungen unter Buchungen\n"
                      "  • Ista-Extraktion → KI-Auslesen von Ista-Heizkostenabrechnungen",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL,
                 justify="left").pack(anchor="w", padx=16, pady=(10, 4))

        # Bereich auswählen
        sel_f = tk.Frame(parent, bg=BG_CARD)
        sel_f.pack(fill="x", padx=16, pady=4)
        tk.Label(sel_f, text="Bereich:", bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(side="left")
        self._train_bereich_var = tk.StringVar(value="KI-Assistent")
        train_bereiche = ["KI-Assistent", "Beleg-Analyse", "Ista-Extraktion"]
        cb = ttk.Combobox(sel_f, textvariable=self._train_bereich_var,
                          values=train_bereiche, state="readonly", width=20, font=FONT_SMALL)
        cb.pack(side="left", padx=(4, 16))
        cb.bind("<<ComboboxSelected>>", self._load_training)
        make_btn(sel_f, "📥 Laden", self._load_training, color=BG_INPUT, fg=TEXT).pack(side="left")
        make_btn(sel_f, "💾 Speichern", self._save_training, color=SUCCESS).pack(side="left", padx=(8, 0))

        tk.Label(parent, text="Feld-Hinweise (was soll die KI für diesen Bereich beachten?):",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w", padx=16, pady=(10, 2))
        self._train_feld_text = tk.Text(parent, height=6, font=FONT_BODY,
                                        bg=BG_INPUT, fg=TEXT, relief="flat",
                                        wrap="word", padx=8, pady=6)
        self._train_feld_text.pack(fill="x", padx=16, pady=(0, 8))

        tk.Label(parent, text="System-Zusatz (wird an den KI-System-Prompt angehängt):",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w", padx=16, pady=(4, 2))
        self._train_sys_text = tk.Text(parent, height=8, font=FONT_BODY,
                                       bg=BG_INPUT, fg=TEXT, relief="flat",
                                       wrap="word", padx=8, pady=6)
        self._train_sys_text.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        self._load_training()

    def _load_training(self, event=None):
        bereich = self._train_bereich_var.get()
        conn = get_db()
        r = conn.execute("SELECT * FROM ki_training WHERE bereich=?", (bereich,)).fetchone()
        conn.close()
        self._train_feld_text.delete("1.0", "end")
        self._train_sys_text.delete("1.0", "end")
        if r:
            self._train_feld_text.insert("1.0", r["feld_hinweise"] or "")
            self._train_sys_text.insert("1.0", r["system_zusatz"] or "")

    def _save_training(self):
        bereich = self._train_bereich_var.get()
        feld = self._train_feld_text.get("1.0", "end").strip()
        sys_z = self._train_sys_text.get("1.0", "end").strip()
        conn = get_db()
        conn.execute(
            "INSERT OR REPLACE INTO ki_training "
            "(bereich, feld_hinweise, system_zusatz, geaendert_am, geaendert_von) "
            "VALUES (?,?,?,CURRENT_TIMESTAMP,?)",
            (bereich, feld, sys_z, _CURRENT_USER["id"] if _CURRENT_USER else None))
        conn.commit()
        conn.close()
        messagebox.showinfo("Gespeichert", f"KI-Training für '{bereich}' gespeichert.", parent=self)


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

        # ── Tab 4: Matching (#74) ─────────────────────────────────────────────
        t_match_outer, t_match = self._scrollable_tab(nb)
        nb.add(t_match_outer, text="🔗 Matching")
        self._section(t_match, "Auto-Matching Schwellwerte")
        tk.Label(t_match,
                 text="Legt fest, ab welchem Confidence Score (0–100) eine Zuordnung\n"
                      "automatisch gebucht wird bzw. als Vorschlag angezeigt wird.",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL, justify="left"
                 ).pack(anchor="w", padx=20, pady=(0, 8))

        self._path_field(t_match,
                         "Auto-Buchung ab Score (Standard: 80)",
                         "matching_schwelle_auto", is_path=False)
        self._path_field(t_match,
                         "Vorschlag anzeigen ab Score (Standard: 60)",
                         "matching_schwelle_vorschlag", is_path=False)

        self._section(t_match, "Matching-Toleranzen")
        tk.Label(t_match,
                 text="Betrag-Toleranz: bis zu welcher prozentualen Abweichung noch Punkte vergeben werden.\n"
                      "Datum-Fenster: Buchungsdatum vs. Fälligkeitsdatum in Tagen.\n\n"
                      "Diese Werte sind derzeit fix (±1 % Betrag, ±7 Tage Datum → Vollpunkte).\n"
                      "Eine GUI-Konfiguration folgt in einem späteren Update.",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL, justify="left"
                 ).pack(anchor="w", padx=20, pady=(0, 8))

        self._section(t_match, "Matching-Log (Audit Trail)")
        tk.Label(t_match,
                 text="Jede automatische und manuell bestätigte Zuordnung wird in der\n"
                      "Tabelle kontoauszug_match_log protokolliert (GoB § 239 HGB).",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL, justify="left"
                 ).pack(anchor="w", padx=20, pady=(0, 4))
        btn_log_row = tk.Frame(t_match, bg=BG_CARD)
        btn_log_row.pack(fill="x", padx=20, pady=(0, 12))
        make_btn(btn_log_row, "📋 Matching-Log anzeigen", self._show_match_log,
                 color=ACCENT2).pack(side="left")

        # ── Tab 5: Buchungsregeln (#84) ───────────────────────────────────────
        t_regeln_outer, t_regeln = self._scrollable_tab(nb)
        nb.add(t_regeln_outer, text="⚙ Buchungsregeln")
        self._build_regeln_tab(t_regeln)

        # ── Tab 6: Kostenarten (#85) ──────────────────────────────────────────
        t_kat_outer, t_kat = self._scrollable_tab(nb)
        nb.add(t_kat_outer, text="📋 Kostenarten")
        self._build_kostenarten_tab(t_kat)

        # ── Tab 7: KI-Administration (nur für Berechtigte) ────────────────────
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

    # ── Tab: Buchungsregeln (#84) ─────────────────────────────────────────────

    def _build_regeln_tab(self, parent):
        tk.Label(parent,
            text="Automatisch gelernte Zuordnungsregeln — können hier korrigiert oder gelöscht werden",
            bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w", padx=20, pady=(6, 2))
        cols_r = ("Auftraggeber / Empfänger", "Kategorie", "Typ", "Konto", "Treffer", "Korrektur")
        fr, self.tree_r = make_table(parent, cols_r, height=16)
        fr.pack(fill="both", expand=True, padx=20, pady=4)
        for c, w in zip(cols_r, [220, 130, 90, 110, 70, 80]):
            self.tree_r.heading(c, text=c); self.tree_r.column(c, width=w, anchor="w")
        btn_r = tk.Frame(parent, bg=BG_CARD)
        btn_r.pack(fill="x", padx=20, pady=(0, 8))
        make_btn(btn_r, "✏ Korrigieren", self._edit_regel, color=BG_INPUT, fg=TEXT).pack(side="left", padx=(0,6))
        make_btn(btn_r, "🗑 Löschen",    self._delete_regel, color=DANGER).pack(side="left")
        make_btn(btn_r, "🔄 Aktualisieren", self._load_regeln, color=BG_INPUT, fg=TEXT).pack(side="right")
        self._load_regeln()

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
        ttk.Combobox(body, textvariable=kat_var, values=BuchhaltungPage.aktive_kategorien(),
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

    # ── Tab: Kostenarten (#85) ────────────────────────────────────────────────

    def _build_kostenarten_tab(self, parent):
        tk.Label(parent,
            text="WEG-Kostenkategorien verwalten — deaktivierte Kategorien können nicht mehr zugewiesen werden",
            bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w", padx=20, pady=(6, 2))
        cols_k = ("Kategorie", "Oberkategorie", "Umlagefähig", "Schlüssel", "Status", "Verwendungen")
        fk, self.tree_k = make_table(parent, cols_k, height=16)
        fk.pack(fill="both", expand=True, padx=20, pady=4)
        for c, w in zip(cols_k, [180, 180, 100, 140, 80, 100]):
            self.tree_k.heading(c, text=c); self.tree_k.column(c, width=w, anchor="w")
        self.tree_k.tag_configure("deaktiviert", foreground=TEXT_LIGHT)
        btn_k = tk.Frame(parent, bg=BG_CARD)
        btn_k.pack(fill="x", padx=20, pady=(0, 8))
        make_btn(btn_k, "＋ Neue Kategorie", self._new_kostenart, color=ACCENT2).pack(side="left", padx=(0,6))
        make_btn(btn_k, "✏ Bearbeiten", self._edit_kostenart, color=BG_INPUT, fg=TEXT).pack(side="left", padx=(0,6))
        make_btn(btn_k, "🔄 Aktivieren/Deaktivieren", self._toggle_kostenart, color=WARNING, fg=TEXT_WHITE).pack(side="left", padx=(0,6))
        make_btn(btn_k, "🗑 Löschen", self._delete_kostenart, color=DANGER).pack(side="left")
        self._load_kostenarten()

    def _load_kostenarten(self):
        for i in self.tree_k.get_children(): self.tree_k.delete(i)
        conn = get_db()
        deaktiviert = BuchhaltungPage._deaktivierte_kategorien()
        for idx, kat_name in enumerate(BuchhaltungPage.KATEGORIEN):
            meta = BuchhaltungPage.KOSTENARTEN.get(kat_name, {})
            count = conn.execute(
                "SELECT COUNT(*) FROM zahlungen WHERE kategorie=?", (kat_name,)
            ).fetchone()[0]
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

    @staticmethod
    def _umlageschluessel_aus_aufteilungen() -> tuple:
        """Lädt Umlageschlüssel aus aufteilungen-Tabelle (#GH79)."""
        basis_typen = ["MEA", "Wohnfläche", "Verbrauch", "Verbrauch/Wohnfläche",
                       "HeizKV", "Kopfanzahl", "Wasserkosten nach Punkten", "–"]
        try:
            conn = get_db()
            try:
                rows = conn.execute(
                    "SELECT name, typ, beschreibung FROM aufteilungen WHERE aktiv=1 ORDER BY name"
                ).fetchall()
            finally:
                conn.close()
            name_zu_typ: dict = {}
            typ_zu_name: dict = {}
            tooltips: dict = {}
            namen: list = []
            for r in rows:
                name = (r["name"] or "").strip() or r["typ"]
                typ = (r["typ"] or "").strip() or name
                desc = (r["beschreibung"] or "").strip()
                name_zu_typ[name] = typ
                typ_zu_name[typ] = name
                tip = f"Typ: {typ}"
                if desc:
                    tip += f"\n{desc}"
                tooltips[name] = tip
                if name not in namen:
                    namen.append(name)
            for t in basis_typen:
                if t not in typ_zu_name:
                    name_zu_typ[t] = t
                    typ_zu_name[t] = t
                    tooltips[t] = f"Standard-Schlüssel: {t}"
                    if t not in namen:
                        namen.append(t)
            return namen or basis_typen, name_zu_typ, typ_zu_name, tooltips
        except Exception:
            basis_map = {t: t for t in basis_typen}
            return basis_typen, basis_map, basis_map.copy(), {t: f"Standard-Schlüssel: {t}" for t in basis_typen}

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
        ober_vals = sorted(set(m.get("kategorie", "Sonstiges") for m in BuchhaltungPage.KOSTENARTEN.values()))
        ttk.Combobox(body, textvariable=ober_var, values=ober_vals, font=FONT_BODY).pack(fill="x", ipady=4)
        tk.Label(body, text="Umlageschlüssel", bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w", pady=(8,0))
        schluessel_var = tk.StringVar(value="MEA")
        _namen, _name_zu_typ, _typ_zu_name, _tooltips = self._umlageschluessel_aus_aufteilungen()
        schluessel_cb = ttk.Combobox(body, textvariable=schluessel_var,
                     values=_namen, font=FONT_BODY)
        schluessel_cb.pack(fill="x", ipady=4)
        make_tooltip(schluessel_cb, lambda: _tooltips.get(schluessel_var.get(), ""))
        uml_var = tk.BooleanVar(value=False)
        tk.Checkbutton(body, text="Umlagefähig", variable=uml_var, bg=BG_CARD,
                       fg=TEXT, font=FONT_BODY, activebackground=BG_CARD).pack(anchor="w", pady=(8,0))
        def _save():
            name = name_var.get().strip()
            if not name:
                messagebox.showwarning("Pflichtfeld", "Name der Kategorie ist erforderlich.", parent=win)
                return
            if name in BuchhaltungPage.KATEGORIEN:
                messagebox.showwarning("Duplikat", f"Kategorie '{name}' existiert bereits.", parent=win)
                return
            angezeigter_name = schluessel_var.get()
            typ_schluessel = _name_zu_typ.get(angezeigter_name, angezeigter_name)
            BuchhaltungPage.KATEGORIEN.insert(-1, name)
            BuchhaltungPage.KOSTENARTEN[name] = {
                "kategorie": ober_var.get(),
                "umlagefaehig": uml_var.get(),
                "schluessel": typ_schluessel
            }
            cfg = load_config()
            custom = cfg.get("custom_kategorien", [])
            custom.append({"name": name, "kategorie": ober_var.get(),
                          "umlagefaehig": uml_var.get(), "schluessel": typ_schluessel})
            cfg["custom_kategorien"] = custom
            save_config(cfg)
            win.destroy()
            self._load_kostenarten()
        btn_row = tk.Frame(win, bg=BG_CARD)
        btn_row.pack(fill="x", padx=20, pady=(0,12))
        make_btn(btn_row, "Abbrechen", win.destroy, color=BG_INPUT, fg=TEXT).pack(side="right", padx=(6,0))
        make_btn(btn_row, "Speichern", _save, color=ACCENT2).pack(side="right")

    def _edit_kostenart(self):
        """Bestehende Kategorie bearbeiten."""
        sel = self.tree_k.selection()
        if not sel: return
        idx = int(sel[0])
        if idx >= len(BuchhaltungPage.KATEGORIEN): return
        kat_name = BuchhaltungPage.KATEGORIEN[idx]
        meta = BuchhaltungPage.KOSTENARTEN.get(kat_name, {})
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
        ober_vals = sorted(set(m.get("kategorie", "Sonstiges") for m in BuchhaltungPage.KOSTENARTEN.values()))
        ttk.Combobox(body, textvariable=ober_var, values=ober_vals, font=FONT_BODY).pack(fill="x", ipady=4)
        tk.Label(body, text="Umlageschlüssel", bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL).pack(anchor="w", pady=(8,0))
        _namen_e, _name_zu_typ_e, _typ_zu_name_e, _tooltips_e = self._umlageschluessel_aus_aufteilungen()
        gespeicherter_typ = meta.get("schluessel", "MEA")
        anzeige_start = _typ_zu_name_e.get(gespeicherter_typ, gespeicherter_typ)
        schluessel_var = tk.StringVar(value=anzeige_start)
        schluessel_cb_e = ttk.Combobox(body, textvariable=schluessel_var,
                     values=_namen_e, font=FONT_BODY)
        schluessel_cb_e.pack(fill="x", ipady=4)
        make_tooltip(schluessel_cb_e, lambda: _tooltips_e.get(schluessel_var.get(), ""))
        uml = meta.get("umlagefaehig", False)
        uml_var = tk.BooleanVar(value=uml if isinstance(uml, bool) else False)
        tk.Checkbutton(body, text="Umlagefähig", variable=uml_var, bg=BG_CARD,
                       fg=TEXT, font=FONT_BODY, activebackground=BG_CARD).pack(anchor="w", pady=(8,0))
        def _save():
            angezeigter_name = schluessel_var.get()
            typ_schluessel = _name_zu_typ_e.get(angezeigter_name, angezeigter_name)
            BuchhaltungPage.KOSTENARTEN[kat_name] = {
                "kategorie": ober_var.get(),
                "umlagefaehig": uml_var.get(),
                "schluessel": typ_schluessel
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
        if idx >= len(BuchhaltungPage.KATEGORIEN): return
        kat_name = BuchhaltungPage.KATEGORIEN[idx]
        deaktiviert = BuchhaltungPage._deaktivierte_kategorien()
        if kat_name in deaktiviert:
            deaktiviert.discard(kat_name)
        else:
            deaktiviert.add(kat_name)
        BuchhaltungPage._save_deaktivierte(deaktiviert)
        self._load_kostenarten()

    def _delete_kostenart(self):
        """Kategorie löschen (nur wenn nicht in Buchungen verwendet)."""
        sel = self.tree_k.selection()
        if not sel: return
        idx = int(sel[0])
        if idx >= len(BuchhaltungPage.KATEGORIEN): return
        kat_name = BuchhaltungPage.KATEGORIEN[idx]
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
        BuchhaltungPage.KATEGORIEN.remove(kat_name)
        BuchhaltungPage.KOSTENARTEN.pop(kat_name, None)
        cfg = load_config()
        custom = cfg.get("custom_kategorien", [])
        cfg["custom_kategorien"] = [c for c in custom if c.get("name") != kat_name]
        deakt = set(cfg.get("deaktivierte_kategorien", []))
        deakt.discard(kat_name)
        cfg["deaktivierte_kategorien"] = sorted(deakt)
        save_config(cfg)
        self._load_kostenarten()

    # ── Tab: KI-Administration ────────────────────────────────────────────────

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
        """#79 Backup v2: ZIP-Archiv mit DB + einstellungen.json + SHA256-Metadaten."""
        import hashlib, zipfile, json as _json
        backup_ordner = self._vars.get("pfad_backup", tk.StringVar()).get().strip()
        if not backup_ordner:
            backup_ordner = str(Path.home())
            messagebox.showinfo("Backup-Ordner",
                "Kein Backup-Ordner konfiguriert. Backup wird im Home-Verzeichnis gespeichert.",
                parent=self)

        db_path = Path(get_db_path())
        einst_path = CONFIG_PATH  # Path-Objekt

        def sha256_of(path):
            h = hashlib.sha256()
            try:
                with open(path, "rb") as f:
                    for chunk in iter(lambda: f.read(65536), b""):
                        h.update(chunk)
                return h.hexdigest()
            except Exception:
                return None

        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_name = f"hausverwaltung_backup_{ts}.zip"
            zip_ziel = os.path.join(backup_ordner, zip_name)

            meta = {
                "erstellt": datetime.now().isoformat(),
                "app_version": APP_VERSION,
                "dateien": {}
            }

            with zipfile.ZipFile(zip_ziel, "w", zipfile.ZIP_DEFLATED) as zf:
                # Datenbank
                zf.write(str(db_path), arcname="hausverwaltung.db")
                meta["dateien"]["hausverwaltung.db"] = {
                    "sha256": sha256_of(db_path),
                    "groesse": db_path.stat().st_size
                }
                # Einstellungen (optional – kann fehlen)
                if einst_path.exists():
                    zf.write(str(einst_path), arcname="einstellungen.json")
                    meta["dateien"]["einstellungen.json"] = {
                        "sha256": sha256_of(einst_path),
                        "groesse": einst_path.stat().st_size
                    }
                # SHA256-Manifest
                zf.writestr("backup_meta.json", _json.dumps(meta, ensure_ascii=False, indent=2))

            # #80 – Timestamp in einstellungen.json speichern (für Dashboard-KPI)
            try:
                cfg = load_config()
                cfg["letztes_backup"] = datetime.now().isoformat()
                save_config(cfg)
            except Exception:
                pass

            messagebox.showinfo("Backup erstellt",
                f"ZIP-Backup gespeichert:\n{zip_ziel}\n\n"
                f"Enthält: {', '.join(meta['dateien'].keys())} + backup_meta.json",
                parent=self)
        except Exception as exc:
            messagebox.showerror("Backup-Fehler",
                f"Backup konnte nicht erstellt werden:\n{exc}", parent=self)

    def _db_restore(self):
        """#79 Wiederherstellen: unterstützt sowohl .zip (v2) als auch .db (v1)."""
        import shutil, hashlib, zipfile, json as _json

        if not messagebox.askyesno(
            "⚠ Warnung",
            "Die aktuelle Datenbank wird durch die Backup-Datei ersetzt!\n"
            "Alle nicht gesicherten Änderungen gehen verloren.\n\n"
            "Fortfahren?", icon="warning", parent=self):
            return

        quelle = filedialog.askopenfilename(
            parent=self, title="Backup-Datei wählen",
            filetypes=[("Backup-Archiv", "*.zip *.db"), ("ZIP-Backup (v2)", "*.zip"),
                       ("Datenbank-Backup (v1)", "*.db"), ("Alle Dateien", "*.*")])
        if not quelle:
            return

        db_path = Path(get_db_path())

        # Eigenes Sicherheits-Backup der aktuellen DB
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            auto_backup = str(db_path) + f".vor_restore_{ts}.bak"
            shutil.copy2(str(db_path), auto_backup)
        except Exception:
            auto_backup = None

        try:
            quelle_lower = quelle.lower()
            if quelle_lower.endswith(".zip"):
                # ── ZIP v2 ──────────────────────────────────────────────────
                with zipfile.ZipFile(quelle, "r") as zf:
                    namen = zf.namelist()
                    if "hausverwaltung.db" not in namen:
                        messagebox.showerror("Ungültiges Backup",
                            "Die ZIP-Datei enthält keine hausverwaltung.db.", parent=self)
                        return

                    # SHA256 prüfen falls Manifest vorhanden
                    pruef_info = ""
                    if "backup_meta.json" in namen:
                        meta_raw = zf.read("backup_meta.json").decode("utf-8")
                        meta = _json.loads(meta_raw)
                        db_data = zf.read("hausverwaltung.db")
                        ist_hash = hashlib.sha256(db_data).hexdigest()
                        soll_hash = meta.get("dateien", {}).get("hausverwaltung.db", {}).get("sha256")
                        if soll_hash and ist_hash != soll_hash:
                            messagebox.showerror("Integritätsfehler",
                                "SHA256-Prüfsumme stimmt nicht überein!\n"
                                "Das Backup könnte beschädigt sein.", parent=self)
                            return
                        erstellt = meta.get("erstellt", "unbekannt")
                        version = meta.get("app_version", "?")
                        pruef_info = f"\nBackup vom: {erstellt}\nApp-Version: v{version}\n✓ SHA256-Prüfsumme OK"

                    # Dateien extrahieren
                    zf.extract("hausverwaltung.db", path=str(db_path.parent))
                    # Extrahierte Datei an den richtigen Ort bewegen
                    extracted = db_path.parent / "hausverwaltung.db"
                    if extracted != db_path:
                        shutil.move(str(extracted), str(db_path))

                    # einstellungen.json wiederherstellen (optional)
                    if "einstellungen.json" in namen:
                        zf.extract("einstellungen.json", path=str(CONFIG_PATH.parent))
                        extracted_einst = CONFIG_PATH.parent / "einstellungen.json"
                        if extracted_einst != CONFIG_PATH:
                            shutil.move(str(extracted_einst), str(CONFIG_PATH))

                info = f"Datenbank erfolgreich wiederhergestellt aus:\n{quelle}{pruef_info}"
            else:
                # ── .db v1 (Rückwärtskompatibilität) ────────────────────────
                shutil.copy2(quelle, str(db_path))
                info = f"Datenbank erfolgreich wiederhergestellt aus:\n{quelle}"

            if auto_backup:
                info += f"\n\nSicherheits-Backup der alten Datenbank:\n{auto_backup}"
            messagebox.showinfo("Wiederhergestellt", info, parent=self)

        except Exception as exc:
            messagebox.showerror("Fehler",
                f"Wiederherstellung fehlgeschlagen:\n{exc}", parent=self)

    def _show_match_log(self):
        """#71 – Matching-Log (kontoauszug_match_log) in einem Popup anzeigen."""
        win = tk.Toplevel(self)
        win.title("Matching-Log (Audit Trail)")
        win.geometry("960x500")
        win.configure(bg=BG_CARD)
        win.grab_set()
        tk.Label(win, text="Matching-Log – GoB Audit Trail (kontoauszug_match_log)",
                 bg=BG_CARD, fg=TEXT, font=FONT_H2).pack(padx=20, pady=(14, 4), anchor="w")
        cols = ("ID", "KA-ID", "Rg-ID", "Score", "Methode", "Erstellt", "Bestätigt", "Abgelehnt")
        f, tree = make_table(win, cols, height=18)
        f.pack(fill="both", expand=True, padx=20, pady=8)
        for c, w in zip(cols, [50, 60, 60, 70, 140, 140, 140, 80]):
            tree.heading(c, text=c)
            tree.column(c, width=w, anchor="w")
        tree.column("Score", anchor="e")
        conn = get_db()
        try:
            for r in conn.execute(
                "SELECT id, kontoauszug_id, rechnung_id, score, methode, "
                "erstellt_am, bestaetigt_am, abgelehnt "
                "FROM kontoauszug_match_log ORDER BY id DESC LIMIT 500"
            ).fetchall():
                tree.insert("", "end", values=(
                    r[0], r[1], r[2] or "–", f"{r[3]:.0f}" if r[3] else "–",
                    r[4] or "–", (r[5] or "")[:16], (r[6] or "–")[:16],
                    "Ja" if r[7] else "Nein"))
        finally:
            conn.close()
        make_btn(win, "Schließen", win.destroy, color=ACCENT2).pack(pady=(0, 14))

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
            self._aktiv_var = tk.IntVar(value=int(r["aktiv"] if "aktiv" in r.keys() else 1))
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
                "Einstellungen", "KI-Assistent", "KI-Administration", "KI-Protokoll", "Ista-Wärme"]

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
        # Header – zwei Buttons: PDF-Import und manuelle Erfassung (#55)
        hdr = tk.Frame(self, bg=BG_CARD)
        hdr.pack(fill="x", padx=20, pady=(18, 6))
        tk.Label(hdr, text="🔥 Ista-Wärmeabrechnung",
                 bg=BG_CARD, fg=TEXT, font=FONT_H2).pack(side="left")
        make_btn(hdr, "✏️ Manuell erfassen", self._manuell_erfassen_komplett).pack(side="right", padx=(6, 0))
        make_btn(hdr, "📥 Ista-PDF importieren", self._import_pdf).pack(side="right")
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=20)

        # Info-Banner
        info = tk.Frame(self, bg="#EBF5FB", bd=0)
        info.pack(fill="x", padx=20, pady=(8, 4))
        tk.Label(info,
                 text="ℹ  Ista liefert Heizkostenabrechnungen als PDF. "
                      "Importieren Sie das PDF oder erfassen Sie die Werte manuell. "
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
                        "konto_typ, status, eigentuemer_id, abrechnungsrelevant, abrechnungsjahr) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (
                            abr["abrechnungszeitraum_bis"] or f"{abr['abrechnungsjahr']}-12-31",
                            -abs(pos["heizkosten_gesamt"]),
                            "Ausgabe", "Heizung",
                            f"Ista Heizkosten {abr['abrechnungsjahr']} – {pos['ista_einheit_bezeichnung'] or pos['ista_einheit_nr'] or ''}",
                            "Wohngeldkonto", "Geprüft",
                            None, 1, abr["abrechnungsjahr"]
                        )
                    )
                    conn2.commit()
                    erstellt += 1

                # Warmwasser-Buchung
                if (pos["warmwasserkosten_gesamt"] or 0) > 0:
                    conn2.execute(
                        "INSERT INTO zahlungen (datum, betrag, typ, kategorie, beschreibung, "
                        "konto_typ, status, eigentuemer_id, abrechnungsrelevant, abrechnungsjahr) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (
                            abr["abrechnungszeitraum_bis"] or f"{abr['abrechnungsjahr']}-12-31",
                            -abs(pos["warmwasserkosten_gesamt"]),
                            "Ausgabe", "Warmwasser",
                            f"Ista Warmwasserkosten {abr['abrechnungsjahr']} – {pos['ista_einheit_bezeichnung'] or pos['ista_einheit_nr'] or ''}",
                            "Wohngeldkonto", "Geprüft",
                            None, 1, abr["abrechnungsjahr"]
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

                # #52 Wenn kein/wenig Text → OCR via KI-Vision (Bild senden)
                ist_bild_pdf = len(pdf_text.strip()) < 100

                if ist_bild_pdf:
                    _log("⚠ Kein/wenig Text extrahiert – PDF evtl. gescannt (Bild-PDF)")
                    _log("  → Versuche KI-Vision-Analyse (OCR per KI) …")
                else:
                    _log(f"  ✓ Textextraktion OK ({len(pdf_text.strip())} Zeichen)")

                _update_status("🤖 KI analysiert Ista-Daten …")
                _log("\n🤖 Starte KI-Analyse …")

                cfg = load_config()
                ki_daten = None

                if ist_bild_pdf:
                    # OCR via KI-Vision: PDF-Seiten als Bilder senden (#52)
                    ki_daten = self._ki_extrahieren_bild(pdf_pfad, cfg, _log)
                elif pdf_text.strip():
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

    def _ki_extrahieren_bild(self, pdf_pfad: str, cfg: dict, _log) -> dict:
        """#52 – OCR via KI-Vision: Sendet PDF-Seiten als Bilder an die KI-API."""
        import base64, time as _time, json as _json
        _t0 = _time.time()
        _feld_hinweise, _system_zusatz = _lade_ki_training("Ista-Extraktion")

        # PDF-Seiten zu Bildern konvertieren (benötigt pypdf ≥ 4.x)
        bilder_b64 = []
        try:
            import pypdf
            with open(pdf_pfad, "rb") as fh:
                pdf_bytes = fh.read()
            # Sende das gesamte PDF als Base64 (Anthropic unterstützt PDF-Analyse)
            bilder_b64 = [base64.standard_b64encode(pdf_bytes).decode("ascii")]
            _log(f"   PDF: {len(pdf_bytes)} Bytes als Bild-Eingabe vorbereitet")
        except Exception as ex:
            _log(f"   ⚠ PDF konnte nicht für Bildanalyse vorbereitet werden: {ex}")
            return None

        if not bilder_b64:
            _log("   ⚠ Keine Bilddaten – KI-Vision-Analyse abgebrochen")
            return None

        prompt = (
            "Analysiere diese Ista-Heizkostenabrechnung (als PDF/Bild). "
            "Führe zunächst OCR durch und extrahiere dann alle Daten als JSON.\n"
            "Antworte NUR mit einem JSON-Objekt.\n\n"
            "Felder:\n"
            '  "abrechnungsjahr": Abrechnungsjahr (Integer)\n'
            '  "abrechnungszeitraum_von": Startdatum YYYY-MM-DD\n'
            '  "abrechnungszeitraum_bis": Enddatum YYYY-MM-DD\n'
            '  "objekt_adresse": Objektadresse\n'
            '  "ista_auftragsnummer": Liegenschaftsnummer\n'
            '  "gesamtkosten_heizung": Gesamte Heizkosten als Zahl\n'
            '  "gesamtkosten_warmwasser": Gesamte Warmwasserkosten als Zahl\n'
            '  "gesamtkosten_gesamt": Gesamtkosten als Zahl\n'
            '  "positionen": Array pro Wohneinheit/Mieter:\n'
            '    [{"ista_einheit_nr":"...", "ista_einheit_bezeichnung":"...",\n'
            '      "mieter_name":"...", "hke":0, "hke_anteil_pct":0,\n'
            '      "warmwasser_m3":0, "warmwasser_anteil_pct":0,\n'
            '      "heizkosten_grundkosten":0, "heizkosten_verbrauchskosten":0,\n'
            '      "heizkosten_gesamt":0, "warmwasserkosten_gesamt":0,\n'
            '      "gesamtkosten":0, "vorauszahlung":0, "nachzahlung_guthaben":0}]'
        )
        if _feld_hinweise:
            prompt += f"\n\nZusätzliche Hinweise:\n{_feld_hinweise}"

        try:
            aktiv = cfg.get("ki_aktives_modell", "")
            if aktiv:
                anbieter, modell = KIAssistentPage._parse_modell_auswahl(aktiv)
            else:
                anbieter = cfg.get("ki_anbieter", "anthropic")
                modell = cfg.get("ki_modell", "claude-opus-4-6")
            _log(f"   Anbieter: {anbieter}, Modell: {modell} (Vision/PDF-Modus)")

            import urllib.request
            if anbieter == "anthropic":
                api_key = cfg.get("ki_api_key", "")
                if not api_key:
                    _log("   ⚠ Kein Anthropic API-Key konfiguriert")
                    return None
                system_text = "Du bist ein Experte für Heizkostenabrechnungen der Firma Ista."
                if _system_zusatz:
                    system_text += "\n" + _system_zusatz
                # Anthropic Vision: PDF als document block
                content_blocks = [
                    {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": bilder_b64[0]}},
                    {"type": "text", "text": prompt}
                ]
                body = _json.dumps({
                    "model": modell,
                    "max_tokens": 4096,
                    "system": system_text,
                    "messages": [{"role": "user", "content": content_blocks}]
                }).encode()
                req = urllib.request.Request(
                    "https://api.anthropic.com/v1/messages",
                    data=body,
                    headers={
                        "Content-Type": "application/json",
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01"
                    }
                )
                with urllib.request.urlopen(req, timeout=120) as resp:
                    result = _json.loads(resp.read().decode())
                antwort = result.get("content", [{}])[0].get("text", "")
            else:
                _log("   ⚠ KI-Vision nur mit Anthropic-API unterstützt")
                return None

            # JSON parsen
            antwort = antwort.strip()
            if antwort.startswith("```"):
                antwort = antwort.split("\n", 1)[-1].rsplit("```", 1)[0]
            ki_daten = _json.loads(antwort)

            dauer = int((_time.time() - _t0) * 1000)
            _log(f"   ✅ KI-Vision-Analyse erfolgreich ({dauer} ms)")
            ki_log("Ista-Extraktion", "Vision-OCR", os.path.basename(pdf_pfad),
                   str(ki_daten)[:500], modell, anbieter, dauer)
            return ki_daten

        except Exception as ex:
            dauer = int((_time.time() - _t0) * 1000)
            _log(f"   ❌ KI-Vision-Fehler: {ex}")
            ki_log("Ista-Extraktion", "Vision-Fehler", os.path.basename(pdf_pfad),
                   "", modell if 'modell' in dir() else "?", anbieter if 'anbieter' in dir() else "?",
                   dauer, str(ex))
            return None

    def _ki_extrahieren(self, pdf_text: str, cfg: dict, _log) -> dict:
        """Versucht KI-basierte Extraktion der Ista-Daten."""
        import time as _time
        _t0 = _time.time()
        # KI-Training laden (#46)
        _feld_hinweise, _system_zusatz = _lade_ki_training("Ista-Extraktion")
        prompt = (
            "Analysiere diese Ista-Heizkostenabrechnung und extrahiere die Daten als JSON.\n"
            "Antworte NUR mit einem JSON-Objekt.\n\n"
            "Felder:\n"
            '  "abrechnungsjahr": Abrechnungsjahr (Integer, z.B. 2025)\n'
            '  "abrechnungszeitraum_von": Startdatum YYYY-MM-DD\n'
            '  "abrechnungszeitraum_bis": Enddatum YYYY-MM-DD\n'
            '  "objekt_adresse": Objektadresse\n'
            '  "ista_auftragsnummer": Liegenschaftsnummer falls vorhanden\n'
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
        # KI-Training-Hinweise anhängen (#46)
        if _feld_hinweise:
            prompt += f"\n\nZusätzliche Hinweise:\n{_feld_hinweise}"
        if _system_zusatz:
            prompt = _system_zusatz + "\n\n" + prompt

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
            # KI-Protokoll (#45)
            ki_log("Ista-Extraktion", "Extraktion",
                   pdf_text[:200], str(ki_daten)[:400],
                   modell, anbieter, int((_time.time() - _t0) * 1000))
            return ki_daten

        except Exception as ex:
            ki_log("Ista-Extraktion", "Fehler",
                   pdf_text[:200], "",
                   modell, anbieter, int((_time.time() - _t0) * 1000), str(ex))
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
        """Manuelle Eingabe nach fehlgeschlagenem PDF-Import → delegiert an Komplett-Dialog."""
        dlg.destroy()
        self._manuell_erfassen_komplett(pdf_pfad=pdf_pfad)

    # ── #55 Manuelle Ista-Erfassung (Gesamtwerte + Positionen pro Wohnung) ───

    def _manuell_erfassen_komplett(self, pdf_pfad: str = None):
        """#55 – Vollständige manuelle Erfassung: Gesamtwerte UND Einzelpositionen
        pro Wohnung/Mieter mit Plausibilitätsprüfung."""
        if not hat_recht("Ista-Wärme", "schreiben"):
            messagebox.showwarning("Berechtigung", "Keine Schreibberechtigung.", parent=self)
            return

        dlg = tk.Toplevel(self)
        dlg.title("Ista-Abrechnung manuell erfassen")
        dlg.geometry("920x700")
        dlg.minsize(800, 600)
        dlg.configure(bg=BG_CARD)
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()

        # ── Scrollbarer Container ────────────────────────────────────────────
        canvas = tk.Canvas(dlg, bg=BG_CARD, highlightthickness=0)
        vsb = ttk.Scrollbar(dlg, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=BG_CARD)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        # Mausrad-Scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        dlg.bind("<Destroy>", lambda e: canvas.unbind_all("<MouseWheel>") if e.widget == dlg else None)

        # ── Sektion 1: Gesamtwerte ───────────────────────────────────────────
        tk.Label(scroll_frame, text="📊 Ista-Abrechnung – Gesamtwerte",
                 bg=BG_CARD, fg=TEXT, font=FONT_H2).pack(padx=20, pady=(16, 8), anchor="w")

        gesamt_frame = tk.Frame(scroll_frame, bg=BG_CARD)
        gesamt_frame.pack(fill="x", padx=20, pady=(0, 8))

        felder = {}
        cfg = load_config()
        weg_name = cfg.get("weg_strasse", "")
        weg_plz = cfg.get("weg_plz", "")
        weg_ort = cfg.get("weg_ort", "")
        default_adresse = f"{weg_name}, {weg_plz} {weg_ort}".strip(", ")

        for label, key, default in [
            ("Abrechnungsjahr *", "abrechnungsjahr", str(date.today().year - 1)),
            ("Zeitraum von (JJJJ-MM-TT)", "abrechnungszeitraum_von", f"{date.today().year-1}-01-01"),
            ("Zeitraum bis (JJJJ-MM-TT)", "abrechnungszeitraum_bis", f"{date.today().year-1}-12-31"),
            ("Objekt-Adresse", "objekt_adresse", default_adresse),
            ("Liegenschaftsnummer", "ista_auftragsnummer", ""),  # #61
            ("Gesamtkosten Heizung (€)", "gesamtkosten_heizung", "0,00"),
            ("Gesamtkosten Warmwasser (€)", "gesamtkosten_warmwasser", "0,00"),
            ("Gesamtkosten Gesamt (€)", "gesamtkosten_gesamt", "0,00"),
        ]:
            row = tk.Frame(gesamt_frame, bg=BG_CARD)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=label, bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL,
                     width=28, anchor="w").pack(side="left")
            var = tk.StringVar(value=default)
            tk.Entry(row, textvariable=var, bg=BG_INPUT, fg=TEXT, font=FONT_BODY,
                     relief="flat", bd=0).pack(side="left", fill="x", expand=True, ipady=4)
            felder[key] = var

        # #60 – Abrechnungsjahr-Änderung aktualisiert Zeitraum automatisch
        def _on_jahr_changed(*_):
            jahr_str = felder["abrechnungsjahr"].get().strip()
            if len(jahr_str) == 4 and jahr_str.isdigit():
                felder["abrechnungszeitraum_von"].set(f"{jahr_str}-01-01")
                felder["abrechnungszeitraum_bis"].set(f"{jahr_str}-12-31")
        felder["abrechnungsjahr"].trace_add("write", _on_jahr_changed)

        tk.Frame(scroll_frame, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(12, 8))

        # ── Sektion 2: Positionen pro Wohnung/Mieter ────────────────────────
        tk.Label(scroll_frame, text="🏠 Positionen pro Wohnung / Mieter",
                 bg=BG_CARD, fg=TEXT, font=FONT_H2).pack(padx=20, anchor="w")
        tk.Label(scroll_frame,
                 text="Erfassen Sie hier die Einzelwerte für jede Wohnung. "
                      "Sie können Wohnungen aus der Datenbank übernehmen oder frei eingeben.",
                 bg=BG_CARD, fg=TEXT_LIGHT, font=FONT_SMALL,
                 wraplength=860).pack(padx=20, pady=(2, 6), anchor="w")

        # Wohnungen laden
        conn = get_db()
        try:
            wohnungen_db = conn.execute(
                "SELECT w.id, w.bezeichnung, w.wohnflaeche_qm, "
                "  COALESCE(m.vorname || ' ' || m.name, e.vorname || ' ' || e.name, '–') as bewohner "
                "FROM wohnungen w "
                "LEFT JOIN mieter m ON m.id = w.mieter_id "
                "LEFT JOIN eigentuemer e ON e.id = w.eigentuemer_id "
                "WHERE w.aktiv = 1 ORDER BY w.bezeichnung"
            ).fetchall()
        finally:
            conn.close()

        # Button-Leiste für Positionen
        pos_ctrl = tk.Frame(scroll_frame, bg=BG_CARD)
        pos_ctrl.pack(fill="x", padx=20, pady=(0, 4))
        make_btn(pos_ctrl, "➕ Position hinzufügen", lambda: _add_position()).pack(side="left", padx=(0, 6))
        make_btn(pos_ctrl, "📋 Alle Wohnungen laden", lambda: _load_all_wohnungen()).pack(side="left", padx=(0, 6))
        make_btn(pos_ctrl, "🗑 Letzte entfernen", lambda: _remove_last_position(),
                 color=DANGER).pack(side="left")

        # Container für die Positions-Zeilen
        pos_container = tk.Frame(scroll_frame, bg=BG_CARD)
        pos_container.pack(fill="x", padx=20, pady=(4, 8))

        # Spaltenüberschriften
        header_fr = tk.Frame(pos_container, bg=BG_INPUT)
        header_fr.pack(fill="x", pady=(0, 4))
        for txt, w in [("Nr.", 4), ("Wohnung/Einheit", 14), ("Mieter", 14),
                        ("Heizkosten €", 10), ("Warmwasser €", 10), ("Gesamt €", 10),
                        ("Vorauszahlung €", 12), ("Nachz./Guthaben €", 13)]:
            tk.Label(header_fr, text=txt, bg=BG_INPUT, fg=TEXT_LIGHT, font=FONT_SMALL,
                     width=w, anchor="w").pack(side="left", padx=1)

        positionen_rows = []  # Liste von dicts {frame, felder}

        def _add_position(wohnung_bez="", mieter="", heiz="0,00", ww="0,00",
                          gesamt="0,00", voraus="0,00", nachz="0,00"):
            idx = len(positionen_rows) + 1
            row_fr = tk.Frame(pos_container, bg=BG_CARD if idx % 2 else BG_INPUT)
            row_fr.pack(fill="x", pady=1)
            bg = BG_CARD if idx % 2 else BG_INPUT

            tk.Label(row_fr, text=str(idx), bg=bg, fg=TEXT_LIGHT, font=FONT_SMALL,
                     width=4, anchor="center").pack(side="left", padx=1)

            pf = {}
            for key, default, w in [
                ("wohnung", wohnung_bez, 14), ("mieter", mieter, 14),
                ("heizkosten", heiz, 10), ("warmwasser", ww, 10),
                ("gesamt", gesamt, 10), ("vorauszahlung", voraus, 12),
                ("nachzahlung", nachz, 13),
            ]:
                var = tk.StringVar(value=default)
                e = tk.Entry(row_fr, textvariable=var, bg=BG_INPUT, fg=TEXT,
                             font=FONT_SMALL, relief="flat", bd=0, width=w)
                e.pack(side="left", padx=1, ipady=2)
                pf[key] = var

            # Auto-Berechnung: Heiz + WW = Gesamt, wenn Gesamt leer
            def _auto_gesamt(*_args):
                try:
                    h = float(pf["heizkosten"].get().replace(",", ".") or 0)
                    w = float(pf["warmwasser"].get().replace(",", ".") or 0)
                    g = float(pf["gesamt"].get().replace(",", ".") or 0)
                    if abs(g - (h + w)) > 0.01 and g == 0:
                        pf["gesamt"].set(f"{h + w:.2f}".replace(".", ","))
                except ValueError:
                    pass
            pf["heizkosten"].trace_add("write", _auto_gesamt)
            pf["warmwasser"].trace_add("write", _auto_gesamt)

            positionen_rows.append({"frame": row_fr, "felder": pf})
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _remove_last_position():
            if positionen_rows:
                last = positionen_rows.pop()
                last["frame"].destroy()
                canvas.configure(scrollregion=canvas.bbox("all"))

        def _load_all_wohnungen():
            """#62 – Lädt aktive Wohnungen gefiltert nach Abrechnungsjahr."""
            if positionen_rows:
                if not messagebox.askyesno("Wohnungen laden",
                    "Vorhandene Positionen werden beibehalten.\n"
                    "Fehlende Wohnungen werden hinzugefügt.", parent=dlg):
                    return
            # Jahr aus Formular lesen
            jahr_str = felder["abrechnungsjahr"].get().strip()
            try:
                jahr_int = int(jahr_str)
                von_str = f"{jahr_int}-01-01"
                bis_str = f"{jahr_int}-12-31"
            except ValueError:
                messagebox.showwarning("Kein Jahr",
                    "Bitte zuerst ein gültiges Abrechnungsjahr eingeben.", parent=dlg)
                return
            # Wohnungen + Mieter (die im Abrechnungsjahr aktiv waren) laden
            conn2 = get_db()
            try:
                w_rows = conn2.execute(
                    "SELECT w.id, w.bezeichnung, w.wohnflaeche_qm, "
                    "  COALESCE(e.vorname || ' ' || e.name, '') AS eigentuemer "
                    "FROM wohnungen w "
                    "LEFT JOIN eigentuemer e ON e.id = w.eigentuemer_id "
                    "WHERE w.aktiv = 1 ORDER BY w.bezeichnung"
                ).fetchall()
                m_rows = conn2.execute(
                    "SELECT m.wohnung_id, m.vorname || ' ' || m.name AS mietername "
                    "FROM mieter m "
                    "WHERE m.einzug <= ? "
                    "  AND (m.auszug IS NULL OR m.auszug = '' OR m.auszug >= ?) "
                    "ORDER BY m.wohnung_id, m.einzug",
                    (bis_str, von_str)
                ).fetchall()
            finally:
                conn2.close()
            # Mieter je Wohnung gruppieren
            mieter_map: dict = {}
            for m in m_rows:
                mieter_map.setdefault(m["wohnung_id"], []).append(m["mietername"])
            existing = {r["felder"]["wohnung"].get().strip().lower() for r in positionen_rows}
            for w in w_rows:
                bez = w["bezeichnung"] or ""
                mieter_liste = mieter_map.get(w["id"], [])
                if not mieter_liste:
                    # Keine Mieter → Eigentümer als Bewohner oder Leerzeichen
                    bewohner = w["eigentuemer"] or "–"
                    if bez.strip().lower() not in existing:
                        _add_position(wohnung_bez=bez, mieter=bewohner)
                else:
                    # Für jeden Mieter im Jahr eine eigene Zeile
                    for mname in mieter_liste:
                        key = f"{bez.strip().lower()}|{mname.strip().lower()}"
                        if key not in existing:
                            _add_position(wohnung_bez=bez, mieter=mname)
                            existing.add(key)

        # ── Sektion 3: Plausibilitäts-Anzeige ────────────────────────────────
        tk.Frame(scroll_frame, bg=BORDER, height=1).pack(fill="x", padx=20, pady=(8, 6))

        plaus_frame = tk.Frame(scroll_frame, bg="#FEF9E7")
        plaus_frame.pack(fill="x", padx=20, pady=(0, 8))
        plaus_lbl = tk.Label(plaus_frame, text="⏳ Plausibilitätsprüfung: Erfassen Sie Positionen …",
                              bg="#FEF9E7", fg="#7D6608", font=FONT_SMALL, wraplength=860, justify="left")
        plaus_lbl.pack(padx=12, pady=8, anchor="w")

        def _check_plausibilitaet():
            """#55 – Prüft ob Summe der Positionen ≈ Gesamtkosten."""
            try:
                g_heiz = float(felder["gesamtkosten_heizung"].get().replace(",", ".") or 0)
                g_ww = float(felder["gesamtkosten_warmwasser"].get().replace(",", ".") or 0)
                g_ges = float(felder["gesamtkosten_gesamt"].get().replace(",", ".") or 0)
            except ValueError:
                plaus_lbl.config(text="⚠ Gesamtwerte ungültig – bitte Zahlen eingeben.",
                                  bg="#FDEDEC", fg=DANGER)
                plaus_frame.config(bg="#FDEDEC")
                return False

            sum_heiz = 0.0
            sum_ww = 0.0
            sum_ges = 0.0
            for r in positionen_rows:
                pf = r["felder"]
                try:
                    sum_heiz += float(pf["heizkosten"].get().replace(",", ".") or 0)
                    sum_ww += float(pf["warmwasser"].get().replace(",", ".") or 0)
                    sum_ges += float(pf["gesamt"].get().replace(",", ".") or 0)
                except ValueError:
                    pass

            abweichungen = []
            ok = True
            if g_heiz > 0 and abs(sum_heiz - g_heiz) > 0.99:
                abweichungen.append(
                    f"Heizung: Summe Positionen {sum_heiz:,.2f} € ≠ Gesamt {g_heiz:,.2f} € "
                    f"(Δ {abs(sum_heiz - g_heiz):,.2f} €)")
                ok = False
            if g_ww > 0 and abs(sum_ww - g_ww) > 0.99:
                abweichungen.append(
                    f"Warmwasser: Summe Positionen {sum_ww:,.2f} € ≠ Gesamt {g_ww:,.2f} € "
                    f"(Δ {abs(sum_ww - g_ww):,.2f} €)")
                ok = False
            if g_ges > 0 and abs(sum_ges - g_ges) > 0.99:
                abweichungen.append(
                    f"Gesamt: Summe Positionen {sum_ges:,.2f} € ≠ Gesamt {g_ges:,.2f} € "
                    f"(Δ {abs(sum_ges - g_ges):,.2f} €)")
                ok = False

            if not positionen_rows:
                plaus_lbl.config(
                    text="ℹ Keine Positionen erfasst – nur Gesamtwerte werden gespeichert.",
                    bg="#EBF5FB", fg="#1A5276")
                plaus_frame.config(bg="#EBF5FB")
                return True
            elif ok:
                plaus_lbl.config(
                    text=f"✅ Plausibel: {len(positionen_rows)} Positionen, Summen stimmen überein.\n"
                         f"   Heizung: {sum_heiz:,.2f} €  |  Warmwasser: {sum_ww:,.2f} €  |  "
                         f"Gesamt: {sum_ges:,.2f} €",
                    bg="#EAFAF1", fg=SUCCESS)
                plaus_frame.config(bg="#EAFAF1")
                return True
            else:
                plaus_lbl.config(
                    text="⚠ Abweichungen:\n" + "\n".join(f"   • {a}" for a in abweichungen) +
                         "\n   Prüfen Sie die Eingaben oder speichern Sie trotzdem.",
                    bg="#FEF9E7", fg="#7D6608")
                plaus_frame.config(bg="#FEF9E7")
                return False

        # ── Buttons am Ende ──────────────────────────────────────────────────
        btn_frame = tk.Frame(scroll_frame, bg=BG_CARD)
        btn_frame.pack(fill="x", padx=20, pady=(4, 16))

        def _on_pruefen():
            _check_plausibilitaet()

        def _on_save():
            plaus_ok = _check_plausibilitaet()
            if not plaus_ok and positionen_rows:
                if not messagebox.askyesno("Abweichung",
                    "Die Summe der Positionen weicht von den Gesamtwerten ab.\n"
                    "Trotzdem speichern?", parent=dlg):
                    return
            try:
                _pf = lambda v: float(v.replace(",", ".")) if v else 0
                daten = {
                    "abrechnungsjahr": int(felder["abrechnungsjahr"].get() or date.today().year - 1),
                    "abrechnungszeitraum_von": felder["abrechnungszeitraum_von"].get() or None,
                    "abrechnungszeitraum_bis": felder["abrechnungszeitraum_bis"].get() or None,
                    "objekt_adresse": felder["objekt_adresse"].get(),
                    "ista_auftragsnummer": felder["ista_auftragsnummer"].get(),
                    "gesamtkosten_heizung": _pf(felder["gesamtkosten_heizung"].get()),
                    "gesamtkosten_warmwasser": _pf(felder["gesamtkosten_warmwasser"].get()),
                    "gesamtkosten_gesamt": _pf(felder["gesamtkosten_gesamt"].get()),
                    "positionen": [],
                }
                for r in positionen_rows:
                    pf = r["felder"]
                    pos = {
                        "ista_einheit_nr": "",
                        "ista_einheit_bezeichnung": pf["wohnung"].get().strip(),
                        "mieter_name": pf["mieter"].get().strip(),
                        "hke": 0,
                        "hke_anteil_pct": 0,
                        "warmwasser_m3": 0,
                        "warmwasser_anteil_pct": 0,
                        "heizkosten_grundkosten": 0,
                        "heizkosten_verbrauchskosten": 0,
                        "heizkosten_gesamt": _pf(pf["heizkosten"].get()),
                        "warmwasserkosten_gesamt": _pf(pf["warmwasser"].get()),
                        "gesamtkosten": _pf(pf["gesamt"].get()),
                        "vorauszahlung": _pf(pf["vorauszahlung"].get()),
                        "nachzahlung_guthaben": _pf(pf["nachzahlung"].get()),
                    }
                    daten["positionen"].append(pos)

                self._save_import(dlg, pdf_pfad, daten)
            except ValueError as e:
                messagebox.showerror("Eingabefehler", f"Ungültige Eingabe: {e}", parent=dlg)

        make_btn(btn_frame, "🔍 Plausibilität prüfen", _on_pruefen,
                 color=ACCENT).pack(side="left", padx=(0, 8))
        make_btn(btn_frame, "💾 Speichern & Importieren", _on_save).pack(side="left", padx=(0, 8))
        make_btn(btn_frame, "Abbrechen", dlg.destroy, color=BG_INPUT, fg=TEXT).pack(side="left")

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
        ("🧾", "Rechnungen",    RechnungenPage),   # #65/#66
        ("🔧", "Wartung",        WartungPage),
        ("📋", "Nebenkosten",    NebenkostenPage),
        ("🔥", "Ista-Wärme",     IstaPage),
        ("💧", "Wasserkosten",   WasserkostenPage),
        ("⚖",  "Aufteilungen",   AufteilungenPage),
        ("✉️",  "Nachrichten",    NachrichtenPage),
        ("📁", "Dokumente",      DokumentePage),
        ("🤖", "KI-Assistent",   KIAssistentPage),
        ("📊", "KI-Protokoll",   KiProtokollPage),
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
        # Optionale Pakete prüfen – NACH deiconify(), damit transiente Dialoge sichtbar sind
        _fehlend = _prüfe_pakete()
        if _fehlend:
            _dlg = AbhängigkeitenDialog(self, _fehlend)
            self.wait_window(_dlg)
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

        # #70 – Nebenkosten-Unterkategorien: Ista-Wärme, Wasserkosten, Aufteilungen
        _NK_SUB_CLASSES = {IstaPage, WasserkostenPage, AufteilungenPage}
        _nk_idx  = next(i for i, (_, _, c) in enumerate(self.PAGES) if c == NebenkostenPage)
        _sub_idxs = {i for i, (_, _, c) in enumerate(self.PAGES) if c in _NK_SUB_CLASSES}
        self._nk_idx   = _nk_idx
        self._sub_idxs = _sub_idxs

        self._nav_btns = [None] * len(self.PAGES)
        nav_frame = tk.Frame(sidebar, bg=BG_SIDEBAR)
        nav_frame.pack(fill="x", pady=8)

        # Sub-Frame für Nebenkosten-Unterpunkte (wird nach Nebenkosten-Button eingefügt)
        self._nk_sub_frame = tk.Frame(nav_frame, bg=BG_SIDEBAR)

        for i, (icon, label, PageClass) in enumerate(self.PAGES):
            if i in _sub_idxs:
                # Unterpunkt: kompakteres Layout, eingerückt
                btn = tk.Button(self._nk_sub_frame,
                    text=f"    ↳ {icon}  {label}",
                    command=lambda idx=i: self._switch(idx),
                    bg=BG_SIDEBAR, fg=SIDEBAR_FG,
                    font=("Segoe UI", 9), relief="flat", bd=0,
                    anchor="w", padx=8, pady=6,
                    activebackground="#253545",
                    activeforeground=TEXT_WHITE,
                    cursor="hand2")
                btn.pack(fill="x", padx=(12, 8), pady=0)
            else:
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
                if i == _nk_idx:
                    # Sub-Frame direkt nach dem Nebenkosten-Button einsetzen
                    self._nk_sub_frame.pack(fill="x", after=btn)
            self._nav_btns[i] = btn

        # Sub-Frame initial ausblenden
        self._nk_sub_frame.pack_forget()

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
                continue  # ausgeblendete Seite
            is_sub = hasattr(self, '_sub_idxs') and i in self._sub_idxs
            if i == idx:
                btn.config(bg="#253545", fg=SIDEBAR_ACT)
            elif is_sub:
                btn.config(bg=BG_SIDEBAR, fg=SIDEBAR_FG)
            else:
                btn.config(bg=BG_SIDEBAR, fg=SIDEBAR_FG)
        # #70 – Nebenkosten Sub-Frame ein-/ausblenden
        if hasattr(self, '_nk_sub_frame') and self._nk_sub_frame:
            nk_active = idx == self._nk_idx or (hasattr(self, '_sub_idxs') and idx in self._sub_idxs)
            if nk_active:
                self._nk_sub_frame.pack(fill="x", after=self._nav_btns[self._nk_idx])
            else:
                self._nk_sub_frame.pack_forget()
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
        _row(body, "DB-Pfad:", str(get_db_path()))

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
        # KEIN transient() — transiente Fenster werden beim withdrawn Parent unsichtbar
        self.grab_set()
        self.resizable(False, False)
        self.configure(bg=BG_CARD)
        self.geometry("580x420")
        self._pakete = fehlende_pakete
        self._status_vars = {}
        self._build()
        # Immer am Bildschirm-Mittelpunkt zentrieren (unabhängig vom Parent-Zustand)
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"+{(sw - 580) // 2}+{(sh - 420) // 2}")

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
