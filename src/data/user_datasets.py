import io
import re
from pathlib import Path
from typing import Protocol

import duckdb
import pandas as pd


class UploadedFile(Protocol):
    name: str

    def getvalue(self) -> bytes: ...


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _table_name(value: str, existing: set[str]) -> str:
    name = re.sub(r"\W", "_", value, flags=re.UNICODE).strip("_") or "dataset"
    if name[0].isdigit():
        name = f"table_{name}"
    name = name[:120]

    candidate = name
    suffix = 2
    while candidate.casefold() in existing:
        ending = f"_{suffix}"
        candidate = f"{name[:120 - len(ending)]}{ending}"
        suffix += 1

    existing.add(candidate.casefold())
    return candidate


def _read_file(uploaded_file: UploadedFile) -> list[tuple[str, pd.DataFrame]]:
    extension = Path(uploaded_file.name).suffix.lower()
    content = io.BytesIO(uploaded_file.getvalue())

    if extension == ".csv":
        frames = [(Path(uploaded_file.name).stem, pd.read_csv(content, sep=None, engine="python"))]
    elif extension == ".json":
        frames = [(Path(uploaded_file.name).stem, pd.read_json(content))]
    elif extension == ".xlsx":
        sheets = pd.read_excel(content, sheet_name=None)
        frames = [
            (f"{Path(uploaded_file.name).stem}_{sheet_name}", frame)
            for sheet_name, frame in sheets.items()
        ]
    else:
        raise ValueError(f"Format non pris en charge : {extension or '(sans extension)'}")

    for _, frame in frames:
        for column in frame.columns:
            column_name = str(column).lower()
            if (
                ("date" not in column_name and "time" not in column_name)
                or pd.api.types.is_numeric_dtype(frame[column].dtype)
            ):
                continue
            parsed = pd.to_datetime(frame[column], errors="coerce", format="mixed")
            if parsed.notna().any() and (frame[column].isna() | parsed.notna()).all():
                frame[column] = parsed

    return frames


def load_uploaded_files(
    uploaded_files: list[UploadedFile],
) -> tuple[duckdb.DuckDBPyConnection, list[tuple[str, int, list[str]]]]:
    """Charge des fichiers tabulaires dans des tables DuckDB isolées en mémoire."""
    if not uploaded_files:
        raise ValueError("Choisissez au moins un fichier CSV, XLSX ou JSON.")

    connection = duckdb.connect(":memory:")
    existing_tables: set[str] = set()
    table_details: list[tuple[str, int, list[str]]] = []

    try:
        for uploaded_file in uploaded_files:
            try:
                frames = _read_file(uploaded_file)
                for requested_name, frame in frames:
                    if len(frame.columns) == 0:
                        raise ValueError("le fichier ne contient aucune colonne")

                    table_name = _table_name(requested_name, existing_tables)
                    connection.register("_uploaded_frame", frame)
                    try:
                        connection.execute(
                            f"CREATE TABLE {_quote_identifier(table_name)} "
                            "AS SELECT * FROM _uploaded_frame"
                        )
                    finally:
                        connection.unregister("_uploaded_frame")

                    table_details.append(
                        (table_name, len(frame), [str(column) for column in frame.columns])
                    )
            except Exception as error:
                raise ValueError(
                    f"Impossible de charger « {Path(uploaded_file.name).name} » : {error}"
                ) from error
    except Exception:
        connection.close()
        raise

    return connection, table_details
