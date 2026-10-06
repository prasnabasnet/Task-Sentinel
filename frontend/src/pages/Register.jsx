import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import ApiHint from '../components/ApiHint'
import { ErrorBanner } from '../components/ui'

export default function Register() {
  const { user, register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', username: '', password: '', organization_name: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to="/" replace />

  const onChange = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }))

  const onSubmit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await register(form)
      navigate('/')
    } catch (err) {
      setError(err.message || 'Registration failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={onSubmit}>
        <div className="auth-brand">
          <span className="brand-mark">TM</span>
          <h1>Create Organization</h1>
          <p className="muted">Sign up as Organization Admin (ORG_ADMIN)</p>
        </div>

        <ErrorBanner message={error} onDismiss={() => setError('')} />

        <label className="field">
          <span>Organization Name</span>
          <input
            name="organization_name"
            value={form.organization_name}
            onChange={onChange}
            placeholder="e.g. Acme Corp"
            required
          />
        </label>

        <label className="field">
          <span>Email</span>
          <input name="email" type="email" value={form.email} onChange={onChange} required />
        </label>

        <label className="field">
          <span>Username</span>
          <input name="username" value={form.username} onChange={onChange} required />
        </label>

        <label className="field">
          <span>Password</span>
          <input
            name="password"
            type="password"
            value={form.password}
            onChange={onChange}
            required
            minLength={8}
          />
        </label>

        <button type="submit" className="btn btn-primary btn-block" disabled={busy}>
          {busy ? 'Creating…' : 'Create account'}
          <ApiHint method="POST" path="/api/users/auth/register/" />
        </button>

        <p className="auth-footer">
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </form>
    </div>
  )
}
