"""add role column to user

Revision ID: 9777d118ee9f
Revises: fea7603c1552
Create Date: 2026-03-07 10:09:18.718032

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9777d118ee9f'
down_revision: Union[str, Sequence[str], None] = 'fea7603c1552'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1️⃣ create enum type first
    user_role = postgresql.ENUM('admin', 'customer', 'mechanic', name='user_role')
    user_role.create(op.get_bind(), checkfirst=True)

    # 2️⃣ add column using this enum
    op.add_column(
        'users',
        sa.Column('role', user_role, nullable=False, server_default='customer')
    )


def downgrade() -> None:
    """Downgrade schema."""
    # 1️⃣ drop column first
    op.drop_column('users', 'role')
    # 2️⃣ drop enum type
    user_role = postgresql.ENUM('admin', 'customer', 'mechanic', name='user_role')
    user_role.drop(op.get_bind(), checkfirst=True)