"""add scan_error to sitemap_entries

Revision ID: 20260422_0002
Revises: 20260422_0001
Create Date: 2026-04-22 00:20:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260422_0002"
down_revision = "20260422_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sitemap_entries", sa.Column("scan_error", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("sitemap_entries", "scan_error")

