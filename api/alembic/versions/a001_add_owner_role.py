"""add owner role to user_role enum

Revision ID: a001_owner_role
Revises: 5c85006f0eff
Create Date: 2026-03-19
"""
from typing import Sequence, Union
from alembic import op

revision: str = "a001_owner_role"
down_revision: Union[str, None] = "5c85006f0eff"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL: add 'owner' to the user_role enum
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'owner' BEFORE 'admin'")


def downgrade() -> None:
    # Cannot easily remove enum values in PostgreSQL
    # Would need to recreate the type — left as no-op
    pass
