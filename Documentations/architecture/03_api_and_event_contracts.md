# 03 — API Gateway & Redpanda Event Contracts

**Parent Index:** [Architecture Master Index](./README.md)  
**Scope:** External Edge APIs (`/api/v1/*`), SSE Protocols, Webhooks & Redpanda Event Mesh (11 Topics)

---

## 1. Global Edge API Conventions

All external traffic enters via `traefik-gateway` over HTTPS (`https://api.tailored.app/api/v1/...` or `/api/v1/...` same-origin proxy).

### 1.1 Standard Headers

| Header | Direction | Required | Format & Semantics |
| :--- | :--- | :---: | :--- |
| `Authorization` | Client -> Edge | Protected routes | `Bearer <RS256_JWT>` (15-min TTL; refreshed via `HttpOnly` rotating cookie or `/auth/refresh`) |
| `traceparent` | Client -> Edge -> Mesh | Recommended | W3C Trace Context (`00-{32-hex-trace-id}-{16-hex-span-id}-01`); Traefik generates one if omitted |
| `X-Feature-Key` | Client -> Edge -> Mesh | Recommended | Canonical UX feature identifier (e.g., `studio.cv.tailor`); falls back to route-level feature mapping if absent |
| `Idempotency-Key` | Client -> Edge | All POST mutations | Client UUIDv4 preventing double charges or duplicate creations on retry |
| `If-Match` / `version` | Client -> Edge | Optimistic edits | Resource `version` integer (`master_profiles`, `generated_documents`) returning `409 Conflict` on stale write |
| `X-Trace-Id` | Edge -> Client | Always returned | Echoes 32-hex `trace_id` on every response (including errors) for support debugging |

### 1.2 Standard Error Contract (RFC 7807)

```json
{
  "type": "https://tailored.app/errors/insufficient-credits",
  "title": "Insufficient Credits",
  "status": 402,
  "detail": "Tailoring a new CV requires 1 credit, but your available balance is 0.",
  "error_code": "INSUFFICIENT_CREDITS",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "feature_key": "studio.cv.tailor",
  "metadata": {
    "required_credits": 1,
    "available_credits": 0,
    "resume_action": "tailor_cv"
  }
}
```

### 1.3 Pagination & SSE Wire Format

- **Cursor Pagination:** `GET /api/v1/... ?cursor=<opaque>&limit=25` returns `{ "items": [...], "next_cursor": "...", "total_estimate": 142 }`.
- **SSE Frame Format:** Standard `text/event-stream` with `id:`, `event:`, `data:` JSON lines and `15s` `: heartbeat` keepalive comments.

---

## 2. Complete REST & SSE Endpoint Catalog (Mapped to 22 UX Blueprints)

### 2.1 Auth, Identity, Preferences, Privacy & Feature Flags (`auth-service`)

Covers UX specs `00`, `03`, `04`, `19`, `21`.

| Method | Path | Auth | UX Spec | Purpose |
| :--- | :--- | :---: | :---: | :--- |
| `POST` | `/api/v1/auth/register` | Public | `03` | Register email/password -> issues unverified session + triggers 6-digit OTP |
| `POST` | `/api/v1/auth/login` | Public | `03` | Authenticate email/password (+ TOTP challenge if 2FA enabled) |
| `POST` | `/api/v1/auth/refresh` | Refresh Cookie | `03` | Rotate refresh token and issue fresh 15-min RS256 access JWT |
| `POST` | `/api/v1/auth/logout` | User | `19` | Revoke current `session_id` immediately in Redis & DB |
| `GET` | `/api/v1/auth/oauth/{provider}/start` | Public | `03` | Google / LinkedIn OAuth PKCE redirect (preserves `pendingIntent` state token) |
| `GET` | `/api/v1/auth/oauth/{provider}/callback` | Public | `03` | Exchanges code, links/creates user, issues tokens |
| `POST` | `/api/v1/auth/verify-email` | User/OTP | `04` | Validates 6-digit OTP -> unlocks starter 2-credit grant (`user.verified`) |
| `POST` | `/api/v1/auth/otp/resend` | Public | `04` | Rate-limited OTP resend (`60s` cooldown) |
| `POST` | `/api/v1/auth/forgot-password` | Public | `04` | Sends password-reset OTP/link (anti-enumeration constant-time response) |
| `POST` | `/api/v1/auth/reset-password` | Public | `04` | Resets password and revokes all active sessions |
| `GET` | `/api/v1/account/security` | User | `19` | Email, password status, linked SSO providers, 2FA status (`can_unlink_oauth` flags) |
| `POST` | `/api/v1/account/change-email` | User | `19` | Keeps current email active until new email OTP verifies |
| `POST` | `/api/v1/account/change-password` | User | `19` | Sets/updates password (satisfies OAuth unlink guard) |
| `DELETE` | `/api/v1/account/oauth/{provider}` | User | `19` | Unlinks SSO only if password or another SSO exists (`400` otherwise) |
| `POST` | `/api/v1/account/2fa/setup` & `/enable` & `/disable` | User | `19` | TOTP secret QR + single-use recovery code generation/verification |
| `GET` / `DELETE` | `/api/v1/account/sessions` & `/{session_id}` | User | `19` | Lists active devices & revokes single/all other sessions immediately |
| `GET` / `PATCH` | `/api/v1/account/preferences` | User | `19` | Layer 1 Workspace Ergonomics (`home_route`, `density`, `studio_mode`, `currency`, `chat_side`) |
| `GET` / `PATCH` | `/api/v1/account/privacy` | User | `19` | Granular toggles (`analytics_micro_signals`, `ai_passive_learning`, `proactive_nudges`) |
| `GET` | `/api/v1/flags` | Optional | `00` | Evaluates active feature flags for current user/anon session |
| `POST` | `/api/v1/account/export` & `GET /export/{id}` | User | `19` | Triggers async GDPR `.zip` archive (`documents-service`) & returns status/link |
| `DELETE` | `/api/v1/account` | User | `19` | Password/2FA + `"DELETE"` verification -> starts GDPR Crypto-Shredding Erasure Saga |

