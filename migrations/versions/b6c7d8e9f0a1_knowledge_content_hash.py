"""knowledge content hash

Revision ID: b6c7d8e9f0a1
Revises: a5b6c7d8e9f0
Create Date: 2026-10-23
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b6c7d8e9f0a1"
down_revision: Union[str, None] = "a5b6c7d8e9f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("knowledge_docs", sa.Column("content_hash", sa.String(length=64), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("knowledge_docs") as batch_op:
        batch_op.drop_column("content_hash")
