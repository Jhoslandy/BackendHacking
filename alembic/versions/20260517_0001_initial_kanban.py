"""initial kanban schema

Revision ID: 20260517_0001
Revises:
Create Date: 2026-05-17
"""

from pathlib import Path
from typing import Sequence, Union

from alembic import op

revision: str = "20260517_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

BASE_DIR = Path(__file__).resolve().parents[2]


def _read_sql(relative_path: str) -> str:
    return (BASE_DIR / relative_path).read_text(encoding="utf-8")


def _execute_sql_file(relative_path: str) -> None:
    sql = _read_sql(relative_path)
    for statement in sql.split(";"):
        statement = statement.strip()
        if statement:
            op.execute(statement)


def upgrade() -> None:
    _execute_sql_file("migrations/001_create_kanban_schema.sql")
    _execute_sql_file("seeders/001_seed_roles.sql")


def downgrade() -> None:
    _execute_sql_file("migrations/001_drop_kanban_schema.sql")
