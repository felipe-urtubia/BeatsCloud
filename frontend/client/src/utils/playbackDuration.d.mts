export function resolveTrackPlayback(
  track: {
    duration: number;
    playbackAuthorized?: boolean;
    fullSrc?: string;
    previewSrc?: string;
  },
  mode: string,
  purchased?: boolean
): { src: string | null; duration: number };
