"""add emprestimos table and dias_emprestimo_padrao to livros

Revision ID: 20260421_0002
Revises: 20260418_0001
Create Date: 2026-04-21 00:01:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260421_0002"
down_revision: str | None = "20260418_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add dias_emprestimo_padrao column to livros
    op.add_column(
        "livros",
        sa.Column(
            "dias_emprestimo_padrao",
            sa.Integer(),
            nullable=False,
            server_default="7",
        ),
    )

    # Create emprestimos table
    op.create_table(
        "emprestimos",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("pessoa_id", sa.Uuid(), nullable=False),
        sa.Column("livro_id", sa.Uuid(), nullable=False),
        sa.Column(
            "data_emprestimo",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "data_devolucao_prevista",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "data_devolucao_real",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default="true"),
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
        sa.ForeignKeyConstraint(
            ["livro_id"],
            ["livros.id"],
            name=op.f("fk_emprestimos_livro_id_livros"),
        ),
        sa.ForeignKeyConstraint(
            ["pessoa_id"],
            ["pessoas.id"],
            name=op.f("fk_emprestimos_pessoa_id_pessoas"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_emprestimos")),
    )
    op.create_index(
        op.f("ix_emprestimos_livro_id"), "emprestimos", ["livro_id"], unique=False
    )
    op.create_index(
        op.f("ix_emprestimos_pessoa_id"), "emprestimos", ["pessoa_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_emprestimos_pessoa_id"), table_name="emprestimos")
    op.drop_index(op.f("ix_emprestimos_livro_id"), table_name="emprestimos")
    op.drop_table("emprestimos")
    op.drop_column("livros", "dias_emprestimo_padrao")
