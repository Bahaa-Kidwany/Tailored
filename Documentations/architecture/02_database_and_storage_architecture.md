# 02 — Database & Polyglot Storage Architecture

**Parent Index:** [Architecture Master Index](./README.md)  
**Storage Engines:** PostgreSQL 16 (+ `pgvector`), ClickHouse, Redis 7, MinIO (S3-Compatible Object Store)

---

## 1. Logical Database-per-Service Isolation Design

In production and local Docker Compose, a single tuned PostgreSQL 16 cluster hosts **10 logically isolated databases** (9 domain databases + `langfuse_db`). Each microservice connects using its own **least-privilege PostgreSQL role** whose permissions are strictly scoped to its own database—making cross-service SQL joins technically impossible.

### 1.1 Isolation & Evolution Rules

1. **Zero Cross-DB Foreign Keys or Joins:** Cross-service references store immutable UUIDv7 identifiers (e.g., `user_id`, `job_id`, `doc_id`) and exchange snapshots or resolve enrichment via internal REST / Redpanda events.
2. **Independent Alembic Trees:** Every service owns `services/<name>/alembic/versions/` and executes schema migrations independently in CI/CD before rolling traffic.
3. **UUIDv7 Primary Keys:** Time-ordered UUIDv7 keys avoid sequential ID enumeration across public URLs (`/jobs/:id`, `/pipeline/:id`) while preserving B-Tree insert locality. Legacy integer IDs from the prototype (`jobs.id`, `user_profiles.id`) are handled via an optional `legacy_int_id` bridge column during cutover.
4. **Shared Outbox & Consumer Dedup Pattern:** Every transactional PostgreSQL database includes `outbox_events` and `processed_events` tables managed by `tailored_kit`.
5. **Zero-Rewrite VPS-to-Cluster Split:** Moving `ai_agent_db` or `jobs_db` onto a separate PostgreSQL VPS in the future requires only changing one `DATABASE_URL` environment variable.

```sql
-- Standard Outbox & Consumer Idempotency Tables (present in every transactional DB)
CREATE TABLE outbox_events (
    event_id        UUID PRIMARY KEY,
    aggregate_type  VARCHAR(64) NOT NULL,
    aggregate_id    VARCHAR(128) NOT NULL,
    topic           VARCHAR(128) NOT NULL,
    event_type      VARCHAR(128) NOT NULL,
    partition_key   VARCHAR(128) NOT NULL,
    payload         JSONB NOT NULL,
    headers         JSONB NOT NULL DEFAULT '{}'::jsonb, -- traceparent, feature_key, schema_version
    published_at    TIMESTAMPTZ,
    retry_count     INT NOT NULL DEFAULT 0,
    last_error      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_outbox_unpublished ON outbox_events (created_at) WHERE published_at IS NULL;

CREATE TABLE processed_events (
    event_id        UUID PRIMARY KEY,
    consumer_group  VARCHAR(128) NOT NULL,
    processed_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 2. The 3-Layer User Profile & Preferences Architecture

Because Tailored serves explicit user customization ([17_master_profile_and_personas.md](file:///d:/Tailored/frontend/ux_designs/17_master_profile_and_personas.md), [19_account_security_and_preferences.md](file:///d:/Tailored/frontend/ux_designs/19_account_security_and_preferences.md)) **and** passive AI behavioral adaptation, user state is cleanly separated into **three distinct architectural layers** across three isolated databases:

```mermaid
flowchart LR
    subgraph Layer1["Layer 1: Account, Ergonomics & Privacy (auth_db)"]
        L1A["Credentials, OAuth, 2FA, Active Sessions"]
        L1B["Workspace Preferences (home_route, density, studio_mode, currency, chat_side)"]
        L1C["Privacy Consents (telemetry_enabled, ai_behavior_learning, proactive_nudges)"]
    end

    subgraph Layer2["Layer 2: Master Career Identity (profile_db)"]
        L2A["PersonalInfo + Multi-Country Contacts (+20, +966, +971)"]
        L2B["Residence, Relocation & Target Locations"]
        L2C["CareerPersonas (title, bio, skills, experience, projects, certs)"]
        L2D["Education, Languages, CustomSections, Base LaTeX Templates"]
    end

    subgraph Layer3["Layer 3: Learned Behavioral Profile (ai_agent_db)"]
        L3A["Tier 0 Aggregates (accept/skip ratios, implicit city/role drift, dwell affinity)"]
        L3B["Tier 1 Grounded Facts (pgvector embeddings + source_event_ids)"]
        L3C["Editable & Clearable via /account AI Memory Inspector"]
    end

    Layer1 -->|"user_id + consent flags"| Layer2
    Layer2 -->|"Explicit grounded facts (Never auto-mutated)"| Layer3
    Layer1 -->|"Privacy consent gate"| Layer3
