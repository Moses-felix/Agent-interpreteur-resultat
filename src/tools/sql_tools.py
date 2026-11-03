
import duckdb
from pathlib import Path
from streamlit.runtime.scriptrunner import get_script_run_ctx

DB_PATH = (Path(__file__).parent.parent.parent / "data" / "sales.duckdb").resolve()
_ACTIVE_DATASETS: dict[str, duckdb.DuckDBPyConnection | None] = {}
_LAST_RESULTS: dict[str, object] = {}


def _session_id() -> str | None:
    context = get_script_run_ctx(suppress_warning=True)
    return context.session_id if context else None


def set_active_dataset(
    session_id: str,
    connection: duckdb.DuckDBPyConnection | None,
) -> None:
    _ACTIVE_DATASETS[session_id] = connection
    _LAST_RESULTS.pop(session_id, None)


def _connection() -> tuple[duckdb.DuckDBPyConnection, bool]:
    session_id = _session_id()
    active_connection = _ACTIVE_DATASETS.get(session_id) if session_id else None
    if active_connection is not None:
        return active_connection, False
    return duckdb.connect(str(DB_PATH), read_only=True), True


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def get_last_result():
    """Retourne le DataFrame du dernier run_sql réussi."""
    return _LAST_RESULTS.get(_session_id() or "default")


def get_table_schemas() -> list[tuple[str, list[tuple[str, str]]]]:
    """Retourne les tables et colonnes du dataset actif."""
    con, should_close = _connection()
    try:
        table_names = [row[0] for row in con.execute("SHOW TABLES").fetchall()]
        return [
            (
                table_name,
                [
                    (row[0], row[1])
                    for row in con.execute(
                        f"DESCRIBE {_quote_identifier(table_name)}"
                    ).fetchall()
                ],
            )
            for table_name in table_names
        ]
    finally:
        if should_close:
            con.close()


def get_database_schema() -> str:
    """Formate le schéma actif pour le contexte du modèle."""
    schemas = get_table_schemas()
    if not schemas:
        return "Aucune table n'est disponible dans le dataset actif."
    return "\n".join(
        f"- {table_name} : "
        + ", ".join(f"{column} ({type_name})" for column, type_name in columns)
        for table_name, columns in schemas
    )


def run_sql(query: str) -> str:
    """
    Exécute une requête SQL SELECT en lecture seule.
    Retourne un tableau formaté en texte (tronqué à 50 lignes).
    """
    query = query.strip().rstrip(";")
    
    if not query.lower().lstrip().startswith("select"):
        return "❌ Erreur : seules les requêtes SELECT sont autorisées."
    
    con, should_close = _connection()
    try:
        df = con.execute(query).fetchdf()
    except Exception as e:
        return f"❌ Erreur SQL : {e}"
    finally:
        if should_close:
            con.close()

    _LAST_RESULTS[_session_id() or "default"] = df

    if df.empty:
        return "Aucun résultat."
    
    truncated = df.head(50)
    header = " | ".join(str(c) for c in truncated.columns)
    sep = "-" * len(header)
    rows = "\n".join(
        " | ".join(str(v) for v in row)
        for row in truncated.itertuples(index=False)
    )
    
    result = f"{header}\n{sep}\n{rows}"
    if len(df) > 50:
        result += f"\n... ({len(df) - 50} lignes supplémentaires)"
    return result


def list_tables() -> str:
    """Liste les tables disponibles dans la base."""
    con, should_close = _connection()
    try:
        rows = con.execute("SHOW TABLES").fetchall()
    finally:
        if should_close:
            con.close()
    return "\n".join(r[0] for r in rows)


def describe_table(table_name: str) -> str:
    """Retourne le schéma d'une table (colonnes + types)."""
    con, should_close = _connection()
    try:
        rows = con.execute(f"DESCRIBE {_quote_identifier(table_name)}").fetchall()
    except Exception as e:
        return f"❌ Table inconnue '{table_name}' : {e}"
    finally:
        if should_close:
            con.close()
    lines = [f"{r[0]} ({r[1]})" for r in rows]
    return "\n".join(lines)



TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "list_tables",
            "description": "Liste toutes les tables disponibles dans la base de données. À appeler en premier si tu ne connais pas le schéma.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "describe_table",
            "description": "Retourne les colonnes et types d'une table. À utiliser avant d'écrire du SQL si tu n'es pas sûr du schéma.",
            "parameters": {
                "type": "object",
                "properties": {
                    "table_name": {
                        "type": "string",
                        "description": "Nom exact de la table (ex: 'sales', 'products')."
                    }
                },
                "required": ["table_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_sql",
            "description": "Exécute une requête SQL SELECT en lecture seule et retourne les résultats. Utilise le dialecte DuckDB (compatible PostgreSQL).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "La requête SQL SELECT. Ne pas inclure de point-virgule final."
                    }
                },
                "required": ["query"],
            },
        },
    },
]


def execute_tool(name: str, args: dict) -> str:
    if name == "list_tables":
        return list_tables()
    if name == "describe_table":
        return describe_table(**args)
    if name == "run_sql":
        return run_sql(**args)
    if name == "plot_chart":
        from src.tools.plot_tools import plot_chart
        return plot_chart(**args)
    if name == "analyze_series":
        from src.tools.analysis_tools import analyze_series
        return analyze_series(**args)
    return f"❌ Outil inconnu : {name}"