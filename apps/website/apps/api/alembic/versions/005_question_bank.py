"""Persist teacher-reviewed textbook exercises."""
from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "question_bank_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("teacher_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("material_id", sa.Integer(), sa.ForeignKey("study_materials.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chapter_id", sa.String(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("options", sa.JSON(), nullable=False),
        sa.Column("answer", sa.String(1), nullable=False),
        sa.Column("skill", sa.String(20), nullable=False),
        sa.Column("source_quote", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    for column in ("teacher_user_id", "material_id", "chapter_id"):
        op.create_index(f"ix_question_bank_items_{column}", "question_bank_items", [column])


def downgrade():
    op.drop_table("question_bank_items")
