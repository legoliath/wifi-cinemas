"""add shoot_role to shoot_accesses

Revision ID: a002_shoot_role
Revises: a001_owner_role
Create Date: 2026-03-19
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "a002_shoot_role"
down_revision: Union[str, None] = "a001_owner_role"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("shoot_accesses", sa.Column("shoot_role", sa.String(20), server_default="user", nullable=False))


def downgrade() -> None:
    op.drop_column("shoot_accesses", "shoot_role")
