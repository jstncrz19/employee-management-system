"""add leave integrity constraints

Revision ID: d4e1b7f9c3a2
Revises: 08e85b47cb1c
Create Date: 2026-09-06
"""

from alembic import op


revision = "d4e1b7f9c3a2"
down_revision = "08e85b47cb1c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_leaves_valid_date_range",
        "leaves",
        "end_date >= start_date",
    )
    op.create_check_constraint(
        "ck_leave_balances_total_days_nonnegative",
        "leave_balances",
        "total_days >= 0",
    )
    op.create_check_constraint(
        "ck_leave_balances_used_days_valid",
        "leave_balances",
        "used_days >= 0 AND used_days <= total_days",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_leave_balances_used_days_valid",
        "leave_balances",
        type_="check",
    )
    op.drop_constraint(
        "ck_leave_balances_total_days_nonnegative",
        "leave_balances",
        type_="check",
    )
    op.drop_constraint(
        "ck_leaves_valid_date_range",
        "leaves",
        type_="check",
    )
