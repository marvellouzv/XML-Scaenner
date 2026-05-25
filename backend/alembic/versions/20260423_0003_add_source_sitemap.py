"""add source_sitemap to sitemap_entries

Revision ID: 20260423_0003
Revises: 20260422_0002
Create Date: 2026-04-23 00:10:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260423_0003"
down_revision = "20260422_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sitemap_entries", sa.Column("source_sitemap", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("sitemap_entries", "source_sitemap")

