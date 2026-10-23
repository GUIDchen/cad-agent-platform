"""knowledge doc embeddings

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8
Create Date: 2026-10-23
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f4a5b6c7d8e9"
down_revision: Union[str, None] = "e3f4a5b6c7d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("knowledge_docs", sa.Column("embedding_json", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("knowledge_docs") as batch_op:
        batch_op.drop_column("embedding_json")
