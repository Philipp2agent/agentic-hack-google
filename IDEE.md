# IDEE: VoxField Copilot – Hands-Free Voice Agent für Servicetechniker

> **Kern in einem Satz:** Ein autonomer, sprachgesteuerter Vor-Ort-Assistent mit Gradium Voice und Gemini, der Technikern freihändig bei Diagnose, Teilebeschaffung und Dokumentation hilft und vor unumkehrbaren Aktionen verbindliche Sprach-Freigaben einholt.

---

## 1. Problem
Servicetechniker und Handwerker stehen vor komplexen Industrieanlagen oder Haustechniksystemen mit Handschuhen, Werkzeug und schmutzigen Händen. Bei Störungen müssen sie bisher:
1. Handschuhe ausziehen, Smartphone/Laptop bedienen oder Hotline anrufen.
2. Fehlercodes mühsam manuell in PDF-Handbüchern und ERP/Katalogen nachschlagen.
3. Teure Teilebestellungen oder Kundenfreigaben manuell per Mail/Portal abwickeln.
4. Nach getaner Arbeit handschriftlich oder abends am PC Berichte tippen (oft lückenhaft).

## 2. Echter Nutzer (Persona)
**Stefan (42), Servicetechniker für Heizungs- und Klimatechnik in Zürich.**
- Arbeitet mobil vor Ort in Kellern und Technikräumen.
- Hat bei laufendem Fehler beide Hände an der Anlage.
- Benötigt sofortige, präzise Antworten ohne Bildschirmtippen.
- Darf Reparaturfreigaben und Ersatzteile bis 500 CHF eigenverantwortlich beauftragen, muss dies aber sauber auditieren.

---

## 3. Die Lösung: VoxField Copilot
Ein multimodaler KI-Agent mit:
- **Gradium Voice Front Door:** Natürlicher, unterbrechbarer Sprachdialog mit semantischer Pausenerkennung auf Deutsch/Englisch.
- **Gemini 3.8 Flash Orchestrator:** Plant Diagnoseschritte, wählt Werkzeuge (Fehlercode-DB, Ersatzteilkatalog, Ticket-System), steuert den Workflow.
- **Human Checkpoint (DeepMind-Kriterium 3):** Sobald Geld ausgegeben oder verbindliche Verträge ausgelöst werden (z. B. Express-Ersatzteil für 180 CHF bestellen), hält der Agent an und verlangt Stefans ausdrückliche Sprachfreigabe.
- **Gemini Nano Banana (Multimodal / bild.py):** Erstellt bei Bedarf schematische Einbau-/Explosionsskizzen des betroffenen Bauteils.
- **Automatischer Einsatzbericht:** Generiert am Ende strukturiertes Einsatzprotokoll mit Audio-Zusammenfassung via Gradium / Gemini Audio.

---

## 4. 2-Minuten-Demo-Ablauf (Video & Jury-Live)
| Zeit | Wer | Aktion / Interaktion | Sichtbares / Hörbares Ergebnis |
|---|---|---|---|
| **0:00 - 0:25** | Stefan | Spricht freihändig ins Headset/Web: *"Hallo Vox, ich stehe an Wärmepumpe WP-400. Fehlercode E-74 blinkt, Überdruckventil zischt."* | Gradium STT transkribiert in Echtzeit; Voice-Antwort: *"Fehler E-74: Überdruckventil V-12 blockiert. Ich prüfe Handbuch und Lagerbestand."* |
| **0:25 - 0:55** | Agent | Führt Tools autonom aus: diagnostiziert Ursache, schlägt Dichtungstausch vor, generiert Bauteilskizze mit Gemini Nano Banana. | Dashboard zeigt Bauteilskizze und Teilenummer `V12-SEAL-2026`. Agent liest Handlungsanweisung vor. |
| **0:55 - 1:25** | Agent & Stefan | **Human Checkpoint:** Agent: *"Dichtungssatz im Zentrallager Zürich verfügbar. Express-Kurier kostet 140 CHF. Soll ich die Bestellung jetzt verbindlich auslösen?"* Stefan: *"Ja, bitte bestellen!"* | Unumkehrbare Aktion wird erst nach Freigabe getriggert. Bestätigung: *"Bestellung #8491 ausgelöst, Kurier ETA 45 Minuten."* |
| **1:25 - 2:00** | Agent | Agent fasst Einsatzbericht zusammen, schließt Ticket im System, erzeugt Audioprotokoll für den Kunden. | Vollständiger Einsatzbericht auf dem Dashboard sichtbar; Audio-Zusammenfassung wird abgespielt. |

