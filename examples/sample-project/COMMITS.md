# Commit History (Last 30 Commits)

| Commit | Date | Author | Message |
|--------|------|--------|---------|
| `a3f91c2` | 2026-10-10 14:32:00 | Alex Rivera | feat(dlq): add dead-letter-queue redrive CLI command skeleton |
| `b7e42d1` | 2026-10-10 13:15:22 | Maya Chen | fix(retry): handle exponential backoff edge case on 503 responses |
| `c2d89a4` | 2026-10-10 11:45:10 | Alex Rivera | feat(paypal): add schema validation for payment.capture.completed |
| `d4b12f7` | 2026-10-10 10:20:05 | Sam Miller | docs(stand): update morning standup status and sprint deliverables |
| `e8a33c1` | 2026-10-10 09:05:40 | Maya Chen | test(webhooks): add concurrent webhook replay test cases |
| `f1c78e9` | 2026-10-09 17:40:12 | Alex Rivera | refactor(ledger): streamline double-entry balancing assertion |
| `10a24b8` | 2026-10-09 16:12:33 | Sam Miller | feat(metrics): register prometheus latency summary |
| `21b35c9` | 2026-10-09 14:50:18 | Maya Chen | fix(security): sanitize incoming header logs for webhook signature |
| `32c46d0` | 2026-10-09 11:22:01 | Alex Rivera | feat(stripe): add support for account.updated webhook payload |
| `43d57e1` | 2026-10-09 09:30:45 | Sam Miller | chore(deps): bump redis-py from 5.0.1 to 5.0.2 |
| `54e68f2` | 2026-10-08 18:10:00 | Alex Rivera | release: bump version to 0.2.1 |
| `65f7903` | 2026-10-08 16:45:12 | Maya Chen | perf(idempotency): reduce redis key lookup latency via pipeline |
| `76a8014` | 2026-10-08 14:15:20 | Sam Miller | fix(config): allow setting max_retry_attempts via environment |
| `87b9125` | 2026-10-08 11:05:50 | Alex Rivera | feat(ledger): implement multi-currency account validation |
| `98ca236` | 2026-10-08 09:20:30 | Maya Chen | test(ledger): cover zero-sum balance requirement across legs |
| `a9db347` | 2026-10-07 17:35:14 | Sam Miller | docs(readme): add sequence diagram for webhook ingestion |
| `baec458` | 2026-10-07 15:10:05 | Alex Rivera | feat(webhooks): add HMAC signature timing-safe comparison |
| `cbfd569` | 2026-10-07 13:40:22 | Maya Chen | refactor(storage): separate raw payload store from parsed events |
| `dc0e670` | 2026-10-07 10:15:18 | Sam Miller | fix(timeout): increase downstream webhook forward timeout to 5s |
| `ed1f781` | 2026-10-07 08:50:00 | Alex Rivera | feat(dlq): persist unparseable payloads with quarantine flag |
| `fe2a892` | 2026-10-06 18:00:10 | Maya Chen | test(api): mock external webhook sender for integration tests |
| `0f3b9a3` | 2026-10-06 16:25:44 | Sam Miller | ci: add github action workflow for pytest and ruff |
| `1e4ca04` | 2026-10-06 14:10:30 | Alex Rivera | feat(models): define Transaction and Entry domain dataclasses |
| `2d5db15` | 2026-10-06 11:35:12 | Maya Chen | refactor(config): use pydantic-settings for typed environment vars |
| `3c6ec26` | 2026-10-05 17:50:00 | Alex Rivera | release: bump version to 0.2.0 |
| `4b7fd37` | 2026-10-05 15:20:19 | Sam Miller | feat(idempotency): implement redis setnx based mutex lock |
| `5a80e48` | 2026-10-05 11:45:00 | Maya Chen | feat(stripe): verify stripe-signature timestamp freshness |
| `6b91f59` | 2026-10-04 16:30:10 | Alex Rivera | feat(ledger): add basic in-memory append ledger engine |
| `7ca206a` | 2026-10-04 14:10:00 | Sam Miller | feat(api): create basic webhook router with /health and /events |
| `8db317b` | 2026-10-04 10:00:00 | Alex Rivera | init: initial project scaffolding with pyproject.toml and README |
