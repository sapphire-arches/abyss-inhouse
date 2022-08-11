"""use wider type for snowflakes


Revision ID: f7b78829141e
Revises: d3165a54c06b
Create Date: 2022-08-11 02:53:49.632330

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f7b78829141e'
down_revision = 'd3165a54c06b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('users', 'discord_id',
        type_=sa.BigInteger
    )


def downgrade() -> None:
    op.alter_column('users', 'discord_id',
        type_=sa.Integer
    )
