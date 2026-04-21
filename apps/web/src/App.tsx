import { useEffect, useMemo, useState } from 'react'

const API_BASE_URL = 'http://localhost:8000'

type Livro = {
  id: string
  titulo: string
  autor: string
  isbn: string
  ano_publicacao: number | null
  disponivel: boolean
}

type TokenResponse = {
  access_token: string
  token_type: string
}

type UserResponse = {
  id: string
  username: string
}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('bb_token')
  const headers = new Headers(options.headers)
  headers.set('Content-Type', 'application/json')
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => null)
    const message = error?.error?.message ?? error?.detail ?? 'Erro inesperado'
    throw new Error(message)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

export function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('bb_token'))
  const [username, setUsername] = useState('')
  const [senha, setSenha] = useState('')
  const [authError, setAuthError] = useState('')
  const [user, setUser] = useState<UserResponse | null>(null)
  const [livros, setLivros] = useState<Livro[]>([])
  const [loadingLivros, setLoadingLivros] = useState(false)
  const [livroError, setLivroError] = useState('')
  const [livroForm, setLivroForm] = useState({ titulo: '', autor: '', isbn: '', ano_publicacao: '', disponivel: true })

  useEffect(() => {
    if (!token) {
      setUser(null)
      return
    }

    apiFetch<UserResponse>('/api/v1/auth/me')
      .then(setUser)
      .catch(() => {
        localStorage.removeItem('bb_token')
        setToken(null)
        setUser(null)
      })
  }, [token])

  const isAuthenticated = useMemo(() => Boolean(token), [token])

  async function loadLivros() {
    setLoadingLivros(true)
    try {
      const response = await apiFetch<{ items: Livro[] }>('/api/v1/livros')
      setLivros(response.items)
    } finally {
      setLoadingLivros(false)
    }
  }

  useEffect(() => {
    loadLivros().catch(() => undefined)
  }, [])

  async function handleLogin(event: React.FormEvent) {
    event.preventDefault()
    setAuthError('')

    try {
      const response = await apiFetch<TokenResponse>('/api/v1/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username, senha }),
      })
      localStorage.setItem('bb_token', response.access_token)
      setToken(response.access_token)
      setUsername('')
      setSenha('')
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : 'Falha no login')
    }
  }

  async function handleCreateLivro(event: React.FormEvent) {
    event.preventDefault()
    setLivroError('')

    try {
      await apiFetch('/api/v1/livros', {
        method: 'POST',
        body: JSON.stringify({
          titulo: livroForm.titulo,
          autor: livroForm.autor,
          isbn: livroForm.isbn,
          ano_publicacao: livroForm.ano_publicacao ? Number(livroForm.ano_publicacao) : null,
          disponivel: livroForm.disponivel,
        }),
      })
      setLivroForm({ titulo: '', autor: '', isbn: '', ano_publicacao: '', disponivel: true })
      await loadLivros()
    } catch (error) {
      setLivroError(error instanceof Error ? error.message : 'Falha ao criar livro')
    }
  }

  async function handleDeleteLivro(id: string) {
    setLivroError('')

    try {
      await apiFetch(`/api/v1/livros/${id}`, { method: 'DELETE' })
      await loadLivros()
    } catch (error) {
      setLivroError(error instanceof Error ? error.message : 'Falha ao excluir livro')
    }
  }

  return (
    <div className="shell">
      <main className="app">
        <section className="hero">
          <div>
            <p className="eyebrow">Boa Biblioteca</p>
            <h1>Catálogo operacional com base neutra e foco no fluxo.</h1>
            <p className="lead">
              Login JWT, lista pública de livros e ações protegidas já integradas à API.
            </p>
          </div>
          <div className="status-card">
            <span>Status</span>
            <strong>{isAuthenticated ? `Logado como ${user?.username ?? 'usuário'}` : 'Sessão desconectada'}</strong>
          </div>
        </section>

        {!isAuthenticated ? (
          <section className="panel grid-two">
            <form className="card form" onSubmit={handleLogin}>
              <h2>Entrar</h2>
              <label>
                Usuário
                <input value={username} onChange={(event) => setUsername(event.target.value)} />
              </label>
              <label>
                Senha
                <input type="password" value={senha} onChange={(event) => setSenha(event.target.value)} />
              </label>
              {authError ? <p className="error">{authError}</p> : null}
              <button type="submit">Acessar</button>
            </form>

            <div className="card muted">
              <h2>Fluxo atual</h2>
              <ul>
                <li>Listagem de livros pública</li>
                <li>Login JWT para ações protegidas</li>
                <li>UI neutra, pronta para evoluir para RBAC</li>
              </ul>
            </div>
          </section>
        ) : null}

        <section className="panel">
          <div className="section-head">
            <h2>Livros</h2>
            <button type="button" onClick={() => loadLivros().catch(() => undefined)}>
              Recarregar
            </button>
          </div>

          {isAuthenticated ? (
            <form className="card form grid-compact" onSubmit={handleCreateLivro}>
              <h3>Novo livro</h3>
              {livroError ? <p className="error">{livroError}</p> : null}
              <label>
                Título
                <input value={livroForm.titulo} onChange={(event) => setLivroForm({ ...livroForm, titulo: event.target.value })} />
              </label>
              <label>
                Autor
                <input value={livroForm.autor} onChange={(event) => setLivroForm({ ...livroForm, autor: event.target.value })} />
              </label>
              <label>
                ISBN
                <input value={livroForm.isbn} onChange={(event) => setLivroForm({ ...livroForm, isbn: event.target.value })} />
              </label>
              <label>
                Ano
                <input value={livroForm.ano_publicacao} onChange={(event) => setLivroForm({ ...livroForm, ano_publicacao: event.target.value })} />
              </label>
              <label className="checkbox">
                <input
                  type="checkbox"
                  checked={livroForm.disponivel}
                  onChange={(event) => setLivroForm({ ...livroForm, disponivel: event.target.checked })}
                />
                Disponível
              </label>
              <button type="submit">Criar livro</button>
            </form>
          ) : null}

          <div className="list">
            {loadingLivros ? <p>Carregando...</p> : null}
            {!loadingLivros && livros.length === 0 ? <p>Nenhum livro encontrado.</p> : null}
            {livros.map((livro) => (
              <article className="card book" key={livro.id}>
                <div>
                  <h3>{livro.titulo}</h3>
                  <p>{livro.autor}</p>
                  <small>
                    ISBN {livro.isbn} · {livro.ano_publicacao ?? 'sem ano'}
                  </small>
                </div>
                <div className="book-actions">
                  <span className={livro.disponivel ? 'pill available' : 'pill unavailable'}>
                    {livro.disponivel ? 'Disponível' : 'Indisponível'}
                  </span>
                  {isAuthenticated ? (
                    <button type="button" className="ghost" onClick={() => handleDeleteLivro(livro.id).catch(() => undefined)}>
                      Excluir
                    </button>
                  ) : null}
                </div>
              </article>
            ))}
          </div>
        </section>
      </main>
    </div>
  )
}
