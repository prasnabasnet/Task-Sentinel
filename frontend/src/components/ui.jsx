export function PriorityBadge({ priority }) {
  const map = {
    LOW: 'priority-low',
    MEDIUM: 'priority-medium',
    HIGH: 'priority-high',
    CRITICAL: 'priority-critical',
  }
  return <span className={`badge ${map[priority] || ''}`}>{priority}</span>
}

export function StatusBadge({ status }) {
  const labels = {
    TODO: 'To Do',
    IN_PROGRESS: 'In Progress',
    DONE: 'Done',
  }
  const map = {
    TODO: 'status-todo',
    IN_PROGRESS: 'status-progress',
    DONE: 'status-done',
  }
  return <span className={`badge ${map[status] || ''}`}>{labels[status] || status}</span>
}

export function Modal({ title, onClose, children, wide }) {
  return (
    <div className="modal-backdrop" onClick={onClose} role="presentation">
      <div
        className={`modal ${wide ? 'modal-wide' : ''}`}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        <div className="modal-header">
          <h2>{title}</h2>
          <button type="button" className="btn btn-ghost btn-sm" onClick={onClose}>
            ✕
          </button>
        </div>
        <div className="modal-body">{children}</div>
      </div>
    </div>
  )
}

export function EmptyState({ title, subtitle }) {
  return (
    <div className="empty-state">
      <h3>{title}</h3>
      {subtitle && <p className="muted">{subtitle}</p>}
    </div>
  )
}

export function ErrorBanner({ message, onDismiss }) {
  if (!message) return null
  return (
    <div className="error-banner">
      <span>{message}</span>
      {onDismiss && (
        <button type="button" className="btn btn-ghost btn-sm" onClick={onDismiss}>
          Dismiss
        </button>
      )}
    </div>
  )
}
