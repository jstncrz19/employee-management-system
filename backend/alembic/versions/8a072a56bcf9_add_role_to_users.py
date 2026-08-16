"""add role to users

Revision ID: 8a072a56bcf9
Revises: bfcc04027c65
Create Date: 2026-08-16 10:54:29.407133

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8a072a56bcf9'
down_revision: Union[str, Sequence[str], None] = 'bfcc04027c65'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'users',
        sa.Column(
            'role',
            sa.String(length=20),
            nullable=False,
            server_default='employee'
        )
    )

    op.alter_column(
        'users',
        'role',
        server_default=None
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'role')