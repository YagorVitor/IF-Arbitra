export function captainFlow(round, group) {
  if (['PUBLISHED', 'ARCHIVED'].includes(round.status)) return 'result';
  if (!group) return round.formation_mode === 'GROUPS' && round.registration_open ? 'group' : 'registration-unavailable';
  if (group.preference_version > 0 && group.preferences?.length > 0) return 'waiting';
  return round.preferences_open ? 'preferences' : 'preferences-unavailable';
}
