import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { projectsApi, tasksApi } from '../api'
import ApiHint from '../components/ApiHint'
import { ErrorBanner, Modal, PriorityBadge } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { useTaskSocket } from '../hooks/useProjectSocket'
import TaskDetail from './TaskDetail'

const COLUMNS = [
  { key: 'TODO', title: 'To Do' },
  { key: 'IN_PROGRESS', title: 'In Progress' },
  { key: 'DONE', title: 'Done' },
]

export default function Board() {
  const { user } = useAuth()
  const { projectId } = useParams()
  const navigate = useNavigate()
  const [project, setProject] = useState(null)

  const canCreateTask =
    ['SUPERADMIN', 'ORG_ADMIN', 'PM', 'ADMIN'].includes(user?.role) || (project && project.owner?.id === user?.id)
  const [tasks, setTasks] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [selectedTaskId, setSelectedTaskId] = useState(null)
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({
    title: '',
    description: '',
    priority: 'MEDIUM',
    status: 'TODO',
  })
  const [busy, setBusy] = useState(false)

  const handleTaskEvent = useCallback((event) => {
    if (!event) return
    const { action, task, task_id } = event

    if (action === 'created' && task) {
      setTasks((prev) => {
        if (prev.some((t) => String(t.id) === String(task.id))) return prev
        return [...prev, task]
      })
    } else if (action === 'updated' && task) {
      setTasks((prev) => {
        const exists = prev.some((t) => String(t.id) === String(task.id))
        if (exists) {
          return prev.map((t) => (String(t.id) === String(task.id) ? { ...t, ...task } : t))
        }
        return [...prev, task]
      })
    } else if (action === 'deleted' && (task_id != null || task?.id != null)) {
      const idToDelete = task_id != null ? task_id : task?.id
      setTasks((prev) => prev.filter((t) => String(t.id) !== String(idToDelete)))
    }
  }, [])

  useTaskSocket(projectId, handleTaskEvent)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const [proj, taskList] = await Promise.all([
        projectsApi.get(projectId),
        tasksApi.list({ project: projectId }),
      ])
      setProject(proj)
      setTasks(Array.isArray(taskList) ? taskList : taskList.results || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    load()
  }, [load])

  const moveTask = async (task, status) => {
    if (task.status === status) return
    const prev = tasks
    setTasks((list) => list.map((t) => (t.id === task.id ? { ...t, status } : t)))
    try {
      await tasksApi.update(task.id, { status })
    } catch (err) {
      setTasks(prev)
      setError(err.message)
    }
  }

  const createTask = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await tasksApi.create({ ...form, project: Number(projectId) })
      setShowCreate(false)
      setForm({ title: '', description: '', priority: 'MEDIUM', status: 'TODO' })
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const onDragStart = (e, taskId) => {
    e.dataTransfer.setData('text/task-id', String(taskId))
  }

  const onDrop = (e, status) => {
    e.preventDefault()
    const id = Number(e.dataTransfer.getData('text/task-id'))
    const task = tasks.find((t) => t.id === id)
    if (task) moveTask(task, status)
  }

  return (
    <div className="board-page">
      <div className="page-header">
        <div>
          <button type="button" className="btn btn-ghost btn-sm" onClick={() => navigate('/')}>
            ← Projects
          </button>
          <h1>{project?.name || 'Board'}</h1>
          <p className="muted">
            Drag issues between columns
            <ApiHint method="GET" path={`/api/tasks/?project=${projectId}`} />
            <ApiHint method="PATCH" path="/api/tasks/<id>/" note="Used when dragging cards" />
          </p>
        </div>
        <div className="row">
          <button
            type="button"
            className="btn"
            onClick={() => navigate(`/projects/${projectId}/backlog`)}
          >
            Backlog
          </button>
          {canCreateTask && (
            <button type="button" className="btn btn-primary" onClick={() => setShowCreate(true)}>
              Create issue
              <ApiHint method="POST" path="/api/tasks/" />
            </button>
          )}
        </div>
      </div>

      <ErrorBanner message={error} onDismiss={() => setError('')} />

      {loading ? (
        <p className="muted">Loading board…</p>
      ) : (
        <div className="board">
          {COLUMNS.map((col) => {
            const columnTasks = tasks.filter((t) => t.status === col.key)
            return (
              <div
                key={col.key}
                className="board-column"
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => onDrop(e, col.key)}
              >
                <div className="column-header">
                  <span>{col.title}</span>
                  <span className="count">{columnTasks.length}</span>
                </div>
                <div className="column-body">
                  {columnTasks.map((task) => (
                    <button
                      type="button"
                      key={task.id}
                      className="issue-card"
                      draggable
                      onDragStart={(e) => onDragStart(e, task.id)}
                      onClick={() => setSelectedTaskId(task.id)}
                    >
                      <div className="issue-key">TM-{task.id}</div>
                      <div className="issue-title">{task.title}</div>
                      <div className="issue-meta">
                        <PriorityBadge priority={task.priority} />
                        <div style={{ display: 'flex', gap: '2px' }}>
                          {task.assignees?.map((a) => (
                            <span key={a.id} className="assignee-chip" title={a.email}>
                              {(a.first_name?.[0] || a.email?.[0] || '?').toUpperCase()}
                            </span>
                          ))}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {showCreate && (
        <Modal title="Create issue" onClose={() => setShowCreate(false)}>
          <form onSubmit={createTask} className="stack">
            <label className="field">
              <span>Summary</span>
              <input
                value={form.title}
                onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
                required
              />
            </label>
            <label className="field">
              <span>Description</span>
              <textarea
                rows={4}
                value={form.description}
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
              />
            </label>
            <div className="row">
              <label className="field grow">
                <span>Priority</span>
                <select
                  value={form.priority}
                  onChange={(e) => setForm((f) => ({ ...f, priority: e.target.value }))}
                >
                  <option value="LOW">Low</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="HIGH">High</option>
                  <option value="CRITICAL">Critical</option>
                </select>
              </label>
              <label className="field grow">
                <span>Status</span>
                <select
                  value={form.status}
                  onChange={(e) => setForm((f) => ({ ...f, status: e.target.value }))}
                >
                  <option value="TODO">To Do</option>
                  <option value="IN_PROGRESS">In Progress</option>
                  <option value="DONE">Done</option>
                </select>
              </label>
            </div>
            <div className="row end">
              <button type="button" className="btn" onClick={() => setShowCreate(false)}>
                Cancel
              </button>
              <button type="submit" className="btn btn-primary" disabled={busy}>
                Create
                <ApiHint method="POST" path="/api/tasks/" />
              </button>
            </div>
          </form>
        </Modal>
      )}

      {selectedTaskId && (
        <TaskDetail
          taskId={selectedTaskId}
          onClose={() => setSelectedTaskId(null)}
          onChanged={load}
        />
      )}
    </div>
  )
}
