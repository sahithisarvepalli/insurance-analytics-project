import duckdb
import pytest

from src.dw_load import run_dw_load
from src.transform import run_transform


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


@pytest.mark.integration
def test_dw_load_with_custom_output_dir(tmp_path):
    """run_dw_load must load summary CSVs from a non-default output_dir.

    Mirrors the GitHub Actions matrix usage where each client has its own isolated output directory
    (e.g. outputs/client_a/).
    """
    custom_dir = str(tmp_path / "client_test")
    dw_path = str(tmp_path / "client_test_dw.duckdb")

    # Generate the summary CSVs in the custom directory via run_transform
    run_transform(output_dir=custom_dir)

    # Now load the DW using the same custom directory — should pick up those CSVs
    run_dw_load(dw_path, output_dir=custom_dir)

    conn = duckdb.connect(dw_path)
    try:
        tables = {r[0] for r in conn.execute("SHOW TABLES").fetchall()}
        summary_tables = {
            "summary_kpis",
            "summary_monthly",
            "summary_loss_ratio",
            "summary_network",
        }
        assert summary_tables.issubset(tables), (
            f"Expected summary tables to be loaded from '{custom_dir}', "
            f"missing: {summary_tables - tables}"
        )
        # Summary tables must contain rows loaded from the custom dir
        kpi_count = conn.execute("SELECT COUNT(*) FROM summary_kpis").fetchone()[0]
        assert kpi_count > 0, "summary_kpis must be non-empty after loading from custom output_dir"
    finally:
        conn.close()
