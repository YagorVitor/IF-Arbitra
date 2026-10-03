import { test } from 'node:test';
import assert from 'node:assert/strict';
import { captainFlow } from './captainFlow.js';

const openRound = { status: 'OPEN', formation_mode: 'GROUPS', registration_open: true, preferences_open: true };
const confirmed = { id: 'group', preference_version: 0, preferences: [] };
const submitted = { ...confirmed, preference_version: 1, preferences: ['staff'] };

test('captain progresses only after group confirmation and successful preference submission', () => {
  assert.equal(captainFlow(openRound, null), 'group');
  assert.equal(captainFlow(openRound, confirmed), 'preferences');
  assert.equal(captainFlow(openRound, submitted), 'waiting');
  assert.equal(captainFlow(openRound, { ...confirmed, preferences: ['staff'] }), 'preferences');
});

test('closed windows never mark missing preferences as submitted', () => {
  const closed = { ...openRound, registration_open: false, preferences_open: false };
  assert.equal(captainFlow(closed, null), 'registration-unavailable');
  assert.equal(captainFlow(closed, confirmed), 'preferences-unavailable');
  assert.equal(captainFlow(closed, submitted), 'waiting');
  assert.equal(captainFlow({ ...closed, status: 'PROCESSED' }, submitted), 'waiting');
});

test('published and archived rounds direct captains to the result even without allocation', () => {
  for (const status of ['PUBLISHED', 'ARCHIVED']) {
    assert.equal(captainFlow({ ...openRound, status }, submitted), 'result');
    assert.equal(captainFlow({ ...openRound, status }, null), 'result');
  }
});
