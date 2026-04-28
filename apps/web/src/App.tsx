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

type Papel = 'admin' | 'atendente' | 'leitor'

type UserResponse = {
  id: string
  username: string
  pessoa_id: string
  papel: Papel
}

type RegisterResponse = {
  status: 'created' | 'verification_required'
  message: string
  verification_code: string | null
}

type Pessoa = {
  id: string
  nome: string
  email: string
}

type Emprestimo = {
  id: string
  pessoa_id: string
  livro_id: string
  data_emprestimo: string
  data_devolucao_prevista: string
  data_devolucao_real: string | null
  ativo: boolean
}

type PaginatedResponse<T> = {
  items: T[]
  total: number
  page: number
  page_size: number
}

const DATE_FORMATTER = new Intl.DateTimeFormat('pt-BR', {
  dateStyle: 'medium',
  timeStyle: 'short',
})

function formatDate(value: string) {
  return DATE_FORMATTER.format(new Date(value))
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
  const [registerNome, setRegisterNome] = useState('')
  const [registerEmail, setRegisterEmail] = useState('')
  const [registerUsername, setRegisterUsername] = useState('')
  const [registerSenha, setRegisterSenha] = useState('')
  const [registerVerifyEmail, setRegisterVerifyEmail] = useState('')
  const [registerVerifyCode, setRegisterVerifyCode] = useState('')
  const [registerError, setRegisterError] = useState('')
  const [registerSuccess, setRegisterSuccess] = useState('')
  const [registerNeedsVerification, setRegisterNeedsVerification] = useState(false)
  const [user, setUser] = useState<UserResponse | null>(null)
  const [livros, setLivros] = useState<Livro[]>([])
  const [pessoas, setPessoas] = useState<Pessoa[]>([])
  const [emprestimos, setEmprestimos] = useState<Emprestimo[]>([])
  const [loadingLivros, setLoadingLivros] = useState(false)
  const [loadingPessoas, setLoadingPessoas] = useState(false)
  const [loadingEmprestimos, setLoadingEmprestimos] = useState(false)
  const [livroError, setLivroError] = useState('')
  const [pessoaError, setPessoaError] = useState('')
  const [emprestimoError, setEmprestimoError] = useState('')
  const [emprestimoSuccess, setEmprestimoSuccess] = useState('')
  const [livroForm, setLivroForm] = useState({ titulo: '', autor: '', isbn: '', ano_publicacao: '', disponivel: true })
  const [emprestimoForm, setEmprestimoForm] = useState({ pessoa_id: '', livro_id: '' })

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
  const userRole = useMemo(() => user?.papel ?? null, [user])
  const canManageCatalog = useMemo(
    () => userRole === 'admin' || userRole === 'atendente',
    [userRole],
  )
  const canManageLoans = useMemo(
    () => userRole === 'admin' || userRole === 'atendente',
    [userRole],
  )
  const livrosDisponiveis = useMemo(
    () => livros.filter((livro) => livro.disponivel),
    [livros],
  )
  const livroById = useMemo(
    () => new Map(livros.map((livro) => [livro.id, livro])),
    [livros],
  )
  const pessoaById = useMemo(
    () => new Map(pessoas.map((pessoa) => [pessoa.id, pessoa])),
    [pessoas],
  )

  useEffect(() => {
    if (!isAuthenticated || !canManageLoans) {
      return
    }

    if (pessoas.length > 0) {
      setEmprestimoForm((current) => {
        if (current.pessoa_id && pessoaById.has(current.pessoa_id)) {
          return current
        }

        return { ...current, pessoa_id: pessoas[0].id }
      })
    }

    if (livrosDisponiveis.length > 0) {
      setEmprestimoForm((current) => {
        if (current.livro_id && livrosDisponiveis.some((livro) => livro.id === current.livro_id)) {
          return current
        }

        return { ...current, livro_id: livrosDisponiveis[0].id }
      })
    }
  }, [canManageLoans, isAuthenticated, livrosDisponiveis, pessoaById, pessoas])

  async function loadLivros() {
    setLoadingLivros(true)
    try {
      const response = await apiFetch<PaginatedResponse<Livro>>('/api/v1/livros')
      setLivros(response.items)
    } finally {
      setLoadingLivros(false)
    }
  }

  async function loadPessoas() {
    setLoadingPessoas(true)
    setPessoaError('')

    try {
      const response = await apiFetch<PaginatedResponse<Pessoa>>('/api/v1/pessoas?page_size=100')
      setPessoas(response.items)
    } catch (error) {
      setPessoaError(error instanceof Error ? error.message : 'Falha ao carregar pessoas')
    } finally {
      setLoadingPessoas(false)
    }
  }

  async function loadEmprestimos() {
    setLoadingEmprestimos(true)
    setEmprestimoError('')

    try {
      const response = await apiFetch<PaginatedResponse<Emprestimo>>('/api/v1/emprestimos?page_size=100')
      setEmprestimos(response.items)
    } catch (error) {
      setEmprestimoError(error instanceof Error ? error.message : 'Falha ao carregar empréstimos')
    } finally {
      setLoadingEmprestimos(false)
    }
  }

  useEffect(() => {
    loadLivros().catch(() => undefined)
  }, [])

  useEffect(() => {
    if (!isAuthenticated) {
      setPessoas([])
      setEmprestimos([])
      setEmprestimoForm({ pessoa_id: '', livro_id: '' })
      setPessoaError('')
      setEmprestimoError('')
      setEmprestimoSuccess('')
      return
    }

    if (canManageLoans) {
      Promise.all([loadPessoas(), loadEmprestimos(), loadLivros()]).catch(() => undefined)
      return
    }

    setPessoas([])
    Promise.all([loadEmprestimos(), loadLivros()]).catch(() => undefined)
  }, [canManageLoans, isAuthenticated])

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

  async function handleRegister(event: React.FormEvent) {
    event.preventDefault()
    setRegisterError('')
    setRegisterSuccess('')

    try {
      const response = await apiFetch<RegisterResponse>('/api/v1/auth/register', {
        method: 'POST',
        body: JSON.stringify({
          nome: registerNome,
          email: registerEmail,
          username: registerUsername,
          senha: registerSenha,
        }),
      })

      if (response.status === 'verification_required') {
        setRegisterNeedsVerification(true)
        setRegisterVerifyEmail(registerEmail)
        setRegisterSuccess(
          response.verification_code
            ? `${response.message} Codigo (dev): ${response.verification_code}`
            : response.message,
        )
        return
      }

      setRegisterNeedsVerification(false)
      setRegisterVerifyEmail('')
      setRegisterVerifyCode('')
      setUsername(registerUsername)
      setSenha(registerSenha)
      setRegisterNome('')
      setRegisterEmail('')
      setRegisterUsername('')
      setRegisterSenha('')
      setRegisterSuccess('Cadastro concluído. Agora clique em Acessar para entrar.')
    } catch (error) {
      setRegisterError(error instanceof Error ? error.message : 'Falha no cadastro')
    }
  }

  async function handleRegisterVerify(event: React.FormEvent) {
    event.preventDefault()
    setRegisterError('')
    setRegisterSuccess('')

    try {
      const response = await apiFetch<RegisterResponse>('/api/v1/auth/register/verify', {
        method: 'POST',
        body: JSON.stringify({
          email: registerVerifyEmail,
          code: registerVerifyCode,
        }),
      })

      setRegisterNeedsVerification(false)
      setRegisterVerifyCode('')
      setUsername(registerUsername)
      setSenha(registerSenha)
      setRegisterNome('')
      setRegisterEmail('')
      setRegisterUsername('')
      setRegisterSenha('')
      setRegisterSuccess(response.message)
    } catch (error) {
      setRegisterError(error instanceof Error ? error.message : 'Falha na verificação')
    }
  }

  function handleLogout() {
    localStorage.removeItem('bb_token')
    setToken(null)
    setUser(null)
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

  async function handleCreateEmprestimo(event: React.FormEvent) {
    event.preventDefault()
    setEmprestimoError('')
    setEmprestimoSuccess('')

    try {
      await apiFetch('/api/v1/emprestimos', {
        method: 'POST',
        body: JSON.stringify({
          pessoa_id: emprestimoForm.pessoa_id,
          livro_id: emprestimoForm.livro_id,
        }),
      })

      setEmprestimoForm((current) => ({ ...current, livro_id: '' }))
      setEmprestimoSuccess('Empréstimo registrado com sucesso.')
      await Promise.all([loadLivros(), loadEmprestimos()])
    } catch (error) {
      setEmprestimoError(error instanceof Error ? error.message : 'Falha ao registrar empréstimo')
    }
  }

  async function handleReturnEmprestimo(emprestimoId: string) {
    setEmprestimoError('')
    setEmprestimoSuccess('')

    try {
      await apiFetch(`/api/v1/emprestimos/${emprestimoId}/devolver`, {
        method: 'PATCH',
      })

      setEmprestimoSuccess('Devolução registrada com sucesso.')
      await Promise.all([loadLivros(), loadEmprestimos()])
    } catch (error) {
      setEmprestimoError(error instanceof Error ? error.message : 'Falha ao devolver empréstimo')
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
            {isAuthenticated && userRole ? <p className="role-pill">Papel: {userRole}</p> : null}
            {isAuthenticated ? (
              <button type="button" className="ghost" onClick={handleLogout}>
                Sair
              </button>
            ) : null}
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

            <form className="card form" onSubmit={handleRegister}>
              <h2>Criar conta</h2>
              <label>
                Nome
                <input value={registerNome} onChange={(event) => setRegisterNome(event.target.value)} />
              </label>
              <label>
                Email
                <input
                  type="email"
                  value={registerEmail}
                  onChange={(event) => setRegisterEmail(event.target.value)}
                />
              </label>
              <label>
                Usuário
                <input
                  value={registerUsername}
                  onChange={(event) => setRegisterUsername(event.target.value)}
                />
              </label>
              <label>
                Senha
                <input
                  type="password"
                  value={registerSenha}
                  onChange={(event) => setRegisterSenha(event.target.value)}
                />
              </label>
              {registerError ? <p className="error">{registerError}</p> : null}
              {registerSuccess ? <p>{registerSuccess}</p> : null}
              <button type="submit">Cadastrar</button>

              {registerNeedsVerification ? (
                <>
                  <hr />
                  <h3>Validar código</h3>
                  <label>
                    Email
                    <input
                      type="email"
                      value={registerVerifyEmail}
                      onChange={(event) => setRegisterVerifyEmail(event.target.value)}
                    />
                  </label>
                  <label>
                    Código
                    <input
                      value={registerVerifyCode}
                      onChange={(event) => setRegisterVerifyCode(event.target.value)}
                    />
                  </label>
                  <button type="button" onClick={(event) => void handleRegisterVerify(event)}>
                    Confirmar código
                  </button>
                </>
              ) : null}
            </form>
          </section>
        ) : null}

        <section className="panel">
          <div className="section-head">
            <h2>Livros</h2>
            <button type="button" onClick={() => loadLivros().catch(() => undefined)}>
              Recarregar
            </button>
          </div>

          {isAuthenticated && canManageCatalog ? (
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
                  {isAuthenticated && canManageCatalog ? (
                    <button type="button" className="ghost" onClick={() => handleDeleteLivro(livro.id).catch(() => undefined)}>
                      Excluir
                    </button>
                  ) : null}
                </div>
              </article>
            ))}
          </div>
        </section>

        {isAuthenticated ? (
          <section className="panel">
            <div className="section-head">
              <h2>Empréstimos</h2>
              <button
                type="button"
                onClick={() => Promise.all([loadLivros(), loadPessoas(), loadEmprestimos()]).catch(() => undefined)}
              >
                Recarregar
              </button>
            </div>

            <div className="grid-two">
              {canManageLoans ? (
                <form className="card form" onSubmit={handleCreateEmprestimo}>
                  <h3>Novo empréstimo</h3>
                  {emprestimoError ? <p className="error">{emprestimoError}</p> : null}
                  {emprestimoSuccess ? <p>{emprestimoSuccess}</p> : null}

                  <label>
                    Pessoa
                    <select
                      value={emprestimoForm.pessoa_id}
                      onChange={(event) =>
                        setEmprestimoForm({ ...emprestimoForm, pessoa_id: event.target.value })
                      }
                    >
                      <option value="">Selecione uma pessoa</option>
                      {pessoas.map((pessoa) => (
                        <option key={pessoa.id} value={pessoa.id}>
                          {pessoa.nome} · {pessoa.email}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label>
                    Livro disponível
                    <select
                      value={emprestimoForm.livro_id}
                      onChange={(event) =>
                        setEmprestimoForm({ ...emprestimoForm, livro_id: event.target.value })
                      }
                    >
                      <option value="">Selecione um livro</option>
                      {livrosDisponiveis.map((livro) => (
                        <option key={livro.id} value={livro.id}>
                          {livro.titulo} · {livro.autor}
                        </option>
                      ))}
                    </select>
                  </label>

                  <button type="submit" disabled={pessoas.length === 0 || livrosDisponiveis.length === 0}>
                    Registrar empréstimo
                  </button>

                  {pessoaError ? <p className="error">{pessoaError}</p> : null}
                  {!loadingPessoas && pessoas.length === 0 ? (
                    <p className="help-text">Nenhuma pessoa disponível para vincular.</p>
                  ) : null}
                  {!loadingLivros && livrosDisponiveis.length === 0 ? (
                    <p className="help-text">Nenhum livro disponível para empréstimo.</p>
                  ) : null}
                </form>
              ) : (
                <div className="card form muted">
                  <h3>Seu histórico</h3>
                  <p className="help-text">
                    Como leitor, você pode consultar apenas os próprios empréstimos.
                  </p>
                </div>
              )}

              <div className="card form loan-list-card">
                <h3>Empréstimos registrados</h3>
                {emprestimoError ? <p className="error">{emprestimoError}</p> : null}
                {emprestimoSuccess ? <p>{emprestimoSuccess}</p> : null}
                {loadingEmprestimos ? <p>Carregando...</p> : null}
                {!loadingEmprestimos && emprestimos.length === 0 ? <p>Nenhum empréstimo encontrado.</p> : null}

                <div className="list compact">
                  {emprestimos.map((emprestimo) => {
                    const pessoa = pessoaById.get(emprestimo.pessoa_id)
                    const livro = livroById.get(emprestimo.livro_id)
                    const pessoaNome =
                      pessoa?.nome ??
                      (emprestimo.pessoa_id === user?.pessoa_id ? 'Você' : emprestimo.pessoa_id)

                    return (
                      <article className="card book loan" key={emprestimo.id}>
                        <div>
                          <h3>{livro?.titulo ?? emprestimo.livro_id}</h3>
                          <p>{pessoaNome}</p>
                          <small>
                            Empréstimo em {formatDate(emprestimo.data_emprestimo)} · Previsto em{' '}
                            {formatDate(emprestimo.data_devolucao_prevista)}
                          </small>
                        </div>
                        <div className="book-actions">
                          <span className={emprestimo.ativo ? 'pill available' : 'pill unavailable'}>
                            {emprestimo.ativo ? 'Ativo' : 'Devolvido'}
                          </span>
                          {canManageLoans && emprestimo.ativo ? (
                            <button
                              type="button"
                              className="ghost"
                              onClick={() => handleReturnEmprestimo(emprestimo.id).catch(() => undefined)}
                            >
                              Devolver
                            </button>
                          ) : null}
                        </div>
                      </article>
                    )
                  })}
                </div>
              </div>
            </div>
          </section>
        ) : null}
      </main>
    </div>
  )
}
