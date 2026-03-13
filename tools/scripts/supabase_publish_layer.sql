-- Supabase Publish Layer — Aggregated operational data for cross-agent access
-- Run once in Supabase SQL Editor to create the tables.
-- These tables receive summaries from local pipeline scripts.
-- Raw data stays in local SQLite; only "answers" are published here.

-- ============================================================================
-- 1. MTD Summary — Month-to-date billing from Colppy production DB
-- ============================================================================
-- Published by: publish_to_supabase.py --mtd
-- Source: colppy_export.db (pago + facturacion + plan + empresa tables)
-- Definition: new product = pago.primerPago=1. Do NOT use facturacion.fechaAlta (dead column).
-- Counts are products (billing subscriptions), not customers (empresas).
-- ICP: facturacion.CUIT == empresa.CUIT → Pyme, != → Operador
-- Product family: plan.nombre LIKE '%sueldos%' → Sueldos, else → Administración
-- ~20 rows per month

CREATE TABLE IF NOT EXISTS mtd_summary (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    month           TEXT NOT NULL,           -- 'Mar-2026'
    metric          TEXT NOT NULL,           -- 'new_mrr_adm_pyme', 'active_clients', 'payments_collected', etc.
    value           NUMERIC,                 -- amount in ARS or count
    count           INTEGER,                 -- number of items (clients, payments)
    refreshed_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_db_date  TEXT,                    -- last sync date of colppy_export.db
    UNIQUE(month, metric)                    -- upsert by month+metric
);

CREATE INDEX IF NOT EXISTS idx_mtd_month ON mtd_summary(month);

-- ============================================================================
-- 2. Reconciliation Summary — Colppy ↔ HubSpot match results
-- ============================================================================
-- Published by: publish_to_supabase.py --reconciliation
-- Source: reconcile_colppy_hubspot_db_only.py output
-- ~8 rows per month (4 categories × 2 metrics each)

CREATE TABLE IF NOT EXISTS reconciliation_summary (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    year            INTEGER NOT NULL,
    month           INTEGER NOT NULL,        -- 1-12
    category        TEXT NOT NULL,            -- 'match', 'date_mismatch', 'wrong_stage', 'hubspot_only', 'colppy_only'
    deal_count      INTEGER,
    total_amount    NUMERIC,                 -- ARS
    match_rate_pct  NUMERIC,                 -- overall match rate (same for all rows in a month)
    refreshed_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(year, month, category)
);

CREATE INDEX IF NOT EXISTS idx_recon_ym ON reconciliation_summary(year, month);

-- ============================================================================
-- 3. ICP Dashboard — Aggregated metrics by ICP type
-- ============================================================================
-- Published by: publish_to_supabase.py --icp
-- Source: facturacion_hubspot.db + HubSpot MCP
-- ~30 rows per month

CREATE TABLE IF NOT EXISTS icp_dashboard (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    month           TEXT NOT NULL,           -- 'Mar-2026'
    icp_type        TEXT NOT NULL,           -- 'Cuenta Pyme', 'Cuenta Contador'
    metric          TEXT NOT NULL,           -- 'active_clients', 'new_clients', 'churned_clients', 'mrr', 'new_mrr', 'avg_mrr'
    value           NUMERIC,
    count           INTEGER,
    refreshed_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(month, icp_type, metric)
);

CREATE INDEX IF NOT EXISTS idx_icp_month ON icp_dashboard(month);

-- ============================================================================
-- RLS Policies (same pattern as kpi_values)
-- ============================================================================

ALTER TABLE mtd_summary ENABLE ROW LEVEL SECURITY;
ALTER TABLE reconciliation_summary ENABLE ROW LEVEL SECURITY;
ALTER TABLE icp_dashboard ENABLE ROW LEVEL SECURITY;

-- Anon key: read-only
CREATE POLICY "anon_read_mtd" ON mtd_summary FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read_recon" ON reconciliation_summary FOR SELECT TO anon USING (true);
CREATE POLICY "anon_read_icp" ON icp_dashboard FOR SELECT TO anon USING (true);

-- Service role: full access
CREATE POLICY "service_all_mtd" ON mtd_summary FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_all_recon" ON reconciliation_summary FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_all_icp" ON icp_dashboard FOR ALL TO service_role USING (true) WITH CHECK (true);
