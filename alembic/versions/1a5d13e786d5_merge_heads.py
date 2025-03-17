"""merge_heads

Revision ID: 1a5d13e786d5
Revises: 02f86ffcbf2d, 5e2633006bde
Create Date: 2025-03-15 10:57:01.536487

This is an Alembic migration script template. 
Each migration script is generated from this template and contains:
- Automatically generated metadata about the migration
- Upgrade and downgrade functions to apply or revert database changes
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1a5d13e786d5'
down_revision = ('02f86ffcbf2d', '5e2633006bde')
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply the database changes in this migration"""
    pass


def downgrade() -> None:
    """Revert the database changes in this migration"""
    pass 