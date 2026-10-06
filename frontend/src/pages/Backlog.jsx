import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { projectsApi, tasksApi } from '../api'
import ApiHint from '../components/ApiHint'
import { EmptyState, ErrorBanner, PriorityBadge, StatusBadge } from '../components/ui'
import { useTaskSocket } from '../hooks/useProjectSocket'
import TaskDetail from './TaskDetail'

export default function Backlog() {
  const { projectId } = useParams()
  const navigate = useNavigate()
  const [project, setProject] = useState(null)
  const [tasks, setTasks] = useState([])
  const [error, setError] = useState('')
  const [filter, setFilter] = useState({ status: '', priority: '', title: '' })
  const [selectedTaskId, setSelectedTaskId] = useState(null)

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
    setError('')
    try {
      const [proj, taskList] = await Promise.all([
        projectsApi.get(projectId),
        tasksApi.list({ project: projectId, ...filter }),
      ])
      setProject(proj)
      setTasks(Array.isArray(taskList) ? taskList : taskList.results || [])
    } catch (err) {
      setError(err.message)
    }
  }, [projectId, filter])

  useEffect(() => {
    load()
  }, [load])

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
          <h1>{project?.name || 'Backlog'}</h1>
          <p className="muted">
            All issues in this project
            <ApiHint method="GET" path={`/api/tasks/?project=${projectId}`} />
          </p>
        </div>
      </div>

      <ErrorBanner message={error} onDismiss={() => setError('')} />

      <div className="filters row">
        <input
          placeholder="Search title…"
          value={filter.title}
          onChange={(e) => setFilter((f) => ({ ...f, title: e.target.value }))}
        />
        <select
          value={filter.status}
          onChange={(e) => setFilter((f) => ({ ...f, status: e.target.value }))}
        >
          <option value="">All statuses</option>
          <option value="TODO">To Do</option>
          <option value="IN_PROGRESS">In Progress</option>
          <option value="DONE">Done</option>
        </select>
        <select
          value={filter.priority}
          onChange={(e) => setFilter((f) => ({ ...f, priority: e.target.value }))}
        >
          <option value="">All priorities</option>
          <option value="LOW">Low</option>
          <option value="MEDIUM">Medium</option>
          <option value="HIGH">High</option>
          <option value="CRITICAL">Critical</option>
        </select>
      </div>

      {tasks.length === 0 ? (
        <EmptyState title="No issues match" subtitle="Try clearing filters or create an issue from the board." />
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>Key</th>
              <th>Summary</th>
              <th>Status</th>
              <th>Priority</th>
              <th>Assignee</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((t) => (
              <tr key={t.id} onClick={() => setSelectedTaskId(t.id)} className="clickable-row">
                <td className="mono">TM-{t.id}</td>
                <td>{t.title}</td>
                <td>
                  <StatusBadge status={t.status} />
                </td>
                <td>
                  <PriorityBadge priority={t.priority} />
                </td>
                <td>
                  {t.assignees && t.assignees.length > 0
                    ? t.assignees.map((a) => a.email).join(', ')
                    : 'Unassigned'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
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
