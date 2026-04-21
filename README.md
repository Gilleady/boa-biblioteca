# boa-biblioteca

Monorepo da Boa Biblioteca com backend em FastAPI e frontend em React/Vite.

## Visao Geral

O projeto disponibiliza uma API REST versionada (`/api/v1`) para catalogo de livros, pessoas, usuarios e autenticacao JWT, com interface web para login e operacoes do catalogo.

## Stack

- Backend: Python 3.12, FastAPI, SQLAlchemy 2.0 async, asyncpg, Alembic
- Frontend: React, Vite, TypeScript
- Qualidade: Ruff, mypy, pytest
- Infra local: Docker Compose (API + Postgres)

## Arquitetura

- `apps/api/app/api`: rotas HTTP, dependencias e handlers de erro
- `apps/api/app/services`: regras de negocio
- `apps/api/app/repositories`: acesso a dados
- `apps/api/app/models`: modelos ORM
- `apps/api/alembic`: migrations
- `apps/web`: aplicacao frontend

## Pre-requisitos

- Docker e Docker Compose
- Python 3.12+
- Node.js 20+

## Configuracao de Ambiente

O backend usa `apps/api/.env` (carregado automaticamente via settings). Campos principais:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `JWT_EXPIRATION_MINUTES`
- `CORS_ORIGINS`

Se nao informado, valores de desenvolvimento sao usados no backend.

## Execucao Local

### 1. Backend + Banco com Docker

```bash
docker compose up --build
```

API disponivel em `http://localhost:8000`.

### 2. Frontend

```bash
cd apps/web
npm install
npm run dev
```

Frontend disponivel em `http://localhost:5173`.

## Migrations

Aplicar migrations:

```bash
docker compose exec api uv run alembic upgrade head
```

Gerar nova migration:

```bash
docker compose exec api uv run alembic revision --autogenerate -m "sua mensagem"
```

## Documentacao da API

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

Melhores praticas aplicadas na documentacao:

- endpoints agrupados por tags de dominio
- esquema de seguranca Bearer JWT no Swagger
- modelos de erro padronizados e respostas documentadas
- exemplos de payload em schemas principais

## Fluxo JWT (fim a fim)

### 1. Criar pessoa

```bash
curl -X POST "http://localhost:8000/api/v1/pessoas" \
	-H "Content-Type: application/json" \
	-d '{"nome":"Ada Lovelace","email":"ada@example.com"}'
```

### 2. Criar usuario

```bash
curl -X POST "http://localhost:8000/api/v1/usuarios" \
	-H "Content-Type: application/json" \
	-d '{"pessoa_id":"<UUID_DA_PESSOA>","username":"adal","senha":"senha123","ativo":true}'
```

### 3. Fazer login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
	-H "Content-Type: application/json" \
	-d '{"username":"adal","senha":"senha123"}'
```

Resposta esperada:

```json
{
	"access_token": "<JWT>",
	"token_type": "bearer"
}
```

### 4. Consultar sessao atual

```bash
curl "http://localhost:8000/api/v1/auth/me" \
	-H "Authorization: Bearer <JWT>"
```

### 5. Criar livro com rota protegida

```bash
curl -X POST "http://localhost:8000/api/v1/livros" \
	-H "Content-Type: application/json" \
	-H "Authorization: Bearer <JWT>" \
	-d '{"titulo":"Clean Code","autor":"Robert C. Martin","isbn":"9780132350884","ano_publicacao":2008,"disponivel":true}'
```

## Endpoints

Base: `http://localhost:8000/api/v1`

- `GET /livros` (filtros: `titulo`, `autor`, `ano_publicacao`, `disponivel`, `order_by`, `order_direction`)
- `GET /livros/{id}`
- `POST /livros` (protegido)
- `PATCH /livros/{id}` (protegido)
- `DELETE /livros/{id}` (protegido)
- `GET /pessoas` (filtros: `nome`, `email`)
- `GET /pessoas/{id}`
- `POST /pessoas`
- `PATCH /pessoas/{id}`
- `DELETE /pessoas/{id}`
- `GET /usuarios` (filtros: `username`, `ativo`)
- `GET /usuarios/{id}`
- `POST /usuarios`
- `PATCH /usuarios/{id}`
- `DELETE /usuarios/{id}`
- `POST /auth/login`
- `GET /auth/me` (protegido)

## Qualidade e Testes

```bash
cd apps/api
uv sync --dev
uv run ruff check .
uv run ruff format --check .
uv run mypy app tests
uv run pytest
```

## Troubleshooting

- Erro de CORS no frontend:
	- Verifique `CORS_ORIGINS` e confirme que `http://localhost:5173` esta liberado.
- Erro de conexao com banco:
	- Confirme que o container `db` esta healthy no `docker compose ps`.
- `401 Not authenticated`:
	- Verifique se o header `Authorization: Bearer <JWT>` foi enviado.
- Token expirado:
	- Efetue novo login em `/api/v1/auth/login`.
