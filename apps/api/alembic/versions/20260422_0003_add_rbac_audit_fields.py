"""add rbac and audit fields

Revision ID: 20260422_0003
Revises: 20260421_0002
Create Date: 2026-04-22 00:01:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260422_0003"
down_revision: str | None = "20260421_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "usuarios",
        sa.Column(
            "papel",
            sa.String(length=20),
            nullable=False,
            server_default="leitor",
        ),
    )
    op.add_column("usuarios", sa.Column("created_by", sa.Uuid(), nullable=True))
    op.add_column("usuarios", sa.Column("updated_by", sa.Uuid(), nullable=True))
    op.add_column(
        "usuarios",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.text("now()"),
        ),
    )

    op.add_column("pessoas", sa.Column("created_by", sa.Uuid(), nullable=True))
    op.add_column("pessoas", sa.Column("updated_by", sa.Uuid(), nullable=True))
    op.add_column(
        "pessoas",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.text("now()"),
        ),
    )

    op.add_column("emprestimos", sa.Column("created_by", sa.Uuid(), nullable=True))
    op.add_column("emprestimos", sa.Column("updated_by", sa.Uuid(), nullable=True))

    op.create_foreign_key(
        op.f("fk_usuarios_created_by_usuarios"),
        "usuarios",
        "usuarios",
        ["created_by"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_usuarios_updated_by_usuarios"),
        "usuarios",
        "usuarios",
        ["updated_by"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_pessoas_created_by_usuarios"),
        "pessoas",
        "usuarios",
        ["created_by"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_pessoas_updated_by_usuarios"),
        "pessoas",
        "usuarios",
        ["updated_by"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_emprestimos_created_by_usuarios"),
        "emprestimos",
        "usuarios",
        ["created_by"],
        ["id"],
    )
    op.create_foreign_key(
        op.f("fk_emprestimos_updated_by_usuarios"),
        "emprestimos",
        "usuarios",
        ["updated_by"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_emprestimos_updated_by_usuarios"),
        "emprestimos",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_emprestimos_created_by_usuarios"),
        "emprestimos",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_pessoas_updated_by_usuarios"),
        "pessoas",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_pessoas_created_by_usuarios"),
        "pessoas",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_usuarios_updated_by_usuarios"),
        "usuarios",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("fk_usuarios_created_by_usuarios"),
        "usuarios",
        type_="foreignkey",
    )

    op.drop_column("emprestimos", "updated_by")
    op.drop_column("emprestimos", "created_by")
    op.drop_column("pessoas", "updated_at")
    op.drop_column("pessoas", "updated_by")
    op.drop_column("pessoas", "created_by")
    op.drop_column("usuarios", "updated_at")
    op.drop_column("usuarios", "updated_by")
    op.drop_column("usuarios", "created_by")
    op.drop_column("usuarios", "papel")
