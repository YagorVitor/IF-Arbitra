import { api } from '../api/api';

export const groupService = {
  updatePreferences: (groupId, payload) => 
    api.put(`/api/sextets/${groupId}/preferences`, payload)
};
