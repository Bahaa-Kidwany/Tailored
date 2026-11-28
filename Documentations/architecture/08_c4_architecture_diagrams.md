# 08 — C4 Architecture Diagrams (System Context, Container & Per-Service Components)

**Parent Index:** [Architecture Master Index](./README.md)  
**Scope:** Complete C4 Model (`Level 1: System Context`, `Level 2: Container`, and `Level 3: Component` diagrams for all 12 runtime services/workers plus `packages/tailored_kit`)

---

## 1. C4 Level 1 — System Context Diagram

Shows **Tailored** as a single platform, the **actors** who interact with it, and all **external systems** it depends on.

```mermaid
flowchart TB
    JobSeeker["Job Seeker (MENA & Global)\nDiscovers jobs, tailors CVs/CLs,\nchats with AI Coach, tracks pipeline"]
    Operator["Platform Operator / Admin\nMonitors SLOs, feature audits,\nAI evals & DLQs"]

    Tailored["Tailored Platform\nAI Career Copilot & Document Studio\n(12 Services + Polyglot Data + Observability)"]

    OAuth["Google & LinkedIn OAuth\nSSO Identity Providers"]
    Scrapers["External Job Sources\nApify (LinkedIn), Wuzzuf,\nCompany Career Pages"]
    LLMs["LLM Providers\nGoogle Gemini (Flash/Pro)\n& Anthropic Claude"]
    Payments["Payment Gateways\nPaymob (Card/Meeza/Wallet/Fawry)\n& Stripe"]
    Email["Transactional Email\nResend / Postmark"]
    Backups["Off-Site Backup Storage\nCloudflare R2 / Backblaze B2"]

    JobSeeker -->|"HTTPS (REST + SSE)\nWeb App & Telemetry"| Tailored
    Operator -->|"HTTPS (VPN/Admin)\nGrafana, Langfuse, Audit API"| Tailored

    Tailored -->|"OAuth 2.0 PKCE"| OAuth
    Tailored -->|"Job Sweeps & URL Fetch"| Scrapers
    Tailored -->|"Zero-Training Enterprise API"| LLMs
    Tailored -->|"Checkout & Signed Webhooks"| Payments
    Tailored -->|"OTP, Resets & Digests"| Email
    Tailored -->|"Encrypted WAL, Snapshots & Mirror"| Backups
```

---

## 2. C4 Level 2 — Container Diagram (Entire System Topology)

Shows every deployable container, its network segment (`edge_net`, `internal_mesh`, `data_net`, `sandbox_net`), and the communication channels between them.

