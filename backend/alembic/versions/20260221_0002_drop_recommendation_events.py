"""drop recommendation_events table"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260221_0002"
down_revision: Union[str, None] = "20260221_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _datetime_default():
    if op.get_bind().dialect.name == "sqlite":
        return sa.text("(datetime('now'))")
    return sa.text("now()")


def upgrade() -> None:
    op.drop_index("ix_recommendation_events_conversation_id", table_name="recommendation_events")
    op.drop_table("recommendation_events")


def downgrade() -> None:
    ts = _datetime_default()
    op.create_table(
        "recommendation_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("goal_alignment_score", sa.Integer(), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=ts, nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_recommendation_events_conversation_id",
        "recommendation_events",
        ["conversation_id"],
        unique=False,
    )
