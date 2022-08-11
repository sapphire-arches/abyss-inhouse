"""unique discord_id

Revision ID: 34346db5fa3b
Revises: f7b78829141e
Create Date: 2022-08-11 03:10:26.845049

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '34346db5fa3b'
down_revision = 'f7b78829141e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint('uq_users_discord_id', 'users', ['discord_id'])


def downgrade() -> None:
    op.drop_constraint('uq_users_discord_id', 'users', type_='unique')
