import { api } from './client'

export const authApi = {
  login: (email, password) =>
    api.post('/users/auth/login/', { email, password }, { auth: false }),
  register: (payload) =>
    api.post('/users/auth/register/', payload, { auth: false }),
  logout: () => api.post('/users/auth/logout/', {}),
  me: () => api.get('/users/auth/me/'),
  updateProfile: (body) => api.patch('/users/auth/me/', body),
}

export const usersApi = {
  list: () => api.get('/users/'),
  get: (id) => api.get(`/users/${id}/`),
  update: (id, body) => api.patch(`/users/${id}/`, body),
  deactivate: (id) => api.delete(`/users/${id}/`),
  createMember: (body) => api.post('/users/members/', body),
}

export const orgsApi = {
  list: () => api.get('/organizations/'),
  create: (body) => api.post('/organizations/', body),
  get: (id) => api.get(`/organizations/${id}/`),
  update: (id, body) => api.patch(`/organizations/${id}/`, body),
  remove: (id) => api.delete(`/organizations/${id}/`),
}

export const departmentsApi = {
  list: (oid) => api.get(`/organizations/${oid}/departments/`),
  create: (oid, body) => api.post(`/organizations/${oid}/departments/`, body),
  get: (oid, id) => api.get(`/organizations/${oid}/departments/${id}/`),
  update: (oid, id, body) =>
    api.patch(`/organizations/${oid}/departments/${id}/`, body),
  remove: (oid, id) => api.delete(`/organizations/${oid}/departments/${id}/`),
  projects: (oid, id) =>
    api.get(`/organizations/${oid}/departments/${id}/projects/`),
  createProject: (oid, id, body) =>
    api.post(`/organizations/${oid}/departments/${id}/projects/`, body),
}

export const projectsApi = {
  list: (params = {}) => {
    const qs = new URLSearchParams(params).toString()
    return api.get(`/projects/${qs ? `?${qs}` : ''}`)
  },
  create: (body) => api.post('/projects/', body),
  get: (id) => api.get(`/projects/${id}/`),
  update: (id, body) => api.patch(`/projects/${id}/`, body),
  remove: (id) => api.delete(`/projects/${id}/`),
  listMembers: (id) => api.get(`/projects/${id}/members/`),
  addMember: (id, emailOrData) =>
    api.post(
      `/projects/${id}/members/`,
      typeof emailOrData === 'object' ? emailOrData : { email: emailOrData }
    ),

  removeMember: (id, uid) => api.delete(`/projects/${id}/members/${uid}/`),
}

export const tasksApi = {
  list: (params = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== '')
    ).toString()
    return api.get(`/tasks/${qs ? `?${qs}` : ''}`)
  },
  create: (body) => api.post('/tasks/', body),
  get: (id) => api.get(`/tasks/${id}/`),
  update: (id, body) => api.patch(`/tasks/${id}/`, body),
  remove: (id) => api.delete(`/tasks/${id}/`),
}

export const commentsApi = {
  list: (params = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== '')
    ).toString()
    return api.get(`/comments/${qs ? `?${qs}` : ''}`)
  },
  create: (body) => api.post('/comments/', body),
  get: (id) => api.get(`/comments/${id}/`),
  update: (id, body) => api.patch(`/comments/${id}/`, body),
  remove: (id) => api.delete(`/comments/${id}/`),
}
