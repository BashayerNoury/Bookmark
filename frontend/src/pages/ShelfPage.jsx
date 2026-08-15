import { useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import api from '../api'
import { useAuth } from '../AuthContext'

const STATUSES = [
  { value: '', label: 'All' },
  { value: 'want', label: 'Want to read' },
  { value: 'reading', label: 'Reading' },
  { value: 'finished', label: 'Finished' },
]

export default function ShelfPage() {
  const { user, loading: authLoading } = useAuth()
  const [items, setItems] = useState([])
  const [status, setStatus] = useState('')
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    const params = status ? { status } : {}
    const { data } = await api.get('/bookmarks/', { params })
    setItems(data.results || data)
    setLoading(false)
  }

  useEffect(() => {
    if (user) load().catch(() => setLoading(false))
  }, [user, status])

  if (authLoading) return <p className="muted page">Loading…</p>
  if (!user) return <Navigate to="/login" replace />

  const updateStatus = async (id, nextStatus) => {
    await api.patch(`/bookmarks/${id}/`, { status: nextStatus })
    await load()
  }

  const remove = async (id) => {
    await api.delete(`/bookmarks/${id}/`)
    await load()
  }

  return (
    <div className="page">
      <section className="hero compact">
        <div>
          <p className="eyebrow">Your shelf</p>
          <h1>Books you’ve saved</h1>
          <p className="lede">Track what you want to read, what’s in progress, and what you’ve finished.</p>
        </div>
      </section>

      <div className="filters">
        {STATUSES.map((s) => (
          <button
            key={s.value || 'all'}
            type="button"
            className={`chip ${status === s.value ? 'active' : ''}`}
            onClick={() => setStatus(s.value)}
          >
            {s.label}
          </button>
        ))}
      </div>

      {loading ? (
        <p className="muted">Loading shelf…</p>
      ) : items.length === 0 ? (
        <div className="empty card">
          <p>Nothing here yet.</p>
          <Link className="btn primary" to="/">Discover books</Link>
        </div>
      ) : (
        <div className="shelf-list">
          {items.map((item) => (
            <article key={item.id} className="shelf-item card">
              <Link
                to={`/books/${item.book.id}`}
                className="shelf-cover"
                style={{ background: item.book.cover_color }}
              />
              <div className="shelf-body">
                <Link to={`/books/${item.book.id}`} className="book-title">{item.book.title}</Link>
                <p className="book-author">{item.book.author}</p>
                <div className="shelf-actions">
                  <select value={item.status} onChange={(e) => updateStatus(item.id, e.target.value)}>
                    <option value="want">Want to read</option>
                    <option value="reading">Reading</option>
                    <option value="finished">Finished</option>
                  </select>
                  <button type="button" className="btn ghost" onClick={() => remove(item.id)}>Remove</button>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  )
}
