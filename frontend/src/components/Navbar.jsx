import { NavLink, Link } from 'react-router-dom'
import { useAuth } from '../AuthContext'

export default function Navbar() {
  const { user, logout } = useAuth()

  return (
    <header className="nav">
      <div className="nav-inner">
        <Link to="/" className="brand">
          <span className="brand-mark" aria-hidden>📚</span>
          Bookmark
        </Link>
        <nav className="nav-links">
          <NavLink to="/">Discover</NavLink>
          <NavLink to="/recommend">AI Picks</NavLink>
          {user && <NavLink to="/shelf">My Shelf</NavLink>}
        </nav>
        <div className="nav-auth">
          {user ? (
            <>
              <span className="nav-user">Hi, {user.first_name || user.username}</span>
              <button type="button" className="btn ghost" onClick={logout}>Log out</button>
            </>
          ) : (
            <>
              <Link className="btn ghost" to="/login">Log in</Link>
              <Link className="btn primary" to="/register">Sign up</Link>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