```mermaid
flowchart TB
    SPA["React + Vite SPA\n(Browser: Telemetry SDK + SSE Client)"]

    subgraph EdgeNet["edge_net (Public 80/443)"]
        Traefik["traefik-gateway\nTraefik v3.2 (TLS 1.3, ForwardAuth,\nRate Limit, OTel Root Span, SSE)"]
    end

    subgraph InternalMesh["internal_mesh (Service-to-Service HTTP/SSE & OTel)"]
        Auth["auth-service :8001\nFastAPI"]
        Profile["profile-service :8002\nFastAPI"]
        Jobs["jobs-service :8003\nFastAPI"]
        Docs["documents-service :8004\nFastAPI"]
        Pipeline["pipeline-service :8005\nFastAPI"]
        Billing["billing-service :8006\nFastAPI"]
        AiAgent["ai-agent-service :8007\nFastAPI + LangGraph/PydanticAI"]
        Notif["notifications-service :8008\nFastAPI + Scheduler"]
        Telemetry["telemetry-audit-service :8009\nFastAPI + Batch Consumers"]
        Scraper["scraper-worker\nPlaywright + Apify + BS4"]
    end

    subgraph SandboxNet["sandbox_net (internal: true — NO Internet Egress)"]
        Latex["latex-worker\nNon-root Tectonic + ReportLab"]
    end

    subgraph DataNet["data_net (internal: true — Zero Outbound Internet)"]
        Redpanda["Redpanda Broker\n11 Topics + DLQs"]
        PG["PostgreSQL 16 + pgvector\n10 Logical DBs"]
        CH["ClickHouse 24\ntailored_analytics + tailored_audit"]
        Redis["Redis 7\nSessions, Rate Limits, Cache, Pub/Sub"]
        MinIO["MinIO S3\ncv-artifacts, user-uploads, invoices, gdpr-exports"]
    end

    subgraph ObsStack["observability Profile"]
        OTel["otel-collector :4317"]
        Tempo["Grafana Tempo (Traces)"]
        Loki["Grafana Loki (Logs)"]
        Prom["Prometheus (Metrics)"]
        Grafana["Grafana UI"]
        Langfuse["Self-Hosted Langfuse (AI Audit)"]
    end

    SPA -->|"HTTPS REST + SSE"| Traefik
    Traefik -->|"ForwardAuth /internal/verify"| Auth
    Traefik -->|"Trusted X-User-* + traceparent"| Auth & Profile & Jobs & Docs & Pipeline & Billing & AiAgent & Notif & Telemetry

    Auth & Profile & Jobs & Docs & Pipeline & Billing & AiAgent & Notif & Telemetry -->|"Logical DB"| PG
    Auth & Jobs & Billing & AiAgent & Notif & Telemetry & Scraper -->|"Cache / Locks / PubSub"| Redis
    Jobs & Docs & Billing & Scraper & Latex -->|"Objects"| MinIO
    Telemetry -->|"Batch Inserts"| CH

    Auth & Profile & Jobs & Docs & Pipeline & Billing & AiAgent & Notif & Telemetry -->|"Outbox Events"| Redpanda
    Redpanda -->|"Consumer Groups"| Scraper & Latex & AiAgent & Telemetry & Notif & Billing & Docs & Jobs & Profile

    Traefik & Auth & Profile & Jobs & Docs & Pipeline & Billing & AiAgent & Notif & Telemetry & Scraper & Latex -->|"OTLP :4317"| OTel
    OTel --> Tempo & Prom
    InternalMesh -->|"JSON Logs + trace_id"| Loki
    Tempo & Loki & Prom --> Grafana
    AiAgent -->|"Prompts, Tokens, Eval Scores"| Langfuse
```

---

## 3. Shared Cross-Cutting Foundation: `packages/tailored_kit`

Every Python microservice and worker imports `tailored_kit` so tracing, auth, auditing, outbox publishing, and resilience work identically everywhere.

```mermaid
flowchart LR
    Service["Any Python Microservice / Worker"]

    subgraph TailoredKit["packages/tailored_kit (Shared Editable SDK)"]
        Config["config.py\nBaseSettings & Service Metadata"]
        Errors["errors.py\nRFC 7807 ProblemDetail Handlers"]
        AuthCtx["auth/\nRequestContext, require_user, JWKS Client"]
        OTelMod["telemetry_otel/\nTracerProvider, MeterProvider, JSON Logging"]
        AuditMod["audit/\n@audit_feature Decorator, SHA-256 Hashing"]
        Messaging["messaging_redpanda/\nEventEnvelope, Idempotent Producer/Consumer + DLQ"]
        Outbox["outbox/\nOutboxEvent Model + SKIP LOCKED Relay"]
        Flags["feature_flags/\nOpenFeature Client (Redis-cached)"]
        HttpClient["http_client/\nhttpx + traceparent + Retries + pybreaker"]
    end

    Service --> Config & Errors & AuthCtx & OTelMod & AuditMod & Messaging & Outbox & Flags & HttpClient
```

---

## 4. C4 Level 3 — Component Diagrams (All 12 Services & Workers)

### 4.1 `traefik-gateway` (Edge API Gateway)

