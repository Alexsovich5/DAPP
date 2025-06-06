"""Merge migration heads

Revision ID: a71565ed9c0c
Revises: 8748f7fcc78f, 9a5c2d1e8f3b
Create Date: 2025-06-06 12:49:00.609191

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a71565ed9c0c'
down_revision = ('8748f7fcc78f', '9a5c2d1e8f3b')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

