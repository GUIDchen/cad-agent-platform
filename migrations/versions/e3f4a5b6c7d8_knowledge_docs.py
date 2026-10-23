"""knowledge docs

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-10-23
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e3f4a5b6c7d8"
down_revision: Union[str, None] = "d2e3f4a5b6c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "knowledge_docs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_knowledge_docs_title", "knowledge_docs", ["title"])
    op.create_index("ix_knowledge_docs_created_by", "knowledge_docs", ["created_by"])
    op.create_index("ix_knowledge_docs_created_at", "knowledge_docs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_knowledge_docs_created_at", table_name="knowledge_docs")
    op.drop_index("ix_knowledge_docs_created_by", table_name="knowledge_docs")
    op.drop_index("ix_knowledge_docs_title", table_name="knowledge_docs")
    op.drop_table("knowledge_docs")
