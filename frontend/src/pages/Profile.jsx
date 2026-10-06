import { useEffect, useState } from 'react'
import { authApi } from '../api'
import { useAuth } from '../context/AuthContext'
import { ErrorBanner } from '../components/ui'
import ApiHint from '../components/ApiHint'

export default function Profile() {
  const { user, refresh } = useAuth()
  const [formData, setFormData] = useState({
    display_name: '',
    bio: '',
    avatar_url: '',
  })
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (user?.profile) {
      setFormData({
        display_name: user.profile.display_name || '',
        bio: user.profile.bio || '',
        avatar_url: user.profile.avatar_url || '',
      })
    }
  }, [user])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    setSuccess('')
    try {
      await authApi.updateProfile(formData)
      await refresh()
      setSuccess('Profile updated successfully!')
    } catch (err) {
      setError(err.message || 'Failed to update profile.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto', padding: '1rem' }}>
      <div className="page-header">
        <div>
          <h1>My Profile</h1>
          <p className="muted">
            Manage your personal profile details
            <ApiHint method="PATCH" path="/api/users/auth/me/" />
          </p>
        </div>
      </div>

      <ErrorBanner message={error} onDismiss={() => setError('')} />

      {success && (
        <div className="banner success" style={{ marginBottom: '1rem', padding: '0.75rem', borderRadius: '4px', backgroundColor: '#e6fffa', color: '#008b8b', border: '1px solid #b2f5ea' }}>
          {success}
        </div>
      )}

      <form onSubmit={handleSubmit} className="panel stack" style={{ padding: '2rem' }}>
        <div style={{ display: 'flex', gap: '1.5rem', marginBottom: '2rem', alignItems: 'center' }}>
          {formData.avatar_url ? (
            <img
              src={formData.avatar_url}
              alt="Avatar Preview"
              style={{ width: '80px', height: '80px', borderRadius: '50%', objectFit: 'cover', border: '2px solid var(--primary)' }}
            />
          ) : (
            <div style={{ width: '80px', height: '80px', borderRadius: '50%', backgroundColor: '#e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '2rem', color: 'var(--primary)', fontWeight: 'bold' }}>
              {(formData.display_name?.[0] || user?.username?.[0] || '?').toUpperCase()}
            </div>
          )}
          <div>
            <h3 style={{ margin: 0 }}>{user?.username}</h3>
            <span className="muted small">{user?.email} • {user?.role}</span>
          </div>
        </div>

        <label className="field">
          <span>Display Name</span>
          <input
            type="text"
            value={formData.display_name}
            onChange={(e) => setFormData((f) => ({ ...f, display_name: e.target.value }))}
            placeholder="e.g. John Doe"
          />
        </label>

        <label className="field">
          <span>Avatar Image URL</span>
          <input
            type="url"
            value={formData.avatar_url}
            onChange={(e) => setFormData((f) => ({ ...f, avatar_url: e.target.value }))}
            placeholder="https://example.com/avatar.jpg"
          />
        </label>


        <label className="field">
          <span>Bio</span>
          <textarea
            rows={4}
            value={formData.bio}
            onChange={(e) => setFormData((f) => ({ ...f, bio: e.target.value }))}
            placeholder="Tell us about yourself..."
            maxLength={500}
          />
        </label>

        <div className="row end" style={{ marginTop: '1rem' }}>
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </form>
    </div>
  )
}
