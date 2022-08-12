"""nonnull user properties

Revision ID: c64f1acfbb9b
Revises: 16c733b334bb
Create Date: 2022-08-11 21:30:13.243388

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c64f1acfbb9b'
down_revision = '16c733b334bb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('subscriber', existing_type=sa.Boolean,
                server_default='FALSE', nullable=False)
        batch_op.alter_column('vip', existing_type=sa.Boolean,
                server_default='FALSE', nullable=False)
        batch_op.alter_column('bot_admin', existing_type=sa.Boolean,
                server_default='FALSE', nullable=False)


def downgrade() -> None:
    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('subscriber', existing_type=sa.Boolean,
                server_default=None, nullable=True)
        batch_op.alter_column('vip', existing_type=sa.Boolean,
                server_default=None, nullable=True)
        batch_op.alter_column('bot_admin', existing_type=sa.Boolean,
                server_default=None, nullable=True)
