"""add user_id to documents

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-15

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("user_id", sa.String(36), nullable=True),
    )
    # Backfill existing rows with a sentinel UUID — they belong to nobody
    op.execute(
        "UPDATE documents SET user_id = '00000000-0000-0000-0000-000000000000'"
    )
    op.alter_column("documents", "user_id", nullable=False)
    op.create_index("ix_documents_user_id", "documents", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_documents_user_id", table_name="documents")
    op.drop_column("documents", "user_id")
