"""notifications and comments

Revision ID: d2e3f4a5b6c7
Revises: c1a2b3d4e5f6
Create Date: 2026-10-23
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d2e3f4a5b6c7"
down_revision: Union[str, None] = "c1a2b3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("link", sa.String(length=256), nullable=False),
        sa.Column("read", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_created_at", "notifications", ["created_at"])
    op.create_index("ix_notifications_user_read", "notifications", ["user_id", "read"])

    op.create_table(
        "comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("drawing_id", sa.Integer(), nullable=False),
        sa.Column("version_id", sa.Integer(), nullable=True),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["drawing_id"], ["drawings.id"]),
        sa.ForeignKeyConstraint(["version_id"], ["versions.id"]),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_comments_drawing_id", "comments", ["drawing_id"])
    op.create_index("ix_comments_version_id", "comments", ["version_id"])
    op.create_index("ix_comments_author_id", "comments", ["author_id"])
    op.create_index("ix_comments_created_at", "comments", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_comments_created_at", table_name="comments")
    op.drop_index("ix_comments_author_id", table_name="comments")
    op.drop_index("ix_comments_version_id", table_name="comments")
    op.drop_index("ix_comments_drawing_id", table_name="comments")
    op.drop_table("comments")

    op.drop_index("ix_notifications_user_read", table_name="notifications")
    op.drop_index("ix_notifications_created_at", table_name="notifications")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")
