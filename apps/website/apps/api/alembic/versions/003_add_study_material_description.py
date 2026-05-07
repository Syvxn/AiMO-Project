"""Ensure study materials have description column."""

from alembic import op
import sqlalchemy as sa


revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if "study_materials" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("study_materials")}
    if "description" not in columns:
        op.add_column(
            "study_materials",
            sa.Column("description", sa.String(), nullable=False, server_default=""),
        )
        op.alter_column("study_materials", "description", server_default=None)


def downgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if "study_materials" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("study_materials")}
    if "description" in columns:
        op.drop_column("study_materials", "description")