```mermaid
flowchart LR
    Client["React SPA / External Webhooks"]
    AuthVerify["auth-service\n/internal/verify"]
    RedisRL["Redis\nrl:{policy}:{key}"]
    OTel["otel-collector"]
    Backends["Internal Microservices\n(:8001–:8009)"]

    subgraph Traefik["traefik-gateway (edge_net + internal_mesh)"]
        TLS["TLS 1.3 Terminator\nACME Let's Encrypt"]
        HeaderScrub["Header Sanitizer\nStrips client X-User-* / X-Internal-*"]
        OTelRoot["OTel Middleware\nInjects W3C traceparent"]
        RateLimit["Rate Limiter\nPublic 30/m, Auth 5/m, API 120/m, AI 20/m"]
        ForwardAuth["ForwardAuth Middleware\nVerifies JWT + Revocation"]
        Router["Path Router & SSE Pass-Through\nZero-buffering for :stream"]
    end

    Client --> TLS --> HeaderScrub --> OTelRoot --> RateLimit --> ForwardAuth --> Router
    RateLimit <--> RedisRL
    ForwardAuth <-->|"JWT + Route"| AuthVerify
    OTelRoot --> OTel
    Router --> Backends
```

---

### 4.2 `auth-service` (`:8001`)

Owns identity, sessions, workspace ergonomics (Layer 1), privacy consents, feature flags, pseudonym vault, and GDPR erasure coordination.

```mermaid
flowchart TB
    Traefik["traefik-gateway"]
    OAuthExt["Google & LinkedIn OAuth"]
    NotifOut["Redpanda: identity.lifecycle.v1"]

    subgraph AuthSvc["auth-service (:8001)"]
        AuthAPI["Auth & Recovery Router\n/auth/register, login, refresh, otp, reset"]
        OAuthCtrl["OAuth PKCE Controller\nSole-login unlink guard"]
        AccountAPI["Account & Security Router\n/account/security, 2fa, sessions, prefs, privacy"]
        VerifyAPI["Internal ForwardAuth\n/internal/verify + /.well-known/jwks.json"]
        FlagSvc["Feature Flag Registry\nOpenFeature rules + rollout %"]
        GDPRCoord["GDPR Erasure Coordinator\nCrypto-shredding & Saga"]
        OutboxRelay["tailored_kit Outbox Relay"]
    end

    AuthDB[("auth_db (PG16)\nusers, oauth_identities, user_sessions,\notp_verifications, totp_mfa,\nworkspace_preferences, privacy_consents,\nfeature_flags, outbox_events")]
    VaultDB[("privacy_vault_db (PG16)\nidentity_pseudonyms\n(user_id <-> analytics_anon_id)")]
    Redis[("Redis\nsession:revoked:*, rl:*, ff:catalog")]

    Traefik --> AuthAPI & OAuthCtrl & AccountAPI & VerifyAPI
    OAuthCtrl <--> OAuthExt
    AuthAPI & OAuthCtrl & AccountAPI & VerifyAPI --> AuthDB
    FlagSvc --> AuthDB & Redis
    VerifyAPI --> Redis
    GDPRCoord --> AuthDB & VaultDB & Redis
    OutboxRelay --> AuthDB
    OutboxRelay --> NotifOut
```

---

### 4.3 `profile-service` (`:8002`)

Owns Master Career Identity (Layer 2), multi-persona tracks, multi-country phone resolution, and base LaTeX templates.

