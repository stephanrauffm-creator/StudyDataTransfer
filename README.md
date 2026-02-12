# StudieDataTransfer – Vorschlag für eine Klinik-Webanwendung

Dieses Repository enthält einen **Umsetzungsvorschlag** für eine interne Webanwendung, mit der Kolleg:innen strukturiert Studiendaten erfassen können.

## Ziel

Eine webbasierte Eingabemaske soll folgende Felder erfassen:

- **PIZ**
- **Untersuchungsdatum**
- **Anbindung Leberambulanz** (ja/nein)
- **Fibroscan-Befund**
  - Lebersteifigkeits-Index
  - CAP-Index

Zusätzlich sollen **Studienanleitungen als PDF** im System hinterlegt und für Mitarbeitende einfach abrufbar sein.

---

## Empfohlene Architektur (praxisnah)

### 1) Web-Frontend (Intranet)

- Formular mit Pflichtfeldprüfung
- Plausibilitätschecks (z. B. Datum nicht in der Zukunft, numerische Werte für Indizes)
- Rollenbasiert (z. B. „Dateneingabe“, „Studienleitung“, „Read-only“)

### 2) Backend + Datenbank (empfohlen)

- Speicherung der Eingaben zuerst in einer **Datenbank** (z. B. PostgreSQL oder MS SQL)
- Vorteile:
  - sichere Transaktionen
  - Auditierbarkeit (wer hat wann geändert)
  - robust bei gleichzeitigen Zugriffen
  - bessere Basis für Auswertungen

### 3) Excel-Export in Netzwerkordner

Wenn Excel im Netzwerkordner zwingend benötigt wird:

- Geplanter Exportjob (z. B. alle 5 Minuten oder stündlich)
- Export erzeugt/aktualisiert eine strukturierte Datei im gewünschten Netzwerkpfad
- Bei Fehlern: Logging + Mail-Hinweis an Admin

> Warum nicht direkt in dieselbe Excel schreiben?
> - Gleichzeitige Zugriffe sind fehleranfällig
> - Dateisperren/Inkonsistenzen möglich
> - Nachvollziehbarkeit und Datenqualität leiden

### 4) PDF-Dokumentenbereich

- Upload-Funktion für Studienanleitungen (PDF)
- Versionierung (z. B. „v1.2 vom 2026-02-01“)
- Sichtbarkeit nur für berechtigte Rollen
- Optional: „Gelesen am“-Bestätigung

---

## Konkreter MVP-Umfang (4–6 Wochen)

1. Login über Klinik-AD/SSO (oder lokale Nutzerverwaltung für Start)
2. Formular für die 5 Kernfelder
3. Listenansicht mit Filter (PIZ, Zeitraum)
4. PDF-Ablage inkl. Download
5. Regelmäßiger Excel-Export in Netzwerkordner
6. Protokollierung (Create/Update inkl. Zeitstempel)

---

## Datenmodell (Vorschlag)

### Tabelle `study_entries`

- `id` (UUID)
- `piz` (String, indexiert)
- `exam_date` (Date)
- `liver_clinic_connected` (Boolean)
- `fibroscan_liver_stiffness_index` (Decimal)
- `fibroscan_cap_index` (Decimal)
- `created_at`, `created_by`
- `updated_at`, `updated_by`

### Tabelle `study_documents`

- `id` (UUID)
- `title`
- `version`
- `file_path` oder Blob-Referenz
- `uploaded_at`, `uploaded_by`

---

## Alternativen zur Excel-Zielablage

### A) Primär Datenbank + Excel nur als Export (empfohlen)

- Beste Datenqualität und Stabilität
- Excel bleibt für bestehende Prozesse verfügbar

### B) Direktes Schreiben in SharePoint-Liste statt Excel-Datei

- Bessere Parallelität als klassische XLSX-Datei
- Gute Integration mit Microsoft 365

### C) REDCap als Studienplattform

- Speziell für klinische Studien
- Audit-Trail, Rechtekonzept, validierte Datenerfassung
- Excel-Export standardmäßig möglich

### D) EDC-System (z. B. Castor, secuTrial, OpenClinica)

- Höherer Implementierungsaufwand
- Dafür regulatorisch oft besser aufgestellt

---

## Sicherheits- und Compliance-Hinweise

- Hosting im Kliniknetz / zertifiziertem Rechenzentrum
- Transportverschlüsselung (TLS)
- Rollen- und Rechtekonzept (Least Privilege)
- Audit-Log unveränderbar speichern
- Aufbewahrungsfristen mit Datenschutzbeauftragten abstimmen
- Falls personenbezogene Daten: DSFA und TOMs prüfen

---

## Empfohlener Tech-Stack (ein möglicher Weg)

- **Frontend:** React + TypeScript
- **Backend:** FastAPI (Python) oder ASP.NET Core
- **DB:** PostgreSQL / MS SQL
- **Dateiablage PDFs:** Netzwerkshare oder Objekt-Storage (intern)
- **Export:** Geplanter Worker (Cron/Task Scheduler)

---

## Nächste Schritte

1. Kurzer Workshop (30–45 min) mit Studienleitung + IT
2. Pflichtfelder, Rollen und Exportformat final abstimmen
3. MVP als klickbaren Prototyp + Pilotstation
4. Nach 2–4 Wochen Feedbackrunde und Ausbau

Wenn gewünscht, kann im nächsten Schritt eine **konkrete Implementierungsskizze** erstellt werden (API-Endpunkte, Datenbankmigrationen, UI-Mockup, Deploymentplan).
