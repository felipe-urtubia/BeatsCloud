import type { UserType } from '../types';

export interface ProtectedSectionNotice {
  title: string;
  description: string;
  requiresLogin: boolean;
}

/**
 * Protect private views without treating a signed-out visitor as an error.
 * Only the owning role may access sales and favorites.
 */
export function getProtectedSectionNotice(
  tab: string,
  role: UserType | null | undefined,
): ProtectedSectionNotice | null {
  const isPrivateTab = ['carrito', 'perfil', 'ventas', 'favoritos'].includes(tab);
  if (!isPrivateTab) return null;

  if (!role) {
    return {
      title: tab === 'carrito'
        ? 'Inicia sesión para ver tu carrito'
        : 'Inicia sesión para acceder a esta sección',
      description: 'Accede con tu cuenta para continuar. Si aún no tienes una, puedes registrarte.',
      requiresLogin: true,
    };
  }

  if (tab === 'ventas' && role !== 'productor') {
    return {
      title: 'Esta sección es para productores',
      description: 'Cambia a una cuenta de productor para consultar tus ventas.',
      requiresLogin: false,
    };
  }

  if (tab === 'favoritos' && role !== 'artista') {
    return {
      title: 'Esta sección es para artistas',
      description: 'Cambia a una cuenta de artista para consultar tus favoritos.',
      requiresLogin: false,
    };
  }

  return null;
}