```mermaid
flowchart TB
    Traefik["traefik-gateway"]
    AiAgent["ai-agent-service\n(Internal REST)"]
    RPIn["Redpanda: identity.lifecycle.v1"]
    RPOut["Redpanda: profile.events.v1"]

    subgraph ProfileSvc["profile-service (:8002)"]
        ProfileAPI["Master Profile Router\n/profiles/me, onboarding-step"]
        PersonaAPI["Persona & Location Router\n/personas, active-persona, target_locations"]
        LatexParser["LaTeX CV Parser\n(Migrated LatexCvParser)"]
        TemplateSynth["Base .tex Synthesizer\n& Multi-Country Contact Resolver"]
        InternalAPI["Internal Summary API\n/internal/profiles/{user_id}/summary"]
        ErasureConsumer["GDPR Erasure Consumer"]
        OutboxRelay["tailored_kit Outbox Relay"]
    end

    ProfileDB[("profile_db (PG16)\nmaster_profiles, contact_numbers,\ntarget_locations, career_personas,\neducation_records, spoken_languages,\nbase_cv_templates, outbox_events")]
    MinIO[("MinIO: user-uploads")]

    Traefik --> ProfileAPI & PersonaAPI & LatexParser
    AiAgent --> InternalAPI
    ProfileAPI & PersonaAPI & LatexParser & TemplateSynth & InternalAPI --> ProfileDB
    LatexParser --> MinIO
    RPIn --> ErasureConsumer --> ProfileDB
    OutboxRelay --> ProfileDB
    OutboxRelay --> RPOut
```

---

### 4.4 `jobs-service` (`:8003`)

Owns public `/explore` feed, Radar feed, 5-D multi-persona Zero-Drop fit scoring, Interest List, and URL/JD/screenshot ingestion.

```mermaid
flowchart TB
    Traefik["traefik-gateway"]
    AiAgent["ai-agent-service\n(Extract JD / Context)"]
    RPIn["Redpanda: profile.events.v1,\njobs.events.v1, identity.lifecycle.v1"]
    RPOut["Redpanda: jobs.commands.v1,\njobs.events.v1"]

    subgraph JobsSvc["jobs-service (:8003)"]
        ExploreAPI["Public Explore Router\n/explore/jobs (sanitized)"]
        RadarAPI["Radar & Interest Router\n/jobs, /jobs/{id}, /interest, /hide"]
        IngestAPI["Ingest Coordinator\n/ingest-url, /extract-description, /ingest-screenshot"]
        Scorer5D["5-D Multi-Persona Scorer\nZero-Drop Deterministic Engine"]
        DedupHash["Canonical SHA-256 Deduplicator"]
        EventConsumer["Profile/Job Event Consumer\nRescores on persona/profile change"]
        OutboxRelay["tailored_kit Outbox Relay"]
    end

    JobsDB[("jobs_db (PG16)\njobs, job_fit_scores,\nuser_job_interactions,\nscrape_runs, outbox_events")]
    MinIO[("MinIO: user-uploads")]

    Traefik --> ExploreAPI & RadarAPI & IngestAPI
    AiAgent <--> RadarAPI & IngestAPI
    ExploreAPI & RadarAPI & IngestAPI & Scorer5D & DedupHash --> JobsDB
    IngestAPI --> MinIO
    RPIn --> EventConsumer --> Scorer5D --> JobsDB
    OutboxRelay --> JobsDB
    OutboxRelay --> RPOut
```

---

### 4.5 `scraper-worker` (Headless Async Worker)

Executes external scraping (Apify LinkedIn, Wuzzuf, company pages, Playwright) and screenshot OCR prep with spend protection.

```mermaid
flowchart LR
    RPIn["Redpanda:\njobs.commands.v1"]
    RPOut["Redpanda:\njobs.events.v1"]
    ExtSites["Apify / Wuzzuf /\nCompany Sites"]
    MinIO[("MinIO: user-uploads")]
    Redis[("Redis:\napify:daily_items:*")]

    subgraph ScraperWkr["scraper-worker (internal_mesh + data_net)"]
        CmdConsumer["Idempotent Consumer\n(scraper-worker-cg)"]
        BudgetGuard["Apify Spend Guard\nDaily item & actor caps"]
        ApifyRunner["Apify LinkedIn Runner\nJobs & Posts"]
        WuzzufRunner["Two-Tier Wuzzuf\n& Company Crawler"]
        PlaywrightRunner["Playwright Stealth Fetch\n& Screenshot OCR Prep"]
        Normalizer["Raw Posting Normalizer\n+ Canonical Hash"]
    end

    RPIn --> CmdConsumer --> BudgetGuard
    BudgetGuard <--> Redis
    BudgetGuard --> ApifyRunner & WuzzufRunner & PlaywrightRunner
    ApifyRunner & WuzzufRunner & PlaywrightRunner <--> ExtSites
    PlaywrightRunner <--> MinIO
    ApifyRunner & WuzzufRunner & PlaywrightRunner --> Normalizer --> RPOut
```

