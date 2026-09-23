import { api } from '../api/api';

function newestFirst(rounds) {
  return [...rounds].sort((a, b) => {
    const aDate = new Date(a.registration_opens_at || 0).getTime();
    const bDate = new Date(b.registration_opens_at || 0).getTime();
    return bDate - aDate;
  });
}

export const roundService = {
  getAll: () => api.get('/api/rounds'),

  getById: (id) => api.get(`/api/rounds/${id}`),

  async getAllOrdered() {
    return newestFirst(await api.get('/api/rounds'));
  },

  async getRegistrationRound() {
    const rounds = await this.getAllOrdered();
    return rounds.find((round) => round.registration_open) || null;
  },

  async getPreferencesRound() {
    const rounds = await this.getAllOrdered();
    return rounds.find((round) => round.preferences_open) || null;
  },

  async getCurrentRound() {
    const rounds = await this.getAllOrdered();
    return rounds.find((round) => round.registration_open || round.preferences_open)
      || rounds[0]
      || null;
  },

  async getResultRound() {
    const rounds = await this.getAllOrdered();
    return rounds.find((round) => ['PUBLISHED', 'ARCHIVED'].includes(round.status))
      || rounds[0]
      || null;
  },

  // Mantido como alias para componentes existentes; não retorna rodada fora de uma janela aberta.
  getActiveRound() {
    return this.getCurrentRound();
  },

  getMySextet: (roundId) => api.get(`/api/rounds/${roundId}/my-sextet`),
  getResults: (roundId) => api.get(`/api/rounds/${roundId}/results`),
  createSextet: (roundId, payload) => api.post(`/api/rounds/${roundId}/sextets`, payload),
};
