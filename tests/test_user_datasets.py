import io

import pandas as pd

from src.data.user_datasets import load_uploaded_files
from src.tools import sql_tools


class FakeUpload:
    def __init__(self, name: str, content: bytes):
        self.name = name
        self._content = content

    def getvalue(self) -> bytes:
        return self._content


def test_load_multiple_formats_as_separate_tables():
    excel = io.BytesIO()
    with pd.ExcelWriter(excel, engine="openpyxl") as writer:
        pd.DataFrame({"city": ["Paris"], "population": [2]}).to_excel(
            writer, index=False, sheet_name="cities"
        )
        pd.DataFrame({"region": ["IDF"]}).to_excel(
            writer, index=False, sheet_name="regions"
        )

    files = [
        FakeUpload("orders.csv", b"item,amount,order_date\nbook,12,2026-01-02\npen,3,2026-01-03\n"),
        FakeUpload("customers.json", b'[{"name":"Ada","active":true}]'),
        FakeUpload("places.xlsx", excel.getvalue()),
    ]

    connection, details = load_uploaded_files(files)
    try:
        assert [name for name, _, _ in details] == [
            "orders",
            "customers",
            "places_cities",
            "places_regions",
        ]
        assert [count for _, count, _ in details] == [2, 1, 1, 1]
        assert connection.execute("SELECT amount FROM orders").fetchone() == (12,)
        assert "TIMESTAMP" in connection.execute(
            "DESCRIBE orders"
        ).fetchall()[2][1]
        assert connection.execute("SELECT name FROM customers").fetchone() == ("Ada",)
        assert connection.execute(
            "SELECT city FROM places_cities"
        ).fetchone() == ("Paris",)
        assert connection.execute(
            "SELECT region FROM places_regions"
        ).fetchone() == ("IDF",)
    finally:
        connection.close()


def test_duplicate_table_names_are_made_unique():
    files = [
        FakeUpload("data.csv", b"value\n1\n"),
        FakeUpload("data.json", b'[{"value":2}]'),
    ]

    connection, details = load_uploaded_files(files)
    try:
        assert [name for name, _, _ in details] == ["data", "data_2"]
        assert connection.execute("SELECT value FROM data_2").fetchone() == (2,)
    finally:
        connection.close()


def test_unsupported_file_format_is_reported():
    try:
        load_uploaded_files([FakeUpload("notes.txt", b"not a table")])
    except ValueError as error:
        assert "Format non pris en charge" in str(error)
    else:
        raise AssertionError("Un format non pris en charge doit être refusé.")


def test_sql_tools_use_the_active_uploaded_dataset():
    connection, _ = load_uploaded_files(
        [FakeUpload("metrics.csv", b"team,score\nA,10\nB,20\n")]
    )
    original_session_id = sql_tools._session_id
    sql_tools._session_id = lambda: "test-upload-session"
    sql_tools.set_active_dataset("test-upload-session", connection)

    try:
        assert sql_tools.list_tables() == "metrics"
        assert "score (BIGINT)" in sql_tools.describe_table("metrics")
        assert "30" in sql_tools.run_sql("SELECT SUM(score) AS total FROM metrics")
        assert "metrics" in sql_tools.get_database_schema()
    finally:
        sql_tools.set_active_dataset("test-upload-session", None)
        sql_tools._session_id = original_session_id
        connection.close()
