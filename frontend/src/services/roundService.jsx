import { api } from '../api/api';

export const roundService = {
  getAll: () => api.get('/api/rounds'),
  
  getById: (id) => api.get(`/api/rounds/${id}`),
  
  getActiveRound: async () => {
    const rounds = await api.get('/api/rounds');
    return rounds.find(r => r.status === 'OPEN' || r.preferences_open) || rounds[0];
  },

  getMySextet: (roundId) => api.get(`/api/rounds/${roundId}/my-sextet`),
  getResults: (roundId) => api.get(`/api/rounds/${roundId}/results`),
  createSextet: (roundId, payload) => api.post(`/api/rounds/${roundId}/sextets`, payload),
};