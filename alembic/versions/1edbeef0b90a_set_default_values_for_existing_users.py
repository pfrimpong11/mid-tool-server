"""set_default_values_for_existing_users

Revision ID: 1edbeef0b90a
Revises: 0aa8e7b50a6d
Create Date: 2025-10-03 23:22:54.592677

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1edbeef0b90a'
down_revision: Union[str, None] = '0aa8e7b50a6d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Set default values for existing users
    op.execute("""
        UPDATE users 
        SET 
            dark_mode = false,
            interface_scale = 'normal',
            default_analysis_model = 'advanced',
            email_notifications = true,
            push_notifications = true,
            analysis_notifications = true,
            report_notifications = true,
            data_retention_period = '1year',
            anonymous_analytics = true,
            data_sharing = false
        WHERE 
            dark_mode IS NULL OR
            interface_scale IS NULL OR
            default_analysis_model IS NULL OR
            email_notifications IS NULL OR
            push_notifications IS NULL OR
            analysis_notifications IS NULL OR
            report_notifications IS NULL OR
            data_retention_period IS NULL OR
            anonymous_analytics IS NULL OR
            data_sharing IS NULL
    """)


def downgrade() -> None:
    # No need to revert default values as they are sensible defaults
    pass