### 2.2 Master Profile & Personas (`profile-service`)

Covers UX specs `01`, `05`, `17`.

| Method | Path | Auth | UX Spec | Purpose |
| :--- | :--- | :---: | :---: | :--- |
| `GET` / `PUT` | `/api/v1/profiles/me` | User | `05`, `17` | Reads/updates full assembled `UserProfile` with `version` optimistic locking |
| `POST` | `/api/v1/profiles/me/onboarding-step` | User | `05` | Saves partial steps `1..6` smoothly without losing progress |
| `POST` | `/api/v1/profiles/parse-latex` | User/Public* | `01`, `05`, `17` | Parses `.tex` CV via [LatexCvParser](file:///d:/Tailored/backend/app/pipeline/latex_cv_parser.py#L138) (*rate-limited preview on Landing) |
| `POST` / `PATCH` / `DELETE` | `/api/v1/profiles/me/personas` & `/{persona_id}` | User | `17` | Add, edit, delete, or set primary Career Persona |
| `PATCH` | `/api/v1/profiles/me/active-persona` | User | `00`, `17` | Persists active persona switcher selection across devices |
| `GET` / `POST` | `/api/v1/profiles/me/base-templates` | User | `11`, `17` | Synthesizes or uploads base LaTeX templates |

### 2.3 Job Discovery, Public Explore, 5-D Fit & Interest List (`jobs-service`)

Covers UX specs `01`, `02`, `07`, `08`, `09`, `10`.

| Method | Path | Auth | UX Spec | Purpose |
| :--- | :--- | :---: | :---: | :--- |
| `GET` | `/api/v1/explore/jobs` | Public | `02` | Sanitized public preview feed (strips direct recruiter emails & personal scores) |
| `POST` | `/api/v1/jobs/auto-search` | User | `08` | Triggers background `scraper-worker` sweep (`scrape_run_id`) + immediate cached ranked feed |
| `GET` | `/api/v1/jobs` | User | `07`, `08` | Personalized Zero-Drop ranked Radar feed (`?persona_id=&source=&min_score=&include_hidden=false`) |
| `GET` | `/api/v1/jobs/{job_id}` | User | `09` | Full job detail + 5-D Multi-Persona Fit Breakdown + Tailoring Opportunities |
| `POST` | `/api/v1/jobs/ingest-url` | User | `01`, `10` | Enqueues/fetches URL via [UrlJobFetcher](file:///d:/Tailored/backend/app/pipeline/url_job_fetcher.py#L18), extracts `JobInsights`, scores fit, saves to Interest |
| `POST` | `/api/v1/jobs/extract-description` | User | `01`, `10` | Extracts pasted JD text via `ai-agent-service` Flash tier, scores fit, saves to Interest |
| `POST` | `/api/v1/jobs/ingest-screenshot` | User | `10` | Uploads JD image to MinIO -> Vision OCR extraction -> scores fit -> Interest |
| `GET` / `POST` / `DELETE` | `/api/v1/interest` & `/{job_id}` | User | `10` | Lists, bookmarks, or removes jobs from Interest List |
| `POST` / `DELETE` | `/api/v1/jobs/{job_id}/hide` | User | `08` | Quiet `X` Hide triage (with `[Undo]` support via `DELETE`) |

### 2.4 CV Studio, Cover Letter Studio & Document Archive (`documents-service`)

Covers UX specs `11`, `12`, `13`, `14`.

| Method | Path | Auth | UX Spec | Purpose |
| :--- | :--- | :---: | :---: | :--- |
| `POST` | `/api/v1/cv-fit` | User | `12` | Checks `already_unlocked` (`0 cr`) or places `1 cr` hold -> queues AI tailor + LaTeX compile |
| `GET` | `/api/v1/cv-fit` & `/{doc_id}` | User | `11`, `12` | Lists tailored CVs or fetches full `.tex`, `section_plan`, `bullet_diffs`, compile status |
| `PATCH` | `/api/v1/cv-fit/{doc_id}` | User | `12` | Saves manual LaTeX/inline edits (`0 cr`), creates `document_versions` entry, optionally triggers recompile |
| `POST` | `/api/v1/cv-fit/{doc_id}/recompile` | User | `12` | Enqueues `latex-worker` compile (`0 cr` for already unlocked document) |
| `POST` | `/api/v1/cv-fit/{doc_id}/undo` | User | `12` | Restores prior `version_no` cleanly |
| `GET` | `/api/v1/cv-fit/{doc_id}/download/{kind}` | User | `11`, `12` | Streams `pdf` or `tex` cleanly from MinIO (`0 cr`) |
| `POST` | `/api/v1/cover-letter` | User | `13`, `14` | Places `1 cr` hold -> drafts tailored cover letter -> commits `1 cr` (or auto-refunds on error) |
| `GET` / `PATCH` | `/api/v1/cover-letter` & `/{doc_id}` | User | `13` | Lists, fetches, or edits cover letters (`0 cr`) |
| `GET` | `/api/v1/cover-letter/{doc_id}/download` | User | `13`, `14` | Downloads clean PDF/TXT/MD cover letter |

### 2.5 Application Pipeline CRM & Outreach (`pipeline-service`)

Covers UX specs `07`, `14`, `15`, `16`.

| Method | Path | Auth | UX Spec | Purpose |
| :--- | :--- | :---: | :---: | :--- |
| `GET` / `POST` | `/api/v1/pipeline` | User | `15` | Lists action-sorted pipeline items (`?status=&q=`) or adds job (`saved`/`in_process`) |
| `GET` | `/api/v1/pipeline/metrics` | User | `07`, `15` | Counts across stages (`total`, `in_process`, `applied`, `interview`, `overdue_followups`) |
| `GET` / `PATCH` / `DELETE` | `/api/v1/pipeline/{item_id}` | User | `15`, `16` | Updates stage (`applied` freezes snapshot + schedules 7d follow-up), notes, recruiter email |
| `POST` / `PATCH` | `/api/v1/pipeline/{item_id}/rounds` | User | `16` | Adds or edits structured interview round notes |
| `GET` | `/api/v1/pipeline/{item_id}/outreach` | User | `14` | Generates Gmail Web URL, `mailto:` URI, subject, body & artifact links |
| `POST` | `/api/v1/pipeline/{item_id}/dispatch` | User | `14` | Marks dispatched, logs `outreach_dispatches`, freezes documents snapshot |

### 2.6 Credits Wallet, Checkout & Webhooks (`billing-service`)

Covers UX specs `00`, `06`, `18`.

| Method | Path | Auth | UX Spec | Purpose |
| :--- | :--- | :---: | :---: | :--- |
| `GET` | `/api/v1/credits/balance` | User | `00`, `18` | Live `available_credits`, `held_credits`, `low_balance_threshold`, currency |
| `GET` | `/api/v1/credits/packs` | Optional | `06`, `18` | Regional pack catalog (`?currency=EGP|SAR|AED|USD`) |
| `GET` | `/api/v1/credits/ledger` | User | `18` | Chronological usage, pack purchases, and automatic compile-failure refunds |
| `POST` | `/api/v1/credits/checkout` | User | `06`, `18` | Creates Paymob (Card/Meeza/Wallet/Fawry) or Stripe checkout session/client secret |
| `GET` | `/api/v1/credits/orders/{order_id}` | User | `18` | Polls pending Fawry reference status |
| `GET` | `/api/v1/credits/invoices/{order_id}/pdf` | User | `18` | Streams receipt PDF from MinIO `invoices` |
| `POST` | `/api/v1/webhooks/paymob` | HMAC Verified | `18` | Paymob async callback -> idempotently grants credits + emits `billing.pack.purchased` |
| `POST` | `/api/v1/webhooks/stripe` | Sig Verified | `18` | Stripe webhook -> idempotently grants credits + emits `billing.pack.purchased` |

### 2.7 AI Agent Coach & Behavioral Memory (`ai-agent-service`)

Covers UX specs `00`, `12`, `13`, `19`.

| Method | Path | Auth | UX Spec | Purpose |
| :--- | :--- | :---: | :---: | :--- |
| `GET` / `POST` | `/api/v1/agent/threads` | User | `12`, `13` | Lists thread history (`[History ▾]`) or creates a role/workspace thread |
| `GET` | `/api/v1/agent/threads/{thread_id}` | User | `12`, `13` | Loads messages, collapsed receipts, and checkpoints |
| `POST` | `/api/v1/agent/threads/{thread_id}/messages:stream` | User | `00`, `12`, `13` | **SSE Stream:** `thinking_step`, `text_delta`, `proposal_card`, `action_card`, `resource_list`, `audit_summary`, `done` (`0 cr`) |
| `POST` | `/api/v1/agent/threads/{thread_id}/branch` | User | `00 §5.3` | Rewinds to prior `checkpoint_id` and streams edited user branch |
| `POST` | `/api/v1/agent/proposals/{proposal_id}/resolve` | User | `00`, `12`, `13` | `action: apply | skip | undo | refine` -> updates `documents-service` + records Langfuse eval score |
| `POST` | `/api/v1/agent/actions/{action_id}/confirm` | User | `00`, `12`, `13` | Executes confirmed cross-service `ActionCard` (e.g., `pipeline_stage`) or cancels |
| `GET` / `DELETE` | `/api/v1/agent/memory` & `/{fact_id}` | User | `19` | **AI Memory Inspector:** lists learned behavioral facts + source provenance, deletes single fact, or wipes all memory |
| `POST` | `/api/v1/agent/suggestions/{id}/resolve` | User | `07`, `20` | Records `clicked` / `dismissed` for proactive suggestion calibration |

### 2.8 Notifications, Telemetry & Admin Audits (`notifications-service` & `telemetry-audit-service`)

| Method | Path | Auth | UX Spec | Purpose |
| :--- | :--- | :---: | :---: | :--- |
| `GET` | `/api/v1/notifications` | User | `20` | Lists active inbox notifications (`?category=&unread_only=`) |
| `GET` | `/api/v1/notifications/stream` | User | `00`, `20` | **SSE Stream:** Live badge updates, compile completions, AI insights (`Redis Pub/Sub`) |
| `PATCH` | `/api/v1/notifications/{id}/read` & `/snooze` | User | `20` | Marks read/archived or sets `snoozed_until` |
| `POST` | `/api/v1/notifications/mark-all-read` | User | `20` | Bulk mark read |
| `POST` | `/api/v1/telemetry/events` | Optional | `00`–`21` | High-throughput batched micro-signal ingestion (`202 Accepted`) |
| `GET` | `/api/v1/admin/audit/features` & `/traces/{trace_id}` | Admin | Ops | Queries ClickHouse `feature_audit_logs` & joins metrics across services |

---

## 3. Redpanda Event Bus Specification

### 3.1 Canonical Event Envelope (JSON Schema)

Every message published onto Redpanda conforms to `EventEnvelope` in `tailored_kit`:

```json
{
  "event_id": "019a2f7e-4b10-7c21-9d44-8a1e5502c001",
  "event_type": "documents.compile.succeeded",
  "schema_version": "1.0",
  "occurred_at": "2026-11-26T10:15:30.412Z",
  "producer_service": "latex-worker",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "feature_key": "studio.cv.tailor",
  "idempotency_key": "doc_88412_v1_compile",
  "actor": {
    "user_id": "019a2f10-0001-7000-8000-000000000042",
    "analytics_anon_id": "019a2f11-9910-7000-8000-111111110099"
  },
  "payload": {
    "doc_id": "doc_88412",
    "credit_hold_id": "019a2f7d-1200-7000-8000-000000000007",
    "pdf_object_key": "019a2f10.../doc_88412/v1/cv.pdf",
    "compiler": "tectonic"
  }
}
```
- **Kafka Record Headers:** `traceparent`, `X-Feature-Key`, `schema_version`, `event_type` are mirrored into Kafka headers so OTel consumer instrumentation continues spans without deserializing payloads first.

### 3.2 Redpanda Topic Registry (11 Topics + DLQs)

| # | Topic Name | Partitions | Partition Key | Retention | Producer(s) | Consumer Group(s) | Key Events |
| :-: | :--- | :---: | :--- | :---: | :--- | :--- | :--- |
| 1 | `identity.lifecycle.v1` | `3` | `user_id` | `30d` | `auth-service` | `billing-starter-cg`, `profile-init-cg`, `all-erasure-cgs`, `notif-email-cg` | `user.registered`, `user.verified`, `user.erasure.requested`, `service.erasure.completed`, `privacy.consent.updated` |
| 2 | `profile.events.v1` | `3` | `user_id` | `14d` | `profile-service` | `jobs-rescore-cg`, `ai-context-cg` | `profile.updated`, `persona.changed`, `profile.latex_parsed` |
| 3 | `jobs.commands.v1` | `6` | `user_id` | `7d` | `jobs-service` | `scraper-worker-cg` | `scrape.radar.requested`, `ingest.url.requested`, `ingest.screenshot.requested` |
| 4 | `jobs.events.v1` | `6` | `canonical_hash` | `14d` | `scraper-worker`, `jobs-service` | `ai-jd-extractor-cg`, `jobs-scorer-cg`, `notif-match-cg` | `job.raw.discovered`, `job.insights.extracted`, `job.high_match.detected` |
| 5 | `documents.commands.v1` | `6` | `user_id` | `7d` | `documents-service`, `ai-agent-service` | `ai-tailor-cg`, `latex-worker-cg`, `gdpr-export-cg` | `cv.tailor.requested`, `cover_letter.draft.requested`, `latex.compile.requested`, `gdpr.export.requested` |
| 6 | `documents.events.v1` | `6` | `user_id` | `30d` | `ai-agent-service`, `latex-worker`, `documents-service` | `docs-status-cg`, `billing-saga-cg`, `notif-doc-cg` | `cv.tailor.failed`, `latex.compile.succeeded`, `latex.compile.failed`, `gdpr.export.ready` |
| 7 | `pipeline.events.v1` | `3` | `user_id` | `30d` | `pipeline-service` | `docs-freeze-cg`, `notif-followup-cg`, `ai-behavior-cg` | `pipeline.item.applied`, `pipeline.followup.due`, `pipeline.interview.scheduled` |
| 8 | `billing.events.v1` | `3` | `user_id` | `90d` | `billing-service` | `notif-billing-cg`, `audit-sink-cg` | `credits.pack.purchased`, `credits.low_balance`, `credits.refunded` |
| 9 | `telemetry.interactions.v1` | `12` | `analytics_anon_id` | `7d` | `telemetry-audit-service` | `clickhouse-analytics-cg`, `ai-behavior-cg` | `ui.job.dwelled`, `ui.jd.scrolled`, `ui.job.hidden`, `ui.studio.abandoned`, `ui.proposal.resolved`, `ui.cmdk.queried` |
| 10 | `ai.events.v1` | `6` | `user_id` | `30d` | `ai-agent-service` | `notif-ai-cg`, `langfuse-eval-cg`, `clickhouse-analytics-cg` | `ai.proposal.resolved`, `ai.memory.distilled`, `ai.suggestion.emitted`, `ai.metric.intercepted` |
| 11 | `audit.trail.v1` | `6` | `feature_key` | `90d` | All services (`@audit_feature`) | `clickhouse-audit-cg` | `audit.feature.executed` |

---

## 4. Transactional Outbox, Retries & Dead-Letter Queue (DLQ) Rules

1. **Outbox Relay Loop (`tailored_kit.outbox.relay`):** Each service runs an internal asyncio background task (or sidecar process) polling `WHERE published_at IS NULL ORDER BY created_at LIMIT 100 FOR UPDATE SKIP LOCKED` every `200ms` (with instant `pg_notify` wakeup on insert), publishing batches to Redpanda with `acks="all"`, and stamping `published_at = NOW()`.
2. **Idempotent Consumption:** Before handling any event, `tailored_kit.messaging_redpanda.consumer` opens a DB transaction and executes `INSERT INTO processed_events(event_id, consumer_group) VALUES (:id, :cg) ON CONFLICT DO NOTHING`. If `rowcount == 0`, the offset is committed immediately as a duplicate.
3. **Retry & DLQ Escalation:** Transient failures retry up to `5` times with exponential backoff (`1s, 4s, 16s, 60s, 300s` via retry topic or async delay) before moving the envelope + exception stack + `trace_id` to `<topic>.dlq` and firing a Prometheus alert. Operators inspect and replay DLQ events via a `tailored_kit` CLI script after fixing the root cause.
