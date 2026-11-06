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
  url.searchParams.delete('tab');
  url.searchParams.delete('resource');
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


export type MainTab =
  | 'descubrir'
  | 'catalogo'
  | 'usuarios'
  | 'sobre_nosotros'
  | 'carrito'
  | 'perfil'
  | 'ventas'
  | 'favoritos';

export type CatalogResource =
  | 'all'
  | 'instrumental'
  | 'loop'
  | 'acapella'
  | 'drumkit';

const validTabs: readonly MainTab[] = [
  'descubrir', 'catalogo', 'usuarios', 'sobre_nosotros',
  'carrito', 'perfil', 'ventas', 'favoritos',
];
const validResources: readonly CatalogResource[] = [
  'all', 'instrumental', 'loop', 'acapella', 'drumkit',
];

export function readPageNavigation(search: string): {
  tab: MainTab;
  resource: CatalogResource;
} {
  const params = new URLSearchParams(search);
  const rawTab = params.get('tab');
  const tab: MainTab = rawTab === 'inicio'
    ? 'descubrir'
    : validTabs.includes(rawTab as MainTab)
      ? rawTab as MainTab
      : 'descubrir';
  const rawResource = params.get('resource');
  const resource: CatalogResource =
    tab === 'catalogo' && validResources.includes(rawResource as CatalogResource)
      ? rawResource as CatalogResource
      : 'all';
  return { tab, resource };
}

export function makeTabUrl(
  href: string, tab: string, resource: CatalogResource = 'all'
): string {
  const url = new URL(href);
  const normalized = readPageNavigation(`?tab=${encodeURIComponent(tab)}`).tab;
  url.searchParams.delete('profile');
  url.searchParams.delete('track');
  url.searchParams.set('tab', normalized);
  if (normalized === 'catalogo' && resource !== 'all') {
    url.searchParams.set('resource', resource);
  } else {
    url.searchParams.delete('resource');
  }
  return `${url.pathname}${url.search}${url.hash}`;
}
