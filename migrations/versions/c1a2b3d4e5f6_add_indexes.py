"""add query indexes

Revision ID: c1a2b3d4e5f6
Revises: a15581f49ebb
Create Date: 2026-10-22
"""
from typing import Sequence, Union

from alembic import op

revision: str = "c1a2b3d4e5f6"
down_revision: Union[str, None] = "a15581f49ebb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_projects_owner_id", "projects", ["owner_id"])
    op.create_index("ix_drawings_status", "drawings", ["status"])
    op.create_index("ix_versions_created_by", "versions", ["created_by"])
    op.create_index("ix_jobs_type", "jobs", ["type"])
    op.create_index("ix_approvals_status", "approvals", ["status"])
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor_id", table_name="audit_logs")
    op.drop_index("ix_approvals_status", table_name="approvals")
    op.drop_index("ix_jobs_type", table_name="jobs")
    op.drop_index("ix_versions_created_by", table_name="versions")
    op.drop_index("ix_drawings_status", table_name="drawings")
    op.drop_index("ix_projects_owner_id", table_name="projects")
