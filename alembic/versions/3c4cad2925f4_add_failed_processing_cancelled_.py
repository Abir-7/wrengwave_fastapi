"""add_failed_processing_cancelled_disputed_to_payment_status

Revision ID: 3c4cad2925f4
Revises: c308eea42fa8
Create Date: 2026-04-07 11:13:32.166287

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c4cad2925f4'
down_revision: Union[str, Sequence[str], None] = 'c308eea42fa8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # PostgreSQL requires ALTER TYPE to add new enum values
    # Each value must be added individually
    op.execute("ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'failed'")
    op.execute("ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'processing'")
    op.execute("ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'cancelled'")
    op.execute("ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'disputed'")


def downgrade() -> None:
    # PostgreSQL does NOT support removing enum values directly.
    # To roll back you must recreate the type from scratch.
    op.execute("""
        ALTER TABLE payments
            ALTER COLUMN status TYPE VARCHAR
            USING status::VARCHAR
    """)

    op.execute("DROP TYPE payment_status")

    op.execute("""
        CREATE TYPE payment_status AS ENUM (
            'paid', 'unpaid', 'refunded', 'hold'
        )
    """)

    op.execute("""
        ALTER TABLE payments
            ALTER COLUMN status TYPE payment_status
            USING status::payment_status
    """)