---

### 4.6 `documents-service` (`:8004`)

Owns Tailored CVs, Cover Letters, version history (`Cmd+Z`), Frozen Application Snapshots, MinIO streaming, and GDPR `.zip` export assembly.

```mermaid
flowchart TB
    Traefik["traefik-gateway"]
    Billing["billing-service\n(Internal /credits/hold)"]
    Pipeline["pipeline-service\n(Internal Snapshot Freeze)"]
    RPIn["Redpanda: documents.events.v1,\npipeline.events.v1, identity.lifecycle.v1"]
    RPOut["Redpanda: documents.commands.v1"]

    subgraph DocsSvc["documents-service (:8004)"]
        CvClAPI["CV & Cover Letter Router\n/cv-fit, /cover-letter, /undo, /recompile"]
        DownloadAPI["Artifact Streamer\n/download/{kind}"]
        UnlockGuard["Already-Unlocked Guard\n(0 cr check for existing job+persona)"]
        SnapshotMgr["Frozen Snapshot Manager\nCopies PDF/TEX on pipeline 'applied'"]
        GdprZip["GDPR Archive Builder\nAsync .zip across services"]
        StatusConsumer["Compile & Pipeline Consumer"]
        OutboxRelay["tailored_kit Outbox Relay"]
    end

    DocsDB[("documents_db (PG16)\ngenerated_documents, document_versions,\nfrozen_application_snapshots,\ngdpr_export_jobs, outbox_events")]
    MinIO[("MinIO: cv-artifacts,\ngdpr-exports")]

    Traefik --> CvClAPI & DownloadAPI
    CvClAPI --> UnlockGuard -->|"Net-new 1 cr"| Billing
    Pipeline --> SnapshotMgr
    CvClAPI & DownloadAPI & SnapshotMgr & GdprZip --> DocsDB
    DownloadAPI & SnapshotMgr & GdprZip <--> MinIO
    RPIn --> StatusConsumer --> DocsDB
    OutboxRelay --> DocsDB
    OutboxRelay --> RPOut
```

---

### 4.7 `latex-worker` (Sandboxed Compiler Worker)

Hardened non-root compiler with **no internet egress** (`sandbox_net`) that renders `.tex` via Tectonic (`--no-shell-escape`) with ReportLab ATS fallback.

```mermaid
flowchart LR
    RPIn["Redpanda:\ndocuments.commands.v1"]
    RPOut["Redpanda:\ndocuments.events.v1"]
    MinIO[("MinIO:\ncv-artifacts")]

    subgraph LatexWkr["latex-worker (sandbox_net + data_net ONLY)"]
        CmdConsumer["Idempotent Consumer\n(latex-worker-cg)"]
        Sanitizer["LaTeX Macro Unwrapper\n& Visual Template Enforcer"]
        Tectonic["Tectonic / XeLaTeX\n--no-shell-escape, 30s timeout,\nnon-root UID 10001, read-only root"]
        ReportLab["ReportLab ATS Fallback\nHigh-fidelity PDF generator"]
        Uploader["Artifact Uploader\nComputes SHA-256 & emits status"]
    end

    RPIn --> CmdConsumer --> Sanitizer --> Tectonic
    Tectonic -->|"On failure"| ReportLab
    Tectonic & ReportLab --> Uploader
    Uploader --> MinIO
    Uploader --> RPOut
```

---

### 4.8 `pipeline-service` (`:8005`)

