# Backlog & Aufgaben (PayPulse)

## Hohe Prioritaet (P0 / P1)
- [x] Stripe HMAC Signaturvalidierung implementieren
- [x] Redis Distributed Lock fuer Idempotency-Keys
- [x] Dead-Letter-Queue Speicherung fuer unzustellbare Payloads
- [ ] PayPal Capture und Refund Webhook Handler fertigstellen
- [ ] DLQ Redrive CLI Tool (`paypulse dlq redrive`)
- [ ] Ledger Reconciler fuer taegliche Bank-Settlements

## Mittlere Prioritaet (P2)
- [x] Prometheus Counter fuer `webhooks_received_total` und `webhooks_failed_total`
- [x] Latenz-Histogramm fuer Webhook Delivery
- [ ] OpenAPI 3.1 Dokumentation generieren und veroeffentlichen
- [ ] Redis Health Check Endpoint (`/health/ready`)
- [ ] Slack Notification Webhook bei wiederholten Signaturfehlern

## Bekannte Fehler / Bugs
- [x] FIX-104: HTTP Timeout bei langsamen Downstream-Empfaengern (auf 5s begrenzt)
- [ ] FIX-112: Doppelter Alarm bei Redis Cluster Node Failover
