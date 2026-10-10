# Projektstand: PayPulse

**Datum:** 2026-10-10  
**Release-Ziel:** v0.3.0 (Geplant: 2026-10-12)  
**Lead:** Alex Rivera  

## Letzte Fortschritte (Letzte 24h)
- Webhook HMAC-SHA256 Signaturpruefung fuer Stripe v3 erfolgreich implementiert (PR #42).
- Redis-basierte Idempotency-Sperre mit 48h TTL ausgestattet.
- Dead-Letter-Queue (DLQ) fuer fehlerhafte Payloads aufgesetzt.
- Prometheus-Metriken unter `/metrics` fuer Durchsatz und Latenz integriert.

## Aktuell in Arbeit
- Idempotency-Handler fuer PayPal Capture Webhooks (`feature/paypal-webhook-support`).
- Replay-Mechanismus fuer fehlgeschlagene Webhook-Dispatches in der DLQ.
- Settlement Reconciliation Report Generator.

## Blocker & Offene Fragen
- Warten auf Freischaltung der neuen PayPal v2 Sandbox-Credentials.
- Frage an Philipp/Finance: Sollen Teilerstattungen (partial refunds) im Ledger als separate Transaktion oder als Deltabuchung gefuehrt werden?

## Naechste Meilensteine
1. PayPal Webhook End-to-End Test abschliessen.
2. Reconciliation Batch Runner validieren.
3. Release Tag v0.3.0 erstellen.