Owns the multi-channel Application Pipeline CRM, interview round notes, 7-day follow-up state machine, and Gmail/`mailto:` outreach composer.

```mermaid
flowchart TB
    Traefik["traefik-gateway"]
    AiAgent["ai-agent-service\n(Internal ActionCard Execution)"]
    Docs["documents-service\n(Artifact Links)"]
    RPIn["Redpanda: identity.lifecycle.v1"]
    RPOut["Redpanda: pipeline.events.v1"]

    subgraph PipelineSvc["pipeline-service (:8005)"]
        PipeAPI["Pipeline CRM Router\n/pipeline, /metrics, /{id}"]
        RoundAPI["Interview Rounds Router\n/{id}/rounds"]
        OutreachComp["Outreach Package Composer\nGmail Web URL & mailto: URI"]
        StageMachine["Stage State Machine\nsaved -> in_process -> applied -> interview"]
        FollowUpChk["7-Day Follow-Up Evaluator"]
        OutboxRelay["tailored_kit Outbox Relay"]
    end

    PipeDB[("pipeline_db (PG16)\npipeline_items, interview_round_notes,\noutreach_dispatches, outbox_events")]

    Traefik --> PipeAPI & RoundAPI & OutreachComp
    AiAgent --> PipeAPI
    OutreachComp --> Docs
    PipeAPI & RoundAPI & StageMachine & FollowUpChk --> PipeDB
    RPIn --> PipeDB
    OutboxRelay --> PipeDB
    OutboxRelay --> RPOut
```

---

### 4.9 `billing-service` (`:8006`)

Owns optimistic-locked Credit Wallets, immutable credit ledger, regional packs (`EGP`/`SAR`/`AED`/`USD`), Paymob/Stripe webhooks, and the Credit Hold/Commit/Auto-Refund Saga.

```mermaid
flowchart TB
    Traefik["traefik-gateway"]
    Docs["documents-service\n(Internal Hold Request)"]
    Gateways["Paymob & Stripe\nCheckout + Webhooks"]
    RPIn["Redpanda: identity.lifecycle.v1,\ndocuments.events.v1"]
    RPOut["Redpanda: billing.events.v1"]

    subgraph BillingSvc["billing-service (:8006)"]
        WalletAPI["Wallet & Ledger Router\n/credits/balance, /packs, /ledger"]
        CheckoutAPI["Checkout & Invoice Router\n/credits/checkout, /orders/{id}, /invoices"]
        WebhookCtrl["Signed Webhook Verifier\nPaymob HMAC-SHA512 & Stripe Sig"]
        HoldSaga["Credit Hold / Commit / Refund Saga\nOptimistic-locked wallet + idempotency"]
        InvoiceGen["PDF Receipt Generator"]
        OutboxRelay["tailored_kit Outbox Relay"]
    end

    BillingDB[("billing_db (PG16)\ncredit_wallets, credit_ledger_entries,\ncredit_holds, credit_packs_catalog,\npayment_orders, outbox_events")]
    MinIO[("MinIO: invoices")]

    Traefik --> WalletAPI & CheckoutAPI & WebhookCtrl
    Gateways <--> CheckoutAPI & WebhookCtrl
    Docs --> HoldSaga
    RPIn --> HoldSaga
    WalletAPI & CheckoutAPI & WebhookCtrl & HoldSaga --> BillingDB
    InvoiceGen --> MinIO
    OutboxRelay --> BillingDB
    OutboxRelay --> RPOut
```

---

### 4.10 `ai-agent-service` (`:8007`)

Dual-Path AI Engine: **(A)** Interactive Studio Coach SSE + Paid CV/CL Generation + JD Extractor, and **(B)** Passive Ambient Behavioral Consumer + `pgvector` Memory + Calm Proactive Suggestions.

