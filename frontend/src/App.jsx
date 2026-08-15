import { useCallback, useEffect, useRef, useState } from 'react'
import api from './api'
import './index.css'

const STARTERS = [
  {
    title: 'Cozy fantasy',
    prompt: 'Recommend a cozy fantasy with found family vibes',
  },
  {
    title: 'Dark thriller',
    prompt: 'I want a dark psychological thriller with a twist',
  },
  {
    title: 'More like…',
    prompt: 'Books like Project Hail Mary — smart, fun, and adventurous',
  },
  {
    title: 'Short & thoughtful',
    prompt: 'Suggest something short, literary, and thoughtful',
  },
]

function getSystemTheme() {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function getInitialThemePreference() {
  const saved = localStorage.getItem('bookmark-theme')
  if (saved === 'light' || saved === 'dark' || saved === 'system') return saved
  return 'system'
}

function resolveTheme(preference) {
  return preference === 'system' ? getSystemTheme() : preference
}

function nextThemePreference(preference) {
  if (preference === 'system') return 'light'
  if (preference === 'light') return 'dark'
  return 'system'
}

function themeLabel(preference) {
  if (preference === 'system') return 'System'
  if (preference === 'light') return 'Light'
  return 'Dark'
}

const CHAPTERS_KEY = 'bookmark-chapters'

function loadChapters() {
  try {
    const raw = localStorage.getItem(CHAPTERS_KEY)
    const parsed = raw ? JSON.parse(raw) : []
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function saveChapters(chapters) {
  localStorage.setItem(CHAPTERS_KEY, JSON.stringify(chapters))
}

function chapterTitleFromMessages(messages) {
  const firstUser = messages.find((m) => m.role === 'user')
  if (!firstUser?.content) return 'Untitled chapter'
  const text = firstUser.content.trim()
  return text.length > 42 ? `${text.slice(0, 42)}…` : text
}

function formatReply(text) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g)
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i}>{part.slice(2, -2)}</strong>
    }
    return <span key={i}>{part}</span>
  })
}

function IconNew() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path d="M12 5v14M5 12h14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

function IconSend() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path d="M12 19V5M5 12l7-7 7 7" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function IconSun() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden>
      <circle cx="12" cy="12" r="4" stroke="currentColor" strokeWidth="1.8" />
      <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  )
}

function IconMoon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path d="M21 14.5A8.5 8.5 0 1 1 9.5 3a7 7 0 0 0 11.5 11.5z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
    </svg>
  )
}

function IconMenu() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path d="M4 7h16M4 12h16M4 17h16" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  )
}

function IconSystem() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden>
      <rect x="3" y="4" width="18" height="13" rx="2" stroke="currentColor" strokeWidth="1.8" />
      <path d="M8 20h8M12 17v3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  )
}

function IconPin({ filled = false }) {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M15 4.5 19.5 9l-3.2.8L12 14.1 9.9 12l4.3-4.3L15 4.5z"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinejoin="round"
        fill={filled ? 'currentColor' : 'none'}
      />
      <path d="m12 14.1-6.6 6.6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  )
}

function ThemeIcon({ preference }) {
  if (preference === 'system') return <IconSystem />
  if (preference === 'light') return <IconSun />
  return <IconMoon />
}

function getGoodreadsUrl(book) {
  const isbn = typeof book.isbn === 'string' ? book.isbn.trim() : ''
  if (isbn) {
    return `https://www.goodreads.com/search?q=${encodeURIComponent(isbn)}`
  }
  const q = [book.title, book.author].filter(Boolean).join(' ')
  return `https://www.goodreads.com/search?q=${encodeURIComponent(q)}`
}

