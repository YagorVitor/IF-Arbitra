import { api } from '../api/api';

export const adminService = {
  students: () => api.get('/api/admin/students'),
  addStudent: (name, email) => api.post('/api/admin/students', { name, email }),
  removeStudent: (id) => api.delete(`/api/admin/students/${id}`),
  dispatchCredentials: () => api.post('/api/admin/students/dispatch-credentials'),
  staff: () => api.get('/api/staff'),
  addStaff: (name, email) => api.post('/api/admin/staff', { name, email }),
  removeStaff: (id) => api.delete(`/api/admin/staff/${id}`),
};
