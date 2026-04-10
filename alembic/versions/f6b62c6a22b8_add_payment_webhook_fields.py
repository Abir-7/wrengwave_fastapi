"""add payment webhook fields

Revision ID: f6b62c6a22b8
Revises: e1954a548278
Create Date: 2026-04-10 09:12:45.505501

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6b62c6a22b8'
down_revision: Union[str, Sequence[str], None] = 'e1954a548278'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.execute("ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'failed'")
    op.execute("ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'partially_refunded'")

    op.add_column('payments', sa.Column('amount_refunded', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('payments', sa.Column('refund_reason', sa.String(), nullable=True))
    op.add_column('payments', sa.Column('failure_message', sa.String(), nullable=True))
    op.add_column('payments', sa.Column('failure_code', sa.String(), nullable=True))
    op.add_column('payments', sa.Column('transfer_id', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('payments', 'transfer_id')
    op.drop_column('payments', 'failure_code')
    op.drop_column('payments', 'failure_message')
    op.drop_column('payments', 'refund_reason')
    op.drop_column('payments', 'amount_refunded')