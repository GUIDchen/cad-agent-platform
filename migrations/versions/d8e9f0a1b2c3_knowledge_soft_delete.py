"""knowledge soft delete

Revision ID: d8e9f0a1b2c3
Revises: c7d8e9f0a1b2
Create Date: 2026-10-23
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d8e9f0a1b2c3"
down_revision: Union[str, None] = "c7d8e9f0a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("knowledge_docs", sa.Column("deleted_at", sa.DateTime(), nullable=True))
    op.create_index("ix_knowledge_docs_deleted_at", "knowledge_docs", ["deleted_at"])


def downgrade() -> None:
    op.drop_index("ix_knowledge_docs_deleted_at", table_name="knowledge_docs")
    with op.batch_alter_table("knowledge_docs") as batch_op:
        batch_op.drop_column("deleted_at")
