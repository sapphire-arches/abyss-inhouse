"""add game tracking

Revision ID: 5abe92eb70be
Revises: c64f1acfbb9b
Create Date: 2022-08-18 22:27:59.674488

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5abe92eb70be'
down_revision = 'c64f1acfbb9b'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('game',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('game_player',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('game_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['game_id'], ['game.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('game_player')
    op.drop_table('game')
