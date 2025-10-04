"""Add WebSocket real-time indexes and optimizations

Revision ID: 791169cd0a5c
Revises: a0fc025ad089
Create Date: 2025-09-24 17:09:57.058980

"""

import sqlalchemy as sa  # noqa: F401
from alembic import op

# revision identifiers, used by Alembic.
revision = "791169cd0a5c"
down_revision = "a0fc025ad089"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add indexes for user presence queries (real-time lookup optimization)
    op.create_index(
        "ix_user_presence_user_id_status", "user_presence", ["user_id", "status"]
    )
    op.create_index("ix_user_presence_last_seen", "user_presence", ["last_seen"])
    op.create_index(
        "ix_user_presence_status_last_seen", "user_presence", ["status", "last_seen"]
    )

    # Add indexes for soul connections real-time queries
    op.create_index(
        "ix_soul_connections_user_status",
        "soul_connections",
        ["user1_id", "user2_id", "status"],
    )
    op.create_index(
        "ix_soul_connections_stage_activity",
        "soul_connections",
        ["connection_stage", "last_activity_at"],
    )
    op.create_index(
        "ix_soul_connections_energy_updated",
        "soul_connections",
        ["current_energy_level", "updated_at"],
    )

    # Add indexes for daily revelations (real-time revelation tracking)
    op.create_index(
        "ix_daily_revelations_connection_day",
        "daily_revelations",
        ["connection_id", "day_number"],
    )
    op.create_index(
        "ix_daily_revelations_user_created",
        "daily_revelations",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_daily_revelations_shared_status",
        "daily_revelations",
        ["is_shared", "created_at"],
    )

    # Add indexes for messages (real-time messaging optimization)
    op.create_index(
        "ix_messages_connection_created", "messages", ["connection_id", "created_at"]
    )
    op.create_index(
        "ix_messages_sender_created", "messages", ["sender_id", "created_at"]
    )
    op.create_index(
        "ix_messages_type_created", "messages", ["message_type", "created_at"]
    )

    # Add indexes for user engagement analytics (real-time activity tracking)
    op.create_index(
        "ix_user_engagement_user_event",
        "user_engagement_analytics",
        ["user_id", "event_type"],
    )
    op.create_index(
        "ix_user_engagement_session_time",
        "user_engagement_analytics",
        ["session_id", "event_time"],
    )
    op.create_index(
        "ix_user_engagement_event_time",
        "user_engagement_analytics",
        ["event_type", "event_time"],
    )

    # Add partial indexes for active connections (WebSocket connection tracking)
    op.execute(
        """
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_user_presence_online_users
        ON user_presence (user_id, last_seen DESC)
        WHERE status IN ('online', 'typing')
    """
    )

    op.execute(
        """
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_soul_connections_active_recent
        ON soul_connections (id, last_activity_at DESC)
        WHERE status = 'active' AND last_activity_at > NOW() - INTERVAL '7 days'
    """
    )

    # Add composite indexes for real-time compatibility calculations
    op.create_index(
        "ix_personalized_content_user_type_created",
        "personalized_content",
        ["user_profile_id", "content_type", "created_at"],
    )
    op.create_index(
        "ix_content_feedback_content_sentiment",
        "content_feedback",
        ["content_id", "sentiment_score", "created_at"],
    )


def downgrade() -> None:
    # Drop indexes in reverse order
    op.drop_index("ix_content_feedback_content_sentiment", "content_feedback")
    op.drop_index("ix_personalized_content_user_type_created", "personalized_content")

    # Drop partial indexes
    op.execute("DROP INDEX IF EXISTS ix_soul_connections_active_recent")
    op.execute("DROP INDEX IF EXISTS ix_user_presence_online_users")

    # Drop regular indexes
    op.drop_index("ix_user_engagement_event_time", "user_engagement_analytics")
    op.drop_index("ix_user_engagement_session_time", "user_engagement_analytics")
    op.drop_index("ix_user_engagement_user_event", "user_engagement_analytics")

    op.drop_index("ix_messages_type_created", "messages")
    op.drop_index("ix_messages_sender_created", "messages")
    op.drop_index("ix_messages_connection_created", "messages")

    op.drop_index("ix_daily_revelations_shared_status", "daily_revelations")
    op.drop_index("ix_daily_revelations_user_created", "daily_revelations")
    op.drop_index("ix_daily_revelations_connection_day", "daily_revelations")

    op.drop_index("ix_soul_connections_energy_updated", "soul_connections")
    op.drop_index("ix_soul_connections_stage_activity", "soul_connections")
    op.drop_index("ix_soul_connections_user_status", "soul_connections")

    op.drop_index("ix_user_presence_status_last_seen", "user_presence")
    op.drop_index("ix_user_presence_last_seen", "user_presence")
    op.drop_index("ix_user_presence_user_id_status", "user_presence")
