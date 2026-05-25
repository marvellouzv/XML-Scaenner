"""init schema

Revision ID: 20260422_0001
Revises:
Create Date: 2026-04-22 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260422_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scan_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sitemap_url", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_scan_sessions_id"), "scan_sessions", ["id"], unique=False)

    op.create_table(
        "sitemap_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("lastmod", sa.String(), nullable=True),
        sa.Column("changefreq", sa.String(), nullable=True),
        sa.Column("priority", sa.String(), nullable=True),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("scan_status", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["scan_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sitemap_entries_id"), "sitemap_entries", ["id"], unique=False)
    op.create_index(op.f("ix_sitemap_entries_session_id"), "sitemap_entries", ["session_id"], unique=False)
    op.create_index(op.f("ix_sitemap_entries_url"), "sitemap_entries", ["url"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_sitemap_entries_url"), table_name="sitemap_entries")
    op.drop_index(op.f("ix_sitemap_entries_session_id"), table_name="sitemap_entries")
    op.drop_index(op.f("ix_sitemap_entries_id"), table_name="sitemap_entries")
    op.drop_table("sitemap_entries")
    op.drop_index(op.f("ix_scan_sessions_id"), table_name="scan_sessions")
    op.drop_table("scan_sessions")

