"""init

Revision ID: b89b11048344
Revises: 
Create Date: 2022-08-10 21:06:31.990665

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b89b11048344'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('discord_id', sa.Integer),
        sa.Column('subscriber', sa.Boolean),
        sa.Column('vip', sa.Boolean),
        sa.Column('bot_admin', sa.Boolean),
    )

    op.create_table(
        'queue',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, unique=True),
        sa.Column('enroll_time', sa.DateTime, unique=True),
        sa.ForeignKeyConstraint(('user_id',), ['users.id']),
    )


def downgrade() -> None:
    op.drop_table('queue')
    op.drop_table('users')
