"""add_channel_id_game_tracking

Revision ID: 45daf9159d15
Revises: b817ee67379c
Create Date: 2022-08-19 22:43:48.587869

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '45daf9159d15'
down_revision = 'b817ee67379c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('game',
        sa.Column('channel_id', sa.BigInteger())
    )


def downgrade() -> None:
    op.drop_column('game', 'channel_id')
