# Schnittstellenspezifikation & Datenmodelle (DawnDispatch)

Dieses Dokument definiert die zentralen Datenmodelle und Dateischnittstellen fuer das System **DawnDispatch**. Alle Komponenten (`src/core`, `src/voice`, `src/dashboard`) kommunizieren ueber diese JSON-Strukturen unter `src/data/`.

---

## 1. Uebersicht der Datenstroeme

```
Repo Events (git log, PRs, STAND.md)
              │
              ▼
    [src/core/repo_events]
              │
              ▼
    src/data/overnight_events.json
              │
              ▼
    [src/core/agenda_synth (Gemini 3.8 Flash)]
              │
              ▼
       src/data/agenda.json
              │
      ┌───────┴───────────────────────┐
      ▼                               ▼
[src/voice/ (gradbot Voice Call)]   [src/dashboard/ (Web UI)]
      │                               │
      │ log_decision()                │ Checkpoint Confirmation
      ▼                               ▼
src/data/decisions.json        src/data/actions.json
      │                               ▲
      └──────► [src/core/action_engine] ┘
```

---

## 2. Datenmodelle (JSON Schemas)

### 2.1 OvernightEvent (`src/data/overnight_events.json`)
Repraesentiert ein Ereignis des naechtlichen Agentenschwarms (Repo-Commits, PRs, Agenten-Logs).

- `id` (string): Eindeutige Kennung (z. B. `"evt-001"`).
- `source` (string): Herkunft des Ereignisses (z. B. `"git commit 3cdd23d"` oder `"PR #4"`).
- `agent_id` (string): ID des ausfuehrenden Agenten (z. B. `"hack-bau1"`, `"hack-visual"`).
- `title` (string): Kurzer Praegnanz-Titel.
- `details` (string): Ausfuehrlichere Beschreibung des Ergebnisses oder Status.
- `severity` (string): Enum: `"INFO"`, `"WARNING"`, `"ERROR"`.
- `proposed_action` (string): Vom Aggregator vorgeschlagene Folgehandlung.

### 2.2 AgendaItem (`src/data/agenda.json`)
Vom Gemini 3.8 Flash Synthesizer erstellte Diskussionspunkte fuer den morgendlichen Voice-Call (max. 3 Punkte, straff moderiert).

- `item_id` (string): Kennung des Agendapunkts (z. B. `"agenda-01"`).
- `topic` (string): Kurztitel des Themas.
- `question_for_lead` (string): Praezise Frage fuer den Lead im Call.
- `recommended_action` (string): Handlungsempfehlung des Systems.
- `is_irreversible` (boolean): `true`, wenn die Entscheidung irreversible Konsequenzen hat (z. B. Loeschungen, Deployments, DB-Resets).

### 2.3 DecisionRecord (`src/data/decisions.json`)
Ergebnis der Live-Entscheidung waehrend des Voice-Calls (erfasst per Tool-Call `log_decision`).

- `item_id` (string): Referenz auf `AgendaItem.item_id`.
- `decision_type` (string): Enum: `"APPROVE"`, `"REJECT"`, `"HOLD"`, `"AMEND"`.
- `voice_notes` (string): Auszug/Zusammenfassung aus dem Gespraech des Leads.
- `timestamp` (string): ISO-8601 Zeitstempel.
- `human_verified` (boolean): Kennzeichnung, ob die Bestaetigung vom Menschen stammt (`true`).

### 2.4 ActionExecution (`src/data/actions.json`)
Folgeausfuehrungen basierend auf den Beschluessen.

- `action_id` (string): Eindeutige Aktions-ID (z. B. `"act-101"`).
- `item_id` (string): Referenz auf das Agendaprodukt.
- `action_type` (string): Technische Aktionskennung.
- `status` (string): Enum:
  - `"PENDING"`: Eingeplant.
  - `"EXECUTING"`: In Bearbeitung.
  - `"COMPLETED"`: Erfolgreich abgeschlossen.
  - `"BLOCKED_ON_CHECKPOINT"`: Wartet auf 1-Klick-Freigabe im Dashboard fuer irreversible Aktionen.
- `artifacts` (object): Ergebnisartefakte (Links, Logs, Commit-IDs, Port-Angaben).

---

## 3. Tool-Calling Schnittstelle fuer Voice-Agent (`src/voice/`)

Der Voice-Agent (`gradbot` + Gemini 3.8 Flash) stellt folgende Werkzeuge bereit:

1. `log_decision(item_id: str, decision: str, notes: str)`:
   - Traegt den Beschluss in `src/data/decisions.json` ein.
   - `decision` muss einer von `APPROVE`, `REJECT`, `HOLD`, `AMEND` sein.
2. `mark_irreversible_checkpoint(item_id: str, reason: str)`:
   - Markiert eine Aktion als unumkehrbar in `src/data/actions.json` mit Status `BLOCKED_ON_CHECKPOINT`.
   - Das Dashboard zeigt dafuer einen auffaelligen Freigabe-Knopf an.
