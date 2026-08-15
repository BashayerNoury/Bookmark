import { useCallback, useEffect, useRef, useState } from 'react'
import api from './api'
import './index.css'

const SUGGESTIONS = [
  'Cozy fantasy with found family',
  'Dark psychological thriller',
  'Books like Project Hail Mary',
  'Something short and thoughtful',
  'Funny mystery for a rainy day',
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

function BookChip({ book }) {
  return (
    <div className="book-chip">
      <div className="book-chip-cover" />
      <div className="book-chip-body">
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
    <div className={`msg ${isUser ? 'user' : 'assistant'}`}>
      <div className="msg-avatar" aria-hidden>
        {isUser ? 'You' : 'B'}
      </div>
      <div className="msg-content">
        <div className="msg-text">
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

export default function App() {
  const [theme, setTheme] = useState(getInitialTheme)
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
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'))
  }

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
      setError('Something went wrong. Is the API running on port 8000?')
      setMessages((prev) => prev.filter((m) => m.id !== userMsg.id))
      setInput(text)
    } finally {
      setLoading(false)
      textareaRef.current?.focus()
    }
  }, [loading, messages])

  const onKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      send(input)
    }
  }

  const newChat = () => {
    setMessages([])
    setError('')
    setInput('')
    textareaRef.current?.focus()
  }

  const empty = messages.length === 0 && !loading

  return (
    <div className="chat-app">
      <aside className="sidebar">
        <div className="sidebar-top">
          <div className="logo">
            <span className="logo-mark">B</span>
            <span>Bookmark</span>
          </div>
          <button type="button" className="new-chat" onClick={newChat}>
            + New chat
          </button>
        </div>
        <p className="sidebar-note">AI book recommendations</p>
        <div className="sidebar-footer">
          <button type="button" className="theme-toggle" onClick={toggleTheme}>
            {theme === 'light' ? 'Dark mode' : 'Light mode'}
          </button>
        </div>
      </aside>

      <div className="chat-main">
        <header className="chat-topbar">
          <span className="model-name">Bookmark</span>
          <div className="topbar-actions">
            <button type="button" className="theme-toggle mobile-only" onClick={toggleTheme}>
              {theme === 'light' ? 'Dark' : 'Light'}
            </button>
            <button type="button" className="new-chat mobile-only" onClick={newChat}>
              New chat
            </button>
          </div>
        </header>

        <div className="chat-scroll">
          {empty ? (
            <div className="welcome">
              <div className="welcome-logo">B</div>
              <h1>What are you in the mood to read?</h1>
              <p>Ask Bookmark for book recommendations.</p>
              <div className="suggestions">
                {SUGGESTIONS.map((s) => (
                  <button key={s} type="button" className="suggestion" onClick={() => send(s)}>
                    {s}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="messages">
              {messages.map((m) => (
                <Message key={m.id} message={m} />
              ))}
              {loading && (
                <div className="msg assistant">
                  <div className="msg-avatar" aria-hidden>B</div>
                  <div className="msg-content">
                    <div className="typing">
                      <span /><span /><span />
                    </div>
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        <div className="composer-wrap">
          {error && <p className="chat-error">{error}</p>}
          <form
            className="composer"
            onSubmit={(e) => {
              e.preventDefault()
              send(input)
            }}
          >
            <textarea
              ref={textareaRef}
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder="Message Bookmark…"
              disabled={loading}
            />
            <button type="submit" className="send" disabled={loading || !input.trim()} aria-label="Send">
              ↑
            </button>
          </form>
          <p className="disclaimer">Bookmark recommends from its catalog.</p>
        </div>
      </div>
    </div>
  )
}
