import { Link } from 'react-router-dom'

function Stars({ rating }) {
  const full = Math.round(Number(rating) || 0)
  return (
    <span className="stars" title={`${rating} / 5`}>
      {'★'.repeat(Math.min(full, 5))}
      <span className="stars-empty">{'★'.repeat(Math.max(0, 5 - full))}</span>
    </span>
  )
}

export default function BookCard({ book, onToggleBookmark, busy }) {
  const genres = book.genres?.map((g) => g.name).join(' · ') || 'General'

  return (
    <article className="book-card">
      <Link to={`/books/${book.id}`} className="book-cover" style={{ background: book.cover_color }}>
        <span className="book-cover-title">{book.title}</span>
        <span className="book-cover-author">{book.author}</span>
      </Link>
      <div className="book-meta">
        <Link to={`/books/${book.id}`} className="book-title">{book.title}</Link>
        <p className="book-author">{book.author}</p>
        <p className="book-genres">{genres}</p>
        <div className="book-footer">
          <Stars rating={book.average_rating} />
          <span className="muted">{Number(book.average_rating).toFixed(1)}</span>
          {onToggleBookmark && (
            <button
              type="button"
              className={`btn icon ${book.is_bookmarked ? 'bookmarked' : ''}`}
              onClick={() => onToggleBookmark(book)}
              disabled={busy}
              aria-label={book.is_bookmarked ? 'Remove bookmark' : 'Add bookmark'}
              title={book.is_bookmarked ? 'Remove from shelf' : 'Save to shelf'}
            >
              {book.is_bookmarked ? '★' : '☆'}
            </button>
          )}
        </div>
      </div>
    </article>
  )
}
