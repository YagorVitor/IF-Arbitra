import { api } from '../api/api';

export const sextetService = {
  updatePreferences: (sextetId, payload) => 
    api.put(`/api/sextets/${sextetId}/preferences`, payload)
};