import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'
import { usersApi } from '../api'
import ApiHint from '../components/ApiHint'
import { EmptyState, ErrorBanner, Modal } from '../components/ui'
import { useAuth } from '../context/AuthContext'

export default function Users() {
  const { user } = useAuth()
  const [users, setUsers] = useState([])
  const [error, setError] = useState('')
  const [showOnboard, setShowOnboard] = useState(false)
  const [memberForm, setMemberForm] = useState({
    email: '',
    username: '',
    password: '',
    role: 'TM',
  })
  const [busy, setBusy] = useState(false)

  const isSuperOrOrgAdmin =
    user?.role === 'SUPERADMIN' || user?.role === 'ORG_ADMIN' || user?.role === 'ADMIN'

  const loadUsers = async () => {
    setError('')
    try {
      const data = await usersApi.list()
      setUsers(Array.isArray(data) ? data : data.results || [])
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => {
    if (isSuperOrOrgAdmin) {
      loadUsers()
    }
  }, [isSuperOrOrgAdmin])

  if (!isSuperOrOrgAdmin) return <Navigate to="/" replace />

  const changeRole = async (id, role) => {
    try {
      await usersApi.update(id, { role })
      await loadUsers()
    } catch (err) {
      setError(err.message)
    }
  }

  const deactivate = async (id) => {
    if (!confirm('Deactivate this user?')) return
    try {
      await usersApi.deactivate(id)
      await loadUsers()
    } catch (err) {
      setError(err.message)
    }
  }

  const onboardMember = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await usersApi.createMember(memberForm)
      setShowOnboard(false)
      setMemberForm({ email: '', username: '', password: '', role: 'TM' })
      await loadUsers()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Organization Members & Users</h1>
          <p className="muted">
            Manage organization team members and roles
            <ApiHint method="GET" path="/api/users/" />
          </p>
        </div>
        <button
          type="button"
          className="btn btn-primary"
          onClick={() => setShowOnboard(true)}
        >
          + Add Member
          <ApiHint method="POST" path="/api/users/members/" />
        </button>
      </div>

      <ErrorBanner message={error} onDismiss={() => setError('')} />

      {users.length === 0 ? (
        <EmptyState title="No users found" />
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Email</th>
              <th>Username</th>
              <th>Role</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td className="mono">{u.id}</td>
                <td>{u.email}</td>
                <td>{u.username}</td>
                <td>
                  <select
                    value={u.role}
                    onChange={(e) => changeRole(u.id, e.target.value)}
                    disabled={u.id === user.id}
                  >
                    {(user?.role === 'SUPERADMIN' || user?.is_superuser) && (
                      <option value="SUPERADMIN">SUPERADMIN</option>
                    )}
                    <option value="ORG_ADMIN">ORG_ADMIN</option>
                    <option value="PM">PM</option>
                    <option value="TM">TM</option>
                  </select>
                  <ApiHint method="PATCH" path={`/api/users/${u.id}/`} />
                </td>
                <td>
                  <button
                    type="button"
                    className="btn btn-ghost btn-sm danger"
                    disabled={u.id === user.id}
                    onClick={() => deactivate(u.id)}
                  >
                    Deactivate
                    <ApiHint method="DELETE" path={`/api/users/${u.id}/`} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {showOnboard && (
        <Modal title="Add Team Member" onClose={() => setShowOnboard(false)}>
          <form onSubmit={onboardMember} className="stack">
            <label className="field">
              <span>Email</span>
              <input
                type="email"
                value={memberForm.email}
                onChange={(e) => setMemberForm((f) => ({ ...f, email: e.target.value }))}
                required
              />
            </label>

            <label className="field">
              <span>Username</span>
              <input
                value={memberForm.username}
                onChange={(e) => setMemberForm((f) => ({ ...f, username: e.target.value }))}
                required
              />
            </label>

            <label className="field">
              <span>Password</span>
              <input
                type="password"
                value={memberForm.password}
                onChange={(e) => setMemberForm((f) => ({ ...f, password: e.target.value }))}
                required
                minLength={8}
              />
            </label>

            <label className="field">
              <span>Role</span>
              <select
                value={memberForm.role}
                onChange={(e) => setMemberForm((f) => ({ ...f, role: e.target.value }))}
              >
                <option value="PM">Project Manager (PM)</option>
                <option value="TM">Team Member (TM)</option>
              </select>
            </label>

            <div className="row end">
              <button type="button" className="btn" onClick={() => setShowOnboard(false)}>
                Cancel
              </button>
              <button type="submit" className="btn btn-primary" disabled={busy}>
                {busy ? 'Adding…' : 'Add Member'}
                <ApiHint method="POST" path="/api/users/members/" />
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}

