import os
import sys

from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))  # noqa: E402

from src.utils import get_engine


def test_schema_tables_exist():
    eng = get_engine()
    with eng.connect() as con:
        res = con.execute(
            text(
                """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_schema = 'insurance'
              AND table_name IN ('member','provider','claim')
        """
            )
        )
        rows = list(res)
        assert len(rows) >= 3, "Expected tables member, provider, claim in schema insurance."
