import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { departmentsApi, orgsApi, projectsApi, usersApi } from '../api'
import ApiHint from '../components/ApiHint'
import { EmptyState, ErrorBanner, Modal } from '../components/ui'
import { useAuth } from '../context/AuthContext'

export default function Projects() {
  const { user } = useAuth()
  const [projects, setProjects] = useState([])
  const [departments, setDepartments] = useState([])
  const [usersList, setUsersList] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ name: '', description: '', department: '', member_ids: [] })
  const [busy, setBusy] = useState(false)

  const canCreate = ['SUPERADMIN', 'ORG_ADMIN', 'PM', 'ADMIN'].includes(user?.role)

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await projectsApi.list()
      setProjects(Array.isArray(data) ? data : data.results || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const openCreateModal = async () => {
    setShowCreate(true)
    setError('')
    try {
      // Fetch orgs -> departments and users list for assignment
      const [orgsData, usersData] = await Promise.all([
        orgsApi.list(),
        usersApi.list(),
      ])
      const orgList = Array.isArray(orgsData) ? orgsData : orgsData.results || []
      const uList = Array.isArray(usersData) ? usersData : usersData.results || []
      setUsersList(uList)

      let allDepts = []
      for (const org of orgList) {
        try {
          const dData = await departmentsApi.list(org.id)
          const dList = Array.isArray(dData) ? dData : dData.results || []
          allDepts = [...allDepts, ...dList.map(d => ({ ...d, orgName: org.name }))]
        } catch (e) {
          // ignore
        }
      }
      setDepartments(allDepts)
      if (allDepts.length > 0) {
        setForm(f => ({ ...f, department: String(allDepts[0].id) }))
      }
    } catch (err) {
      setError(err.message)
    }
  }

  const create = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      const payload = {
        name: form.name,
        description: form.description,
        department: Number(form.department),
        member_ids: form.member_ids.map(Number),
      }
      await projectsApi.create(payload)
      setShowCreate(false)
      setForm({ name: '', description: '', department: '', member_ids: [] })
      await load()
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
          <h1>Projects</h1>
          <p className="muted">
            Select a project to open its board
            <ApiHint method="GET" path="/api/projects/" />
          </p>
        </div>
        {canCreate && (
          <button type="button" className="btn btn-primary" onClick={openCreateModal}>
            Create project
            <ApiHint method="POST" path="/api/projects/" />
          </button>
        )}
      </div>

      <ErrorBanner message={error} onDismiss={() => setError('')} />

      {loading ? (
        <p className="muted">Loading projects…</p>
      ) : projects.length === 0 ? (
        <EmptyState title="No projects yet" subtitle="Create a project to get started." />
      ) : (
        <div className="project-grid">
          {projects.map((p) => (
            <Link key={p.id} to={`/projects/${p.id}/board`} className="project-card">
              <div className="project-card-top">
                <span className="project-icon">{p.name.slice(0, 1).toUpperCase()}</span>
                <div>
                  <div className="project-name">{p.name}</div>
                  <div className="muted small">
                    Owner: {p.owner?.email || '—'} · {p.task_count ?? 0} issues ·{' '}
                    {p.member_count ?? 0} members
                  </div>
                </div>
              </div>
              <p className="project-desc">{p.description || 'No description'}</p>
            </Link>
          ))}
        </div>
      )}

      {showCreate && (
        <Modal title="Create project" onClose={() => setShowCreate(false)}>
          <form onSubmit={create} className="stack">
            <label className="field">
              <span>Name</span>
              <input
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                required
              />
            </label>

            <label className="field">
              <span>Department</span>
              <select
                value={form.department}
                onChange={(e) => setForm((f) => ({ ...f, department: e.target.value }))}
                required
              >
                <option value="">Select a department...</option>
                {departments.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name} ({d.orgName || 'Org'})
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>Description</span>
              <textarea
                rows={3}
                value={form.description}
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              />
            </label>

            <div className="field">
              <span>Assign Team Members</span>
              <div style={{ maxHeight: '120px', overflowY: 'auto', border: '1px solid var(--border)', borderRadius: '3px', padding: '8px', background: '#fff' }}>
                {usersList.length === 0 ? (
                  <span className="muted">No users found</span>
                ) : (
                  usersList.map((u) => {
                    const isChecked = form.member_ids.includes(u.id)
                    return (
                      <label key={u.id} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '4px 0', cursor: 'pointer', fontWeight: 'normal' }}>
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={(e) => {
                            const checked = e.target.checked
                            setForm((f) => {
                              const newIds = checked
                                ? [...f.member_ids, u.id]
                                : f.member_ids.filter((id) => id !== u.id)
                              return { ...f, member_ids: newIds }
                            })
                          }}
                        />
                        <span>{u.email} ({u.role})</span>
                      </label>
                    )
                  })
                )}
              </div>
            </div>

            <div className="row end">
              <button type="button" className="btn" onClick={() => setShowCreate(false)}>
                Cancel
              </button>
              <button type="submit" className="btn btn-primary" disabled={busy}>
                Create
                <ApiHint method="POST" path="/api/projects/" />
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}
