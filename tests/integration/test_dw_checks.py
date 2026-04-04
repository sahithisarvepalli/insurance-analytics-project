import duckdb

from src.dw_load import run_dw_load, run_quality_checks


def test_dw_quality_checks(tmp_path):
    dw_path = str(tmp_path / "qa_insurance_dw.duckdb")
    run_dw_load(dw_path)
    conn = duckdb.connect(dw_path)
    try:
        results = run_quality_checks(conn)
        assert results.get("status") == "ok"
    finally:
        conn.close()
