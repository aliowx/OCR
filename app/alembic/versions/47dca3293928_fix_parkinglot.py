"""fix_parkinglot

Revision ID: 47dca3293928
Revises: 5431213bf91b
Create Date: 2024-06-15 12:10:21.999100

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '47dca3293928'
down_revision = '5431213bf91b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('parkinglot', 'name_parking', new_column_name='name_parkinglot')


def downgrade() -> None:
    op.alter_column('parkinglot', 'name_parkinglot', new_column_name='name_parking')
