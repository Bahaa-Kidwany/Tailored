CREATE DATABASE IF NOT EXISTS tailored_analytics;
CREATE DATABASE IF NOT EXISTS tailored_audit;

CREATE TABLE IF NOT EXISTS tailored_analytics.user_behavior_events
(
    event_id          UUID,
    occurred_at       DateTime64(3, 'UTC'),
    received_at       DateTime64(3, 'UTC'),
    analytics_anon_id UUID,
    session_id        UUID,
    trace_id          FixedString(32),
    feature_key       LowCardinality(String),
    event_name        LowCardinality(String),
    route             LowCardinality(String),
    persona_track     LowCardinality(String),
    job_id            Nullable(UUID),
    doc_id            Nullable(String),
    duration_ms       UInt32 DEFAULT 0,
    scroll_depth_pct  UInt8 DEFAULT 0,
    numeric_value     Float32 DEFAULT 0,
    properties_json   String
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(occurred_at)
ORDER BY (feature_key, event_name, analytics_anon_id, occurred_at)
TTL occurred_at + INTERVAL 24 MONTH DELETE;

CREATE MATERIALIZED VIEW IF NOT EXISTS tailored_analytics.mv_feature_daily_usage
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

CREATE MATERIALIZED VIEW IF NOT EXISTS tailored_analytics.mv_ai_proposal_quality
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

CREATE TABLE IF NOT EXISTS tailored_audit.feature_audit_logs
(
    audit_id           UUID,
    occurred_at        DateTime64(3, 'UTC'),
    trace_id           FixedString(32),
    span_id            FixedString(16),
    feature_key        LowCardinality(String),
    service_name       LowCardinality(String),
    action             LowCardinality(String),
    outcome            LowCardinality(String),
    actor_user_id_hash FixedString(64),
    resource_type      LowCardinality(String),
    resource_id        String,
    before_hash        FixedString(64),
    after_hash         FixedString(64),
    diff_summary       String,
    credit_delta       Int16 DEFAULT 0,
    duration_ms        UInt32,
    active_flags_json  String,
    error_code         LowCardinality(String)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(occurred_at)
ORDER BY (feature_key, service_name, occurred_at, trace_id);
