"""Add user safety and moderation system

Revision ID: 45ad82d7349b
Revises: dbaac808d228
Create Date: 2025-08-19 21:44:34.782776

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '45ad82d7349b'
down_revision = 'dbaac808d228'  # Skip the problematic migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types for safety system
    report_category_enum = postgresql.ENUM(
        'harassment', 'fake_profile', 'inappropriate_photos', 'inappropriate_content',
        'spam', 'scam', 'violence_threats', 'hate_speech', 'underage',
        'impersonation', 'safety_concern', 'other',
        name='reportcategory',
        create_type=False
    )
    report_category_enum.create(op.get_bind(), checkfirst=True)

    report_status_enum = postgresql.ENUM(
        'pending', 'in_review', 'resolved', 'dismissed', 'escalated',
        name='reportstatus',
        create_type=False
    )
    report_status_enum.create(op.get_bind(), checkfirst=True)

    safety_status_enum = postgresql.ENUM(
        'clear', 'active', 'flagged', 'restricted', 'suspended', 'banned', 'under_review',
        name='safetystatus',
        create_type=False
    )
    safety_status_enum.create(op.get_bind(), checkfirst=True)

    # Create user_reports table
    op.create_table('user_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('reporter_id', sa.Integer(), nullable=False),
        sa.Column('reported_user_id', sa.Integer(), nullable=False),
        sa.Column('category', report_category_enum, nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('evidence_urls', sa.Text(), nullable=True),
        sa.Column('status', report_status_enum, server_default='pending', nullable=True),
        sa.Column('admin_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['reporter_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['reported_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for user_reports
    op.create_index('ix_user_reports_category', 'user_reports', ['category'])
    op.create_index('ix_user_reports_created_at', 'user_reports', ['created_at'])
    op.create_index('ix_user_reports_id', 'user_reports', ['id'])
    op.create_index('ix_user_reports_reporter_id', 'user_reports', ['reporter_id'])
    op.create_index('ix_user_reports_reported_user_id', 'user_reports', ['reported_user_id'])
    op.create_index('ix_user_reports_status', 'user_reports', ['status'])

    # Create blocked_users table
    op.create_table('blocked_users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('blocker_id', sa.Integer(), nullable=False),
        sa.Column('blocked_user_id', sa.Integer(), nullable=False),
        sa.Column('reason', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['blocked_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['blocker_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('blocker_id', 'blocked_user_id', name='unique_block_relationship')
    )
    
    # Create indexes for blocked_users
    op.create_index('ix_blocked_users_blocked_user_id', 'blocked_users', ['blocked_user_id'])
    op.create_index('ix_blocked_users_blocker_id', 'blocked_users', ['blocker_id'])
    op.create_index('ix_blocked_users_created_at', 'blocked_users', ['created_at'])
    op.create_index('ix_blocked_users_id', 'blocked_users', ['id'])

    # Create user_safety_profiles table
    op.create_table('user_safety_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('safety_status', safety_status_enum, server_default='active', nullable=True),
        sa.Column('restriction_reason', sa.Text(), nullable=True),
        sa.Column('restriction_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('restriction_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_reports', sa.Integer(), server_default='0', nullable=True),
        sa.Column('last_report_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('safety_score', sa.Integer(), server_default='100', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='unique_user_safety_profile')
    )
    
    # Create indexes for user_safety_profiles
    op.create_index('ix_user_safety_profiles_id', 'user_safety_profiles', ['id'])
    op.create_index('ix_user_safety_profiles_safety_status', 'user_safety_profiles', ['safety_status'])
    op.create_index('ix_user_safety_profiles_total_reports', 'user_safety_profiles', ['total_reports'])
    op.create_index('ix_user_safety_profiles_user_id', 'user_safety_profiles', ['user_id'])

    # Create moderation_actions table
    op.create_table('moderation_actions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('target_user_id', sa.Integer(), nullable=False),
        sa.Column('moderator_id', sa.Integer(), nullable=False),
        sa.Column('action_type', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('related_report_id', sa.Integer(), nullable=True),
        sa.Column('duration_hours', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.ForeignKeyConstraint(['moderator_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['related_report_id'], ['user_reports.id'], ),
        sa.ForeignKeyConstraint(['target_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for moderation_actions
    op.create_index('ix_moderation_actions_action_type', 'moderation_actions', ['action_type'])
    op.create_index('ix_moderation_actions_created_at', 'moderation_actions', ['created_at'])
    op.create_index('ix_moderation_actions_id', 'moderation_actions', ['id'])
    op.create_index('ix_moderation_actions_is_active', 'moderation_actions', ['is_active'])
    op.create_index('ix_moderation_actions_moderator_id', 'moderation_actions', ['moderator_id'])
    op.create_index('ix_moderation_actions_target_user_id', 'moderation_actions', ['target_user_id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('moderation_actions')
    op.drop_table('user_safety_profiles')
    op.drop_table('blocked_users')
    op.drop_table('user_reports')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS safetystatus')
    op.execute('DROP TYPE IF EXISTS reportstatus') 
    op.execute('DROP TYPE IF EXISTS reportcategory')

