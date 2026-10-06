"""Link students to their teacher's class."""

from alembic import op
import sqlalchemy as sa


revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = {column["name"] for column in inspector.get_columns("users")}
    foreign_keys = {
        constraint.get("name") for constraint in inspector.get_foreign_keys("users")
    }

    with op.batch_alter_table("users") as batch_op:
        if "class_code" not in columns:
            batch_op.add_column(sa.Column("class_code", sa.String(length=8), nullable=True))
        if "teacher_user_id" not in columns:
            batch_op.add_column(sa.Column("teacher_user_id", sa.Integer(), nullable=True))
        if "fk_users_teacher_user_id_users" not in foreign_keys:
            batch_op.create_foreign_key(
                "fk_users_teacher_user_id_users",
                "users",
                ["teacher_user_id"],
                ["id"],
            )

    indexes = {index["name"] for index in sa.inspect(connection).get_indexes("users")}
    if "ix_users_class_code" not in indexes:
        op.create_index("ix_users_class_code", "users", ["class_code"], unique=True)
    if "ix_users_teacher_user_id" not in indexes:
        op.create_index("ix_users_teacher_user_id", "users", ["teacher_user_id"])


def downgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    indexes = {index["name"] for index in inspector.get_indexes("users")}
    if "ix_users_teacher_user_id" in indexes:
        op.drop_index("ix_users_teacher_user_id", table_name="users")
    if "ix_users_class_code" in indexes:
        op.drop_index("ix_users_class_code", table_name="users")

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint("fk_users_teacher_user_id_users", type_="foreignkey")
        batch_op.drop_column("teacher_user_id")
        batch_op.drop_column("class_code")