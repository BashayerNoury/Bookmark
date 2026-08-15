import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api'
import { useAuth } from '../AuthContext'
import BookCard from '../components/BookCard'

const MOODS = ['cozy', 'dark', 'adventurous', 'romantic', 'thoughtful', 'thrilling', 'funny', 'inspiring']

export default function RecommendPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [mood, setMood] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [busyId, setBusyId] = useState(null)

  const run = async (event) => {
    event?.preventDefault()
    setLoading(true)
    setError('')
    try {
      const { data } = await api.post('/recommend/', { query, mood, limit: 6 })
      setResult(data)
    } catch {
      setError('Recommendation service failed. Try again.')
    } finally {
      setLoading(false)
    }
  }

  const toggleBookmark = async (book) => {
    if (!user) return navigate('/login')
    setBusyId(book.id)
    try {
      const { data } = await api.post('/bookmarks/toggle/', { book_id: book.id })
      setResult((prev) => ({
        ...prev,
        books: prev.books.map((b) =>
          b.id === book.id ? { ...b, is_bookmarked: data.bookmarked } : b,
        ),
      }))
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div className="page">
      <section className="hero compact">
        <div>
          <p className="eyebrow">Personal recommender</p>
          <h1>AI picks for your next chapter</h1>
          <p className="lede">
            Describe what you want to read. Bookmark scores the catalog against your query,
            mood, and shelf history{user ? '' : ' (sign in for taste-aware picks)'}.
          </p>
        </div>
      </section>

      <form className="recommend-form card" onSubmit={run}>
        <label>
          What are you in the mood for?
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. space survival with humor, quiet literary fiction…"
          />
        </label>
        <div className="mood-row">
          <span>Mood</span>
          <div className="filters">
            <button type="button" className={`chip ${!mood ? 'active' : ''}`} onClick={() => setMood('')}>Any</button>
            {MOODS.map((m) => (
              <button
                key={m}
                type="button"
                className={`chip ${mood === m ? 'active' : ''}`}
                onClick={() => setMood(m)}
              >
                {m}
              </button>
            ))}
          </div>
        </div>
        <button type="submit" className="btn primary" disabled={loading}>
          {loading ? 'Thinking…' : 'Recommend books'}
        </button>
      </form>

      {error && <p className="banner error">{error}</p>}

      {result && (
        <section className="recommend-results">
          <div className="explain card">
            <h2>Why these?</h2>
            <p>{result.explanation}</p>
          </div>
          <div className="book-grid">
            {result.books.map((book) => (
              <BookCard
                key={book.id}
                book={book}
                onToggleBookmark={toggleBookmark}
                busy={busyId === book.id}
              />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
