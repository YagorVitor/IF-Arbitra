import { api } from '../api/api';

export const studentService = {
  search: (query) => api.get(`/api/students?q=${encodeURIComponent(query)}`)
  
};