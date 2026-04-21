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

## Endpoints iniciais (API v1)

Base: `http://localhost:8000/api/v1`

- `GET /livros` com paginação e filtros: `titulo`, `autor`, `ano_publicacao`, `disponivel`, `order_by`, `order_direction`
- `GET /livros/{id}`
- `POST /livros`
- `PATCH /livros/{id}`
- `DELETE /livros/{id}`
- `GET /pessoas` com paginação e filtros: `nome`, `email`
- `GET /pessoas/{id}`
- `POST /pessoas`
- `PATCH /pessoas/{id}`
- `DELETE /pessoas/{id}`
- `GET /usuarios` com paginação e filtros: `username`, `ativo`
- `GET /usuarios/{id}`
- `POST /usuarios`
- `PATCH /usuarios/{id}`
- `DELETE /usuarios/{id}`

Exemplo de listagem de livros com filtros:

```bash
curl "http://localhost:8000/api/v1/livros?autor=Martin&ano_publicacao=2011&order_by=titulo&order_direction=asc"
```

Exemplo de criação de pessoa:

```bash
curl -X POST "http://localhost:8000/api/v1/pessoas" \
	-H "Content-Type: application/json" \
	-d '{"nome":"Ada Lovelace","email":"ada@example.com"}'
```

Exemplo de criação de usuário:

```bash
curl -X POST "http://localhost:8000/api/v1/usuarios" \
	-H "Content-Type: application/json" \
	-d '{"pessoa_id":"<UUID_DA_PESSOA>","username":"adal","senha":"senha","ativo":true}'
```

Login e sessão:

- `POST /api/v1/auth/login` com `username` e `senha`
- `GET /api/v1/auth/me` para recuperar o usuário autenticado com o token JWT
