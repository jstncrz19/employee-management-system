"""change employee number to integer

Revision ID: bfcc04027c65
Revises: fc175a76e68e
Create Date: 2026-08-15 21:10:30.844957

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "bfcc04027c65"
down_revision: Union[str, Sequence[str], None] = "fc175a76e68e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Convert existing employee numbers from EMP-001 format
    # to their numeric equivalent before changing the column type.
    op.execute("""
        UPDATE employees
        SET employee_number = regexp_replace(employee_number, '[^0-9]', '', 'g')
    """)

    # Change employee_number from VARCHAR to INTEGER.
    op.alter_column(
        "employees",
        "employee_number",
        existing_type=sa.VARCHAR(length=50),
        type_=sa.Integer(),
        existing_nullable=False,
        postgresql_using="employee_number::integer",
    )


def downgrade() -> None:
    """Downgrade schema."""

    # Convert INTEGER back to VARCHAR.
    op.alter_column(
        "employees",
        "employee_number",
        existing_type=sa.Integer(),
        type_=sa.VARCHAR(length=50),
        existing_nullable=False,
    )