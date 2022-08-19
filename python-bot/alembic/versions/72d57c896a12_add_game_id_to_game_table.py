"""add game_id to game table

Revision ID: 72d57c896a12
Revises: 5abe92eb70be
Create Date: 2022-08-18 23:01:20.693557

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '72d57c896a12'
down_revision = '5abe92eb70be'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('game', sa.Column('dota2_match_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('game', 'dota2_match_id')