```mermaid
flowchart TB
    Traefik["traefik-gateway"]
    Prof["profile-service"]
    Jobs["jobs-service"]
    Pipe["pipeline-service"]
    Docs["documents-service"]
    LLMs["Gemini Flash/Pro & Claude"]
    Langfuse["Self-Hosted Langfuse"]
    RPIn["Redpanda: telemetry.interactions.v1,\ndocuments.commands.v1, jobs/pipeline events"]
    RPOut["Redpanda: documents.commands.v1,\ndocuments.events.v1, ai.events.v1"]

    subgraph AiSvc["ai-agent-service (:8007)"]
        CoachAPI["Studio Coach SSE & Memory API\n/agent/threads, :stream, /branch,\n/proposals/resolve, /actions/confirm, /memory"]
        CtxAsm["Context Assembler\n(~8k token budget + Top-K pgvector)"]
        Runtime["Stateful Agent Runtime\nLangGraph / PydanticAI + Checkpoints"]
        MetricGuard["Zero-Hallucination Metric Guard\nBlocks unverified numbers"]
        ModelRouter["Tiered Multi-Model Router\nTier 0 Rules -> Tier 1 Flash -> Tier 2 Pro/Claude"]
        TailorOrch["Paid CV/CL Tailor & JD Extractor"]
        BehaviorConsumer["Ambient Behavior Consumer (ai-behavior-cg)\nConsent Gate -> Tier 0 -> Tier 1 Distiller -> Nudges"]
        OutboxRelay["tailored_kit Outbox Relay"]
    end

    AiDB[("ai_agent_db (PG16 + pgvector)\nuser_behavior_profiles, behavioral_memory_facts,\nagent_threads, agent_checkpoints, agent_messages,\nproposal_cards, proactive_suggestions, outbox_events")]
    Redis[("Redis: ai:nudge:cooldown:*")]

    Traefik --> CoachAPI
    CoachAPI --> CtxAsm --> Runtime --> MetricGuard --> ModelRouter
    CtxAsm <--> Prof & Jobs & Pipe & Docs
    ModelRouter <--> LLMs
    Runtime & BehaviorConsumer --> Langfuse
    TailorOrch --> ModelRouter
    RPIn --> TailorOrch & BehaviorConsumer
    BehaviorConsumer <--> Redis
    CoachAPI & CtxAsm & Runtime & BehaviorConsumer --> AiDB
    OutboxRelay --> AiDB
    OutboxRelay --> RPOut
```

---

### 4.11 `notifications-service` (`:8008`)

Owns the signal-focused Inbox & Bell Drawer, snooze wakeups, live SSE push via Redis Pub/Sub, and transactional/digest emails.

```mermaid
flowchart TB
    Traefik["traefik-gateway"]
    EmailExt["Resend / Postmark"]
    RPIn["Redpanda: identity.lifecycle.v1,\njobs/documents/pipeline/billing/ai events"]

    subgraph NotifSvc["notifications-service (:8008)"]
        NotifAPI["Inbox & Rules Router\n/notifications, /read, /snooze, /mark-all-read"]
        SSEPush["SSE Live Stream\n/notifications/stream"]
        EventFanIn["Multi-Topic Event Consumer\nDeduplicates & formats 5 signal categories"]
        SnoozeSched["Snooze & Digest Scheduler"]
        EmailSender["Transactional & Digest Emailer"]
    end

    NotifDB[("notifications_db (PG16)\nnotifications, notification_rules,\nemail_dispatch_logs, processed_events")]
    Redis[("Redis Pub/Sub\nsse:notif:{user_id}")]

    Traefik --> NotifAPI & SSEPush
    RPIn --> EventFanIn --> NotifDB
    EventFanIn --> Redis --> SSEPush
    SnoozeSched --> NotifDB & Redis & EmailSender
    EmailSender --> EmailExt
    EmailSender --> NotifDB
```

---

### 4.12 `telemetry-audit-service` (`:8009`)

Owns batched frontend micro-signal ingestion, PII scrubbing, pseudonym lookup, high-throughput ClickHouse batch writers, and admin Feature Audit query APIs.

