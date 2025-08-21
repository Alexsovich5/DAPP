"""Add enhanced performance indexes for Sprint 2.3

Revision ID: enhanced_perf_idx
Revises: add_db_indexes
Create Date: 2025-08-20 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'enhanced_perf_idx'
down_revision = 'add_db_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add enhanced performance indexes for Sprint 2.3 optimization"""
    
    # Photo reveal system performance indexes
    op.execute("CREATE INDEX IF NOT EXISTS ix_photo_reveal_timelines_connection_id ON photo_reveal_timelines (connection_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_photo_reveal_timelines_stage ON photo_reveal_timelines (current_stage)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_photo_reveal_timelines_eligible ON photo_reveal_timelines (photo_reveal_eligible_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_photo_reveal_timelines_auto_reveal ON photo_reveal_timelines (auto_reveal_enabled, photos_revealed)")
    
    # Photo reveal requests performance indexes
    op.execute("CREATE INDEX IF NOT EXISTS ix_photo_reveal_requests_timeline_id ON photo_reveal_requests (timeline_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_photo_reveal_requests_requester_id ON photo_reveal_requests (requester_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_photo_reveal_requests_owner_id ON photo_reveal_requests (photo_owner_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_photo_reveal_requests_status ON photo_reveal_requests (status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_photo_reveal_requests_expires_at ON photo_reveal_requests (expires_at)")
    
    # Composite indexes for photo reveal requests
    op.execute("CREATE INDEX IF NOT EXISTS ix_photo_requests_timeline_status ON photo_reveal_requests (timeline_id, status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_photo_requests_requester_status ON photo_reveal_requests (requester_id, status)")
    
    # Photo reveal permissions performance indexes
    op.execute("CREATE INDEX IF NOT EXISTS ix_photo_permissions_photo_id ON photo_reveal_permissions (photo_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_photo_permissions_connection_id ON photo_reveal_permissions (connection_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_photo_permissions_viewer_id ON photo_reveal_permissions (viewer_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_photo_permissions_owner_id ON photo_reveal_permissions (photo_owner_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_photo_permissions_active ON photo_reveal_permissions (is_active)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_photo_permissions_expires_at ON photo_reveal_permissions (expires_at)")
    
    # Composite indexes for photo permissions
    op.execute("CREATE INDEX IF NOT EXISTS ix_photo_permissions_viewer_active ON photo_reveal_permissions (viewer_id, is_active)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_photo_permissions_connection_active ON photo_reveal_permissions (connection_id, is_active)")
    
    # User photos performance indexes
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_photos_user_id ON user_photos (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_photos_uuid ON user_photos (photo_uuid)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_photos_primary ON user_photos (is_profile_primary)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_photos_moderation_status ON user_photos (moderation_status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_photos_processing_complete ON user_photos (processing_complete)")
    
    # Composite index for user photos
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_photos_user_primary ON user_photos (user_id, is_profile_primary)")
    
    # Analytics and tracking performance indexes
    op.execute("CREATE INDEX IF NOT EXISTS ix_soul_analytics_user_id ON soul_connection_analytics (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_soul_analytics_connection_id ON soul_connection_analytics (connection_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_soul_analytics_created_at ON soul_connection_analytics (created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_soul_analytics_event_type ON soul_connection_analytics (event_type)")
    
    # User safety and moderation indexes
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_reports_reporter_id ON user_reports (reporter_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_reports_reported_id ON user_reports (reported_user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_reports_status ON user_reports (status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_reports_created_at ON user_reports (created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_reports_severity ON user_reports (severity)")
    
    # Composite indexes for safety reports
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_reports_reported_status ON user_reports (reported_user_id, status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_reports_status_severity ON user_reports (status, severity)")
    
    # Discovery and matching optimization indexes
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_age_range ON users (date_of_birth)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_last_active ON users (last_active_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_verification_status ON users (is_verified)")
    
    # Enhanced composite indexes for discovery
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_discovery_active ON users (is_active, is_verified, last_active_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_location_active_age ON users (location, is_active, date_of_birth)")
    
    # Soul connections enhanced indexes
    op.execute("CREATE INDEX IF NOT EXISTS ix_soul_connections_created_at ON soul_connections (created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_soul_connections_updated_at ON soul_connections (updated_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_soul_connections_last_activity ON soul_connections (last_activity_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_soul_connections_reveal_day ON soul_connections (reveal_day)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_soul_connections_compatibility ON soul_connections (compatibility_score)")
    
    # Composite indexes for soul connections timeline
    op.execute("CREATE INDEX IF NOT EXISTS ix_soul_connections_users_active ON soul_connections (user1_id, user2_id, status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_soul_connections_stage_activity ON soul_connections (connection_stage, last_activity_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_soul_connections_reveal_consent ON soul_connections (reveal_day, mutual_reveal_consent)")
    
    # Message optimization for real-time features
    op.execute("CREATE INDEX IF NOT EXISTS ix_messages_type ON messages (message_type)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_messages_connection_type_created ON messages (connection_id, message_type, created_at)")
    
    # Revelation system enhanced indexes
    op.execute("CREATE INDEX IF NOT EXISTS ix_revelations_type ON daily_revelations (revelation_type)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_revelations_is_read ON daily_revelations (is_read)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_revelations_connection_type_day ON daily_revelations (connection_id, revelation_type, day_number)")
    
    # Photo reveal events tracking
    op.execute("CREATE INDEX IF NOT EXISTS ix_photo_events_timeline_id ON photo_reveal_events (timeline_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_photo_events_connection_id ON photo_reveal_events (connection_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_photo_events_user_id ON photo_reveal_events (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_photo_events_type ON photo_reveal_events (event_type)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_photo_events_created_at ON photo_reveal_events (created_at)")
    
    # Composite index for photo events timeline
    op.execute("CREATE INDEX IF NOT EXISTS ix_photo_events_timeline_type_created ON photo_reveal_events (timeline_id, event_type, created_at)")
    
    # Profile and matching optimization
    op.execute("CREATE INDEX IF NOT EXISTS ix_profiles_user_id ON profiles (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_profiles_created_at ON profiles (created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_profiles_updated_at ON profiles (updated_at)")
    
    print("✓ Enhanced performance indexes created successfully")


def downgrade() -> None:
    """Remove enhanced performance indexes"""
    
    # Photo reveal system indexes
    op.drop_index('ix_photo_reveal_timelines_connection_id')
    op.drop_index('ix_photo_reveal_timelines_stage')
    op.drop_index('ix_photo_reveal_timelines_eligible')
    op.drop_index('ix_photo_reveal_timelines_auto_reveal')
    
    # Photo reveal requests indexes
    op.drop_index('ix_photo_reveal_requests_timeline_id')
    op.drop_index('ix_photo_reveal_requests_requester_id')
    op.drop_index('ix_photo_reveal_requests_owner_id')
    op.drop_index('ix_photo_reveal_requests_status')
    op.drop_index('ix_photo_reveal_requests_expires_at')
    op.drop_index('ix_photo_requests_timeline_status')
    op.drop_index('ix_photo_requests_requester_status')
    
    # Photo reveal permissions indexes
    op.drop_index('ix_photo_permissions_photo_id')
    op.drop_index('ix_photo_permissions_connection_id')
    op.drop_index('ix_photo_permissions_viewer_id')
    op.drop_index('ix_photo_permissions_owner_id')
    op.drop_index('ix_photo_permissions_active')
    op.drop_index('ix_photo_permissions_expires_at')
    op.drop_index('ix_photo_permissions_viewer_active')
    op.drop_index('ix_photo_permissions_connection_active')
    
    # User photos indexes
    op.drop_index('ix_user_photos_user_id')
    op.drop_index('ix_user_photos_uuid')
    op.drop_index('ix_user_photos_primary')
    op.drop_index('ix_user_photos_moderation_status')
    op.drop_index('ix_user_photos_processing_complete')
    op.drop_index('ix_user_photos_user_primary')
    
    # Analytics indexes
    op.drop_index('ix_soul_analytics_user_id')
    op.drop_index('ix_soul_analytics_connection_id')
    op.drop_index('ix_soul_analytics_created_at')
    op.drop_index('ix_soul_analytics_event_type')
    
    # Safety and moderation indexes
    op.drop_index('ix_user_reports_reporter_id')
    op.drop_index('ix_user_reports_reported_id')
    op.drop_index('ix_user_reports_status')
    op.drop_index('ix_user_reports_created_at')
    op.drop_index('ix_user_reports_severity')
    op.drop_index('ix_user_reports_reported_status')
    op.drop_index('ix_user_reports_status_severity')
    
    # Discovery optimization indexes
    op.drop_index('ix_users_age_range')
    op.drop_index('ix_users_last_active')
    op.drop_index('ix_users_verification_status')
    op.drop_index('ix_users_discovery_active')
    op.drop_index('ix_users_location_active_age')
    
    # Enhanced soul connections indexes
    op.drop_index('ix_soul_connections_created_at')
    op.drop_index('ix_soul_connections_updated_at')
    op.drop_index('ix_soul_connections_last_activity')
    op.drop_index('ix_soul_connections_reveal_day')
    op.drop_index('ix_soul_connections_compatibility')
    op.drop_index('ix_soul_connections_users_active')
    op.drop_index('ix_soul_connections_stage_activity')
    op.drop_index('ix_soul_connections_reveal_consent')
    
    # Message optimization indexes
    op.drop_index('ix_messages_type')
    op.drop_index('ix_messages_connection_type_created')
    
    # Revelation enhanced indexes
    op.drop_index('ix_revelations_type')
    op.drop_index('ix_revelations_is_read')
    op.drop_index('ix_revelations_connection_type_day')
    
    # Photo reveal events indexes
    op.drop_index('ix_photo_events_timeline_id')
    op.drop_index('ix_photo_events_connection_id')
    op.drop_index('ix_photo_events_user_id')
    op.drop_index('ix_photo_events_type')
    op.drop_index('ix_photo_events_created_at')
    op.drop_index('ix_photo_events_timeline_type_created')
    
    # Profile indexes
    op.drop_index('ix_profiles_user_id')
    op.drop_index('ix_profiles_created_at')
    op.drop_index('ix_profiles_updated_at')
    
    print("✓ Enhanced performance indexes removed")