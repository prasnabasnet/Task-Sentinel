import { useEffect, useState } from 'react'
import { projectsApi, tasksApi } from '../api'
import ApiHint from '../components/ApiHint'
import { ErrorBanner, Modal, PriorityBadge, StatusBadge } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import CommentsSection from '../components/CommentsSection'

export default function TaskDetail({ taskId, onClose, onChanged }) {
  const { user } = useAuth()
  const [task, setTask] = useState(null)
  const [members, setMembers] = useState([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [edit, setEdit] = useState(null)

  const load = async () => {
    setError('')
    try {
      const t = await tasksApi.get(taskId)
      setTask(t)
      setEdit({
        title: t.title,
        description: t.description || '',
        status: t.status,
        priority: t.priority,
        assignee_ids: t.assignees?.map((a) => a.id) || [],
        due_date: t.due_date || '',
      })
      const memberList = await projectsApi.listMembers(t.project)
      setMembers(Array.isArray(memberList) ? memberList : memberList.results || [])
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => {
    load()
  }, [taskId])

  const isRestrictedTM =
    user?.role === 'TM' &&
    task?.created_by?.id !== user?.id

  const save = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      let payload
      if (isRestrictedTM) {
        // TMs can only update status and priority
        payload = {
          status: edit.status,
          priority: edit.priority,
        }
      } else {
        payload = {
          title: edit.title,
          description: edit.description,
          status: edit.status,
          priority: edit.priority,
          due_date: edit.due_date || null,
          assignees: edit.assignee_ids.map(Number),
        }
      }
      await tasksApi.update(taskId, payload)
      await load()
      onChanged?.()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const remove = async () => {
    if (!confirm('Delete this issue?')) return
    setBusy(true)
    try {
      await tasksApi.remove(taskId)
      onChanged?.()
      onClose()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  if (!task || !edit) {
    return (
      <Modal title="Issue" onClose={onClose} wide>
        <p className="muted">Loading…</p>
      </Modal>
    )
  }

  return (
    <Modal title={`TM-${task.id}`} onClose={onClose} wide>
      <ErrorBanner message={error} onDismiss={() => setError('')} />

      <div className="issue-layout">
        <div className="issue-main">
          <form onSubmit={save} className="stack" id="issue-form">
            <label className="field">
              <span>Summary</span>
              <input
                value={edit.title}
                onChange={(e) => setEdit((f) => ({ ...f, title: e.target.value }))}
                disabled={isRestrictedTM}
                required
              />
            </label>
            <label className="field">
              <span>Description</span>
              <textarea
                rows={5}
                value={edit.description}
                onChange={(e) => setEdit((f) => ({ ...f, description: e.target.value }))}
                disabled={isRestrictedTM}
              />
            </label>
          </form>

          <CommentsSection targetType="task" targetId={taskId} />
        </div>

        <aside className="issue-side">
          <div className="side-block">
            <div className="muted small">Status</div>
            <select
              form="issue-form"
              value={edit.status}
              onChange={(e) => setEdit((f) => ({ ...f, status: e.target.value }))}
            >
              <option value="TODO">To Do</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="DONE">Done</option>
            </select>
            <StatusBadge status={edit.status} />
          </div>

          <div className="side-block">
            <div className="muted small">Priority</div>
            <select
              form="issue-form"
              value={edit.priority}
              onChange={(e) => setEdit((f) => ({ ...f, priority: e.target.value }))}
            >
              <option value="LOW">Low</option>
              <option value="MEDIUM">Medium</option>
              <option value="HIGH">High</option>
              <option value="CRITICAL">Critical</option>
            </select>
            <PriorityBadge priority={edit.priority} />
          </div>

          <div className="side-block">
            <div className="muted small">Assignees</div>
            <div className="assignees-list" style={{ maxHeight: '150px', overflowY: 'auto', border: '1px solid var(--border)', borderRadius: '3px', padding: '8px', background: '#fff' }}>
              {members.length === 0 ? (
                <span className="muted">No project members</span>
              ) : (
                members.map((m) => {
                  const isChecked = edit.assignee_ids.includes(m.user_id)
                  return (
                    <label key={m.user_id} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '4px 0', cursor: isRestrictedTM ? 'not-allowed' : 'pointer', fontWeight: 'normal' }}>
                      <input
                        type="checkbox"
                        checked={isChecked}
                        disabled={isRestrictedTM}
                        onChange={(e) => {
                          const checked = e.target.checked
                          setEdit((f) => {
                            const newIds = checked
                              ? [...f.assignee_ids, m.user_id]
                              : f.assignee_ids.filter((id) => id !== m.user_id)
                            return { ...f, assignee_ids: newIds }
                          })
                        }}
                      />
                      <span>{m.email}</span>
                    </label>
                  )
                })
              )}
            </div>
            <ApiHint method="GET" path={`/api/projects/${task.project}/members/`} />
          </div>

          <div className="side-block">
            <div className="muted small">Due date</div>
            <input
              form="issue-form"
              type="date"
              value={edit.due_date}
              disabled={isRestrictedTM}
              onChange={(e) => setEdit((f) => ({ ...f, due_date: e.target.value }))}
            />
          </div>

          <div className="side-block muted small">
            Reporter: {task.created_by?.email || '—'}
            <br />
            Created: {new Date(task.created_at).toLocaleString()}
          </div>

          <div className="stack">
            <button type="submit" form="issue-form" className="btn btn-primary" disabled={busy}>
              Save changes
              <ApiHint method="PATCH" path={`/api/tasks/${taskId}/`} />
            </button>
            {!isRestrictedTM && (
              <button type="button" className="btn btn-danger" disabled={busy} onClick={remove}>
                Delete issue
                <ApiHint method="DELETE" path={`/api/tasks/${taskId}/`} />
              </button>
            )}
          </div>
        </aside>
      </div>
    </Modal>
  )
}
