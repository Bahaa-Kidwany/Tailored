#!/usr/bin/env bash
set -euo pipefail

# Creates 10 logically isolated PostgreSQL databases and least-privilege service roles.
create_db_and_role() {
  local db_name="$1"
  local role_name="$2"
  local role_pass="$3"
  local extra_ext="${4:-}"

  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    DO \$\$
    BEGIN
      IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '${role_name}') THEN
        CREATE ROLE ${role_name} WITH LOGIN PASSWORD '${role_pass}';
      END IF;
    END
    \$\$;
    SELECT 'CREATE DATABASE ${db_name} OWNER ${role_name}'
      WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${db_name}')\gexec
    REVOKE ALL ON DATABASE ${db_name} FROM PUBLIC;
    GRANT ALL PRIVILEGES ON DATABASE ${db_name} TO ${role_name};
EOSQL

  if [ -n "$extra_ext" ]; then
    for ext in $extra_ext; do
      psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$db_name" \
        -c "CREATE EXTENSION IF NOT EXISTS ${ext};"
    done
  fi
}

create_db_and_role "auth_db"          "auth_svc"          "${AUTH_DB_PASSWORD:-tailored_auth_pass}"          "citext"
create_db_and_role "privacy_vault_db" "privacy_vault_svc" "${PRIVACY_VAULT_DB_PASSWORD:-tailored_vault_pass}" ""
create_db_and_role "profile_db"       "profile_svc"       "${PROFILE_DB_PASSWORD:-tailored_profile_pass}"    "citext"
create_db_and_role "jobs_db"          "jobs_svc"          "${JOBS_DB_PASSWORD:-tailored_jobs_pass}"          "citext"
create_db_and_role "documents_db"     "documents_svc"     "${DOCUMENTS_DB_PASSWORD:-tailored_docs_pass}"     ""
create_db_and_role "pipeline_db"      "pipeline_svc"      "${PIPELINE_DB_PASSWORD:-tailored_pipeline_pass}"  "citext"
create_db_and_role "billing_db"       "billing_svc"       "${BILLING_DB_PASSWORD:-tailored_billing_pass}"    ""
create_db_and_role "ai_agent_db"      "ai_agent_svc"      "${AI_AGENT_DB_PASSWORD:-tailored_ai_pass}"        "vector"
create_db_and_role "notifications_db" "notifications_svc" "${NOTIFICATIONS_DB_PASSWORD:-tailored_notif_pass}" ""
create_db_and_role "langfuse_db"      "langfuse_svc"      "${LANGFUSE_DB_PASSWORD:-tailored_langfuse_pass}"  ""