```

| Layer | Owner Service & DB | Mutability | Examples | AI Agent Access Rule |
| :--- | :--- | :--- | :--- | :--- |
| **Layer 1: Account, Workspace & Privacy** | `auth-service` (`auth_db`) | User explicit only | `default_home_route` (`/dashboard`), `list_density` (`cozy`/`dense`), `default_studio_intensity` (`Surgical`/`Metrics+`/`Executive`), `preferred_currency` (`EGP`/`SAR`/`AED`/`USD`), `ai_passive_learning_enabled` | Read-only via JWT/claims or consent check; AI never alters preferences |
| **Layer 2: Master Career Profile & Personas** | `profile-service` (`profile_db`) | User explicit (or confirmed CV Merge Diff) | Multi-country contacts, `CareerPersona` skills/experience/projects/metrics, target locations, base `.tex` | Strictly read-only source of truth; zero hallucination anchor |
| **Layer 3: Learned Behavioral Memory** | `ai-agent-service` (`ai_agent_db`) | Background Redpanda distillation + User delete/clear | *"Prefers concise 1-line quantified bullets"*, *"Frequently views KSA remote ML jobs despite Cairo default"*, *"Skips narrative intros"* | Written autonomously when consent=true; user can inspect/delete individual facts in `/account` |

---

## 3. PostgreSQL Logical Schemas (All 9 Domain Databases)

### 3.1 `auth_db` (`auth-service`)

Powers [03_auth_login_and_register.md](file:///d:/Tailored/frontend/ux_designs/03_auth_login_and_register.md), [04_auth_recovery_and_verification.md](file:///d:/Tailored/frontend/ux_designs/04_auth_recovery_and_verification.md), and [19_account_security_and_preferences.md](file:///d:/Tailored/frontend/ux_designs/19_account_security_and_preferences.md).

| Table | Key Columns & Types | Constraints / Indexes | Purpose |
| :--- | :--- | :--- | :--- |
| `users` | `id UUID PK`, `email CITEXT UNIQUE`, `password_hash TEXT NULL`, `email_verified BOOLEAN`, `status VARCHAR(24)` (`active`/`locked`/`erasing`), `role VARCHAR(24)` (`user`/`admin`), `created_at`, `updated_at` | `UNIQUE(email)` | Core identity (`password_hash` nullable for OAuth-only signups) |
| `oauth_identities` | `id UUID PK`, `user_id UUID FK`, `provider VARCHAR(24)` (`google`/`linkedin`), `provider_user_id TEXT`, `provider_email TEXT`, `linked_at` | `UNIQUE(provider, provider_user_id)`, `INDEX(user_id)` | Enforces sole-login unlink guard (`password_hash IS NOT NULL OR COUNT(oauth) > 1`) |
| `user_sessions` | `id UUID PK`, `user_id UUID FK`, `refresh_token_hash TEXT`, `device_label TEXT`, `ip_prefix VARCHAR(45)`, `geo_city VARCHAR(64)`, `last_active_at`, `expires_at`, `revoked_at NULL` | `INDEX(user_id, revoked_at)` | Active device list & remote `[Revoke]` |
| `otp_verifications` | `id UUID PK`, `user_id UUID FK`, `purpose VARCHAR(32)` (`verify_email`/`reset_pw`/`change_email`), `target_email CITEXT`, `code_hash TEXT`, `attempts INT`, `expires_at`, `consumed_at NULL` | `INDEX(user_id, purpose)` | 6-digit OTP verification & email change safety |
| `totp_mfa` | `user_id UUID PK FK`, `encrypted_secret BYTEA`, `enabled BOOLEAN`, `recovery_codes_hashes JSONB`, `enabled_at` | — | TOTP 2FA + single-use hashed recovery codes |
| `workspace_preferences` | `user_id UUID PK FK`, `default_home_route VARCHAR(32)`, `list_density VARCHAR(16)`, `default_studio_intensity VARCHAR(24)`, `preferred_currency VARCHAR(8)` (`EGP`), `chat_side VARCHAR(8)` (`right`), `collapsed_rail BOOLEAN`, `updated_at` | — | Synced workspace ergonomics across devices |
| `privacy_consents` | `user_id UUID PK FK`, `analytics_micro_signals BOOLEAN DEFAULT TRUE`, `ai_passive_learning BOOLEAN DEFAULT TRUE`, `proactive_nudges BOOLEAN DEFAULT TRUE`, `updated_at` | — | Granular privacy toggles in `/account` |
| `feature_flags` | `key VARCHAR(96) PK`, `enabled BOOLEAN`, `rollout_percent SMALLINT`, `rules_json JSONB`, `description TEXT`, `updated_at` | — | Built-in OpenFeature-compatible rollout registry |
| `feature_flag_overrides` | `flag_key VARCHAR(96) FK`, `user_id UUID`, `enabled BOOLEAN`, `PRIMARY KEY(flag_key, user_id)` | `INDEX(user_id)` | Beta/internal user overrides |

### 3.2 `privacy_vault_db` (`auth-service` vault role only)

Strictly separated from `auth_db` PII and `telemetry-audit-service` analytics storage to implement **Crypto-Shredding**.

| Table | Key Columns & Types | Constraints / Indexes | Purpose |
| :--- | :--- | :--- | :--- |
| `identity_pseudonyms` | `user_id UUID PK`, `analytics_anon_id UUID UNIQUE NOT NULL`, `created_at TIMESTAMPTZ` | `UNIQUE(analytics_anon_id)` | Sole link between real `user_id` and ClickHouse `analytics_anon_id`. Deleted permanently on GDPR account erasure. |

### 3.3 `profile_db` (`profile-service`)

Evolves the normalized relational design of [profile.py](file:///d:/Tailored/backend/app/models/profile.py) and [user_profile.py](file:///d:/Tailored/backend/app/schemas/user_profile.py).

| Table | Key Columns & Types | Constraints / Indexes | Purpose |
| :--- | :--- | :--- | :--- |
| `master_profiles` | `id UUID PK`, `user_id UUID UNIQUE NOT NULL`, `full_name TEXT`, `primary_email CITEXT`, `current_city VARCHAR(96)`, `current_country VARCHAR(96)`, `willing_to_relocate BOOLEAN`, `links_json JSONB`, `custom_sections_json JSONB`, `active_persona_id UUID NULL`, `onboarding_step SMALLINT`, `onboarding_completed BOOLEAN`, `version INT DEFAULT 1`, `updated_at` | `UNIQUE(user_id)` | Core identity metadata & onboarding state |
| `contact_numbers` | `id UUID PK`, `profile_id UUID FK`, `country_code VARCHAR(8)`, `dial_code VARCHAR(12)`, `phone_number VARCHAR(32)`, `is_primary BOOLEAN`, `label VARCHAR(32)` | `INDEX(profile_id)` | Multi-country numbers (`+20`, `+966`, `+971`) |
| `target_locations` | `id UUID PK`, `profile_id UUID FK`, `city VARCHAR(96)`, `country VARCHAR(96)`, `work_modes JSONB`, `is_active_for_search BOOLEAN` | `INDEX(profile_id)` | Target cities & allowed Remote/Hybrid/On-site modes |
| `career_personas` | `id UUID PK`, `profile_id UUID FK`, `target_title TEXT`, `alternative_titles JSONB`, `is_primary BOOLEAN`, `seniority_level VARCHAR(32)`, `years_of_experience SMALLINT`, `summary_bio TEXT`, `skills_json JSONB`, `experience_highlights_json JSONB`, `featured_projects_json JSONB`, `certifications_json JSONB`, `updated_at` | `INDEX(profile_id)` | Multi-persona career tracks for dynamic Best-Fit scoring |
| `education_records` | `id UUID PK`, `profile_id UUID FK`, `institution TEXT`, `degree TEXT`, `field_of_study TEXT`, `graduation_year SMALLINT`, `grade_or_gpa VARCHAR(32)` | `INDEX(profile_id)` | Academic history |
| `spoken_languages` | `id UUID PK`, `profile_id UUID FK`, `language VARCHAR(64)`, `proficiency VARCHAR(32)` | `INDEX(profile_id)` | Language proficiencies |
| `base_cv_templates` | `id UUID PK`, `profile_id UUID FK`, `name VARCHAR(128)`, `source_type VARCHAR(24)` (`synthesized`/`uploaded_tex`), `latex_content TEXT`, `sha256 CHAR(64)`, `is_default BOOLEAN`, `created_at` | `INDEX(profile_id)` | Base CV templates shown in `/cvs` (`11_saved_cvs_and_document_archive.md`) |

### 3.4 `jobs_db` (`jobs-service`)

Evolves [job.py](file:///d:/Tailored/backend/app/models/job.py) and [job_insights.py](file:///d:/Tailored/backend/app/schemas/job_insights.py) to support multi-tenant scoring, Interest List triage, and public `/explore`.

| Table | Key Columns & Types | Constraints / Indexes | Purpose |
| :--- | :--- | :--- | :--- |
| `jobs` | `id UUID PK`, `legacy_int_id BIGINT NULL`, `source_id TEXT`, `canonical_hash CHAR(64) UNIQUE`, `title TEXT`, `company_name TEXT`, `location TEXT`, `country VARCHAR(64)`, `work_mode VARCHAR(24)`, `url TEXT`, `source_type VARCHAR(32)`, `recruiter_email CITEXT NULL`, `raw_description TEXT`, `insights_json JSONB`, `parsed_skills TEXT[]`, `is_public_explore BOOLEAN DEFAULT FALSE`, `is_active BOOLEAN DEFAULT TRUE`, `posted_at TIMESTAMPTZ`, `expires_at TIMESTAMPTZ`, `created_at` | `UNIQUE(canonical_hash)`, `GIN(parsed_skills)`, `INDEX(is_public_explore, created_at DESC)` | Deduplicated global job catalog |
| `job_fit_scores` | `id UUID PK`, `user_id UUID NOT NULL`, `job_id UUID FK`, `best_persona_id UUID NOT NULL`, `overall_score REAL`, `match_level VARCHAR(32)`, `dimensions_json JSONB`, `persona_breakdown_json JSONB`, `tailoring_guidance_json JSONB`, `profile_version INT`, `computed_at TIMESTAMPTZ` | `UNIQUE(user_id, job_id)`, `INDEX(user_id, overall_score DESC)` | Cached 5-D multi-persona Zero-Drop scores (`08`, `09`) |
| `user_job_interactions` | `user_id UUID`, `job_id UUID FK`, `in_interest_list BOOLEAN DEFAULT FALSE`, `is_hidden BOOLEAN DEFAULT FALSE`, `hide_reason VARCHAR(64) NULL`, `ingest_origin VARCHAR(32)` (`radar`/`url`/`jd`/`screenshot`), `screenshot_object_key TEXT NULL`, `updated_at`, `PRIMARY KEY(user_id, job_id)` | `INDEX(user_id, in_interest_list)`, `INDEX(user_id, is_hidden)` | User-specific Interest List & `X` Hide triage state (`10`) |
| `scrape_runs` | `id UUID PK`, `user_id UUID NULL`, `query_text TEXT`, `location TEXT`, `sources JSONB`, `status VARCHAR(24)`, `items_fetched INT`, `items_deduped INT`, `apify_run_id TEXT NULL`, `error_message TEXT NULL`, `created_at`, `finished_at` | `INDEX(user_id, created_at DESC)` | Audit & throttling of Apify/Wuzzuf/Playwright sweeps |

### 3.5 `documents_db` (`documents-service`)

Evolves [document.py](file:///d:/Tailored/backend/app/models/document.py) to separate live editable Studio documents from version history and immutable Frozen Application Snapshots.

| Table | Key Columns & Types | Constraints / Indexes | Purpose |
| :--- | :--- | :--- | :--- |
| `generated_documents` | `id UUID PK`, `doc_id VARCHAR(64) UNIQUE`, `user_id UUID NOT NULL`, `profile_id UUID`, `persona_id UUID`, `job_id UUID`, `doc_type VARCHAR(24)` (`tailored_cv`/`cover_letter`), `status VARCHAR(24)` (`queued`/`tailoring`/`compiling`/`completed`/`failed`), `compile_status VARCHAR(24)`, `credit_hold_id UUID NULL`, `job_title TEXT`, `company_name TEXT`, `fit_score REAL`, `active_version_no INT DEFAULT 1`, `base_latex_content TEXT`, `tailored_latex_content TEXT`, `content_markdown TEXT`, `subject_line TEXT`, `tex_object_key TEXT`, `pdf_object_key TEXT`, `pdf_sha256 CHAR(64)`, `section_plan_json JSONB`, `bullet_diffs_json JSONB`, `created_at`, `updated_at` | `INDEX(user_id, created_at DESC)`, `INDEX(user_id, job_id, persona_id, doc_type)` | Master record for CVs & Cover Letters; drives `already_unlocked` `0 cr` protection |
| `document_versions` | `id UUID PK`, `document_id UUID FK`, `version_no INT`, `source VARCHAR(32)` (`initial_tailor`/`ai_proposal`/`manual_edit`/`undo`), `proposal_card_id UUID NULL`, `latex_or_markdown TEXT`, `pdf_object_key TEXT NULL`, `diff_summary JSONB`, `created_at` | `UNIQUE(document_id, version_no)` | Immutable version timeline & `Cmd+Z` / `[Undo]` rollback |
| `frozen_application_snapshots` | `id UUID PK`, `user_id UUID NOT NULL`, `pipeline_item_id UUID NOT NULL`, `cv_doc_id VARCHAR(64) NULL`, `cv_version_no INT NULL`, `cl_doc_id VARCHAR(64) NULL`, `cl_version_no INT NULL`, `frozen_cv_pdf_key TEXT`, `frozen_cv_tex_key TEXT`, `frozen_cl_pdf_key TEXT`, `frozen_at TIMESTAMPTZ` | `INDEX(user_id, pipeline_item_id)` | Preserves exact sent PDFs even if user later edits Studio draft (`16`) |
| `gdpr_export_jobs` | `id UUID PK`, `user_id UUID NOT NULL`, `status VARCHAR(24)`, `zip_object_key TEXT NULL`, `expires_at TIMESTAMPTZ`, `created_at` | `INDEX(user_id, created_at DESC)` | Tracks async `[Export Complete Archive]` `.zip` builds (`19`) |

### 3.6 `pipeline_db` (`pipeline-service`)

Evolves [pipeline.py](file:///d:/Tailored/backend/app/models/pipeline.py) with rich interview hub fields from [16_application_detail_and_interview_hub.md](file:///d:/Tailored/frontend/ux_designs/16_application_detail_and_interview_hub.md).

| Table | Key Columns & Types | Constraints / Indexes | Purpose |
| :--- | :--- | :--- | :--- |
| `pipeline_items` | `id UUID PK`, `user_id UUID NOT NULL`, `job_id UUID NOT NULL`, `status VARCHAR(24)` (`saved`/`in_process`/`applied`/`interview`/`archived`), `channel_type VARCHAR(24)` (`direct_email`/`external_portal`), `recruiter_name TEXT`, `recruiter_email CITEXT`, `job_title_snapshot TEXT`, `company_snapshot TEXT`, `tailored_cv_doc_id VARCHAR(64) NULL`, `cover_letter_doc_id VARCHAR(64) NULL`, `frozen_snapshot_id UUID NULL`, `notes TEXT`, `compensation_notes TEXT`, `saved_at`, `applied_at NULL`, `follow_up_due_at NULL`, `follow_up_sent_at NULL`, `interview_date NULL`, `updated_at` | `UNIQUE(user_id, job_id)`, `INDEX(user_id, status)`, `INDEX(follow_up_due_at) WHERE status='applied'` | Unified multi-channel Pipeline CRM (`15`, `16`) |
| `interview_round_notes` | `id UUID PK`, `pipeline_item_id UUID FK`, `round_title TEXT`, `scheduled_at TIMESTAMPTZ NULL`, `interviewer TEXT`, `notes TEXT`, `outcome VARCHAR(32)`, `created_at` | `INDEX(pipeline_item_id)` | Structured multi-round prep & notes (`16`) |
| `outreach_dispatches` | `id UUID PK`, `pipeline_item_id UUID FK`, `dispatch_channel VARCHAR(24)` (`gmail_web`/`mailto`/`external_marked`), `to_email CITEXT NULL`, `subject TEXT`, `body_preview TEXT`, `dispatched_at TIMESTAMPTZ` | `INDEX(pipeline_item_id)` | Audit trail of every application dispatch (`14`) |

### 3.7 `billing_db` (`billing-service`)

Powers [06_credits_activation_and_topup_gate.md](file:///d:/Tailored/frontend/ux_designs/06_credits_activation_and_topup_gate.md) and [18_plans_credits_and_billing.md](file:///d:/Tailored/frontend/ux_designs/18_plans_credits_and_billing.md) with zero lost credits.

| Table | Key Columns & Types | Constraints / Indexes | Purpose |
| :--- | :--- | :--- | :--- |
| `credit_wallets` | `user_id UUID PK`, `available_credits INT NOT NULL CHECK (available_credits >= 0)`, `held_credits INT NOT NULL CHECK (held_credits >= 0)`, `low_balance_threshold INT NOT NULL DEFAULT 2`, `version INT NOT NULL DEFAULT 1`, `updated_at` | `CHECK (available_credits >= 0)` | Optimistic-locked balance + active holds |
| `credit_ledger_entries` | `id UUID PK`, `user_id UUID NOT NULL`, `entry_type VARCHAR(32)` (`starter_grant`/`pack_purchase`/`hold_created`/`hold_committed`/`compile_refund`/`manual_adjustment`), `delta INT NOT NULL`, `balance_after INT NOT NULL`, `hold_id UUID NULL`, `reference_doc_id VARCHAR(64) NULL`, `job_target_label TEXT`, `payment_order_id UUID NULL`, `idempotency_key VARCHAR(128) UNIQUE`, `created_at` | `INDEX(user_id, created_at DESC)`, `UNIQUE(idempotency_key)` | Append-only transparent credit audit ledger (`18`) |
| `credit_holds` | `id UUID PK`, `user_id UUID NOT NULL`, `amount INT NOT NULL`, `reason VARCHAR(64)`, `doc_id VARCHAR(64)`, `status VARCHAR(24)` (`held`/`committed`/`refunded`/`expired`), `idempotency_key VARCHAR(128) UNIQUE`, `expires_at TIMESTAMPTZ`, `resolved_at NULL`, `created_at` | `INDEX(status, expires_at)` | Saga tracking for Hold -> Commit / Auto-Refund |
| `credit_packs_catalog` | `pack_id VARCHAR(32) PK`, `name VARCHAR(64)`, `credits INT`, `prices_json JSONB`, `popular BOOLEAN`, `active BOOLEAN` | — | Stores EGP/SAR/AED/USD pack definitions |
| `payment_orders` | `id UUID PK`, `user_id UUID NOT NULL`, `pack_id VARCHAR(32)`, `provider VARCHAR(24)` (`paymob`/`stripe`), `payment_method VARCHAR(32)` (`card`/`meeza`/`wallet`/`fawry`/`apple_pay`), `currency VARCHAR(8)`, `amount_minor BIGINT`, `credits_to_grant INT`, `status VARCHAR(24)` (`pending`/`paid`/`failed`/`expired`), `provider_order_id TEXT`, `fawry_ref_code TEXT NULL`, `invoice_object_key TEXT NULL`, `idempotency_key VARCHAR(128) UNIQUE`, `created_at`, `paid_at NULL` | `INDEX(user_id, created_at DESC)`, `UNIQUE(provider, provider_order_id)` | Checkout & pending Fawry cash payment reconciliation |

### 3.8 `ai_agent_db` (`ai-agent-service`, `pgvector` extension enabled)

Powers both the **Interactive Studio Coach** (`00`, `12`, `13`) and **Ambient Behavioral Memory** (`04`).

| Table | Key Columns & Types | Constraints / Indexes | Purpose |
| :--- | :--- | :--- | :--- |
| `user_behavior_profiles` | `user_id UUID PK`, `dominant_locations_json JSONB`, `implicit_role_drift_json JSONB`, `writing_style_prefs_json JSONB`, `avg_proposal_accept_rate REAL`, `total_events_processed BIGINT`, `last_distilled_at TIMESTAMPTZ NULL`, `updated_at` | — | Tier 0 deterministic behavioral stats (zero LLM cost) |
| `behavioral_memory_facts` | `id UUID PK`, `user_id UUID NOT NULL`, `category VARCHAR(32)` (`writing_style`/`role_drift`/`location_drift`/`skill_gap`/`workflow_habit`), `fact_text TEXT NOT NULL`, `embedding vector(768)`, `confidence REAL`, `source_event_ids UUID[]`, `status VARCHAR(24)` (`active`/`dismissed_by_user`), `created_at`, `last_reinforced_at` | `INDEX(user_id, status)`, `HNSW(embedding vector_cosine_ops)` | Semantic memory facts with full provenance & user-deletable flags |
| `agent_threads` | `id UUID PK`, `user_id UUID NOT NULL`, `surface VARCHAR(24)` (`cv`/`cover_letter`/`workspace`), `scope VARCHAR(16)` (`role`/`workspace`), `doc_id VARCHAR(64) NULL`, `job_id UUID NULL`, `title TEXT`, `active_checkpoint_id UUID NULL`, `created_at`, `updated_at` | `INDEX(user_id, surface, updated_at DESC)` | Conversation threads (`[History ▾]`) |
| `agent_checkpoints` | `id UUID PK`, `thread_id UUID FK`, `parent_checkpoint_id UUID NULL`, `state_json JSONB`, `created_at` | `INDEX(thread_id, created_at)` | Enables `[Edit & Branch from here]` turn branching (`00 §5.3`) |
| `agent_messages` | `id UUID PK`, `thread_id UUID FK`, `checkpoint_id UUID`, `role VARCHAR(16)` (`user`/`assistant`), `content_text TEXT`, `thinking_summary TEXT NULL`, `focused_anchor_json JSONB NULL`, `resources_json JSONB NULL`, `audit_json JSONB NULL`, `langfuse_trace_id VARCHAR(64) NULL`, `created_at` | `INDEX(thread_id, created_at)` | Persisted messages matching `AiChatMessage` |
| `proposal_cards` | `id UUID PK`, `thread_id UUID FK`, `message_id UUID FK`, `doc_id VARCHAR(64)`, `target_anchor_id TEXT`, `target_label TEXT`, `old_text TEXT`, `new_text TEXT`, `is_metric_question BOOLEAN`, `status VARCHAR(24)` (`pending`/`applied`/`skipped`/`undone`), `refine_count SMALLINT DEFAULT 0`, `resolved_at NULL` | `INDEX(doc_id, status)` | Lifecycle of Proposal Diff Cards & feedback scoring |
| `proactive_suggestions` | `id UUID PK`, `user_id UUID NOT NULL`, `rule_key VARCHAR(64)`, `title TEXT`, `body TEXT`, `cta_route TEXT`, `payload_json JSONB`, `status VARCHAR(24)` (`emitted`/`clicked`/`dismissed`/`expired`), `created_at`, `resolved_at NULL` | `INDEX(user_id, created_at DESC)` | Tracks ambient nudges & suppression after dismissal |

### 3.9 `notifications_db` (`notifications-service`)

| Table | Key Columns & Types | Constraints / Indexes | Purpose |
| :--- | :--- | :--- | :--- |
| `notifications` | `id UUID PK`, `user_id UUID NOT NULL`, `category VARCHAR(24)` (`match`/`followup`/`document`/`credit`/`ai_insight`), `title TEXT`, `subtitle TEXT`, `job_id UUID NULL`, `pipeline_id UUID NULL`, `action_label VARCHAR(48)`, `target_path TEXT`, `dedup_key VARCHAR(128) NULL`, `read_at TIMESTAMPTZ NULL`, `archived_at TIMESTAMPTZ NULL`, `snoozed_until TIMESTAMPTZ NULL`, `created_at` | `INDEX(user_id, created_at DESC)`, `UNIQUE(user_id, dedup_key) WHERE dedup_key IS NOT NULL` | Powers Quick Bell Drawer & `/notifications` (`20`) |
| `notification_rules` | `user_id UUID PK`, `min_match_alert_score SMALLINT DEFAULT 85`, `digest_cadence VARCHAR(24)` (`daily_9am`/`weekly`/`off`), `followup_reminders BOOLEAN DEFAULT TRUE`, `low_credit_alerts BOOLEAN DEFAULT TRUE`, `updated_at` | — | Synced with `/account` Card 4 (`19`) |
| `email_dispatch_logs` | `id UUID PK`, `user_id UUID NOT NULL`, `template_key VARCHAR(64)`, `provider_msg_id TEXT`, `status VARCHAR(24)`, `sent_at TIMESTAMPTZ` | `INDEX(user_id, sent_at DESC)` | Delivery audit for OTP, resets, digests |

---

## 4. ClickHouse Analytical & Immutable Audit Schemas

ClickHouse runs with two dedicated databases managed exclusively by `telemetry-audit-service`.

### 4.1 `tailored_analytics.user_behavior_events` (Zero PII)

```sql
CREATE DATABASE IF NOT EXISTS tailored_analytics;

