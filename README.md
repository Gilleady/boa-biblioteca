# boa-biblioteca

Monorepo do projeto de biblioteca com backend em FastAPI na pasta `apps/api`.

## Backend novo

- Python 3.12+
- FastAPI
- SQLAlchemy 2.0 async + asyncpg
- Alembic para migrations
- Ruff, pytest, mypy e pre-commit

## Como rodar localmente

Suba a API e o Postgres com Docker Compose na raiz:

```bash
docker compose up --build
```

A API ficará disponível em http://localhost:8000.

## Como rodar migrations

Com a stack em pé, rode:

```bash
docker compose exec api uv run alembic upgrade head
```

Para criar uma nova migration:

```bash
docker compose exec api uv run alembic revision --autogenerate -m "sua mensagem"
```

## Como rodar testes

No backend:

```bash
cd apps/api
uv sync --dev
uv run pytest
```

## Qualidade

```bash
cd apps/api
uv run ruff check .
uv run ruff format --check .
uv run mypy app tests
```

## Estrutura nova

- `apps/api/app/api` para rotas HTTP
- `apps/api/app/core` para configurações e peças transversais
- `apps/api/app/db` para engine, sessão e base ORM
- `apps/api/alembic` para migrations
