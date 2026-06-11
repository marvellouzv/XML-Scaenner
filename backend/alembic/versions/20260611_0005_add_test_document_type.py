"""add test_document_type to sitemap_entries

Revision ID: 20260611_0005
Revises: 20260429_0004
Create Date: 2026-06-11 12:55:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260611_0005"
down_revision = "20260429_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sitemap_entries", sa.Column("test_document_type", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("sitemap_entries", "test_document_type")
