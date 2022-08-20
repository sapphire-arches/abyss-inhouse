"""add_queue_readyness

Revision ID: 839e8bded915
Revises: 45daf9159d15
Create Date: 2022-08-20 12:45:01.041757

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '839e8bded915'
down_revision = '45daf9159d15'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('queue', sa.Column('ready', sa.Boolean(), nullable=False, server_default='True'))


def downgrade() -> None:
    op.drop_column('queue', sa.Column('ready', sa.Boolean(), nullable=False))
