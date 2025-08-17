"""Add database indexes for performance optimization

Revision ID: add_db_indexes
Revises: eb1f6896899f
Create Date: 2025-08-08 10:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_db_indexes'
down_revision = 'eb1f6896899f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Performance indexes for user queries (skip existing ones)
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_email ON users (email)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_location ON users (location)")  
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_is_active ON users (is_active)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_profile_complete ON users (is_profile_complete)")
    
    # Composite indexes for common matching queries
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_active_location ON users (is_active, location)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_active_age ON users (is_active, date_of_birth)")
    
    # Soul connection performance indexes
    op.execute("CREATE INDEX IF NOT EXISTS ix_soul_connections_user1 ON soul_connections (user1_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_soul_connections_user2 ON soul_connections (user2_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_soul_connections_status ON soul_connections (status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_soul_connections_stage ON soul_connections (connection_stage)")
    
    # Composite indexes for connection queries
    op.execute("CREATE INDEX IF NOT EXISTS ix_soul_connections_user1_status ON soul_connections (user1_id, status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_soul_connections_user2_status ON soul_connections (user2_id, status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_soul_connections_users_status ON soul_connections (user1_id, user2_id, status)")
    
    # Message performance indexes
    op.execute("CREATE INDEX IF NOT EXISTS ix_messages_connection_id ON messages (connection_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_messages_sender_id ON messages (sender_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_messages_created_at ON messages (created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_messages_is_read ON messages (is_read)")
    
    # Composite indexes for message queries
    op.execute("CREATE INDEX IF NOT EXISTS ix_messages_connection_created ON messages (connection_id, created_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_messages_sender_unread ON messages (sender_id, is_read)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_messages_connection_unread ON messages (connection_id, is_read)")
    
    # Revelation performance indexes
    op.execute("CREATE INDEX IF NOT EXISTS ix_revelations_connection_id ON daily_revelations (connection_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_revelations_sender_id ON daily_revelations (sender_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_revelations_day_number ON daily_revelations (day_number)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_revelations_created_at ON daily_revelations (created_at)")
    
    # Composite indexes for revelation queries
    op.execute("CREATE INDEX IF NOT EXISTS ix_revelations_connection_day ON daily_revelations (connection_id, day_number)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_revelations_sender_day ON daily_revelations (sender_id, day_number)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_revelations_connection_sender ON daily_revelations (connection_id, sender_id)")
    
    # Match performance indexes (if matches table exists)
    op.execute("CREATE INDEX IF NOT EXISTS ix_matches_sender_id ON matches (sender_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_matches_receiver_id ON matches (receiver_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_matches_status ON matches (status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_matches_created_at ON matches (created_at)")
    
    # Composite indexes for match queries
    op.execute("CREATE INDEX IF NOT EXISTS ix_matches_sender_status ON matches (sender_id, status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_matches_receiver_status ON matches (receiver_id, status)")


def downgrade() -> None:
    # Drop all created indexes
    # User indexes
    op.drop_index('ix_users_email')
    op.drop_index('ix_users_location')
    op.drop_index('ix_users_is_active')
    op.drop_index('ix_users_profile_complete')
    op.drop_index('ix_users_active_location')
    op.drop_index('ix_users_active_age')
    
    # Soul connection indexes
    op.drop_index('ix_soul_connections_user1')
    op.drop_index('ix_soul_connections_user2')
    op.drop_index('ix_soul_connections_status')
    op.drop_index('ix_soul_connections_stage')
    op.drop_index('ix_soul_connections_user1_status')
    op.drop_index('ix_soul_connections_user2_status')
    op.drop_index('ix_soul_connections_users_status')
    
    # Message indexes
    op.drop_index('ix_messages_connection_id')
    op.drop_index('ix_messages_sender_id')
    op.drop_index('ix_messages_created_at')
    op.drop_index('ix_messages_is_read')
    op.drop_index('ix_messages_connection_created')
    op.drop_index('ix_messages_sender_unread')
    op.drop_index('ix_messages_connection_unread')
    
    # Revelation indexes
    op.drop_index('ix_revelations_connection_id')
    op.drop_index('ix_revelations_sender_id')
    op.drop_index('ix_revelations_day_number')
    op.drop_index('ix_revelations_created_at')
    op.drop_index('ix_revelations_connection_day')
    op.drop_index('ix_revelations_sender_day')
    op.drop_index('ix_revelations_connection_sender')
    
    # Match indexes
    op.drop_index('ix_matches_sender_id')
    op.drop_index('ix_matches_receiver_id')
    op.drop_index('ix_matches_status')
    op.drop_index('ix_matches_created_at')
    op.drop_index('ix_matches_sender_status')
    op.drop_index('ix_matches_receiver_status')