import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import api from '../api'
import { useAuth } from '../AuthContext'
import BookCard from '../components/BookCard'

export default function HomePage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const [books, setBooks] = useState([])
  const [genres, setGenres] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState(null)
  const [error, setError] = useState('')

  const q = searchParams.get('q') || ''
  const genre = searchParams.get('genre') || ''

  useEffect(() => {
    api.get('/genres/').then((res) => setGenres(res.data)).catch(() => {})
    api.get('/stats/').then((res) => setStats(res.data)).catch(() => {})
  }, [])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError('')
    const params = { ordering: '-average_rating' }
    if (q) params.search = q
    if (genre) params.genre = genre
    api
      .get('/books/', { params })
      .then((res) => {
        if (!cancelled) setBooks(res.data.results || res.data)
      })
      .catch(() => {
        if (!cancelled) setError('Could not load books. Is the API running?')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [q, genre])

  const onSearch = (event) => {
    event.preventDefault()
    const form = new FormData(event.target)
    const next = form.get('q')?.toString().trim() || ''
    const params = {}
    if (next) params.q = next
    if (genre) params.genre = genre
    setSearchParams(params)
  }

  const toggleBookmark = async (book) => {
    if (!user) {
      navigate('/login')
      return
    }
    setBusyId(book.id)
    try {
      const { data } = await api.post('/bookmarks/toggle/', { book_id: book.id })
      setBooks((prev) =>
        prev.map((b) => (b.id === book.id ? { ...b, is_bookmarked: data.bookmarked } : b)),
      )
    } catch {
      setError('Could not update bookmark.')
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div className="page">
      <section className="hero">
        <div>
          <p className="eyebrow">AI book recommendations</p>
          <h1>Find your next great read with Bookmark</h1>
          <p className="lede">
            Browse a curated catalog, save books to your shelf, and get personalized picks
            based on your taste and mood.
          </p>
          <form className="search-bar" onSubmit={onSearch}>
            <input name="q" defaultValue={q} placeholder="Search title, author, or vibe…" />
            <button type="submit" className="btn primary">Search</button>
          </form>
          {stats && (
            <p className="stats-line">
              {stats.books} books · {stats.genres} genres
              {stats.bookmarks != null ? ` · ${stats.bookmarks} on your shelf` : ''}
            </p>
          )}
        </div>
        <div className="hero-card">
          <h2>Try AI Picks</h2>
          <p>Tell Bookmark a mood or craving—“cozy fantasy”, “dark thriller”—and get smart matches.</p>
          <button type="button" className="btn primary" onClick={() => navigate('/recommend')}>
            Get recommendations
          </button>
        </div>
      </section>

      <div className="filters">
        <button
          type="button"
          className={`chip ${!genre ? 'active' : ''}`}
          onClick={() => {
            const params = {}
            if (q) params.q = q
            setSearchParams(params)
          }}
        >
          All
        </button>
        {genres.map((g) => (
          <button
            key={g.id}
            type="button"
            className={`chip ${genre === g.slug ? 'active' : ''}`}
            onClick={() => {
              const params = { genre: g.slug }
              if (q) params.q = q
              setSearchParams(params)
            }}
          >
            {g.name}
          </button>
        ))}
      </div>

      {error && <p className="banner error">{error}</p>}
      {loading ? (
        <p className="muted">Loading books…</p>
      ) : books.length === 0 ? (
        <p className="muted">No books matched that search.</p>
      ) : (
        <div className="book-grid">
          {books.map((book) => (
            <BookCard
              key={book.id}
              book={book}
              onToggleBookmark={toggleBookmark}
              busy={busyId === book.id}
            />
          ))}
        </div>
      )}
    </div>
  )
}