---

## 5. Scope: Must-have vs. Nice-to-have (bis 18:00 Feature-Freeze)

### Must-have (Kern bis 18:00)
- [x] Gradium Voice Integration (STT & TTS Dialog-Schleife mit Unterbrechung/Pausen).
- [x] Gemini 3.8 Flash Agent mit Tool-Calling (Diagnose-Tool, Teilekatalog-Tool, Bestell-Tool mit Checkpoint).
- [x] Human-in-the-Loop Checkpoint: Klare Trennung zwischen Lese-Aktionen und Freigabe-Aktionen.
- [x] Visuelles Web-Dashboard (Streamlit/FastAPI/HTML): Live-Transkript, Status des Agenten, generierte Visuals & Ticket-Status.
- [x] Mock-APIs für Katalog & ERP (realistisch mit Zürich-Standorten).

### Nice-to-have (wenn Zeit bleibt)
- [ ] Live-Foto-Analyse: Techniker hält Smartphone-Kamera auf das Bauteil, Gemini analysiert Typenschild.
- [ ] Twilio-Telefonie-Anbindung über gradbot.
- [ ] Export als PDF-Rapport.

---

## 6. Risiken & Gegenmaßnahmen
1. **Latenz in der Sprachschleife:**
   - *Gegenmaßnahme:* Streaming STT über Gradium WebSocket, kurze System-Prompts für schnelle Antworten, Gemini Flash als Orchestrator.
2. **Fehlinterpretation der Bestätigung:**
   - *Gegenmaßnahme:* Eindeutiges Zwei-Phasen-Commit im Agenten (stateful Flag `awaiting_confirmation_for_action`).
3. **Netzwerk / API-Quota am Hackathon:**
   - *Gegenmaßnahme:* Robuste Fallbacks auf lokale Mock-Tools, Caching von Bild-Generierungen für Standard-Demofälle.

---

## 7. 3 Entscheidungen für Philipp (bitte mit z. B. "1A 2A 3A" antworten)

### Entscheidung 1: Einsatz-Szenario
- **1A: Technischer Außendienst / Industrieanlage (FieldOps)** *(Empfehlung)* – Handwerker vor defekter Heizung/Pumpe mit Handschuhen. Extrem nachvollziehbarer Hands-Free Nutzen für die Jury.
- **1B: Facility-Management / Wasserschaden-Notruf (CareOps)** – Hausverwaltung koordiniert nächtlichen Rohrbruch mit Mietern und Notdienst.

### Entscheidung 2: Demo-Kanal & Interface
- **2A: Web-Voice Dashboard (Browser Audio + Live-Screen)** *(Empfehlung)* – Ideale Präsentation für 2-Min-Video und 5-Min-Jury-Demo (man sieht den Agenten denken, hört die Stimme, sieht das generierte Bild).
- **2B: Echter Telefonanruf (Twilio / gradbot)** – Beeindruckend im Audio, aber kein visueller Screen für die Video-Abgabe.

### Entscheidung 3: Visuelle Komponente
- **3A: Bauteil-Skizzen via Gemini Nano Banana (`tools/bild.py`) einbinden** *(Empfehlung)* – Zeigt multimodale Tiefe (Voice + Text + Bildgenerierung).
- **3B: Rein tabellarische / schematische Datenanzeige** – Schlanker, weniger Abhängigkeiten, aber visuell weniger spektakulär.
