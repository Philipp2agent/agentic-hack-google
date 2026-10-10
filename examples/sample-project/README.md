# PayPulse

PayPulse is a lightweight, asynchronous payment webhook ingestion router and reconciliation ledger. It securely receives webhooks from payment providers (Stripe, PayPal, Adyen), verifies HMAC signatures, enforces idempotent execution via Redis locks, and persists transaction events to an append-only ledger.

## Architecture

- **Ingestion Router (`src/paypulse/webhooks.py`)**: Validates webhook authenticity and deduplicates inbound events.
- **Idempotency & Locks**: Prevents double-processing of financial events using distributed lease keys.
- **Ledger Engine (`src/paypulse/ledger.py`)**: Double-entry journal recording credits, debits, and settlement states.
- **Metrics & Observability**: Real-time metrics for latency, error rate, and DLQ status.

## Current Focus (v0.3.0 Sprint)

- Multi-tenant webhook secret rotation.
- Dead-letter-queue (DLQ) replay CLI.
- Settlement reconciliation reports for overnight batch jobs.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
python -m paypulse.main
```
