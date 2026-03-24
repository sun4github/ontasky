#!/usr/bin/env bash
set -euo pipefail

# Required env vars (as you described, DB_ prefix)
: "${DB_HOST:?DB_HOST is required}"
: "${DB_PORT:=5432}"
: "${DB_USER:?DB_USER is required}"
: "${DB_PASSWORD:?DB_PASSWORD is required}"
: "${DB_NAME:?DB_NAME is required}"

SCHEMA="public"
TS="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="${1:-schema_export_${TS}}"
mkdir -p "${OUT_DIR}"

SCHEMA_SQL="${OUT_DIR}/public_schema.sql"
SUMMARY_MD="${OUT_DIR}/public_schema_summary.md"

export PGPASSWORD="${DB_PASSWORD}"

echo "Exporting schema-only SQL..."
pg_dump \
  -h "${DB_HOST}" \
  -p "${DB_PORT}" \
  -U "${DB_USER}" \
  -d "${DB_NAME}" \
  -n "${SCHEMA}" \
  --schema-only \
  --no-owner \
  --no-privileges \
  > "${SCHEMA_SQL}"

echo "Generating markdown summary..."
{
  echo "# PostgreSQL Schema Summary (${SCHEMA})"
  echo
  echo "- Database: ${DB_NAME}"
  echo "- Schema: ${SCHEMA}"
  echo "- Generated: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"
  echo

  echo "## Extensions"
  psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -X -A -t -c "
    SELECT '- ' || extname
    FROM pg_extension
    ORDER BY extname;
  "
  echo

  echo "## Enum Types"
  psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -X -A -F $'\t' -t -c "
    SELECT t.typname, string_agg(e.enumlabel, ', ' ORDER BY e.enumsortorder)
    FROM pg_type t
    JOIN pg_enum e ON e.enumtypid = t.oid
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE n.nspname = '${SCHEMA}'
    GROUP BY t.typname
    ORDER BY t.typname;
  " | while IFS=$'\t' read -r type_name labels; do
    [ -z "${type_name}" ] && continue
    echo "- ${type_name}: ${labels}"
  done
  echo

  echo "## Tables"
  TABLES="$(psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -X -A -t -c "
    SELECT tablename
    FROM pg_tables
    WHERE schemaname = '${SCHEMA}'
    ORDER BY tablename;
  ")"

  if [ -z "${TABLES}" ]; then
    echo "_No tables found in schema ${SCHEMA}_"
  fi

  while IFS= read -r tbl; do
    [ -z "${tbl}" ] && continue

    echo
    echo "### ${tbl}"
    echo
    echo "| Column | Type | Nullable | Default |"
    echo "|---|---|---|---|"

    psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -X -A -F $'\t' -t -c "
      SELECT
        c.column_name,
        c.data_type ||
          COALESCE(
            CASE
              WHEN c.udt_name <> c.data_type AND c.data_type = 'USER-DEFINED' THEN ' (' || c.udt_name || ')'
              ELSE ''
            END, ''
          ) ||
          COALESCE(
            CASE
              WHEN c.character_maximum_length IS NOT NULL THEN '(' || c.character_maximum_length || ')'
              ELSE ''
            END, ''
          ),
        c.is_nullable,
        COALESCE(c.column_default, '')
      FROM information_schema.columns c
      WHERE c.table_schema = '${SCHEMA}'
        AND c.table_name = '${tbl}'
      ORDER BY c.ordinal_position;
    " | while IFS=$'\t' read -r col typ nul def; do
      def="${def//|/\\|}"
      echo "| ${col} | ${typ} | ${nul} | ${def} |"
    done

    echo
    echo "Constraints:"
    psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -X -A -t -c "
      SELECT format('- %s [%s]', conname, contype::text)
      FROM pg_constraint
      WHERE conrelid = ('${SCHEMA}.${tbl}')::regclass
      ORDER BY conname;
    "

    echo
    echo "Indexes:"
    psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -X -A -t -c "
      SELECT '- ' || indexname || ': ' || indexdef
      FROM pg_indexes
      WHERE schemaname='${SCHEMA}' AND tablename='${tbl}'
      ORDER BY indexname;
    "
  done <<< "${TABLES}"
} > "${SUMMARY_MD}"

echo
echo "Done."
echo "SQL dump:      ${SCHEMA_SQL}"
echo "Markdown doc:  ${SUMMARY_MD}"
