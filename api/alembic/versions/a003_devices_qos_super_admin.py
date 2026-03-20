"""devices QoS fields + super_admin role

Revision ID: a003_devices_qos
Revises: a002_shoot_role
Create Date: 2026-03-19
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "a003_devices_qos"
down_revision: Union[str, None] = "a002_shoot_role"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add super_admin to user_role enum
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'super_admin' AFTER 'owner'")

    # Device QoS columns
    op.add_column("devices", sa.Column("category", sa.String(30), server_default="other", nullable=False))
    op.add_column("devices", sa.Column("label", sa.String(255), nullable=True))
    op.add_column("devices", sa.Column("priority", sa.String(20), server_default="normal", nullable=False))
    op.add_column("devices", sa.Column("bandwidth_limit_down", sa.Integer, nullable=True))
    op.add_column("devices", sa.Column("bandwidth_limit_up", sa.Integer, nullable=True))
    op.add_column("devices", sa.Column("is_blocked", sa.Boolean, server_default="false", nullable=False))
    op.add_column("devices", sa.Column("rx_bytes", sa.Float, server_default="0", nullable=False))
    op.add_column("devices", sa.Column("tx_bytes", sa.Float, server_default="0", nullable=False))
    op.add_column("devices", sa.Column("signal_dbm", sa.Integer, nullable=True))
    op.add_column("devices", sa.Column("last_seen", sa.DateTime(timezone=True), server_default=sa.func.now()))


def downgrade() -> None:
    for col in ("category", "label", "priority", "bandwidth_limit_down", "bandwidth_limit_up",
                "is_blocked", "rx_bytes", "tx_bytes", "signal_dbm", "last_seen"):
        op.drop_column("devices", col)
