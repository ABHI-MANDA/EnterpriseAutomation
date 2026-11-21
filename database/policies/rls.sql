-- PostgreSQL Database-Level Row Level Security (RLS) & Append-Only Audit Grants
-- Enforces data boundary defense-in-depth even if an application-layer check is missed.

-- 1. Create Least-Privilege Application Runtime Role
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_rw') THEN
    CREATE ROLE app_rw LOGIN PASSWORD 'CHANGE_ME_SECURE_PASS';
  END IF;
END
$$;

-- 2. Grants for Operational Tables
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_rw;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_rw;

-- 3. Strict Append-Only Protection for Audit, Access & Consent Logs
REVOKE UPDATE, DELETE, TRUNCATE ON audit_log FROM app_rw;
REVOKE UPDATE, DELETE, TRUNCATE ON access_logs FROM app_rw;
REVOKE UPDATE, DELETE, TRUNCATE ON consent_records FROM app_rw;
REVOKE UPDATE, DELETE, TRUNCATE ON activities FROM app_rw;

GRANT SELECT, INSERT ON audit_log TO app_rw;
GRANT SELECT, INSERT ON access_logs TO app_rw;
GRANT SELECT, INSERT ON consent_records TO app_rw;
GRANT SELECT, INSERT ON activities TO app_rw;

-- 4. Enable Row Level Security (RLS)
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE deals ENABLE ROW LEVEL SECURITY;
ALTER TABLE activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE communications ENABLE ROW LEVEL SECURITY;

-- 5. RLS Policies using Session Variables (SET LOCAL app.role, app.region, app.user_id)
DROP POLICY IF EXISTS rls_customers_scope ON customers;
CREATE POLICY rls_customers_scope ON customers FOR ALL TO app_rw
USING (
  current_setting('app.role', true) IN ('super_admin', 'admin', 'management', 'auditor')
  OR region = current_setting('app.region', true)
  OR assignee_id = current_setting('app.user_id', true)
);

DROP POLICY IF EXISTS rls_leads_scope ON leads;
CREATE POLICY rls_leads_scope ON leads FOR ALL TO app_rw
USING (
  current_setting('app.role', true) IN ('super_admin', 'admin', 'management', 'auditor')
  OR region = current_setting('app.region', true)
  OR assignee_id = current_setting('app.user_id', true)
);

DROP POLICY IF EXISTS rls_tasks_scope ON tasks;
CREATE POLICY rls_tasks_scope ON tasks FOR ALL TO app_rw
USING (
  current_setting('app.role', true) IN ('super_admin', 'admin', 'management', 'auditor')
  OR region = current_setting('app.region', true)
  OR assignee_id = current_setting('app.user_id', true)
);

DROP POLICY IF EXISTS rls_deals_scope ON deals;
CREATE POLICY rls_deals_scope ON deals FOR ALL TO app_rw
USING (
  current_setting('app.role', true) IN ('super_admin', 'admin', 'management', 'auditor')
  OR region = current_setting('app.region', true)
);

DROP POLICY IF EXISTS rls_activities_scope ON activities;
CREATE POLICY rls_activities_scope ON activities FOR ALL TO app_rw
USING (
  current_setting('app.role', true) IN ('super_admin', 'admin', 'management', 'auditor')
  OR region = current_setting('app.region', true)
  OR actor_id = current_setting('app.user_id', true)
);
