"""Add study materials and user public ID metadata."""

from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    table_names = set(inspector.get_table_names())

    if "study_materials" not in table_names:
        op.create_table(
            "study_materials",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("original_filename", sa.String(), nullable=False),
            sa.Column("description", sa.String(), nullable=False),
            sa.Column("storage_filename", sa.String(), nullable=False),
            sa.Column("content_type", sa.String(), nullable=False),
            sa.Column("size_bytes", sa.Integer(), nullable=False),
            sa.Column("uploaded_by_user_id", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("storage_filename"),
        )

    material_indexes = {index["name"] for index in inspector.get_indexes("study_materials")}
    if op.f("ix_study_materials_id") not in material_indexes:
        op.create_index(op.f("ix_study_materials_id"), "study_materials", ["id"], unique=False)
    if op.f("ix_study_materials_uploaded_by_user_id") not in material_indexes:
        op.create_index(
            op.f("ix_study_materials_uploaded_by_user_id"),
            "study_materials",
            ["uploaded_by_user_id"],
            unique=False,
        )

    user_columns = {column["name"] for column in inspector.get_columns("users")}
    if "public_user_id" not in user_columns:
        op.add_column("users", sa.Column("public_user_id", sa.String(length=36), nullable=True))
    if "updated_at" not in user_columns:
        op.add_column("users", sa.Column("updated_at", sa.DateTime(), nullable=True))

    users_table = sa.table(
        "users",
        sa.column("id", sa.Integer),
        sa.column("public_user_id", sa.String),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )
    rows = connection.execute(
        sa.select(
            users_table.c.id,
            users_table.c.created_at,
            users_table.c.public_user_id,
            users_table.c.updated_at,
        )
    ).fetchall()
    for row in rows:
        if row.public_user_id is None or row.updated_at is None:
            connection.execute(
                users_table.update()
                .where(users_table.c.id == row.id)
                .values(
                    public_user_id=row.public_user_id or str(uuid4()),
                    updated_at=row.updated_at or row.created_at,
                )
            )

    op.alter_column("users", "public_user_id", existing_type=sa.String(length=36), nullable=False)
    op.alter_column("users", "updated_at", existing_type=sa.DateTime(), nullable=False)

    user_indexes = {index["name"] for index in inspector.get_indexes("users")}
    if op.f("ix_users_public_user_id") not in user_indexes:
        op.create_index(op.f("ix_users_public_user_id"), "users", ["public_user_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_public_user_id"), table_name="users")
    op.drop_column("users", "updated_at")
    op.drop_column("users", "public_user_id")

    op.drop_index(op.f("ix_study_materials_uploaded_by_user_id"), table_name="study_materials")
    op.drop_index(op.f("ix_study_materials_id"), table_name="study_materials")
    op.drop_table("study_materials")