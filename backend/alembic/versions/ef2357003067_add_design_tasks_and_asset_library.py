"""add design tasks and asset library

Revision ID: ef2357003067
Revises: 342ccc5f7fdd
Create Date: 2026-03-02 11:45:29.918999

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ef2357003067"
down_revision: Union[str, None] = "342ccc5f7fdd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "design_tasks",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("task_type", sa.String(50), nullable=False, server_default="other"),
        sa.Column("status", sa.String(50), nullable=False, server_default="not_started"),
        sa.Column("priority", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("assignee_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("due_date", sa.Date, nullable=True),
        sa.Column("community_id", sa.Integer, sa.ForeignKey("communities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_by_user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("content_id", sa.Integer, sa.ForeignKey("contents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "assets",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("asset_type", sa.String(50), nullable=False),
        sa.Column("file_url", sa.String(1000), nullable=False),
        sa.Column("file_key", sa.String(500), nullable=False),
        sa.Column("file_size", sa.Integer, nullable=True),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("tags", sa.JSON, nullable=True),
        sa.Column("community_id", sa.Integer, sa.ForeignKey("communities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("uploaded_by_user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "content_assets",
        sa.Column("content_id", sa.Integer, sa.ForeignKey("contents.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("asset_id", sa.Integer, sa.ForeignKey("assets.id", ondelete="CASCADE"), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table("content_assets")
    op.drop_table("assets")
    op.drop_table("design_tasks")
