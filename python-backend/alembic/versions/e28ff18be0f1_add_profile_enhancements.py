"""add profile enhancements

Revision ID: e28ff18be0f1
Revises: d7b82408b1f2
Create Date: 2025-04-21 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = "e28ff18be0f1"
down_revision = "d7b82408b1f2"
branch_labels = None
depends_on = None


def upgrade():
    # Create VerificationStatus enum type
    verification_status = postgresql.ENUM(
        "unverified", "pending", "verified", name="verificationstatus"
    )
    verification_status.create(op.get_bind())

    # Add new columns to profiles table
    with op.batch_alter_table("profiles", schema=None) as batch_op:
        # Photo management
        batch_op.add_column(
            sa.Column("profile_photos", sa.JSON(), nullable=True))

        # Verification
        batch_op.add_column(
            sa.Column(
                "verification_status",
                sa.Enum("unverified", "pending", "verified",
                        name="verificationstatus"),
                nullable=False,
                server_default="unverified",
            )
        )
        batch_op.add_column(
            sa.Column("verification_date", sa.DateTime(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("verification_method", sa.String(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("verification_document_url", sa.String(), nullable=True)
        )

        # Enhanced preferences
        batch_op.add_column(
            sa.Column("cooking_level", sa.String(), nullable=True))
        batch_op.add_column(
            sa.Column("preferred_dining_time", sa.String(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("preferred_meal_types", sa.String(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("preferred_group_size", sa.Integer(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("food_allergies", sa.String(), nullable=True))
        batch_op.add_column(
            sa.Column("special_diets", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("favorite_cuisines",
                            sa.String(), nullable=True))
        batch_op.add_column(
            sa.Column("price_range", sa.String(), nullable=True))


def downgrade():
    # Drop new columns from profiles table
    with op.batch_alter_table("profiles", schema=None) as batch_op:
        batch_op.drop_column("price_range")
        batch_op.drop_column("favorite_cuisines")
        batch_op.drop_column("special_diets")
        batch_op.drop_column("food_allergies")
        batch_op.drop_column("preferred_group_size")
        batch_op.drop_column("preferred_meal_types")
        batch_op.drop_column("preferred_dining_time")
        batch_op.drop_column("cooking_level")
        batch_op.drop_column("verification_document_url")
        batch_op.drop_column("verification_method")
        batch_op.drop_column("verification_date")
        batch_op.drop_column("verification_status")
        batch_op.drop_column("profile_photos")

    # Drop VerificationStatus enum type
    op.execute("DROP TYPE verificationstatus")
