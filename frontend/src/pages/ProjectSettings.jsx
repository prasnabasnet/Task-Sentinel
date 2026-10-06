import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { projectsApi, usersApi } from '../api'
import ApiHint from '../components/ApiHint'
import { ErrorBanner, Modal } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { useProjectSocket } from '../hooks/useProjectSocket'

export default function ProjectSettings() {
  const { user } = useAuth()
  const { projectId } = useParams()
  const navigate = useNavigate()

  useEffect(() => {
    if (user?.role === 'TM') {
      navigate(`/projects/${projectId}/board`, { replace: true })
    }
  }, [user, projectId, navigate])

  if (user?.role === 'TM') return null

  const [project, setProject] = useState(null)
  const [members, setMembers] = useState([])
  const [form, setForm] = useState({ name: '', description: '' })
  const [orgUsers, setOrgUsers] = useState([])
  const [selectedEmail, setSelectedEmail] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)

  const load = useCallback(async () => {
    setError('')
    try {
      const [proj, memberList, userList] = await Promise.all([
        projectsApi.get(projectId),
        projectsApi.listMembers(projectId),
        usersApi.list(),
      ])
      setProject(proj)
      setForm({ name: proj.name, description: proj.description || '' })
      const existingMembers = Array.isArray(memberList) ? memberList : memberList.results || []
      setMembers(existingMembers)
      const allOrgUsers = Array.isArray(userList) ? userList : userList.results || []
      setOrgUsers(allOrgUsers)
      const existingEmails = new Set(existingMembers.map((m) => m.email))
      const available = allOrgUsers.filter((u) => !existingEmails.has(u.email))
      if (available.length > 0) {
        setSelectedEmail(available[0].email)
      } else {
        setSelectedEmail('')
      }
    } catch (err) {
      setError(err.message)
    }
  }, [projectId])

  useProjectSocket(projectId, useCallback((data) => {
    if (data && ['member_added', 'member_removed', 'project_updated'].includes(data.type)) {
      load()
    }
  }, [load]))

  useEffect(() => {
    load()
  }, [load])

  const save = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await projectsApi.update(projectId, form)
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const addMember = async (e) => {
    e.preventDefault()
    if (!selectedEmail) return
    setBusy(true)
    setError('')
    try {
      await projectsApi.addMember(projectId, selectedEmail)
      setSelectedEmail('')
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }


  const removeMember = async (uid) => {
    setBusy(true)
    try {
      await projectsApi.removeMember(projectId, uid)
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const removeProject = async () => {
    setBusy(true)
    try {
      await projectsApi.remove(projectId)
      navigate('/')
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={() => navigate(`/projects/${projectId}/board`)}
          >
            ← Board
          </button>
          <h1>Project settings</h1>
          <p className="muted">
            {project?.name}
            <ApiHint method="GET" path={`/api/projects/${projectId}/`} />
          </p>
        </div>
      </div>

      <ErrorBanner message={error} onDismiss={() => setError('')} />

      <div className="settings-grid">
        <section className="panel">
          <h2>Details</h2>
          <form onSubmit={save} className="stack">
            <label className="field">
              <span>Name</span>
              <input
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                required
              />
            </label>
            <label className="field">
              <span>Description</span>
              <textarea
                rows={3}
                value={form.description}
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              />
            </label>
            <button type="submit" className="btn btn-primary" disabled={busy}>
              Save
              <ApiHint method="PATCH" path={`/api/projects/${projectId}/`} />
            </button>
          </form>
        </section>

        <section className="panel">
          <h2>
            People
            <ApiHint method="GET" path={`/api/projects/${projectId}/members/`} />
          </h2>
          <ul className="member-list">
            {members.map((m) => (
              <li key={m.user_id}>
                <div>
                  <strong>{m.email}</strong>
                  <div className="muted small">{m.role}</div>
                </div>
                <button
                  type="button"
                  className="btn btn-ghost btn-sm danger"
                  onClick={() => removeMember(m.user_id)}
                >
                  Remove
                  <ApiHint
                    method="DELETE"
                    path={`/api/projects/${projectId}/members/${m.user_id}/`}
                  />
                </button>
              </li>
            ))}
          </ul>

          <form onSubmit={addMember} className="row">
            <select
              value={selectedEmail}
              onChange={(e) => setSelectedEmail(e.target.value)}
              required
              style={{ flex: 1 }}
            >
              <option value="">Select a team member...</option>
              {orgUsers
                .filter((u) => !members.some((m) => m.email === u.email))
                .map((u) => (
                  <option key={u.id} value={u.email}>
                    {u.email} ({u.role})
                  </option>
                ))}
            </select>
            <button type="submit" className="btn btn-primary" disabled={busy || !selectedEmail}>
              Add member
              <ApiHint method="POST" path={`/api/projects/${projectId}/members/`} />
            </button>
          </form>
        </section>

        <section className="panel danger-zone">
          <h2>Danger zone</h2>
          <p className="muted">Delete this project and all of its issues permanently.</p>
          <button type="button" className="btn btn-danger" onClick={() => setConfirmDelete(true)}>
            Delete project
            <ApiHint method="DELETE" path={`/api/projects/${projectId}/`} />
          </button>
        </section>
      </div>

      {confirmDelete && (
        <Modal title="Delete project?" onClose={() => setConfirmDelete(false)}>
          <p>This cannot be undone.</p>
          <div className="row end">
            <button type="button" className="btn" onClick={() => setConfirmDelete(false)}>
              Cancel
            </button>
            <button type="button" className="btn btn-danger" disabled={busy} onClick={removeProject}>
              Delete
            </button>
          </div>
        </Modal>
      )}
    </div>
  )
}
