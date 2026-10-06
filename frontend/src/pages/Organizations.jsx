import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { departmentsApi, orgsApi } from '../api'
import ApiHint from '../components/ApiHint'
import { EmptyState, ErrorBanner, Modal } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import CommentsSection from '../components/CommentsSection'

export default function Organizations() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [orgs, setOrgs] = useState([])
  const [selected, setSelected] = useState(null)
  const [departments, setDepartments] = useState([])
  const [selectedDept, setSelectedDept] = useState(null)
  const [projects, setProjects] = useState([])
  const [error, setError] = useState('')
  const [showOrg, setShowOrg] = useState(false)
  const [showDept, setShowDept] = useState(false)
  const [showProject, setShowProject] = useState(false)
  const [orgForm, setOrgForm] = useState({ name: '', description: '' })
  const [deptForm, setDeptForm] = useState({ name: '', description: '' })
  const [projectForm, setProjectForm] = useState({ name: '', description: '' })
  const [busy, setBusy] = useState(false)

  const loadOrgs = async () => {
    setError('')
    try {
      const data = await orgsApi.list()
      const list = Array.isArray(data) ? data : data.results || []
      setOrgs(list)
      if (selected) {
        const refreshed = list.find((o) => o.id === selected.id)
        setSelected(refreshed || null)
      }
    } catch (err) {
      setError(err.message)
    }
  }

  const loadDepartments = async (org) => {
    if (!org) {
      setDepartments([])
      return
    }
    try {
      const data = await departmentsApi.list(org.id)
      setDepartments(Array.isArray(data) ? data : data.results || [])
    } catch (err) {
      setError(err.message)
    }
  }

  const loadProjects = async (dept) => {
    if (!dept || !selected) {
      setProjects([])
      return
    }
    try {
      const data = await departmentsApi.projects(selected.id, dept.id)
      setProjects(Array.isArray(data) ? data : data.results || [])
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => {
    loadOrgs()
  }, [])

  useEffect(() => {
    loadDepartments(selected)
    setSelectedDept(null)
  }, [selected?.id])

  useEffect(() => {
    loadProjects(selectedDept)
  }, [selectedDept?.id])

  const createOrg = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await orgsApi.create(orgForm)
      setShowOrg(false)
      setOrgForm({ name: '', description: '' })
      await loadOrgs()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const createDept = async (e) => {
    e.preventDefault()
    if (!selected) return
    setBusy(true)
    setError('')
    try {
      await departmentsApi.create(selected.id, deptForm)
      setShowDept(false)
      setDeptForm({ name: '', description: '' })
      await loadDepartments(selected)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const createProject = async (e) => {
    e.preventDefault()
    if (!selected || !selectedDept) return
    setBusy(true)
    setError('')
    try {
      await departmentsApi.createProject(selected.id, selectedDept.id, projectForm)
      setShowProject(false)
      setProjectForm({ name: '', description: '' })
      await loadProjects(selectedDept)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const deleteOrg = async (id) => {
    if (!confirm('Delete this organization?')) return
    try {
      await orgsApi.remove(id)
      if (selected?.id === id) setSelected(null)
      await loadOrgs()
    } catch (err) {
      setError(err.message)
    }
  }

  const deleteDept = async (id) => {
    if (!selected || !confirm('Delete this department?')) return
    try {
      await departmentsApi.remove(selected.id, id)
      await loadDepartments(selected)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Organizations</h1>
          <p className="muted">
            View orgs, departments, and projects
            <ApiHint method="GET" path="/api/organizations/" />
          </p>
        </div>
      </div>

      <ErrorBanner message={error} onDismiss={() => setError('')} />

      <div className="org-layout">
        <section className="panel">
          <h2>Organizations</h2>
          {orgs.length === 0 ? (
            <EmptyState title="No organizations" />
          ) : (
            <ul className="selectable-list">
              {orgs.map((o) => (
                <li key={o.id} className={selected?.id === o.id ? 'selected' : ''}>
                  <button type="button" className="list-main" onClick={() => setSelected(o)}>
                    <strong>{o.name}</strong>
                    <div className="muted small">{o.slug}</div>
                  </button>
                  {(user?.role === 'SUPERADMIN' || user?.is_superuser) && (
                    <button
                      type="button"
                      className="btn btn-ghost btn-sm danger"
                      onClick={() => deleteOrg(o.id)}
                    >
                      Delete
                      <ApiHint method="DELETE" path={`/api/organizations/${o.id}/`} />
                    </button>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="panel">
          {selected ? (
            <>
              {selectedDept ? (
              <>
                <div className="page-header compact">
                  <div>
                    <button
                      type="button"
                      className="btn btn-ghost btn-sm"
                      onClick={() => setSelectedDept(null)}
                      style={{ marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}
                    >
                      ← Back to Departments
                    </button>
                    <h2>{selectedDept.name}</h2>
                    <p className="muted">{selectedDept.description || 'No description'}</p>
                  </div>
                  <button type="button" className="btn btn-primary" onClick={() => setShowProject(true)}>
                    Add project
                    <ApiHint
                      method="POST"
                      path={`/api/organizations/${selected.id}/departments/${selectedDept.id}/projects/`}
                    />
                  </button>
                </div>

                <h3>
                  Projects
                  <ApiHint
                    method="GET"
                    path={`/api/organizations/${selected.id}/departments/${selectedDept.id}/projects/`}
                  />
                </h3>
                {projects.length === 0 ? (
                  <EmptyState title="No projects" subtitle="Create a project to start managing tasks." />
                ) : (
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Description</th>
                        <th />
                      </tr>
                    </thead>
                    <tbody>
                      {projects.map((p) => (
                        <tr key={p.id}>
                          <td>
                            <button
                              type="button"
                              className="btn btn-link"
                              onClick={() => navigate(`/projects/${p.id}/board`)}
                              style={{
                                background: 'none',
                                border: 'none',
                                padding: 0,
                                font: 'inherit',
                                color: 'var(--primary)',
                                cursor: 'pointer',
                                textAlign: 'left',
                                textDecoration: 'underline',
                              }}
                            >
                              <strong>{p.name}</strong>
                            </button>
                          </td>
                          <td>{p.description || <span className="muted">No description</span>}</td>
                          <td>
                            <button
                              type="button"
                              className="btn btn-ghost btn-sm"
                              onClick={() => navigate(`/projects/${p.id}/board`)}
                            >
                              Open Board
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
                <CommentsSection targetType="department" targetId={selectedDept.id} />
              </>
            ) : (
              <>
                <div className="page-header compact">
                  <div>
                    <h2>{selected.name}</h2>
                    <p className="muted">
                      {selected.description || 'No description'}
                      <ApiHint method="GET" path={`/api/organizations/${selected.id}/`} />
                    </p>
                  </div>
                  {['SUPERADMIN', 'ORG_ADMIN', 'ADMIN'].includes(user?.role) && (
                    <button type="button" className="btn btn-primary" onClick={() => setShowDept(true)}>
                      Add department
                      <ApiHint
                        method="POST"
                        path={`/api/organizations/${selected.id}/departments/`}
                      />
                    </button>
                  )}
                </div>

                <h3>
                  Departments
                  <ApiHint
                    method="GET"
                    path={`/api/organizations/${selected.id}/departments/`}
                  />
                </h3>
                {departments.length === 0 ? (
                  <EmptyState title="No departments" />
                ) : (
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Members</th>
                        <th>Projects</th>
                        <th />
                      </tr>
                    </thead>
                    <tbody>
                      {departments.map((d) => (
                        <tr key={d.id}>
                          <td>
                            <button
                              type="button"
                              className="btn btn-link"
                              onClick={() => setSelectedDept(d)}
                              style={{
                                background: 'none',
                                border: 'none',
                                padding: 0,
                                font: 'inherit',
                                color: 'var(--primary)',
                                cursor: 'pointer',
                                textAlign: 'left',
                                textDecoration: 'underline',
                              }}
                            >
                              <strong>{d.name}</strong>
                            </button>
                            <div className="muted small">{d.description}</div>
                          </td>
                          <td>{d.member_count ?? 0}</td>
                          <td>{d.project_count ?? 0}</td>
                          <td>
                            <button
                              type="button"
                              className="btn btn-ghost btn-sm danger"
                              onClick={() => deleteDept(d.id)}
                            >
                              Delete
                              <ApiHint
                                method="DELETE"
                                path={`/api/organizations/${selected.id}/departments/${d.id}/`}
                              />
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
                <CommentsSection targetType="organization" targetId={selected.id} />
              </>
            )}
          </>
          ) : (
            <EmptyState title="Select an organization" subtitle="Details and departments appear here." />
          )}
        </section>
      </div>

      {showOrg && (
        <Modal title="Create organization" onClose={() => setShowOrg(false)}>
          <form onSubmit={createOrg} className="stack">
            <label className="field">
              <span>Name</span>
              <input
                value={orgForm.name}
                onChange={(e) => setOrgForm((f) => ({ ...f, name: e.target.value }))}
                required
              />
            </label>
            <label className="field">
              <span>Description</span>
              <textarea
                rows={3}
                value={orgForm.description}
                onChange={(e) => setOrgForm((f) => ({ ...f, description: e.target.value }))}
              />
            </label>
            <div className="row end">
              <button type="button" className="btn" onClick={() => setShowOrg(false)}>
                Cancel
              </button>
              <button type="submit" className="btn btn-primary" disabled={busy}>
                Create
              </button>
            </div>
          </form>
        </Modal>
      )}

      {showDept && selected && (
        <Modal title="Create department" onClose={() => setShowDept(false)}>
          <form onSubmit={createDept} className="stack">
            <label className="field">
              <span>Name</span>
              <input
                value={deptForm.name}
                onChange={(e) => setDeptForm((f) => ({ ...f, name: e.target.value }))}
                required
              />
            </label>
            <label className="field">
              <span>Description</span>
              <textarea
                rows={3}
                value={deptForm.description}
                onChange={(e) => setDeptForm((f) => ({ ...f, description: e.target.value }))}
              />
            </label>
            <div className="row end">
              <button type="button" className="btn" onClick={() => setShowDept(false)}>
                Cancel
              </button>
              <button type="submit" className="btn btn-primary" disabled={busy}>
                Create
              </button>
            </div>
          </form>
        </Modal>
      )}

      {showProject && selected && selectedDept && (
        <Modal title="Create project" onClose={() => setShowProject(false)}>
          <form onSubmit={createProject} className="stack">
            <label className="field">
              <span>Name</span>
              <input
                value={projectForm.name}
                onChange={(e) => setProjectForm((f) => ({ ...f, name: e.target.value }))}
                required
              />
            </label>
            <label className="field">
              <span>Description</span>
              <textarea
                rows={3}
                value={projectForm.description}
                onChange={(e) => setProjectForm((f) => ({ ...f, description: e.target.value }))}
              />
            </label>
            <div className="row end">
              <button type="button" className="btn" onClick={() => setShowProject(false)}>
                Cancel
              </button>
              <button type="submit" className="btn btn-primary" disabled={busy}>
                Create
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}
