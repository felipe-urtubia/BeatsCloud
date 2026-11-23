export function resolveTrackPlayback(track, mode, purchased = false) {
  const originalDuration =
    Number.isFinite(track.duration) && track.duration > 0
      ? track.duration
      : 180;

  if (mode !== 'hybrid') {
    return { src: null, duration: originalDuration };
  }

  const hasFullAccess = Boolean(track.playbackAuthorized || purchased);

  if (hasFullAccess && track.fullSrc) {
    return { src: track.fullSrc, duration: originalDuration };
  }

  if (track.previewSrc) {
    return {
      src: track.previewSrc,
      duration: Math.min(30, originalDuration),
    };
  }

  return { src: null, duration: 0 };
}
