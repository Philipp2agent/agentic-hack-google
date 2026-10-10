# Changelog

All notable changes to PayPulse will be documented in this file.
The format is based on Keep a Changelog.

## [Unreleased]
### Added
- PayPal Webhook Event Parsing and routing
- DLQ manual replay endpoint
- Daily reconciliation summary model

### Fixed
- Intermittent retry counter reset on HTTP 503 responses

## [0.2.1] - 2026-10-08
### Added
- Webhook delivery latency histogram metrics
### Changed
- Default exponential backoff multiplier adjusted to 1.5
### Fixed
- Async connection pool exhaustion under sudden traffic spikes

## [0.2.0] - 2026-10-01
### Added
- Redis deduplication and idempotency locking layer
- Stripe webhook signature verification with replay protection
- JSON schema validation for incoming webhook payloads

## [0.1.0] - 2026-09-15
### Added
- Initial project structure with FastAPI and asyncio
- Double-entry ledger core tables (accounts, transactions, entries)
- Basic webhook ingestion endpoint `/api/v1/webhooks`
