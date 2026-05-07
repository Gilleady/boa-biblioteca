"""create initial domain tables

Revision ID: 20260418_0001
Revises:
Create Date: 2026-04-18 00:01:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260418_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "livros",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("titulo", sa.String(length=255), nullable=False),
        sa.Column("autor", sa.String(length=255), nullable=False),
        sa.Column("isbn", sa.String(length=20), nullable=False),
        sa.Column("ano_publicacao", sa.Integer(), nullable=True),
        sa.Column("disponivel", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_livros")),
        sa.UniqueConstraint("isbn", name=op.f("uq_livros_isbn")),
    )
    op.create_table(
        "pessoas",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("nome", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pessoas")),
        sa.UniqueConstraint("email", name=op.f("uq_pessoas_email")),
    )
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("pessoa_id", sa.Uuid(), nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("senha_hash", sa.String(length=255), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["pessoa_id"],
            ["pessoas.id"],
            name=op.f("fk_usuarios_pessoa_id_pessoas"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_usuarios")),
        sa.UniqueConstraint("pessoa_id", name=op.f("uq_usuarios_pessoa_id")),
        sa.UniqueConstraint("username", name=op.f("uq_usuarios_username")),
    )


def downgrade() -> None:
    op.drop_table("usuarios")
    op.drop_table("pessoas")
    op.drop_table("livros")