```mermaid
flowchart TB
    Traefik["traefik-gateway"]
    VaultDB[("privacy_vault_db (PG16)\nRead-only pseudonym lookup")]
    Redis[("Redis: anon_map:{user_id}")]
    RPBus["Redpanda:\ntelemetry.interactions.v1\n& audit.trail.v1"]
    CH[("ClickHouse 24\ntailored_analytics.user_behavior_events\ntailored_audit.feature_audit_logs")]

    subgraph TelemetrySvc["telemetry-audit-service (:8009)"]
        IngestAPI["Batch Telemetry Ingest\nPOST /api/v1/telemetry/events (202)"]
        Scrubber["Consent & Allow-List Scrubber\nStrips PII keys"]
        AnonResolver["Pseudonym Resolver\nCached user_id -> analytics_anon_id"]
        AnalyticsWriter["ClickHouse Analytics Batch Consumer\n(clickhouse-analytics-cg)"]
        AuditWriter["ClickHouse Audit Batch Consumer\n(clickhouse-audit-cg)"]
        AuditQueryAPI["Admin Feature Audit API\n/admin/audit/features, /traces/{id}"]
    end

    Traefik --> IngestAPI & AuditQueryAPI
    IngestAPI --> Scrubber --> AnonResolver --> RPBus
    AnonResolver <--> Redis
    AnonResolver <--> VaultDB
    RPBus --> AnalyticsWriter & AuditWriter --> CH
    AuditQueryAPI --> CH
```

---

## 5. Quick Mapping: Services, Stores & Event Topics

| Component | Owned Database / Store | Produces to Redpanda | Consumes from Redpanda |
| :--- | :--- | :--- | :--- |
| `traefik-gateway` | Redis (rate limits) | — | — |
| `auth-service` | `auth_db`, `privacy_vault_db`, Redis | `identity.lifecycle.v1`, `audit.trail.v1` | `identity.lifecycle.v1` (erasure acks) |
| `profile-service` | `profile_db`, MinIO | `profile.events.v1`, `audit.trail.v1` | `identity.lifecycle.v1` |
| `jobs-service` | `jobs_db`, MinIO | `jobs.commands.v1`, `jobs.events.v1`, `audit.trail.v1` | `profile.events.v1`, `jobs.events.v1`, `identity.lifecycle.v1` |
| `scraper-worker` | Redis, MinIO | `jobs.events.v1` | `jobs.commands.v1` |
| `documents-service` | `documents_db`, MinIO | `documents.commands.v1`, `audit.trail.v1` | `documents.events.v1`, `pipeline.events.v1`, `identity.lifecycle.v1` |
| `latex-worker` | MinIO (`cv-artifacts`) | `documents.events.v1` | `documents.commands.v1` |
| `pipeline-service` | `pipeline_db` | `pipeline.events.v1`, `audit.trail.v1` | `identity.lifecycle.v1` |
| `billing-service` | `billing_db`, MinIO (`invoices`) | `billing.events.v1`, `audit.trail.v1` | `identity.lifecycle.v1`, `documents.events.v1` |
| `ai-agent-service` | `ai_agent_db` (`pgvector`), Redis | `documents.commands.v1`, `documents.events.v1`, `ai.events.v1`, `audit.trail.v1` | `telemetry.interactions.v1`, `documents.commands.v1`, `jobs.events.v1`, `pipeline.events.v1`, `profile.events.v1`, `identity.lifecycle.v1` |
| `notifications-service` | `notifications_db`, Redis Pub/Sub | `audit.trail.v1` | `identity.lifecycle.v1`, `jobs.events.v1`, `documents.events.v1`, `pipeline.events.v1`, `billing.events.v1`, `ai.events.v1` |
| `telemetry-audit-service` | ClickHouse (`tailored_analytics`, `tailored_audit`), Redis | `telemetry.interactions.v1` | `telemetry.interactions.v1`, `audit.trail.v1`, `ai.events.v1` |
