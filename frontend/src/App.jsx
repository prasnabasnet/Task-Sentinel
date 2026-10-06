import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import { useAuth } from './context/AuthContext'
import Backlog from './pages/Backlog'
import Board from './pages/Board'
import Login from './pages/Login'
import Organizations from './pages/Organizations'
import ProjectSettings from './pages/ProjectSettings'
import Projects from './pages/Projects'
import Register from './pages/Register'
import Users from './pages/Users'
import Profile from './pages/Profile'

function Protected({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="auth-page muted">Loading…</div>
  if (!user) return <Navigate to="/login" replace />
  return children
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      <Route
        path="/"
        element={
          <Protected>
            <Layout />
          </Protected>
        }
      >
        <Route index element={<Navigate to="/organizations" replace />} />
        <Route path="organizations" element={<Organizations />} />
        <Route path="users" element={<Users />} />
        <Route path="profile" element={<Profile />} />
        <Route path="projects/:projectId/board" element={<Board />} />
        <Route path="projects/:projectId/backlog" element={<Backlog />} />
        <Route path="projects/:projectId/settings" element={<ProjectSettings />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
