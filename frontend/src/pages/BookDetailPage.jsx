import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import api from '../api'
import { useAuth } from '../AuthContext'

export default function BookDetailPage() {
  const { id } = useParams()
  const { user } = useAuth()
  const navigate = useNavigate()
  const [book, setBook] = useState(null)
  const [score, setScore] = useState(5)
  const [review, setReview] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const load = async () => {
    const { data } = await api.get(`/books/${id}/`)
    setBook(data)
    if (data.user_rating) {
      setScore(data.user_rating.score)
      setReview(data.user_rating.review || '')
    }
  }

  useEffect(() => {
    load().catch(() => setError('Book not found.'))
  }, [id])

  const toggle = async () => {
    if (!user) return navigate('/login')
    const { data } = await api.post('/bookmarks/toggle/', { book_id: book.id })
    setBook((prev) => ({
      ...prev,
      is_bookmarked: data.bookmarked,
      bookmark_status: data.bookmarked ? 'want' : null,
    }))
  }

  const saveRating = async (event) => {
    event.preventDefault()
    if (!user) return navigate('/login')
    try {
      await api.post('/ratings/', { book: book.id, score: Number(score), review })
      setMessage('Rating saved.')
      await load()
    } catch {
      setError('Could not save rating.')
    }
  }

  if (error && !book) return <p className="banner error">{error}</p>
  if (!book) return <p className="muted page">Loading…</p>

  return (
    <div className="page detail">
      <Link to="/" className="back">← Back to discover</Link>
      <div className="detail-layout">
        <div className="detail-cover" style={{ background: book.cover_color }}>
          <h1>{book.title}</h1>
          <p>{book.author}</p>
        </div>
        <div className="detail-body">
          <div className="detail-header">
            <div>
              <p className="eyebrow">{book.genres?.map((g) => g.name).join(' · ')}</p>
              <h1>{book.title}</h1>
              <p className="book-author">by {book.author}</p>
            </div>
            <button type="button" className={`btn ${book.is_bookmarked ? 'primary' : 'ghost'}`} onClick={toggle}>
              {book.is_bookmarked ? '★ On your shelf' : '☆ Save to shelf'}
            </button>
          </div>
          <p className="lede">{book.description}</p>
          <dl className="facts">
            <div><dt>Rating</dt><dd>{Number(book.average_rating).toFixed(1)} ({book.ratings_count})</dd></div>
            <div><dt>Published</dt><dd>{book.published_year || '—'}</dd></div>
            <div><dt>Pages</dt><dd>{book.page_count || '—'}</dd></div>
          </dl>
          {book.tags?.length > 0 && (
            <div className="filters">
              {book.tags.map((tag) => (
                <span key={tag} className="chip">{tag}</span>
              ))}
            </div>
          )}

          <form className="rating-form card" onSubmit={saveRating}>
            <h3>Your rating</h3>
            <label>
              Score
              <select value={score} onChange={(e) => setScore(e.target.value)}>
                {[5, 4, 3, 2, 1].map((n) => (
                  <option key={n} value={n}>{n} stars</option>
                ))}
              </select>
            </label>
            <label>
              Review
              <textarea value={review} onChange={(e) => setReview(e.target.value)} rows={3} placeholder="What stood out?" />
            </label>
            <button type="submit" className="btn primary">Save rating</button>
            {message && <p className="success">{message}</p>}
            {error && <p className="error">{error}</p>}
          </form>
        </div>
      </div>
    </div>
  )
}
