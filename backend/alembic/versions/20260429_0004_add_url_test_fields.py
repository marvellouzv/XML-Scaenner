"""add url test fields to sitemap_entries

Revision ID: 20260429_0004
Revises: 20260423_0003
Create Date: 2026-04-29 20:25:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260429_0004"
down_revision = "20260423_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sitemap_entries", sa.Column("test_status", sa.String(), nullable=False, server_default="pending"))
    op.add_column("sitemap_entries", sa.Column("test_error", sa.String(), nullable=True))
    op.add_column("sitemap_entries", sa.Column("test_http_status", sa.Integer(), nullable=True))
    op.add_column("sitemap_entries", sa.Column("test_response_time_ms", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("sitemap_entries", "test_response_time_ms")
    op.drop_column("sitemap_entries", "test_http_status")
    op.drop_column("sitemap_entries", "test_error")
    op.drop_column("sitemap_entries", "test_status")
