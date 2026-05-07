# Setup de Deploy Automático no Azure

Este documento descreve como configurar o deploy automático do Boa Biblioteca para Azure usando o workflow do GitHub Actions.

## Pré-requisitos

1. **Grupo de Recursos no Azure** já criado
2. **App Service para API** (Python 3.12) nomeado `boabiblioteca-api`
3. **Static Web Apps** (para frontend) nomeado `boabiblioteca-web`
4. **Repositório GitHub** com essa branch `main`

## Passo 1: Criar OIDC Service Principal no Azure

Para segurança, usamos OIDC (OpenID Connect) em vez de credenciais de usuário.

Execute no Azure CLI:

```bash
az ad app create --display-name "boabiblioteca-github"

# Anote o appId retornado, depois:
az ad sp create --id <appId>

# Crie a credential OIDC:
az ad app federated-credential create \
  --id <appId> \
  --parameters '{
    "name": "GithubFederation",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:SEU_USUARIO/boa-biblioteca:ref:refs/heads/main",
    "audiences": ["api://AzureADTokenExchange"]
  }'

# Obtenha a subscription ID:
az account show --query id -o tsv

# Obtenha a tenant ID:
az account show --query tenantId -o tsv
```

Anote: `appId`, `subscription-id`, `tenant-id`

## Passo 2: Atribuir permissões ao Service Principal

```bash
az role assignment create \
  --role "Contributor" \
  --assignee <appId> \
  --resource-group <grupo-de-recurso>
```

## Passo 3: Configurar Secrets no GitHub

No repositório GitHub, vá para **Settings > Secrets and variables > Actions** e crie:

### Secrets (valores sensíveis)
- `AZURE_CLIENT_ID`: valor do appId
- `AZURE_TENANT_ID`: tenant ID
- `AZURE_SUBSCRIPTION_ID`: subscription ID
- `AZURE_STATIC_WEB_APPS_API_TOKEN`: token da Static Web Apps (obter no Azure Portal)

### Variables (repositório)
- `VITE_API_BASE_URL`: URL pública da API (ex: `https://boabiblioteca-api.azurewebsites.net`)

## Passo 4: Configurar App Settings no Azure App Service (API)

No App Service `boabiblioteca-api`, vá para **Configuration > Application settings** e adicione:

```
DATABASE_URL = postgresql+asyncpg://user:password@db-host:5432/boabiblioteca
ENVIRONMENT = production
JWT_SECRET_KEY = <seu-secret-key-seguro>
CORS_ORIGINS = ["https://boabiblioteca-web.azurestaticapps.net"]
```

## Passo 5: Configurar Startup Command

No App Service, vá para **Configuration > General settings** e defina:

**Startup Command:**
```
gunicorn -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
```

Alternativa (se preferir usar uvicorn direto):
```
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Passo 6: Configurar Banco de Dados

### Opção A: PostgreSQL Managed (Recomendado para produção)
1. Criar Azure Database for PostgreSQL (flexible server)
2. Atualizar `DATABASE_URL` no App Service
3. Executar migrations

### Opção B: PostgreSQL em Container (Desenvolvimento)
Usar Docker Container Instances ou App Service com Docker.

## Passo 7: Validar e Fazer Deploy

1. Fazer um commit qualquer na branch `main`
2. Ir para **Actions** no GitHub e verificar se o workflow `Build and deploy to Azure - boabiblioteca` foi disparado
3. Se passar todas as validações (ruff, mypy, pytest, build frontend), iniciará o deploy
4. Verificar status em **Deployments** no GitHub
5. Acessar a aplicação em `https://boabiblioteca-api.azurewebsites.net` (API)

## Troubleshooting

### Erro: "Authentication failed"
- Verificar se `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID` estão corretos no GitHub Secrets
- Confirmar que o OIDC federated credential foi criado com o subject correto

### Erro: "Permission denied"
- Verificar se o service principal tem role "Contributor" no grupo de recursos
- Usar `az role assignment list` para verificar

### Erro: "Requirements not met"
- Validação está falhando (ruff, mypy ou pytest)
- Checar logs do workflow em **Actions > Build and deploy to Azure - boabiblioteca**

### Erro: "Connection refused" na API
- Verificar se `DATABASE_URL` está configurado e banco está acessível
- Confirmar que `CORS_ORIGINS` inclui o domain do frontend

## Redeploy Manual

Se precisar redeployer sem fazer commit:

1. Ir para **Actions > Build and deploy to Azure - boabiblioteca**
2. Clicar em **Run workflow > Run workflow**

## Rollback

Para voltar a uma versão anterior:

```bash
git revert <commit-hash>
git push origin main
```

O workflow vai redeployer automaticamente.

---

Para mais detalhes, consulte:
- [Azure OIDC Integration](https://learn.microsoft.com/en-us/azure/active-directory/workload-identities/workload-identity-federation-create-trust-github)
- [GitHub Actions para Azure](https://github.com/Azure/actions-workflow-samples)
