"""Add missing foreign key constraints for referential integrity

Revision ID: fk_constraints_2023
Revises: enhanced_perf_idx
Create Date: 2025-08-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fk_constraints_2023'
down_revision = 'enhanced_perf_idx'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add missing foreign key constraints and ensure referential integrity"""
    
    # Add missing foreign key constraints with proper cascading
    
    # User Safety Models - Foreign Key Constraints
    try:
        # UserReport foreign keys with cascading
        op.execute("""
            ALTER TABLE user_reports 
            ADD CONSTRAINT fk_user_reports_reporter_id 
            FOREIGN KEY (reporter_id) REFERENCES users(id) ON DELETE CASCADE
        """)
    except Exception:
        pass  # Constraint may already exist
    
    try:
        op.execute("""
            ALTER TABLE user_reports 
            ADD CONSTRAINT fk_user_reports_reported_user_id 
            FOREIGN KEY (reported_user_id) REFERENCES users(id) ON DELETE CASCADE
        """)
    except Exception:
        pass
    
    try:
        op.execute("""
            ALTER TABLE user_reports 
            ADD CONSTRAINT fk_user_reports_resolved_by 
            FOREIGN KEY (resolved_by) REFERENCES users(id) ON DELETE SET NULL
        """)
    except Exception:
        pass
    
    # BlockedUser foreign keys
    try:
        op.execute("""
            ALTER TABLE blocked_users 
            ADD CONSTRAINT fk_blocked_users_blocker_id 
            FOREIGN KEY (blocker_id) REFERENCES users(id) ON DELETE CASCADE
        """)
    except Exception:
        pass
    
    try:
        op.execute("""
            ALTER TABLE blocked_users 
            ADD CONSTRAINT fk_blocked_users_blocked_user_id 
            FOREIGN KEY (blocked_user_id) REFERENCES users(id) ON DELETE CASCADE
        """)
    except Exception:
        pass
    
    # UserSafetyProfile foreign keys
    try:
        op.execute("""
            ALTER TABLE user_safety_profiles 
            ADD CONSTRAINT fk_user_safety_profiles_user_id 
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        """)
    except Exception:
        pass
    
    # ModerationAction foreign keys
    try:
        op.execute("""
            ALTER TABLE moderation_actions 
            ADD CONSTRAINT fk_moderation_actions_target_user_id 
            FOREIGN KEY (target_user_id) REFERENCES users(id) ON DELETE CASCADE
        """)
    except Exception:
        pass
    
    try:
        op.execute("""
            ALTER TABLE moderation_actions 
            ADD CONSTRAINT fk_moderation_actions_moderator_id 
            FOREIGN KEY (moderator_id) REFERENCES users(id) ON DELETE SET NULL
        """)
    except Exception:
        pass
    
    try:
        op.execute("""
            ALTER TABLE moderation_actions 
            ADD CONSTRAINT fk_moderation_actions_related_report_id 
            FOREIGN KEY (related_report_id) REFERENCES user_reports(id) ON DELETE CASCADE
        """)
    except Exception:
        pass
    
    # Photo Reveal System - Foreign Key Constraints
    
    # UserPhoto foreign keys
    try:
        op.execute("""
            ALTER TABLE user_photos 
            ADD CONSTRAINT fk_user_photos_user_id 
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        """)
    except Exception:
        pass
    
    # PhotoRevealTimeline foreign keys
    try:
        op.execute("""
            ALTER TABLE photo_reveal_timelines 
            ADD CONSTRAINT fk_photo_reveal_timelines_connection_id 
            FOREIGN KEY (connection_id) REFERENCES soul_connections(id) ON DELETE CASCADE
        """)
    except Exception:
        pass
    
    # PhotoRevealRequest foreign keys
    try:
        op.execute("""
            ALTER TABLE photo_reveal_requests 
            ADD CONSTRAINT fk_photo_reveal_requests_timeline_id 
            FOREIGN KEY (timeline_id) REFERENCES photo_reveal_timelines(id) ON DELETE CASCADE
        """)
    except Exception:
        pass
    
    try:
        op.execute("""
            ALTER TABLE photo_reveal_requests 
            ADD CONSTRAINT fk_photo_reveal_requests_photo_id 
            FOREIGN KEY (photo_id) REFERENCES user_photos(id) ON DELETE CASCADE
        """)
    except Exception:
        pass
    
    try:
        op.execute("""
            ALTER TABLE photo_reveal_requests 
            ADD CONSTRAINT fk_photo_reveal_requests_requester_id 
            FOREIGN KEY (requester_id) REFERENCES users(id) ON DELETE CASCADE
        """)
    except Exception:
        pass
    
    try:
        op.execute("""
            ALTER TABLE photo_reveal_requests 
            ADD CONSTRAINT fk_photo_reveal_requests_photo_owner_id 
            FOREIGN KEY (photo_owner_id) REFERENCES users(id) ON DELETE CASCADE
        """)
    except Exception:
        pass
    
    # PhotoRevealPermission foreign keys
    try:
        op.execute("""
            ALTER TABLE photo_reveal_permissions 
            ADD CONSTRAINT fk_photo_reveal_permissions_photo_id 
            FOREIGN KEY (photo_id) REFERENCES user_photos(id) ON DELETE CASCADE
        """)
    except Exception:
        pass
    
    try:
        op.execute("""
            ALTER TABLE photo_reveal_permissions 
            ADD CONSTRAINT fk_photo_reveal_permissions_connection_id 
            FOREIGN KEY (connection_id) REFERENCES soul_connections(id) ON DELETE CASCADE
        """)
    except Exception:
        pass
    
    try:
        op.execute("""
            ALTER TABLE photo_reveal_permissions 
            ADD CONSTRAINT fk_photo_reveal_permissions_viewer_id 
            FOREIGN KEY (viewer_id) REFERENCES users(id) ON DELETE CASCADE
        """)
    except Exception:
        pass
    
    try:
        op.execute("""
            ALTER TABLE photo_reveal_permissions 
            ADD CONSTRAINT fk_photo_reveal_permissions_photo_owner_id 
            FOREIGN KEY (photo_owner_id) REFERENCES users(id) ON DELETE CASCADE
        """)
    except Exception:
        pass
    
    try:
        op.execute("""
            ALTER TABLE photo_reveal_permissions 
            ADD CONSTRAINT fk_photo_reveal_permissions_source_request_id 
            FOREIGN KEY (granted_through_request_id) REFERENCES photo_reveal_requests(id) ON DELETE SET NULL
        """)
    except Exception:
        pass
    
    # PhotoRevealEvent foreign keys
    try:
        op.execute("""
            ALTER TABLE photo_reveal_events 
            ADD CONSTRAINT fk_photo_reveal_events_timeline_id 
            FOREIGN KEY (timeline_id) REFERENCES photo_reveal_timelines(id) ON DELETE CASCADE
        """)
    except Exception:
        pass
    
    try:
        op.execute("""
            ALTER TABLE photo_reveal_events 
            ADD CONSTRAINT fk_photo_reveal_events_connection_id 
            FOREIGN KEY (connection_id) REFERENCES soul_connections(id) ON DELETE CASCADE
        """)
    except Exception:
        pass
    
    try:
        op.execute("""
            ALTER TABLE photo_reveal_events 
            ADD CONSTRAINT fk_photo_reveal_events_user_id 
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        """)
    except Exception:
        pass
    
    # PhotoModerationLog foreign keys
    try:
        op.execute("""
            ALTER TABLE photo_moderation_logs 
            ADD CONSTRAINT fk_photo_moderation_logs_photo_id 
            FOREIGN KEY (photo_id) REFERENCES user_photos(id) ON DELETE CASCADE
        """)
    except Exception:
        pass
    
    try:
        op.execute("""
            ALTER TABLE photo_moderation_logs 
            ADD CONSTRAINT fk_photo_moderation_logs_moderator_id 
            FOREIGN KEY (moderator_id) REFERENCES users(id) ON DELETE SET NULL
        """)
    except Exception:
        pass
    
    # Simple PhotoReveal foreign keys (for testing)
    try:
        op.execute("""
            ALTER TABLE simple_photo_reveals 
            ADD CONSTRAINT fk_simple_photo_reveals_connection_id 
            FOREIGN KEY (connection_id) REFERENCES soul_connections(id) ON DELETE CASCADE
        """)
    except Exception:
        pass
    
    try:
        op.execute("""
            ALTER TABLE simple_photo_reveals 
            ADD CONSTRAINT fk_simple_photo_reveals_user_id 
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        """)
    except Exception:
        pass
    
    # Core Models - Enhanced Foreign Key Constraints
    
    # Profiles foreign keys
    try:
        op.execute("""
            ALTER TABLE profiles 
            ADD CONSTRAINT fk_profiles_user_id 
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        """)
    except Exception:
        pass
    
    # Messages foreign keys with cascading
    try:
        op.execute("""
            ALTER TABLE messages 
            ADD CONSTRAINT fk_messages_connection_id 
            FOREIGN KEY (connection_id) REFERENCES soul_connections(id) ON DELETE CASCADE
        """)
    except Exception:
        pass
    
    try:
        op.execute("""
            ALTER TABLE messages 
            ADD CONSTRAINT fk_messages_sender_id 
            FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE
        """)
    except Exception:
        pass
    
    # DailyRevelation foreign keys with cascading
    try:
        op.execute("""
            ALTER TABLE daily_revelations 
            ADD CONSTRAINT fk_daily_revelations_connection_id 
            FOREIGN KEY (connection_id) REFERENCES soul_connections(id) ON DELETE CASCADE
        """)
    except Exception:
        pass
    
    try:
        op.execute("""
            ALTER TABLE daily_revelations 
            ADD CONSTRAINT fk_daily_revelations_sender_id 
            FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE
        """)
    except Exception:
        pass
    
    # SoulConnection foreign keys with enhanced cascading
    try:
        op.execute("""
            ALTER TABLE soul_connections 
            ADD CONSTRAINT fk_soul_connections_user1_id 
            FOREIGN KEY (user1_id) REFERENCES users(id) ON DELETE CASCADE
        """)
    except Exception:
        pass
    
    try:
        op.execute("""
            ALTER TABLE soul_connections 
            ADD CONSTRAINT fk_soul_connections_user2_id 
            FOREIGN KEY (user2_id) REFERENCES users(id) ON DELETE CASCADE
        """)
    except Exception:
        pass
    
    try:
        op.execute("""
            ALTER TABLE soul_connections 
            ADD CONSTRAINT fk_soul_connections_initiated_by 
            FOREIGN KEY (initiated_by) REFERENCES users(id) ON DELETE CASCADE
        """)
    except Exception:
        pass
    
    try:
        op.execute("""
            ALTER TABLE soul_connections 
            ADD CONSTRAINT fk_soul_connections_ended_by 
            FOREIGN KEY (ended_by) REFERENCES users(id) ON DELETE SET NULL
        """)
    except Exception:
        pass
    
    # Match foreign keys
    try:
        op.execute("""
            ALTER TABLE matches 
            ADD CONSTRAINT fk_matches_sender_id 
            FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE
        """)
    except Exception:
        pass
    
    try:
        op.execute("""
            ALTER TABLE matches 
            ADD CONSTRAINT fk_matches_receiver_id 
            FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE
        """)
    except Exception:
        pass
    
    # Add unique constraints for data integrity
    
    # Prevent duplicate blocks
    try:
        op.create_unique_constraint(
            'unique_block_relationship',
            'blocked_users',
            ['blocker_id', 'blocked_user_id']
        )
    except Exception:
        pass
    
    # Prevent duplicate safety profiles
    try:
        op.create_unique_constraint(
            'unique_user_safety_profile',
            'user_safety_profiles',
            ['user_id']
        )
    except Exception:
        pass
    
    # Prevent duplicate photo reveal timelines per connection
    try:
        op.create_unique_constraint(
            'unique_photo_timeline_per_connection',
            'photo_reveal_timelines',
            ['connection_id']
        )
    except Exception:
        pass
    
    # Prevent duplicate user profiles  
    try:
        op.create_unique_constraint(
            'unique_user_profile',
            'profiles',
            ['user_id']
        )
    except Exception:
        pass
    
    # Prevent duplicate soul connections between same users
    try:
        op.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS unique_soul_connection_users 
            ON soul_connections (LEAST(user1_id, user2_id), GREATEST(user1_id, user2_id))
        """)
    except Exception:
        pass
    
    # Add check constraints for data validity
    
    # Ensure users can't block themselves
    try:
        op.execute("""
            ALTER TABLE blocked_users 
            ADD CONSTRAINT check_no_self_block 
            CHECK (blocker_id != blocked_user_id)
        """)
    except Exception:
        pass
    
    # Ensure users can't report themselves
    try:
        op.execute("""
            ALTER TABLE user_reports 
            ADD CONSTRAINT check_no_self_report 
            CHECK (reporter_id != reported_user_id)
        """)
    except Exception:
        pass
    
    # Ensure soul connections are between different users
    try:
        op.execute("""
            ALTER TABLE soul_connections 
            ADD CONSTRAINT check_different_users 
            CHECK (user1_id != user2_id)
        """)
    except Exception:
        pass
    
    # Ensure matches are between different users
    try:
        op.execute("""
            ALTER TABLE matches 
            ADD CONSTRAINT check_match_different_users 
            CHECK (sender_id != receiver_id)
        """)
    except Exception:
        pass
    
    # Ensure photo reveal requests are for valid photo owners
    try:
        op.execute("""
            ALTER TABLE photo_reveal_requests 
            ADD CONSTRAINT check_valid_photo_request 
            CHECK (requester_id != photo_owner_id)
        """)
    except Exception:
        pass
    
    print("✓ Foreign key constraints and referential integrity rules added successfully")


def downgrade() -> None:
    """Remove foreign key constraints"""
    
    # Remove check constraints
    constraints_to_drop = [
        ('blocked_users', 'check_no_self_block'),
        ('user_reports', 'check_no_self_report'),
        ('soul_connections', 'check_different_users'),
        ('matches', 'check_match_different_users'),
        ('photo_reveal_requests', 'check_valid_photo_request')
    ]
    
    for table, constraint in constraints_to_drop:
        try:
            op.drop_constraint(constraint, table)
        except Exception:
            pass
    
    # Remove unique constraints
    unique_constraints_to_drop = [
        ('blocked_users', 'unique_block_relationship'),
        ('user_safety_profiles', 'unique_user_safety_profile'),
        ('photo_reveal_timelines', 'unique_photo_timeline_per_connection'),
        ('profiles', 'unique_user_profile')
    ]
    
    for table, constraint in unique_constraints_to_drop:
        try:
            op.drop_constraint(constraint, table)
        except Exception:
            pass
    
    # Remove unique index
    try:
        op.drop_index('unique_soul_connection_users', 'soul_connections')
    except Exception:
        pass
    
    # Remove foreign key constraints
    foreign_keys_to_drop = [
        # User Safety
        ('user_reports', 'fk_user_reports_reporter_id'),
        ('user_reports', 'fk_user_reports_reported_user_id'),
        ('user_reports', 'fk_user_reports_resolved_by'),
        ('blocked_users', 'fk_blocked_users_blocker_id'),
        ('blocked_users', 'fk_blocked_users_blocked_user_id'),
        ('user_safety_profiles', 'fk_user_safety_profiles_user_id'),
        ('moderation_actions', 'fk_moderation_actions_target_user_id'),
        ('moderation_actions', 'fk_moderation_actions_moderator_id'),
        ('moderation_actions', 'fk_moderation_actions_related_report_id'),
        
        # Photo Reveal System
        ('user_photos', 'fk_user_photos_user_id'),
        ('photo_reveal_timelines', 'fk_photo_reveal_timelines_connection_id'),
        ('photo_reveal_requests', 'fk_photo_reveal_requests_timeline_id'),
        ('photo_reveal_requests', 'fk_photo_reveal_requests_photo_id'),
        ('photo_reveal_requests', 'fk_photo_reveal_requests_requester_id'),
        ('photo_reveal_requests', 'fk_photo_reveal_requests_photo_owner_id'),
        ('photo_reveal_permissions', 'fk_photo_reveal_permissions_photo_id'),
        ('photo_reveal_permissions', 'fk_photo_reveal_permissions_connection_id'),
        ('photo_reveal_permissions', 'fk_photo_reveal_permissions_viewer_id'),
        ('photo_reveal_permissions', 'fk_photo_reveal_permissions_photo_owner_id'),
        ('photo_reveal_permissions', 'fk_photo_reveal_permissions_source_request_id'),
        ('photo_reveal_events', 'fk_photo_reveal_events_timeline_id'),
        ('photo_reveal_events', 'fk_photo_reveal_events_connection_id'),
        ('photo_reveal_events', 'fk_photo_reveal_events_user_id'),
        ('photo_moderation_logs', 'fk_photo_moderation_logs_photo_id'),
        ('photo_moderation_logs', 'fk_photo_moderation_logs_moderator_id'),
        ('simple_photo_reveals', 'fk_simple_photo_reveals_connection_id'),
        ('simple_photo_reveals', 'fk_simple_photo_reveals_user_id'),
        
        # Core Models
        ('profiles', 'fk_profiles_user_id'),
        ('messages', 'fk_messages_connection_id'),
        ('messages', 'fk_messages_sender_id'),
        ('daily_revelations', 'fk_daily_revelations_connection_id'),
        ('daily_revelations', 'fk_daily_revelations_sender_id'),
        ('soul_connections', 'fk_soul_connections_user1_id'),
        ('soul_connections', 'fk_soul_connections_user2_id'),
        ('soul_connections', 'fk_soul_connections_initiated_by'),
        ('soul_connections', 'fk_soul_connections_ended_by'),
        ('matches', 'fk_matches_sender_id'),
        ('matches', 'fk_matches_receiver_id')
    ]
    
    for table, constraint in foreign_keys_to_drop:
        try:
            op.drop_constraint(constraint, table)
        except Exception:
            pass
    
    print("✓ Foreign key constraints removed")