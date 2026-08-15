import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'

export default function RegisterPage() {
  const { user, register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    username: '',
    email: '',
    first_name: '',
    password: '',
    password_confirm: '',
  })
  const [error, setError] = useState('')

  if (user) return <Navigate to="/" replace />

  const set = (key) => (e) => setForm((prev) => ({ ...prev, [key]: e.target.value }))

  const onSubmit = async (event) => {
    event.preventDefault()
    setError('')
    try {
      await register(form)
      navigate('/')
    } catch (err) {
      const data = err.response?.data
      setError(typeof data === 'object' ? Object.values(data).flat().join(' ') : 'Registration failed.')
    }
  }

  return (
    <div className="page narrow">
      <form className="card auth-form" onSubmit={onSubmit}>
        <h1>Create your Bookmark</h1>
        <p className="muted">Save books, rate them, and unlock personalized AI picks.</p>
        <label>
          Username
          <input value={form.username} onChange={set('username')} required />
        </label>
        <label>
          First name
          <input value={form.first_name} onChange={set('first_name')} />
        </label>
        <label>
          Email
          <input type="email" value={form.email} onChange={set('email')} />
        </label>
        <label>
          Password
          <input type="password" value={form.password} onChange={set('password')} required minLength={8} />
        </label>
        <label>
          Confirm password
          <input type="password" value={form.password_confirm} onChange={set('password_confirm')} required minLength={8} />
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit" className="btn primary">Sign up</button>
        <p className="muted">Already have an account? <Link to="/login">Log in</Link></p>
      </form>
    </div>
  )
}
