import sqlite3
from dataclasses import dataclass

from app.config import get_settings


@dataclass
class ColumnInfo:
    name: str
    type: str


@dataclass
class TableInfo:
    name: str
    columns: list[ColumnInfo]


def load_schema() -> list[TableInfo]:
    settings = get_settings()
    conn = sqlite3.connect(settings.db_path)
    cur = conn.cursor()
    tables: list[TableInfo] = []
    try:
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        for (table_name,) in cur.fetchall():
            cur.execute(f'PRAGMA table_info("{table_name}")')
            cols = [ColumnInfo(name=row[1], type=row[2]) for row in cur.fetchall()]
            tables.append(TableInfo(name=table_name, columns=cols))
    finally:
        conn.close()
    return tables


def schema_for_prompt() -> str:
    """Human-readable schema description injected into the LLM prompt."""
    tables = load_schema()
    if not tables:
        return "(no tables found)"
    lines = []
    for table in tables:
        lines.append(f"Table `{table.name}`:")
        for col in table.columns:
            lines.append(f"  - {col.name}: {col.type}")
    return "\n".join(lines)
