"""tz aware datetimes

Revision ID: ccd7d27d3c7c
Revises: 69ac357aafd7
Create Date: 2025-09-26 08:55:21.314597

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ccd7d27d3c7c'
down_revision: Union[str, Sequence[str], None] = '69ac357aafd7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # users
    op.alter_column("users", "created_at",
        type_=sa.TIMESTAMP(timezone=True),
        postgresql_using="created_at AT TIME ZONE 'UTC'"
    )

    # refresh_tokens
    op.alter_column("refresh_tokens", "expires_at",
        type_=sa.TIMESTAMP(timezone=True),
        postgresql_using="expires_at AT TIME ZONE 'UTC'"
    )
    op.alter_column("refresh_tokens", "created_at",
        type_=sa.TIMESTAMP(timezone=True),
        postgresql_using="created_at AT TIME ZONE 'UTC'"
    )

    # uploads
    op.alter_column("uploads", "created_at",
        type_=sa.TIMESTAMP(timezone=True),
        postgresql_using="created_at AT TIME ZONE 'UTC'"
    )

    # predictions
    op.alter_column("predictions", "created_at",
        type_=sa.TIMESTAMP(timezone=True),
        postgresql_using="created_at AT TIME ZONE 'UTC'"
    )
    op.alter_column("predictions", "updated_at",
        type_=sa.TIMESTAMP(timezone=True),
        postgresql_using="updated_at AT TIME ZONE 'UTC'"
    )

    # shares
    op.alter_column("shares", "expires_at",
        type_=sa.TIMESTAMP(timezone=True),
        postgresql_using="expires_at AT TIME ZONE 'UTC'"
    )
    op.alter_column("shares", "created_at",
        type_=sa.TIMESTAMP(timezone=True),
        postgresql_using="created_at AT TIME ZONE 'UTC'"
    )

    # webhooks
    op.alter_column("webhooks", "created_at",
        type_=sa.TIMESTAMP(timezone=True),
        postgresql_using="created_at AT TIME ZONE 'UTC'"
    )

    # webhook_deliveries
    op.alter_column("webhook_deliveries", "created_at",
        type_=sa.TIMESTAMP(timezone=True),
        postgresql_using="created_at AT TIME ZONE 'UTC'"
    )
    op.alter_column("webhook_deliveries", "delivered_at",
        type_=sa.TIMESTAMP(timezone=True),
        postgresql_using="delivered_at AT TIME ZONE 'UTC'"
    )

    # idempotency_keys
    op.alter_column("idempotency_keys", "created_at",
        type_=sa.TIMESTAMP(timezone=True),
        postgresql_using="created_at AT TIME ZONE 'UTC'"
    )



def downgrade() -> None:
    """Downgrade schema."""
    # users
    op.alter_column("users", "created_at",
        type_=sa.TIMESTAMP(timezone=False)
    )

    # refresh_tokens
    op.alter_column("refresh_tokens", "expires_at",
        type_=sa.TIMESTAMP(timezone=False)
    )
    op.alter_column("refresh_tokens", "created_at",
        type_=sa.TIMESTAMP(timezone=False)
    )

    # uploads
    op.alter_column("uploads", "created_at",
        type_=sa.TIMESTAMP(timezone=False)
    )

    # predictions
    op.alter_column("predictions", "created_at",
        type_=sa.TIMESTAMP(timezone=False)
    )
    op.alter_column("predictions", "updated_at",
        type_=sa.TIMESTAMP(timezone=False)
    )

    # shares
    op.alter_column("shares", "expires_at",
        type_=sa.TIMESTAMP(timezone=False)
    )
    op.alter_column("shares", "created_at",
        type_=sa.TIMESTAMP(timezone=False)
    )

    # webhooks
    op.alter_column("webhooks", "created_at",
        type_=sa.TIMESTAMP(timezone=False)
    )

    # webhook_deliveries
    op.alter_column("webhook_deliveries", "created_at",
        type_=sa.TIMESTAMP(timezone=False)
    )
    op.alter_column("webhook_deliveries", "delivered_at",
        type_=sa.TIMESTAMP(timezone=False)
    )

    # idempotency_keys
    op.alter_column("idempotency_keys", "created_at",
        type_=sa.TIMESTAMP(timezone=False)
    )