CREATE TABLE tailored_analytics.user_behavior_events
(
    event_id          UUID,
    occurred_at       DateTime64(3, 'UTC'),
    received_at       DateTime64(3, 'UTC'),
    analytics_anon_id UUID,                        -- Pseudonym from privacy_vault_db (NO user_id, email, name, or CV text)
    session_id        UUID,
    trace_id          FixedString(32),
    feature_key       LowCardinality(String),      -- e.g. 'radar.job.dwell', 'studio.cv.proposal.apply'
    event_name        LowCardinality(String),
    route             LowCardinality(String),
    persona_track     LowCardinality(String),      -- Normalized title/role category, never free-text PII
    job_id            Nullable(UUID),
    doc_id            Nullable(String),
    duration_ms       UInt32 DEFAULT 0,
    scroll_depth_pct  UInt8 DEFAULT 0,
    numeric_value     Float32 DEFAULT 0,
    properties_json   String                       -- Strictly allow-listed non-PII JSON payload
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(occurred_at)
ORDER BY (feature_key, event_name, analytics_anon_id, occurred_at)
TTL occurred_at + INTERVAL 24 MONTH DELETE;

-- Materialized View: Daily Feature Adoption & Engagement
CREATE MATERIALIZED VIEW tailored_analytics.mv_feature_daily_usage
ENGINE = SummingMergeTree
PARTITION BY toYYYYMM(day)
ORDER BY (day, feature_key, event_name)
AS SELECT
    toDate(occurred_at) AS day,
    feature_key,
    event_name,
    count() AS event_count,
    uniqState(analytics_anon_id) AS unique_users_state,
    sum(duration_ms) AS total_dwell_ms
FROM tailored_analytics.user_behavior_events
GROUP BY day, feature_key, event_name;

-- Materialized View: AI Coach Proposal Card Accept / Skip / Refine / Undo Quality
CREATE MATERIALIZED VIEW tailored_analytics.mv_ai_proposal_quality
ENGINE = SummingMergeTree
PARTITION BY toYYYYMM(day)
ORDER BY (day, event_name, persona_track)
AS SELECT
    toDate(occurred_at) AS day,
    event_name,
    persona_track,
    count() AS resolution_count,
    uniqState(analytics_anon_id) AS unique_users_state
FROM tailored_analytics.user_behavior_events
WHERE feature_key IN (
    'studio.cv.proposal.apply',
    'studio.cv.proposal.skip',
    'studio.cv.proposal.refine',
    'studio.cv.proposal.undo',
    'studio.cl.proposal.apply',
    'studio.cl.proposal.skip'
)
GROUP BY day, event_name, persona_track;
```

### 4.2 `tailored_audit.feature_audit_logs` (Immutable Compliance & Feature Ledger)

```sql
CREATE DATABASE IF NOT EXISTS tailored_audit;

CREATE TABLE tailored_audit.feature_audit_logs
(
    audit_id           UUID,
    occurred_at        DateTime64(3, 'UTC'),
    trace_id           FixedString(32),
    span_id            FixedString(16),
    feature_key        LowCardinality(String),
    service_name       LowCardinality(String),
    action             LowCardinality(String),
    outcome            LowCardinality(String),     -- 'success' | 'denied' | 'failed' | 'refunded'
    actor_user_id_hash FixedString(64),            -- SHA-256(user_id + monthly/vault salt) or 'anonymous'
    resource_type      LowCardinality(String),
    resource_id        String,
    before_hash        FixedString(64),
    after_hash         FixedString(64),
    diff_summary       String,                     -- Non-PII structural field changes
    credit_delta       Int16 DEFAULT 0,
    duration_ms        UInt32,
    active_flags_json  String,
    error_code         LowCardinality(String)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(occurred_at)
ORDER BY (feature_key, service_name, occurred_at, trace_id);
```

---

## 5. Redis Keyspace & TTL Specification

| Key Pattern | Value Type | TTL | Owner Service | Purpose |
| :--- | :--- | :---: | :--- | :--- |
| `session:revoked:{session_id}` | `"1"` | Remaining JWT TTL (max 15m) | `auth-service` | Immediate access-token invalidation on logout/revoke |
| `rl:{policy}:{key}` | Counter / Sliding Window | `60s`–`3600s` | `traefik-gateway` / `auth-service` | Edge & OTP brute-force rate limiting |
| `anon_map:{user_id}` | `analytics_anon_id` UUID | `24h` (deleted on erasure) | `telemetry-audit-service` | Fast pseudonym resolution without hitting `privacy_vault_db` per batch |
| `ff:catalog` | JSON map of active flags | `30s` (invalidated on publish) | `auth-service` / `tailored_kit` | Sub-millisecond OpenFeature flag evaluation |
| `idem:{service}:{key}` | Status + cached response JSON | `24h` | All services | Distributed API idempotency lock (`SET NX EX`) |
| `sse:notif:{user_id}` | Pub/Sub Channel | Ephemeral | `notifications-service` | Multi-replica real-time inbox & proactive suggestion push |
| `ai:nudge:cooldown:{user_id}:{rule}` | Timestamp | `7d` (or `24h` global) | `ai-agent-service` | Enforces Calm UX nudge ceiling (zero spam) |
| `apify:daily_items:{YYYY-MM-DD}` | Integer counter | `48h` | `scraper-worker` | Global Apify budget safety ceiling |

---

## 6. MinIO (S3-Compatible) Bucket Architecture

| Bucket Name | Access Policy | Key Path Convention | Retention / Lifecycle | Owners |
| :--- | :--- | :--- | :--- | :--- |
| `cv-artifacts` | Private (presigned or authenticated stream via `documents-service`) | `{user_id}/{doc_id}/v{version_no}/cv.tex` & `cv.pdf` | Kept until user deletes doc or GDPR erasure; frozen snapshots copied to `frozen/{snapshot_id}/` | `latex-worker`, `documents-service` |
| `user-uploads` | Private (auto-deleted after parse or kept per user) | `cv-drop/{user_id}/{upload_id}.tex` & `jd-screens/{user_id}/{upload_id}.png` | Raw JD screenshots expire after `90d` via MinIO ILM lifecycle rule | `profile-service`, `jobs-service`, `scraper-worker` |
| `invoices` | Private (streamed via `billing-service`) | `receipts/{user_id}/{order_id}.pdf` | `7 years` (non-PII redacted summary if user erases account) | `billing-service` |
| `gdpr-exports` | Private (one-time presigned link) | `exports/{user_id}/{export_id}.zip` | Strict `24h` automatic ILM expiration | `documents-service` |
