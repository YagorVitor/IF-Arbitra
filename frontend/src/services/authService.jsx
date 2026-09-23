import { api } from "../api/api";

export const authService = {
  async login(login, password) {
    return await api.post('/api/auth/login', {login, password,});
  },

  async getCurrentUser() {
    return await api.get('/api/auth/me');
  },

  async logout() {
    return await api.post('/api/auth/logout');
  },
};