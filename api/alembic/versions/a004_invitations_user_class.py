"""add invitation fields + user_class to shoot_accesses

Revision ID: a004_invitations
Revises: a003_devices_qos
Create Date: 2026-03-19
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "a004_invitations"
down_revision: Union[str, None] = "a003_devices_qos"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("shoot_accesses", sa.Column("user_class", sa.String(50), nullable=True))
    op.add_column("shoot_accesses", sa.Column("invite_token", sa.String(100), nullable=True))
    op.add_column("shoot_accesses", sa.Column("invite_email", sa.String(255), nullable=True))
    op.add_column("shoot_accesses", sa.Column("invite_accepted_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_shoot_accesses_invite_token", "shoot_accesses", ["invite_token"], unique=True)
    # Rename shoot_role to user_class if it exists (from previous migration)
    # Data migration: copy shoot_role values to user_class where applicable
    try:
        op.execute("UPDATE shoot_accesses SET user_class = shoot_role WHERE shoot_role IS NOT NULL AND shoot_role != 'user'")
        op.drop_column("shoot_accesses", "shoot_role")
    except Exception:
        pass  # Column may not exist in fresh installs


def downgrade() -> None:
    op.drop_index("ix_shoot_accesses_invite_token", "shoot_accesses")
    op.drop_column("shoot_accesses", "invite_accepted_at")
    op.drop_column("shoot_accesses", "invite_email")
    op.drop_column("shoot_accesses", "invite_token")
    op.drop_column("shoot_accesses", "user_class")
