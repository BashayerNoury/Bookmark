import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'

export default function LoginPage() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  if (user) return <Navigate to="/" replace />

  const onSubmit = async (event) => {
    event.preventDefault()
    setError('')
    try {
      await login(username, password)
      navigate('/')
    } catch {
      setError('Invalid username or password.')
    }
  }

  return (
    <div className="page narrow">
      <form className="card auth-form" onSubmit={onSubmit}>
        <h1>Welcome back</h1>
        <p className="muted">Log in to sync your shelf and get taste-aware recommendations.</p>
        <label>
          Username
          <input value={username} onChange={(e) => setUsername(e.target.value)} required autoComplete="username" />
        </label>
        <label>
          Password
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required autoComplete="current-password" />
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit" className="btn primary">Log in</button>
        <p className="muted">No account? <Link to="/register">Sign up</Link></p>
      </form>
    </div>
  )
}