function BookChip({ book }) {
  const [coverFailed, setCoverFailed] = useState(false)
  const showCover = Boolean(book.cover_url) && !coverFailed
  const fallbackColor = book.cover_color || 'var(--accent)'

  return (
    <a
      className="book-chip"
      href={getGoodreadsUrl(book)}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={`Open ${book.title} on Goodreads`}
    >
      {showCover ? (
        <img
          className="book-chip-cover"
          src={book.cover_url}
          alt=""
          onError={() => setCoverFailed(true)}
          onLoad={(e) => {
            // Open Library returns a 1×1 GIF for missing covers when default=false is omitted
            if (e.currentTarget.naturalWidth < 2) setCoverFailed(true)
          }}
        />
      ) : (
        <div className="book-chip-cover" style={{ background: fallbackColor }} />
      )}
      <div>
        <p className="book-chip-title">{book.title}</p>
        <p className="book-chip-author">{book.author}</p>
        <p className="book-chip-meta">
          {book.genres?.[0]?.name
            ? book.genres[0].name
            : book.tags?.[0]
              ? book.tags[0]
              : 'Open on Goodreads'}
        </p>
      </div>
    </a>
  )
}

function Message({ message }) {
  const isUser = message.role === 'user'
  return (
    <div className={`turn ${isUser ? 'turn-user' : 'turn-assistant'}`}>
      {!isUser && (
        <div className="turn-avatar" aria-hidden>B</div>
      )}
      <div className={`turn-body ${isUser ? 'bubble' : ''}`}>
        <div className="turn-text">
          {message.content.split('\n').map((line, idx) => (
            <p key={idx}>{line ? formatReply(line) : <br />}</p>
          ))}
        </div>
        {message.books?.length > 0 && (
          <div className="book-chips">
            {message.books.map((book) => (
              <BookChip key={book.id} book={book} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function Composer({ input, setInput, onSend, loading, textareaRef }) {
  const resize = () => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`
  }

  useEffect(() => {
    resize()
  }, [input])

  return (
    <form
      className="composer"
      onSubmit={(e) => {
        e.preventDefault()
        onSend(input)
      }}
    >
      <textarea
        ref={textareaRef}
        rows={1}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            onSend(input)
          }
        }}
        placeholder="Message Bookmark…"
        disabled={loading}
        aria-label="Message Bookmark"
      />
      <button
        type="submit"
        className="send"
        disabled={loading || !input.trim()}
        aria-label="Send message"
      >
        <IconSend />
      </button>
    </form>
  )
}

function AuthForm({ onAuthenticated }) {
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState({ username: '', password: '', passwordConfirm: '', email: '' })
  const [error, setError] = useState('')

  const submit = async (event) => {
    event.preventDefault()
    setError('')
    try {
      if (mode === 'signup') {
        await api.post('/auth/register/', {
          username: form.username,
          email: form.email,
          password: form.password,
          password_confirm: form.passwordConfirm,
        })
      }
      const { data } = await api.post('/auth/login/', {
        username: form.username,
        password: form.password,
      })
      localStorage.setItem('bookmark-access-token', data.access)
      localStorage.setItem('bookmark-refresh-token', data.refresh)
      const profile = await api.get('/auth/me/')
      onAuthenticated(profile.data)
    } catch (requestError) {
      const data = requestError.response?.data
      setError(typeof data === 'object' ? Object.values(data).flat().join(' ') : 'Could not sign you in.')
    }
  }

  return (
    <form className="auth-form" onSubmit={submit}>
      <h2>{mode === 'login' ? 'Sign in to personalize' : 'Create your account'}</h2>
      <p>Import Goodreads once and keep your reading taste across devices.</p>
      <input placeholder="Username" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} required />
      {mode === 'signup' && <input type="email" placeholder="Email (optional)" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />}
      <input type="password" placeholder="Password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required minLength="8" />
      {mode === 'signup' && <input type="password" placeholder="Confirm password" value={form.passwordConfirm} onChange={(e) => setForm({ ...form, passwordConfirm: e.target.value })} required minLength="8" />}
      {error && <p className="form-error">{error}</p>}
      <button className="auth-submit" type="submit">{mode === 'login' ? 'Sign in' : 'Create account'}</button>
      <button className="text-button" type="button" onClick={() => setMode(mode === 'login' ? 'signup' : 'login')}>
        {mode === 'login' ? 'Need an account? Sign up' : 'Already have an account? Sign in'}
      </button>
    </form>
  )
}

function GoodreadsOnboarding({ profile, onImported }) {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const upload = async () => {
    if (!file) return
    setLoading(true)
    setError('')
    try {
      const body = new FormData()
      body.append('file', file)
      const { data } = await api.post('/goodreads/import/', body)
      onImported(data)
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Could not import that file.')
    } finally {
      setLoading(false)
    }
  }

  if (profile) {
    return (
      <div className="goodreads-summary">
        <strong>Goodreads taste imported</strong>
        <span>{profile.imported_rows} books · {profile.favorite_authors?.slice(0, 2).map((item) => item.name).join(', ') || 'taste profile ready'}</span>
      </div>
    )
  }

  return (
    <section className="goodreads-onboarding">
      <p className="eyebrow">Make recommendations yours</p>
      <h2>Import your Goodreads history</h2>
      <p>In Goodreads, go to <strong>My Books → Import and Export → Export Library</strong>. Download the CSV, then upload it here.</p>
      <div className="upload-row">
        <label className="file-input">
          <input type="file" accept=".csv,text/csv" onChange={(e) => setFile(e.target.files?.[0] || null)} />
          {file ? file.name : 'Choose Goodreads CSV'}
        </label>
        <button type="button" className="upload-button" disabled={!file || loading} onClick={upload}>
          {loading ? 'Importing…' : 'Import'}
        </button>
      </div>
      {error && <p className="form-error">{error}</p>}
      <small>Your raw CSV is read once and not stored.</small>
    </section>
  )
}

export default function App() {
  const [themePreference, setThemePreference] = useState(getInitialThemePreference)
  const [resolvedTheme, setResolvedTheme] = useState(() => resolveTheme(getInitialThemePreference()))
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [chapters, setChapters] = useState(loadChapters)
  const [activeChapterId, setActiveChapterId] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [user, setUser] = useState(null)
  const [goodreadsProfile, setGoodreadsProfile] = useState(null)
  const [showAuth, setShowAuth] = useState(false)
  const [showImport, setShowImport] = useState(false)
  const bottomRef = useRef(null)
  const textareaRef = useRef(null)
  const sendingRef = useRef(false)
  const messagesRef = useRef(messages)
  messagesRef.current = messages

  useEffect(() => {
    localStorage.setItem('bookmark-theme', themePreference)
    const apply = () => {
      const next = resolveTheme(themePreference)
      setResolvedTheme(next)
      document.documentElement.setAttribute('data-theme', next)
    }
    apply()

    if (themePreference !== 'system') return undefined
    const media = window.matchMedia('(prefers-color-scheme: dark)')
    const onChange = () => apply()
    media.addEventListener('change', onChange)
    return () => media.removeEventListener('change', onChange)
  }, [themePreference])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, loading])

  useEffect(() => {
    const onResize = () => {
      if (window.innerWidth < 900) setSidebarOpen(false)
      else setSidebarOpen(true)
    }
    onResize()
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])

  useEffect(() => {
    if (!localStorage.getItem('bookmark-access-token')) return
    Promise.all([api.get('/auth/me/'), api.get('/goodreads/import/')])
      .then(([profileResponse, importResponse]) => {
        setUser(profileResponse.data)
        setGoodreadsProfile(importResponse.data.profile || null)
      })
      .catch(() => {
        localStorage.removeItem('bookmark-access-token')
        localStorage.removeItem('bookmark-refresh-token')
      })
  }, [])

  useEffect(() => {
    if (loading) return
    if (messages.length === 0) return

    setActiveChapterId((currentId) => {
      const id = currentId || crypto.randomUUID()
      setChapters((prev) => {
        const existing = prev.find((c) => c.id === id)
        const nextChapter = {
          id,
          title: chapterTitleFromMessages(messages),
          pinned: existing?.pinned || false,
          messages,
          updatedAt: Date.now(),
        }
        const rest = prev.filter((c) => c.id !== id)
        const next = [nextChapter, ...rest].sort((a, b) => {
          if (a.pinned !== b.pinned) return a.pinned ? -1 : 1
          return b.updatedAt - a.updatedAt
        })
        saveChapters(next)
        return next
      })
      return id
    })
  }, [messages, loading])

  const send = useCallback(async (raw) => {
    const text = (raw ?? '').trim()
    if (!text || sendingRef.current) return
    sendingRef.current = true

    setError('')
    setInput('')
    const history = messagesRef.current.map(({ role, content }) => ({ role, content }))
    const userMsg = { id: crypto.randomUUID(), role: 'user', content: text }
    setMessages((prev) => [...prev, userMsg])
    setLoading(true)

    try {
      const { data } = await api.post('/chat/', {
        message: text,
        history,
        limit: 4,
      })
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: data.reply,
          books: data.books || [],
        },
      ])
    } catch {
      setError('Something went wrong. Check that the API is running.')
      setMessages((prev) => prev.filter((m) => m.id !== userMsg.id))
      setInput(text)
    } finally {
      sendingRef.current = false
      setLoading(false)
      requestAnimationFrame(() => textareaRef.current?.focus())
    }
  }, [])

  const newChat = () => {
    setActiveChapterId(null)
    setMessages([])
    setError('')
    setInput('')
    textareaRef.current?.focus()
  }

  const openChapter = (chapter) => {
    setActiveChapterId(chapter.id)
    setMessages(chapter.messages || [])
    setError('')
    setInput('')
    setShowImport(false)
    if (window.innerWidth < 900) setSidebarOpen(false)
  }

  const sortChapters = (list) =>
    [...list].sort((a, b) => {
      if (a.pinned !== b.pinned) return a.pinned ? -1 : 1
      return b.updatedAt - a.updatedAt
    })

  const togglePinActive = () => {
    if (!activeChapterId || messages.length === 0) return
    setChapters((prev) => {
      const next = sortChapters(
        prev.map((c) =>
          c.id === activeChapterId ? { ...c, pinned: !c.pinned, updatedAt: Date.now() } : c,
        ),
      )
      saveChapters(next)
      return next
    })
  }

  const togglePinChapter = (event, chapterId) => {
    event.stopPropagation()
    setChapters((prev) => {
      const next = sortChapters(
        prev.map((c) =>
          c.id === chapterId ? { ...c, pinned: !c.pinned, updatedAt: Date.now() } : c,
        ),
      )
      saveChapters(next)
      return next
    })
  }

  const empty = messages.length === 0 && !loading
  const activeChapter = chapters.find((c) => c.id === activeChapterId)
  const isPinned = Boolean(activeChapter?.pinned)
  const pinnedChapters = chapters.filter((c) => c.pinned)
  const recentChapters = chapters.filter((c) => !c.pinned)

  return (
    <div className={`chat-app ${sidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
      {sidebarOpen && (
        <button
          type="button"
          className="sidebar-backdrop"
          aria-label="Close sidebar"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-head">
          <button type="button" className="btn-new" onClick={newChat}>
            <IconNew />
            New chat
          </button>
        </div>

        <div className="sidebar-scroll">
          <div className="sidebar-section">
            <p className="sidebar-label">Bookmarks</p>
            {pinnedChapters.length === 0 ? (
              <p className="sidebar-empty">Pin a chat to keep it</p>
            ) : (
              pinnedChapters.map((chapter) => (
                <div
                  key={chapter.id}
                  className={`chat-item ${chapter.id === activeChapterId ? 'active' : ''}`}
                >
                  <button
                    type="button"
                    className="chat-item-open"
                    onClick={() => openChapter(chapter)}
                  >
                    {chapter.title}
                  </button>
                  <button
                    type="button"
                    className="chat-item-pin pinned"
                    aria-label="Unpin chapter"
                    onClick={(e) => togglePinChapter(e, chapter.id)}
                  >
                    <IconPin filled />
                  </button>
                </div>
              ))
            )}
          </div>

          <div className="sidebar-section">
            <p className="sidebar-label">Contents</p>
            {recentChapters.length === 0 ? (
              <p className="sidebar-empty">No chats yet</p>
            ) : (
              recentChapters.map((chapter) => (
                <div
                  key={chapter.id}
                  className={`chat-item ${chapter.id === activeChapterId ? 'active' : ''}`}
                >
                  <button
                    type="button"
                    className="chat-item-open"
                    onClick={() => openChapter(chapter)}
                  >
                    {chapter.title}
                  </button>
                  <button
                    type="button"
                    className="chat-item-pin"
                    aria-label="Pin chapter"
                    onClick={(e) => togglePinChapter(e, chapter.id)}
                  >
                    <IconPin />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="sidebar-foot">
          {user ? (
            <>
              <button type="button" className="btn-ghost" onClick={() => setShowImport(true)}>
                Import Goodreads
              </button>
              <div className="account-pill">
                <span className="account-avatar">{(user.first_name || user.username)[0].toUpperCase()}</span>
                <span>{user.first_name || user.username}</span>
              </div>
            </>
          ) : (
            <button type="button" className="btn-ghost" onClick={() => setShowAuth(true)}>
              Sign in to import Goodreads
            </button>
          )}
          <button
            type="button"
            className="btn-ghost"
            onClick={() => setThemePreference((t) => nextThemePreference(t))}
            aria-label={`Theme: ${themeLabel(themePreference)}. Click to change.`}
            title={`Theme: ${themeLabel(themePreference)} (using ${resolvedTheme})`}
          >
            <ThemeIcon preference={themePreference} />
            {themeLabel(themePreference)}
          </button>
        </div>
      </aside>

      <div className="main">
        <header className="topbar">
          <button
            type="button"
            className="icon-btn"
            aria-label="Toggle sidebar"
            onClick={() => setSidebarOpen((v) => !v)}
          >
            <IconMenu />
          </button>
          <button type="button" className="model-chip" aria-label="Bookmark">
            Bookmark
          </button>
          <div className="topbar-spacer" />
          <button
            type="button"
            className={`icon-btn pin-btn ${isPinned ? 'pinned' : ''}`}
            onClick={togglePinActive}
            disabled={!activeChapterId || messages.length === 0}
            aria-label={isPinned ? 'Unpin this chapter' : 'Pin this chapter'}
            title={isPinned ? 'Unpin chapter bookmark' : 'Pin chapter bookmark'}
          >
            <IconPin filled={isPinned} />
          </button>
          <button type="button" className="icon-btn mobile-new" onClick={newChat} aria-label="New chat">
            <IconNew />
          </button>
        </header>

        <div className="thread">
          {showImport && user ? (
            <div className="import-screen">
              <GoodreadsOnboarding
                profile={null}
                onImported={(data) => {
                  setGoodreadsProfile(data.profile)
                  setShowImport(false)
                }}
              />
            </div>
          ) : empty ? (
            <div className="empty-state">
              <div className="empty-hero">
                <div className="brand-mark">B</div>
                <p className="chapter-label">Chapter 1</p>
                <h1>How can I help you today?</h1>
              </div>
              {user ? (
                <GoodreadsOnboarding
                  profile={goodreadsProfile}
                  onImported={(data) => {
                    setGoodreadsProfile(data.profile)
                    setShowImport(false)
                  }}
                />
              ) : (
                <button type="button" className="goodreads-signin" onClick={() => setShowAuth(true)}>
                  Sign in to import Goodreads and personalize your picks
                </button>
              )}
              <div className="starter-grid">
                {STARTERS.map((item) => (
                  <button
                    key={item.title}
                    type="button"
                    className="starter-card"
                    onClick={() => send(item.prompt)}
                  >
                    <span className="starter-title">{item.title}</span>
                    <span className="starter-prompt">{item.prompt}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="turns">
              {messages.map((m) => (
                <Message key={m.id} message={m} />
              ))}
              {loading && (
                <div className="turn turn-assistant">
                  <div className="turn-avatar" aria-hidden>B</div>
                  <div className="turn-body">
                    <div className="thinking">
                      <span /><span /><span />
                    </div>
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        <div className="dock">
          <div className="dock-inner">
            {error && <p className="error-banner">{error}</p>}
            <Composer
              input={input}
              setInput={setInput}
              onSend={send}
              loading={loading}
              textareaRef={textareaRef}
            />
            <p className="fineprint">
              Powered by Google Gemini + Open Library. Cards open on Goodreads.
            </p>
          </div>
        </div>
      </div>
      {showAuth && (
        <div className="auth-overlay">
          <button className="auth-backdrop" type="button" aria-label="Close" onClick={() => setShowAuth(false)} />
          <div className="auth-modal">
            <button className="modal-close" type="button" onClick={() => setShowAuth(false)}>×</button>
            <AuthForm onAuthenticated={(profile) => { setUser(profile); setShowAuth(false) }} />
          </div>
        </div>
      )}
    </div>
  )
}
