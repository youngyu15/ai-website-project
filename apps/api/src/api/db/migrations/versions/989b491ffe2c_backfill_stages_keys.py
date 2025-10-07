"""backfill stages keys

Revision ID: 989b491ffe2c
Revises: 6cf0308f7f36
Create Date: 2025-10-02 19:18:27.310191

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '989b491ffe2c'
down_revision: Union[str, Sequence[str], None] = '6cf0308f7f36'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_FACE = "jsonb_build_object('name','face_detection','status','pending','result',NULL)"
DEFAULT_CLF  = "jsonb_build_object('name','classification','status','pending','result',NULL)"

def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        f"""
        UPDATE predictions
        SET stages =
          jsonb_set(
            jsonb_set(
              COALESCE(stages, '{{}}'::jsonb),
              '{{face_detection}}',
              COALESCE(stages->'face_detection', {DEFAULT_FACE})
            ),
            '{{classification}}',
            COALESCE(stages->'classification', {DEFAULT_CLF})
          )
        WHERE stages IS NULL
           OR NOT (stages ? 'face_detection' AND stages ? 'classification');
        """
    )

    op.alter_column(
        "predictions",
        "stages",
        server_default=sa.text("'{}'::jsonb"),
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
    )
    op.alter_column(
        "predictions",
        "stages",
        nullable=False,
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        """
        UPDATE predictions
        SET stages = '{}'::jsonb
        WHERE (stages ? 'face_detection') AND (stages ? 'classification')
          AND jsonb_typeof(stages->'face_detection') = 'object'
          AND jsonb_typeof(stages->'classification') = 'object';
        """
    )