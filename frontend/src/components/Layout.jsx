import { useState } from 'react'
import { NavLink, Outlet, useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { useProjectSocket } from '../hooks/useProjectSocket'
import ToastContainer from './ToastContainer'
import ApiHint from './ApiHint'
import CommentsSection from './CommentsSection'
import './Layout.css'

export default function Layout() {
  const { user, logout } = useAuth()
  const { addToast } = useToast()
  const navigate = useNavigate()
  const { projectId } = useParams()
  const [showProjectComments, setShowProjectComments] = useState(false)

  const { isConnected } = useProjectSocket(projectId, (data) => {
    if (data && data.message && data.type !== 'connection_established') {
      addToast({
        title: 'Real-time Update',
        message: data.message,
        type: 'info',
      })
    }
  })

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  const displayName = user?.profile?.display_name || user?.username || user?.email
  const initials = (displayName?.[0] || '?').toUpperCase()
  const avatarUrl = user?.profile?.avatar_url

  return (
    <div className="app-shell">
      <ToastContainer />
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="brand-mark">TM</span>
          <span className="brand-name">TaskBoard</span>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section-label">Workspace</div>
          <NavLink
            to="/organizations"
            className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
          >
            Organizations
          </NavLink>
          <NavLink
            to="/profile"
            className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
          >
            Profile
          </NavLink>
          {(user?.role === 'SUPERADMIN' || user?.role === 'ORG_ADMIN' || user?.role === 'ADMIN') && (
            <NavLink
              to="/users"
              className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
            >
              Members
            </NavLink>
          )}

          {projectId && (
            <>
              <div className="nav-section-label">Project</div>
              <NavLink
                to={`/projects/${projectId}/board`}
                className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
              >
                Board
              </NavLink>
              <NavLink
                to={`/projects/${projectId}/backlog`}
                className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
              >
                Backlog
              </NavLink>
              {user?.role !== 'TM' && (
                <NavLink
                  to={`/projects/${projectId}/settings`}
                  className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
                >
                  Settings
                </NavLink>
              )}
              <button
                type="button"
                className={showProjectComments ? 'nav-item active' : 'nav-item'}
                onClick={() => setShowProjectComments(true)}
                style={{
                  background: 'none',
                  border: 'none',
                  width: '100%',
                  textAlign: 'left',
                  cursor: 'pointer',
                  padding: '8px 10px',
                  display: 'block'
                }}
              >
                Comments
              </button>
            </>
          )}
        </nav>

        <div className="sidebar-footer">
          <div className="user-chip">
            {avatarUrl ? (
              <img
                src={avatarUrl}
                alt={displayName}
                className="avatar"
                style={{ objectFit: 'cover' }}
              />
            ) : (
              <span className="avatar">{initials}</span>
            )}
            <div className="user-meta">
              <div className="user-name">{displayName}</div>
              <div className="user-role">{user?.role}</div>
            </div>
          </div>
          <button type="button" className="btn btn-ghost btn-sm logout-btn" onClick={handleLogout}>
            Log out
            <ApiHint method="POST" path="/api/users/auth/logout/" />
          </button>
        </div>
      </aside>

      <div className="main-area">
        <header className="topbar">
          <div className="topbar-title">Task Manager</div>
          <div className="topbar-right" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {projectId && (
              <span
                style={{
                  fontSize: '0.78rem',
                  padding: '3px 8px',
                  borderRadius: '12px',
                  background: isConnected ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                  color: isConnected ? '#10b981' : '#ef4444',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '5px',
                  fontWeight: 500,
                }}
              >
                <span
                  style={{
                    width: '6px',
                    height: '6px',
                    borderRadius: '50%',
                    background: isConnected ? '#10b981' : '#ef4444',
                  }}
                />
                {isConnected ? 'Live Sync' : 'Offline'}
              </span>
            )}
            <span className="muted">{user?.email}</span>
          </div>
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>

      {showProjectComments && (
        <div className="drawer-backdrop" onClick={() => setShowProjectComments(false)}>
          <div className="drawer" onClick={(e) => e.stopPropagation()}>
            <div className="drawer-header">
              <h2>Project Comments</h2>
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={() => setShowProjectComments(false)}
              >
                ✕
              </button>
            </div>
            <div className="drawer-body">
              <CommentsSection targetType="project" targetId={projectId} />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}