#!/usr/bin/env bash
set -euo pipefail

BROKERS="${REDPANDA_BROKERS:-redpanda:9092}"

echo "Waiting for Redpanda at $BROKERS..."
until rpk topic list --brokers "$BROKERS" >/dev/null 2>&1; do
  sleep 2
done

create_topic_with_dlq() {
  local topic="$1"
  local partitions="$2"
  local retention_ms="$3"

  rpk topic create "$topic" --brokers "$BROKERS" -p "$partitions" -r 1 -c "retention.ms=$retention_ms" || true
  rpk topic create "${topic}.dlq" --brokers "$BROKERS" -p 1 -r 1 -c "retention.ms=2592000000" || true
}

DAY_MS=86400000
create_topic_with_dlq "identity.lifecycle.v1"    3  $((30 * DAY_MS))
create_topic_with_dlq "profile.events.v1"        3  $((14 * DAY_MS))
create_topic_with_dlq "jobs.commands.v1"         6  $((7  * DAY_MS))
create_topic_with_dlq "jobs.events.v1"           6  $((14 * DAY_MS))
create_topic_with_dlq "documents.commands.v1"    6  $((7  * DAY_MS))
create_topic_with_dlq "documents.events.v1"      6  $((30 * DAY_MS))
create_topic_with_dlq "pipeline.events.v1"       3  $((30 * DAY_MS))
create_topic_with_dlq "billing.events.v1"        3  $((90 * DAY_MS))
create_topic_with_dlq "telemetry.interactions.v1" 12 $((7 * DAY_MS))
create_topic_with_dlq "ai.events.v1"             6  $((30 * DAY_MS))
create_topic_with_dlq "audit.trail.v1"           6  $((90 * DAY_MS))

echo "Redpanda topics and DLQs initialized:"
rpk topic list --brokers "$BROKERS"
