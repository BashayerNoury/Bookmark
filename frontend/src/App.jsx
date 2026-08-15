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

function getInitialTheme() {
  const saved = localStorage.getItem('bookmark-theme')
  if (saved === 'light' || saved === 'dark') return saved
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
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

function BookChip({ book }) {
  return (
    <div className="book-chip">
      <div className="book-chip-cover" />
      <div>
        <p className="book-chip-title">{book.title}</p>
        <p className="book-chip-author">{book.author}</p>
        <p className="book-chip-meta">
          {Number(book.average_rating).toFixed(1)} ★
          {book.genres?.[0] ? ` · ${book.genres[0].name}` : ''}
        </p>
      </div>
    </div>
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

export default function App() {
  const [theme, setTheme] = useState(getInitialTheme)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const bottomRef = useRef(null)
  const textareaRef = useRef(null)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('bookmark-theme', theme)
  }, [theme])

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

  const send = useCallback(async (raw) => {
    const text = (raw ?? '').trim()
    if (!text || loading) return

    setError('')
    setInput('')
    const history = messages.map(({ role, content }) => ({ role, content }))
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
      setLoading(false)
      requestAnimationFrame(() => textareaRef.current?.focus())
    }
  }, [loading, messages])

  const newChat = () => {
    setMessages([])
    setError('')
    setInput('')
    textareaRef.current?.focus()
  }

  const empty = messages.length === 0 && !loading
  const firstUser = messages.find((m) => m.role === 'user')

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

        <div className="sidebar-section">
          <p className="sidebar-label">Today</p>
          {firstUser ? (
            <button type="button" className="chat-item active" onClick={() => {}}>
              {firstUser.content.slice(0, 42)}{firstUser.content.length > 42 ? '…' : ''}
            </button>
          ) : (
            <p className="sidebar-empty">No chats yet</p>
          )}
        </div>

        <div className="sidebar-foot">
          <button
            type="button"
            className="btn-ghost"
            onClick={() => setTheme((t) => (t === 'light' ? 'dark' : 'light'))}
          >
            {theme === 'light' ? <IconMoon /> : <IconSun />}
            {theme === 'light' ? 'Dark mode' : 'Light mode'}
          </button>
          <div className="account-pill">
            <span className="account-avatar">B</span>
            <span>Bookmark</span>
          </div>
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
          <button type="button" className="model-chip" aria-label="Model">
            Bookmark <span className="caret">▾</span>
          </button>
          <div className="topbar-spacer" />
          <button type="button" className="icon-btn mobile-new" onClick={newChat} aria-label="New chat">
            <IconNew />
          </button>
        </header>

        <div className="thread">
          {empty ? (
            <div className="empty-state">
              <div className="empty-hero">
                <div className="brand-mark">B</div>
                <h1>How can I help you today?</h1>
              </div>
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
              Bookmark can make mistakes. Recommendations are from its catalog.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
