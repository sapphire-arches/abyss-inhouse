"""add_role_id_tracking

Revision ID: b817ee67379c
Revises: ddb838ef749c
Create Date: 2022-08-19 21:30:43.735900

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b817ee67379c'
down_revision = 'ddb838ef749c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('game',
        sa.Column('role_id', sa.BigInteger())
    )


def downgrade() -> None:
    op.drop_column('game', 'role_id')
