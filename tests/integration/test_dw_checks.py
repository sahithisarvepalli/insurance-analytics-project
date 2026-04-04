import duckdb
import pytest

from src.dw_load import run_dw_load, run_quality_checks
from src.transform import run_transform


@pytest.mark.integration
def test_dw_quality_checks(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run_transform()
    dw_path = str(tmp_path / "qa_insurance_dw.duckdb")
    run_dw_load(dw_path, report_dir=str(tmp_path / "build/reports"))
    conn = duckdb.connect(dw_path)
    try:
        results = run_quality_checks(conn)
        assert results.get("status") == "ok"

        expected_keys = {
            "dim_member_count",
            "dim_provider_count",
            "dim_date_count",
            "fact_claims_count",
            "fact_claims_dup_claim_id",
            "missing_member_refs",
            "missing_provider_refs",
            "missing_date_refs",
            "null_member_pk",
            "null_provider_pk",
            "null_date_pk",
        }
        assert expected_keys.issubset(results.keys()), results
        assert results["dim_member_count"] > 0
        assert results["dim_provider_count"] > 0
        assert results["dim_date_count"] > 0
        assert results["fact_claims_count"] > 0
        assert results["fact_claims_dup_claim_id"] == 0
        assert results["missing_member_refs"] == 0
        assert results["missing_provider_refs"] == 0
        assert results["missing_date_refs"] == 0
        assert results["null_member_pk"] == 0
        assert results["null_provider_pk"] == 0
        assert results["null_date_pk"] == 0
    finally:
        conn.close()
