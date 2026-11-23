import test from 'node:test';
import assert from 'node:assert/strict';
import { resolveTrackPlayback } from './playbackDuration.mjs';

const track = {
  duration: 260,
  previewSrc: '/preview/',
  fullSrc: '/reproducir/',
};

test('visitor only gets a 30-second preview', () => {
  assert.deepEqual(resolveTrackPlayback(track, 'hybrid'), {
    src: '/preview/',
    duration: 30,
  });
});

test('purchased track uses complete audio', () => {
  assert.deepEqual(resolveTrackPlayback(track, 'hybrid', true), {
    src: '/reproducir/',
    duration: 260,
  });
});

test('authorized playback uses complete audio', () => {
  assert.deepEqual(
    resolveTrackPlayback(
      { ...track, playbackAuthorized: true },
      'hybrid'
    ),
    { src: '/reproducir/', duration: 260 }
  );
});

test('short previews preserve their shorter duration', () => {
  assert.equal(
    resolveTrackPlayback({ ...track, duration: 12 }, 'hybrid').duration,
    12
  );
});

test('missing full source falls back to preview', () => {
  assert.deepEqual(
    resolveTrackPlayback(
      { ...track, fullSrc: undefined },
      'hybrid',
      true
    ),
    { src: '/preview/', duration: 30 }
  );
});

test('demo playback preserves original duration', () => {
  assert.equal(resolveTrackPlayback(track, 'mock').duration, 260);
});

test('unavailable audio does not expose full source', () => {
  assert.deepEqual(
    resolveTrackPlayback({ duration: 260 }, 'hybrid'),
    { src: null, duration: 0 }
  );
});
