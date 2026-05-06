import { useEffect, useMemo, useState } from 'react'

const API_BASE_URL = 'http://localhost:8000'

type Papel = 'admin' | 'atendente' | 'leitor'

type Livro = {
  id: string
  titulo: string
  autor: string
  isbn: string
  ano_publicacao: number | null
  disponivel: boolean
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

type Usuario = {
  id: string
  username: string
  pessoa_id: string
  papel: Papel
}

type TokenResponse = {
  access_token: string
  token_type: string
}

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

type PaginatedResponse<T> = {
  items: T[]
  total: number
  page: number
  page_size: number
}

type TabKey = 'livros' | 'emprestimos' | 'leitores'

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

  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers })

  if (!response.ok) {
    const error = await response.json().catch(() => null)
    throw new Error(error?.error?.message ?? error?.detail ?? 'Erro inesperado')
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

function TabButton({ active, children, onClick }: { active: boolean; children: string; onClick: () => void }) {
  return (
    <button type="button" className={active ? 'tab active' : 'tab'} onClick={onClick}>
      {children}
    </button>
  )
}

export function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('bb_token'))
  const [user, setUser] = useState<UserResponse | null>(null)
  const [authError, setAuthError] = useState('')
  const [username, setUsername] = useState('')
  const [senha, setSenha] = useState('')

  const [registerNome, setRegisterNome] = useState('')
  const [registerEmail, setRegisterEmail] = useState('')
  const [registerUsername, setRegisterUsername] = useState('')
  const [registerSenha, setRegisterSenha] = useState('')
  const [registerVerifyEmail, setRegisterVerifyEmail] = useState('')
  const [registerVerifyCode, setRegisterVerifyCode] = useState('')
  const [registerError, setRegisterError] = useState('')
  const [registerSuccess, setRegisterSuccess] = useState('')
  const [registerNeedsVerification, setRegisterNeedsVerification] = useState(false)

  const [livros, setLivros] = useState<Livro[]>([])
  const [pessoas, setPessoas] = useState<Pessoa[]>([])
  const [emprestimos, setEmprestimos] = useState<Emprestimo[]>([])
  const [usuarios, setUsuarios] = useState<Usuario[]>([])

  const [loadingLivros, setLoadingLivros] = useState(false)
  const [loadingPessoas, setLoadingPessoas] = useState(false)
  const [loadingEmprestimos, setLoadingEmprestimos] = useState(false)
  const [loadingUsuarios, setLoadingUsuarios] = useState(false)

  const [livroError, setLivroError] = useState('')
  const [pessoaError, setPessoaError] = useState('')
  const [emprestimoError, setEmprestimoError] = useState('')
  const [emprestimoSuccess, setEmprestimoSuccess] = useState('')
  const [leitorError, setLeitorError] = useState('')
  const [leitorSuccess, setLeitorSuccess] = useState('')
  const [leitorSearch, setLeitorSearch] = useState('')
  const [livroSearch, setLivroSearch] = useState('')
  const [emprestimoSearch, setEmprestimoSearch] = useState('')

  const [submittingLeitor, setSubmittingLeitor] = useState(false)

  const [livroForm, setLivroForm] = useState({ titulo: '', autor: '', isbn: '', ano_publicacao: '', disponivel: true })
  const [emprestimoForm, setEmprestimoForm] = useState({ pessoa_id: '', livro_id: '' })
  const [leitorForm, setLeitorForm] = useState({
    nome: '',
    email: '',
    criarUsuario: false,
    username: '',
    senha: '',
    papel: 'leitor' as Papel,
    ativo: true,
  })

  const [activeTab, setActiveTab] = useState<TabKey>('livros')

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
  const canManageCatalog = useMemo(() => userRole === 'admin' || userRole === 'atendente', [userRole])
  const canManageLoans = useMemo(() => userRole === 'admin' || userRole === 'atendente', [userRole])
  const canViewReaders = useMemo(() => userRole === 'admin' || userRole === 'atendente', [userRole])
  const canManageUsers = useMemo(() => userRole === 'admin', [userRole])
  const livrosDisponiveis = useMemo(() => livros.filter((livro) => livro.disponivel), [livros])
  const livroById = useMemo(() => new Map(livros.map((livro) => [livro.id, livro])), [livros])
  const pessoaById = useMemo(() => new Map(pessoas.map((pessoa) => [pessoa.id, pessoa])), [pessoas])
  const usuariosByPessoaId = useMemo(() => new Map(usuarios.map((usuario) => [usuario.pessoa_id, usuario])), [usuarios])
  const filteredPessoas = useMemo(() => {
    const normalizedSearch = leitorSearch.trim().toLowerCase()

    if (!normalizedSearch) {
      return pessoas
    }

    return pessoas.filter((pessoa) => {
      const usuario = usuariosByPessoaId.get(pessoa.id)
      return (
        pessoa.nome.toLowerCase().includes(normalizedSearch) ||
        pessoa.email.toLowerCase().includes(normalizedSearch) ||
        usuario?.username.toLowerCase().includes(normalizedSearch) ||
        usuario?.papel.toLowerCase().includes(normalizedSearch)
      )
    })
  }, [leitorSearch, pessoas, usuariosByPessoaId])

  const filteredLivros = useMemo(() => {
    const normalizedSearch = livroSearch.trim().toLowerCase()

    if (!normalizedSearch) {
      return livros
    }

    return livros.filter((livro) => {
      return (
        livro.titulo.toLowerCase().includes(normalizedSearch) ||
        livro.autor.toLowerCase().includes(normalizedSearch) ||
        livro.isbn.toLowerCase().includes(normalizedSearch)
      )
    })
  }, [livroSearch, livros])

  const filteredEmprestimos = useMemo(() => {
    const normalizedSearch = emprestimoSearch.trim().toLowerCase()

    if (!normalizedSearch) {
      return emprestimos
    }

    return emprestimos.filter((emprestimo) => {
      const pessoa = pessoaById.get(emprestimo.pessoa_id)
      const livro = livroById.get(emprestimo.livro_id)
      return (
        pessoa?.nome.toLowerCase().includes(normalizedSearch) ||
        pessoa?.email.toLowerCase().includes(normalizedSearch) ||
        livro?.titulo.toLowerCase().includes(normalizedSearch) ||
        livro?.autor.toLowerCase().includes(normalizedSearch)
      )
    })
  }, [emprestimoSearch, emprestimos, pessoaById, livroById])

  const availableTabs = useMemo<TabKey[]>(() => {
    const tabs: TabKey[] = ['livros', 'emprestimos']
    if (isAuthenticated && canViewReaders) {
      tabs.push('leitores')
    }
    return tabs
  }, [canManageCatalog, canViewReaders, isAuthenticated])

  useEffect(() => {
    if (!availableTabs.includes(activeTab)) {
      setActiveTab(availableTabs[0])
    }
  }, [activeTab, availableTabs])

  useEffect(() => {
    const tasks = [loadLivros(), loadEmprestimos()]

    if (!isAuthenticated) {
      setPessoas([])
      setUsuarios([])
      setEmprestimoForm({ pessoa_id: '', livro_id: '' })
      setLeitorForm({
        nome: '',
        email: '',
        criarUsuario: false,
        username: '',
        senha: '',
        papel: 'leitor',
        ativo: true,
      })
      Promise.all(tasks).catch(() => undefined)
      return
    }

    if (canManageLoans) {
      tasks.push(loadPessoas())
    }

    if (canViewReaders) {
      tasks.push(loadUsuarios())
    }

    Promise.all(tasks).catch(() => undefined)
  }, [canManageLoans, canViewReaders, isAuthenticated])

  useEffect(() => {
    if (!isAuthenticated || !canManageLoans) {
      return
    }

    if (pessoas.length > 0 && !pessoaById.has(emprestimoForm.pessoa_id)) {
      setEmprestimoForm((current) => ({ ...current, pessoa_id: pessoas[0].id }))
    }

    if (livrosDisponiveis.length > 0 && !livrosDisponiveis.some((livro) => livro.id === emprestimoForm.livro_id)) {
      setEmprestimoForm((current) => ({ ...current, livro_id: livrosDisponiveis[0].id }))
    }
  }, [canManageLoans, emprestimoForm.livro_id, emprestimoForm.pessoa_id, isAuthenticated, livrosDisponiveis, pessoaById, pessoas])

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

  async function loadUsuarios() {
    setLoadingUsuarios(true)
    setLeitorError('')
    try {
      const response = await apiFetch<PaginatedResponse<Usuario>>('/api/v1/usuarios?page_size=100')
      setUsuarios(response.items)
    } catch (error) {
      setLeitorError(error instanceof Error ? error.message : 'Falha ao carregar usuários')
    } finally {
      setLoadingUsuarios(false)
    }
  }

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
        setRegisterSuccess(response.verification_code ? `${response.message} Código (dev): ${response.verification_code}` : response.message)
        return
      }

      setRegisterNeedsVerification(false)
      setRegisterVerifyEmail('')
      setRegisterVerifyCode('')
      setRegisterNome('')
      setRegisterEmail('')
      setRegisterUsername('')
      setRegisterSenha('')
      setUsername(registerUsername)
      setSenha(registerSenha)
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
        body: JSON.stringify({ email: registerVerifyEmail, code: registerVerifyCode }),
      })

      setRegisterNeedsVerification(false)
      setRegisterVerifyCode('')
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
        body: JSON.stringify({ pessoa_id: emprestimoForm.pessoa_id, livro_id: emprestimoForm.livro_id }),
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
      await apiFetch(`/api/v1/emprestimos/${emprestimoId}/devolver`, { method: 'PATCH' })
      setEmprestimoSuccess('Devolução registrada com sucesso.')
      await Promise.all([loadLivros(), loadEmprestimos()])
    } catch (error) {
      setEmprestimoError(error instanceof Error ? error.message : 'Falha ao devolver empréstimo')
    }
  }

  async function handleCreateLeitor(event: React.FormEvent) {
    event.preventDefault()
    setLeitorError('')
    setLeitorSuccess('')

  if (submittingLeitor) return
  setSubmittingLeitor(true)

    const nome = leitorForm.nome.trim()
    const email = leitorForm.email.trim()
    const username = leitorForm.username.trim()

    if (!nome || !email) {
      setLeitorError('Informe nome e email para criar o leitor.')
      return
    }

    if (leitorForm.criarUsuario && (!username || !leitorForm.senha.trim())) {
      setLeitorError('Informe username e senha para criar a conta do leitor.')
      return
    }

    try {
      const pessoa = await apiFetch<Pessoa>('/api/v1/pessoas', {
        method: 'POST',
        body: JSON.stringify({
          nome,
          email,
        }),
      })

      if (leitorForm.criarUsuario) {
        await apiFetch('/api/v1/usuarios', {
          method: 'POST',
          body: JSON.stringify({
            pessoa_id: pessoa.id,
            username,
            senha: leitorForm.senha.trim(),
            papel: userRole === 'atendente' ? 'leitor' : leitorForm.papel,
            ativo: leitorForm.ativo,
          }),
        })
      }

      setLeitorForm({
        nome: '',
        email: '',
        criarUsuario: false,
        username: '',
        senha: '',
        papel: 'leitor',
        ativo: true,
      })
      setLeitorSuccess(leitorForm.criarUsuario ? 'Leitor e conta criados com sucesso.' : 'Leitor criado com sucesso.')
      await Promise.all([loadPessoas(), loadUsuarios()])
    } catch (error) {
      setLeitorError(error instanceof Error ? error.message : 'Falha ao criar leitor')
    } finally {
      setSubmittingLeitor(false)
    }
  }

  function renderBooksSection() {
    return (
      <section className="panel">
        <div className="section-head">
          <h2>Livros</h2>
          <button type="button" onClick={() => loadLivros().catch(() => undefined)}>
            Recarregar
          </button>
        </div>

        {canManageCatalog ? (
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
              <input type="checkbox" checked={livroForm.disponivel} onChange={(event) => setLivroForm({ ...livroForm, disponivel: event.target.checked })} />
              Disponível
            </label>
            <button type="submit">Criar livro</button>
          </form>
        ) : null}

        <label className="card form grid-compact">
          <span>Pesquisar livro</span>
          <input
            value={livroSearch}
            onChange={(event) => setLivroSearch(event.target.value)}
            placeholder="Buscar por título, autor ou ISBN"
          />
        </label>

        <div className="list">
          {loadingLivros ? <p>Carregando...</p> : null}
          {!loadingLivros && filteredLivros.length === 0 ? <p>Nenhum livro encontrado.</p> : null}
          {filteredLivros.map((livro) => (
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
                {canManageCatalog ? (
                  <button type="button" className="ghost" onClick={() => handleDeleteLivro(livro.id).catch(() => undefined)}>
                    Excluir
                  </button>
                ) : null}
              </div>
            </article>
          ))}
        </div>
      </section>
    )
  }

  function renderLoansSection() {
    return (
      <section className="panel">
        <div className="section-head">
          <h2>Empréstimos</h2>
          <button type="button" onClick={() => Promise.all([loadLivros(), loadPessoas(), loadEmprestimos()]).catch(() => undefined)}>
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
                <select value={emprestimoForm.pessoa_id} onChange={(event) => setEmprestimoForm({ ...emprestimoForm, pessoa_id: event.target.value })}>
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
                <select value={emprestimoForm.livro_id} onChange={(event) => setEmprestimoForm({ ...emprestimoForm, livro_id: event.target.value })}>
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
              {!loadingPessoas && pessoas.length === 0 ? <p className="help-text">Nenhuma pessoa disponível para vincular.</p> : null}
              {!loadingLivros && livrosDisponiveis.length === 0 ? <p className="help-text">Nenhum livro disponível para empréstimo.</p> : null}
            </form>
          ) : (
            <div className="card form muted">
              <h3>Seu histórico</h3>
              <p className="help-text">Como leitor, você pode consultar apenas os próprios empréstimos.</p>
            </div>
          )}

          <div className="card form loan-list-card">
            <h3>Empréstimos registrados</h3>
            {emprestimoError ? <p className="error">{emprestimoError}</p> : null}
            {emprestimoSuccess ? <p>{emprestimoSuccess}</p> : null}
            <label className="grid-compact">
              <span>Pesquisar empréstimo</span>
              <input
                value={emprestimoSearch}
                onChange={(event) => setEmprestimoSearch(event.target.value)}
                placeholder="Buscar por pessoa, livro ou autor"
              />
            </label>
            {loadingEmprestimos ? <p>Carregando...</p> : null}
            {!loadingEmprestimos && filteredEmprestimos.length === 0 ? <p>Nenhum empréstimo encontrado.</p> : null}
            <div className="list compact">
              {filteredEmprestimos.map((emprestimo) => {
                const pessoa = pessoaById.get(emprestimo.pessoa_id)
                const livro = livroById.get(emprestimo.livro_id)
                const pessoaNome = pessoa?.nome ?? (emprestimo.pessoa_id === user?.pessoa_id ? 'Você' : emprestimo.pessoa_id)

                return (
                  <article className="card book loan" key={emprestimo.id}>
                    <div>
                      <h3>{livro?.titulo ?? emprestimo.livro_id}</h3>
                      <p>{pessoaNome}</p>
                      <small>
                        Empréstimo em {formatDate(emprestimo.data_emprestimo)} · Previsto em {formatDate(emprestimo.data_devolucao_prevista)}
                      </small>
                    </div>
                    <div className="book-actions">
                      <span className={emprestimo.ativo ? 'pill available' : 'pill unavailable'}>
                        {emprestimo.ativo ? 'Ativo' : 'Devolvido'}
                      </span>
                      {canManageLoans && emprestimo.ativo ? (
                        <button type="button" className="ghost" onClick={() => handleReturnEmprestimo(emprestimo.id).catch(() => undefined)}>
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
    )
  }

  function renderReadersSection() {
    if (!canViewReaders) {
      return null
    }

    return (
      <section className="panel">
        <div className="section-head">
          <h2>Leitores</h2>
          <button type="button" onClick={() => Promise.all([loadPessoas(), loadUsuarios()]).catch(() => undefined)}>
            Recarregar
          </button>
        </div>

        <form className="card form grid-compact" onSubmit={handleCreateLeitor}>
          <h3>Novo leitor</h3>
          {leitorError ? <p className="error">{leitorError}</p> : null}
          {leitorSuccess ? <p>{leitorSuccess}</p> : null}
          <label>
            Nome
            <input value={leitorForm.nome} onChange={(event) => setLeitorForm({ ...leitorForm, nome: event.target.value })} />
          </label>
          <label>
            Email
            <input type="email" value={leitorForm.email} onChange={(event) => setLeitorForm({ ...leitorForm, email: event.target.value })} />
          </label>
          <label className="checkbox">
            <input
              type="checkbox"
              checked={leitorForm.criarUsuario}
              onChange={(event) => setLeitorForm({ ...leitorForm, criarUsuario: event.target.checked })}
            />
            Criar usuário
          </label>
          {leitorForm.criarUsuario ? (
            <>
              <label>
                Username
                <input value={leitorForm.username} onChange={(event) => setLeitorForm({ ...leitorForm, username: event.target.value })} />
              </label>
              <label>
                Senha
                <input type="password" value={leitorForm.senha} onChange={(event) => setLeitorForm({ ...leitorForm, senha: event.target.value })} />
              </label>
              <label>
                Papel
                {userRole === 'atendente' ? (
                  <select value="leitor" disabled>
                    <option value="leitor">leitor</option>
                  </select>
                ) : (
                  <select value={leitorForm.papel} onChange={(event) => setLeitorForm({ ...leitorForm, papel: event.target.value as Papel })}>
                    <option value="leitor">leitor</option>
                    <option value="atendente">atendente</option>
                    <option value="admin">admin</option>
                  </select>
                )}
              </label>
              <label className="checkbox">
                <input
                  type="checkbox"
                  checked={leitorForm.ativo}
                  onChange={(event) => setLeitorForm({ ...leitorForm, ativo: event.target.checked })}
                />
                Ativo
              </label>
            </>
          ) : null}
          <button type="submit">Criar leitor</button>
        </form>

        <label className="card form grid-compact">
          <span>Pesquisar leitor</span>
          <input
            value={leitorSearch}
            onChange={(event) => setLeitorSearch(event.target.value)}
            placeholder="Buscar por nome, email, username ou papel"
          />
        </label>

        <div className="list">
          {loadingPessoas ? <p>Carregando leitores...</p> : null}
          {!loadingPessoas && filteredPessoas.length === 0 ? <p>Nenhum leitor encontrado.</p> : null}
          {filteredPessoas.map((pessoa) => {
            const usuario = usuariosByPessoaId.get(pessoa.id)

            return (
              <article className="card book" key={pessoa.id}>
                <div>
                  <h3>{pessoa.nome}</h3>
                  <p>{pessoa.email}</p>
                  <small>{usuario ? `Conta: ${usuario.username} · Papel: ${usuario.papel}` : 'Sem conta vinculada'}</small>
                </div>
              </article>
            )
          })}
        </div>
      </section>
    )
  }

  return (
    <div className="shell">
      <main className="app">
        <section className="hero">
          <div>
            <p className="eyebrow">Boa Biblioteca</p>
            <h1>Catálogo operacional com foco no fluxo.</h1>
            <p className="lead">Login JWT, catálogo público e áreas protegidas para admin já integradas à API.</p>
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
                <input type="email" value={registerEmail} onChange={(event) => setRegisterEmail(event.target.value)} />
              </label>
              <label>
                Usuário
                <input value={registerUsername} onChange={(event) => setRegisterUsername(event.target.value)} />
              </label>
              <label>
                Senha
                <input type="password" value={registerSenha} onChange={(event) => setRegisterSenha(event.target.value)} />
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
                    <input type="email" value={registerVerifyEmail} onChange={(event) => setRegisterVerifyEmail(event.target.value)} />
                  </label>
                  <label>
                    Código
                    <input value={registerVerifyCode} onChange={(event) => setRegisterVerifyCode(event.target.value)} />
                  </label>
                  <button type="button" onClick={(event) => void handleRegisterVerify(event)}>
                    Confirmar código
                  </button>
                </>
              ) : null}
            </form>
          </section>
        ) : null}

        {isAuthenticated ? (
          <section className="panel tabs-panel">
            <div className="tabs" role="tablist" aria-label="Seções da biblioteca">
              <TabButton active={activeTab === 'livros'} onClick={() => setActiveTab('livros')}>
                Livros
              </TabButton>
              <TabButton active={activeTab === 'emprestimos'} onClick={() => setActiveTab('emprestimos')}>
                Empréstimos
              </TabButton>
              {canViewReaders ? (
                <TabButton active={activeTab === 'leitores'} onClick={() => setActiveTab('leitores')}>
                  Leitores
                </TabButton>
              ) : null}
            </div>

            {activeTab === 'livros' ? renderBooksSection() : null}
            {activeTab === 'emprestimos' ? renderLoansSection() : null}
            {activeTab === 'leitores' ? renderReadersSection() : null}
          </section>
        ) : (
          renderBooksSection()
        )}
      </main>
    </div>
  )
}