import { api } from '../api/api';

export const adminService = {
  students: () => api.get('/api/admin/students'),
  addStudent: (name, email) => api.post('/api/admin/students', { name, email }),
  removeStudent: (id) => api.delete(`/api/admin/students/${id}`),
  dispatchCredentials: () => api.post('/api/admin/students/dispatch-credentials'),
  staff: () => api.get('/api/staff'),
  addStaff: (name, email) => api.post('/api/admin/staff', { name, email }),
  removeStaff: (id) => api.delete(`/api/admin/staff/${id}`),
  rounds: () => api.get('/api/rounds'),
  createRound: (data) => api.post('/api/admin/rounds', data),
  updateRound: (id, data) => api.put(`/api/admin/rounds/${id}`, data),
  transitionRound: (id, action) => api.post(`/api/admin/rounds/${id}/transition`, { action }),
  allocate: (id) => api.post(`/api/admin/rounds/${id}/allocate`),
  results: (id) => api.get(`/api/rounds/${id}/results`),
  sextets: (id) => api.get(`/api/admin/rounds/${id}/sextets`),
  audit: (beforeId) => api.get(`/api/admin/audit${beforeId ? `?before_id=${beforeId}` : ''}`),
};
