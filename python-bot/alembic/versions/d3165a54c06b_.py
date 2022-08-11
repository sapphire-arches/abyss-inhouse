"""empty message

Revision ID: d3165a54c06b
Revises: b89b11048344
Create Date: 2022-08-11 02:42:29.752926

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd3165a54c06b'
down_revision = 'b89b11048344'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('discord_username', sa.String))


def downgrade() -> None:
    op.drop_column('users', 'discord_username')
