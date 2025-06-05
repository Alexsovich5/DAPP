"""Add soul before skin features

Revision ID: 9a5c2d1e8f3b
Revises: e28ff18be0f1
Create Date: 2025-01-05 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9a5c2d1e8f3b'
down_revision = 'e28ff18be0f1'
branch_labels = None
depends_on = None


def upgrade():
    # Add soul before skin fields to users table
    op.add_column('users', sa.Column('emotional_onboarding_completed', sa.Boolean(), nullable=True, default=False))
    op.add_column('users', sa.Column('soul_profile_visibility', sa.String(), nullable=True, default='hidden'))
    op.add_column('users', sa.Column('emotional_depth_score', sa.DECIMAL(precision=5, scale=2), nullable=True))
    op.add_column('users', sa.Column('core_values', sa.JSON(), nullable=True))
    op.add_column('users', sa.Column('personality_traits', sa.JSON(), nullable=True))
    op.add_column('users', sa.Column('communication_style', sa.JSON(), nullable=True))
    op.add_column('users', sa.Column('emotional_responses', sa.JSON(), nullable=True))

    # Create soul_connections table
    op.create_table('soul_connections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user1_id', sa.Integer(), nullable=False),
        sa.Column('user2_id', sa.Integer(), nullable=False),
        sa.Column('connection_stage', sa.String(), nullable=True, default='soul_discovery'),
        sa.Column('compatibility_score', sa.DECIMAL(precision=5, scale=2), nullable=True),
        sa.Column('compatibility_breakdown', sa.JSON(), nullable=True),
        sa.Column('reveal_day', sa.Integer(), nullable=True, default=1),
        sa.Column('mutual_reveal_consent', sa.Boolean(), nullable=True, default=False),
        sa.Column('first_dinner_completed', sa.Boolean(), nullable=True, default=False),
        sa.Column('initiated_by', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=True, default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['initiated_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user1_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user2_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_soul_connections_id'), 'soul_connections', ['id'], unique=False)

    # Create daily_revelations table
    op.create_table('daily_revelations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('connection_id', sa.Integer(), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=False),
        sa.Column('day_number', sa.Integer(), nullable=False),
        sa.Column('revelation_type', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['connection_id'], ['soul_connections.id'], ),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_daily_revelations_id'), 'daily_revelations', ['id'], unique=False)

    # Create messages table
    op.create_table('messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('connection_id', sa.Integer(), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=False),
        sa.Column('message_text', sa.Text(), nullable=False),
        sa.Column('message_type', sa.String(), nullable=True, default='text'),
        sa.Column('is_read', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['connection_id'], ['soul_connections.id'], ),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_messages_id'), 'messages', ['id'], unique=False)


def downgrade():
    # Drop new tables
    op.drop_index(op.f('ix_messages_id'), table_name='messages')
    op.drop_table('messages')
    op.drop_index(op.f('ix_daily_revelations_id'), table_name='daily_revelations')
    op.drop_table('daily_revelations')
    op.drop_index(op.f('ix_soul_connections_id'), table_name='soul_connections')
    op.drop_table('soul_connections')
    
    # Remove soul before skin fields from users table
    op.drop_column('users', 'emotional_responses')
    op.drop_column('users', 'communication_style')
    op.drop_column('users', 'personality_traits')
    op.drop_column('users', 'core_values')
    op.drop_column('users', 'emotional_depth_score')
    op.drop_column('users', 'soul_profile_visibility')
    op.drop_column('users', 'emotional_onboarding_completed')