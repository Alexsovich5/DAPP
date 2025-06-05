"""Add frontend compatibility fields to users table

Revision ID: 8748f7fcc78f
Revises: e28ff18be0f1
Create Date: 2025-05-30 15:49:02.745279

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8748f7fcc78f'
down_revision = 'e28ff18be0f1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add only user fields for frontend compatibility
    op.add_column('users', sa.Column('first_name', sa.String(), nullable=True))
    op.add_column('users', sa.Column('last_name', sa.String(), nullable=True))
    op.add_column('users', sa.Column('date_of_birth', sa.String(), nullable=True))
    op.add_column('users', sa.Column('gender', sa.String(), nullable=True))
    op.add_column('users', sa.Column('bio', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('location', sa.String(), nullable=True))
    op.add_column('users', sa.Column('profile_picture', sa.String(), nullable=True))
    op.add_column('users', sa.Column('interests', sa.JSON(), nullable=True))
    op.add_column('users', sa.Column('dietary_preferences', sa.JSON(), nullable=True))
    op.add_column('users', sa.Column('is_profile_complete', sa.Boolean(), nullable=True, default=False))


def downgrade() -> None:
    # Remove user fields added for frontend compatibility
    op.drop_column('users', 'is_profile_complete')
    op.drop_column('users', 'dietary_preferences')
    op.drop_column('users', 'interests')
    op.drop_column('users', 'profile_picture')
    op.drop_column('users', 'location')
    op.drop_column('users', 'bio')
    op.drop_column('users', 'gender')
    op.drop_column('users', 'date_of_birth')
    op.drop_column('users', 'last_name')
    op.drop_column('users', 'first_name')

