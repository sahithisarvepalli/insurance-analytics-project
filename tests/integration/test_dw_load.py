import duckdb

from src.dw_load import run_dw_load


def test_dw_load_creates_tables_and_counts(tmp_path):
    # Use a temporary DW file to avoid clobbering outputs during tests
    dw_path = str(tmp_path / "test_insurance_dw.duckdb")
    # Ensure environment uses same DATABASE_URL as devcontainer/CI
    run_dw_load(dw_path)

    conn = duckdb.connect(dw_path)
    try:
        tables = {r[0] for r in conn.execute("SHOW TABLES").fetchall()}
        expected = {
            "dim_member",
            "dim_provider",
            "dim_date",
            "fact_claims",
            "summary_kpis",
            "summary_monthly",
            "summary_loss_ratio",
            "summary_network",
        }
        assert expected.issubset(tables)

        # Basic row-count sanity checks
        member_count = conn.execute("SELECT COUNT(*) FROM dim_member").fetchone()[0]
        fact_count = conn.execute("SELECT COUNT(*) FROM fact_claims").fetchone()[0]
        assert member_count > 0
        assert fact_count > 0

        # Primary key uniqueness check for fact_claims.claim_id
        dup = conn.execute(
            "SELECT claim_id, COUNT(*) AS c FROM fact_claims GROUP BY claim_id HAVING COUNT(*) > 1"
        ).fetchall()
        assert len(dup) == 0
    finally:
        conn.close()
