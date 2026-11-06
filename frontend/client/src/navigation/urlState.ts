export type PublicProfileRef = {
  id: string;
  username: string;
  role: 'artista' | 'productor';
};

export function readNavigation(search: string) {
  const params = new URLSearchParams(search);

  return {
    trackId: params.get('track') || null,
    profileUsername: params.get('profile')?.trim() || null,
  };
}

export function makeTrackUrl(href: string, id: string): string {
  const url = new URL(href);
  url.searchParams.set('track', id);
  return `${url.pathname}${url.search}${url.hash}`;
}

export function makeProfileUrl(
  href: string,
  username: string
): string {
  const url = new URL(href);
  url.searchParams.delete('track');
  url.searchParams.set('profile', username);
  return `${url.pathname}${url.search}${url.hash}`;
}

export function makeLeaveProfileUrl(href: string): string {
  const url = new URL(href);
  url.searchParams.delete('profile');
  return `${url.pathname}${url.search}${url.hash}`;
}

export function lookupPublicProfile<T extends PublicProfileRef>(
  users: readonly T[],
  username: string | null
): T | null {
  return username
    ? users.find((user) => user.username === username) ?? null
    : null;
}

export function lookupPublicProfileForRoute<T extends PublicProfileRef>(
  users: readonly T[],
  id: string,
  role: PublicProfileRef['role']
): T | null {
  return users.find(
    (user) => user.id === id && user.role === role
  ) ?? null;
}
