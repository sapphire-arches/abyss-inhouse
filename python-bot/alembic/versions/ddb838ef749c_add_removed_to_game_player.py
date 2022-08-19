"""add removed to game_player

Revision ID: ddb838ef749c
Revises: 72d57c896a12
Create Date: 2022-08-18 23:26:14.739656

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ddb838ef749c'
down_revision = '72d57c896a12'
branch_labels = None
depends_on = None



def upgrade() -> None:
    op.add_column('game_player',
        sa.Column('removed', sa.Boolean(), server_default='FALSE', nullable=False)
    )


def downgrade() -> None:
    op.drop_column('game_player', 'removed')
