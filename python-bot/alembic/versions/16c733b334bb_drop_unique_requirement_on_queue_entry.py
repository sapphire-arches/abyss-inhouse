"""drop unique requirement on queue entry

Revision ID: 16c733b334bb
Revises: 34346db5fa3b
Create Date: 2022-08-11 19:14:55.582600

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '16c733b334bb'
down_revision = '34346db5fa3b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint('queue_user_id_key', 'queue', type_='unique')
    op.add_column('queue', sa.Column(
        'serviced',
        sa.Boolean,
        nullable=False,
        server_default='FALSE',
    ))


def downgrade() -> None:
    op.create_unique_constraint('queue_user_id_key', 'queue', ['user_id'])
    op.drop_column('queue', 'serviced')
