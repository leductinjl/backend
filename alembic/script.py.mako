"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

This is an Alembic migration script template. 
Each migration script is generated from this template and contains:
- Automatically generated metadata about the migration
- Upgrade and downgrade functions to apply or revert database changes
"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    """Apply the database changes in this migration"""
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """Revert the database changes in this migration"""
    ${downgrades if downgrades else "pass"} 