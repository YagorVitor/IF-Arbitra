import { api } from '../api/api';

export const adminService = {
  students: (includeRemoved = false) => api.get(`/api/admin/students${includeRemoved ? '?include_removed=true' : ''}`),
  restoreStudent: (id) => api.post(`/api/admin/students/${id}/restore`),
  issueStudentAccess: (id) => api.post(`/api/admin/students/${id}/access`),
  addStudent: (name, email, is_captain, phone) => api.post('/api/admin/students', { name, email, is_captain, phone: phone || null }),
  setCaptain: (id, is_captain) => api.put(`/api/admin/students/${id}/captain`, { is_captain }),
  removeStudent: (id) => api.delete(`/api/admin/students/${id}`),
  dispatchCredentials: () => api.post('/api/admin/students/dispatch-credentials'),
  staff: () => api.get('/api/staff'),
  addStaff: (name, email) => api.post('/api/admin/staff', { name, email: email || null }),
  removeStaff: (id) => api.delete(`/api/admin/staff/${id}`),
  rounds: () => api.get('/api/rounds'),
  createRound: (data) => api.post('/api/admin/rounds', data),
  updateRound: (id, data) => api.put(`/api/admin/rounds/${id}`, data),
  transitionRound: (id, action) => api.post(`/api/admin/rounds/${id}/transition`, { action }),
  allocate: (id, closeEarly = false) => api.post(`/api/admin/rounds/${id}/allocate${closeEarly ? '?close_early=true' : ''}`),
  results: (id) => api.get(`/api/rounds/${id}/results`),
  adjustAssignments: (id, data) => api.put(`/api/admin/rounds/${id}/assignments`, data),
  groups: (id) => api.get(`/api/admin/rounds/${id}/sextets`),
  audit: (beforeId) => api.get(`/api/admin/audit${beforeId ? `?before_id=${beforeId}` : ''}`),
};
