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
    # Create user_presence table if it doesn't exist
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "user_presence" not in inspector.get_table_names():
        op.create_table(
            "user_presence",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(), nullable=True),
            sa.Column("last_seen", sa.DateTime(), nullable=True),
            sa.Column("last_activity_at", sa.DateTime(), nullable=True),
            sa.Column("connection_metadata", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id"),
        )

    # Add indexes for user presence queries (real-time lookup optimization)
    op.create_index(
        "ix_user_presence_user_id_status",
        "user_presence",
        ["user_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_user_presence_last_seen", "user_presence", ["last_seen"], unique=False
    )
    op.create_index(
        "ix_user_presence_status_last_seen",
        "user_presence",
        ["status", "last_seen"],
        unique=False,
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
        "ix_daily_revelations_sender_created",
        "daily_revelations",
        ["sender_id", "created_at"],
    )
    op.create_index(
        "ix_daily_revelations_read_status",
        "daily_revelations",
        ["is_read", "created_at"],
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
    # Only if table exists
    if "user_engagement_analytics" in inspector.get_table_names():
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
    # Remove CONCURRENTLY as it can't run inside transaction
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_user_presence_online_users
        ON user_presence (user_id, last_seen DESC)
        WHERE status IN ('online', 'typing')
    """
    )

    # Note: Removed partial index with NOW() as it requires IMMUTABLE function
    # This index would need CURRENT_TIMESTAMP instead, but for simplicity
    # we skip this partial index in migrations

    # Add composite indexes for real-time compatibility calculations
    # Only if tables exist
    if "personalized_content" in inspector.get_table_names():
        op.create_index(
            "ix_personalized_content_user_type_created",
            "personalized_content",
            ["user_profile_id", "content_type", "created_at"],
        )
    if "content_feedback" in inspector.get_table_names():
        op.create_index(
            "ix_content_feedback_content_sentiment",
            "content_feedback",
            ["content_id", "sentiment_score", "created_at"],
        )


def downgrade() -> None:
    # Drop indexes in reverse order - use IF EXISTS to make idempotent
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Drop indexes only if tables exist
    if "content_feedback" in inspector.get_table_names():
        op.execute("DROP INDEX IF EXISTS ix_content_feedback_content_sentiment")
    if "personalized_content" in inspector.get_table_names():
        op.execute("DROP INDEX IF EXISTS ix_personalized_content_user_type_created")

    # Drop partial indexes
    op.execute("DROP INDEX IF EXISTS ix_soul_connections_active_recent")
    op.execute("DROP INDEX IF EXISTS ix_user_presence_online_users")

    # Drop regular indexes - only if tables exist
    if "user_engagement_analytics" in inspector.get_table_names():
        op.execute("DROP INDEX IF EXISTS ix_user_engagement_event_time")
        op.execute("DROP INDEX IF EXISTS ix_user_engagement_session_time")
        op.execute("DROP INDEX IF EXISTS ix_user_engagement_user_event")

    op.drop_index("ix_messages_type_created", "messages")
    op.drop_index("ix_messages_sender_created", "messages")
    op.drop_index("ix_messages_connection_created", "messages")

    op.drop_index("ix_daily_revelations_read_status", "daily_revelations")
    op.drop_index("ix_daily_revelations_sender_created", "daily_revelations")
    op.drop_index("ix_daily_revelations_connection_day", "daily_revelations")

    op.drop_index("ix_soul_connections_energy_updated", "soul_connections")
    op.drop_index("ix_soul_connections_stage_activity", "soul_connections")
    op.drop_index("ix_soul_connections_user_status", "soul_connections")

    op.drop_index("ix_user_presence_status_last_seen", "user_presence")
    op.drop_index("ix_user_presence_last_seen", "user_presence")
    op.drop_index("ix_user_presence_user_id_status", "user_presence")

    # Drop user_presence table if it exists
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "user_presence" in inspector.get_table_names():
        op.drop_table("user_presence")
