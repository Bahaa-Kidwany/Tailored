#!/usr/bin/env sh
set -eu

ENDPOINT="${MINIO_ENDPOINT:-http://minio:9000}"
ROOT_USER="${MINIO_ROOT_USER:-tailored_minio}"
ROOT_PASS="${MINIO_ROOT_PASSWORD:-tailored_minio_dev_pass}"

echo "Waiting for MinIO at $ENDPOINT..."
until mc alias set tailored "$ENDPOINT" "$ROOT_USER" "$ROOT_PASS" >/dev/null 2>&1; do
  sleep 2
done

for bucket in cv-artifacts user-uploads invoices gdpr-exports; do
  mc mb --ignore-existing "tailored/$bucket"
done

# Retention ILM policies matching 02_database_and_storage_architecture.md
mc ilm rule add --expire-days 90 "tailored/user-uploads" || true
mc ilm rule add --expire-days 1  "tailored/gdpr-exports" || true

echo "MinIO buckets initialized:"
mc ls tailored/
