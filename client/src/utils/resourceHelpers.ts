import { ResourceType } from '../types';

export interface ResourceBadgeInfo {
  label: string;
  badge: string;
  badgeClass: string;
  borderClass: string;
  dotColor: string;
}

export const RESOURCE_TYPES: { id: ResourceType; label: string; description: string }[] = [
  { id: 'instrumental', label: 'Instrumentales', description: 'Beats completos listos para vocales' },
  { id: 'loop', label: 'Loops & Melodías', description: 'Guitarras, synths y progresiones armónicas' },
  { id: 'acapella', label: 'Acapellas', description: 'Vocales secos y procesados para remix' },
  { id: 'drumkit', label: 'Drum Kits', description: 'Kits de batería, 808s y percusión' },
];

export const getResourceBadgeInfo = (type: ResourceType): ResourceBadgeInfo => {
  switch (type) {
    case 'instrumental':
      return {
        label: 'Instrumental',
        badge: 'BEAT',
        badgeClass: 'text-sky-400 bg-sky-950/80 border-sky-800/50',
        borderClass: 'border-sky-500/30',
        dotColor: 'bg-sky-400',
      };
    case 'acapella':
      return {
        label: 'Acapella',
        badge: 'VOX',
        badgeClass: 'text-purple-400 bg-purple-950/80 border-purple-800/50',
        borderClass: 'border-purple-500/30',
        dotColor: 'bg-purple-400',
      };
    case 'loop':
      return {
        label: 'Loop / Melodía',
        badge: 'LOOP',
        badgeClass: 'text-amber-400 bg-amber-950/80 border-amber-800/50',
        borderClass: 'border-amber-500/30',
        dotColor: 'bg-amber-400',
      };
    case 'drumkit':
      return {
        label: 'Drum Kit',
        badge: 'KIT',
        badgeClass: 'text-emerald-400 bg-emerald-950/80 border-emerald-800/50',
        borderClass: 'border-emerald-500/30',
        dotColor: 'bg-emerald-400',
      };
    default:
      return {
        label: 'Audio',
        badge: 'AUDIO',
        badgeClass: 'text-zinc-400 bg-zinc-800 border-zinc-700',
        borderClass: 'border-zinc-700',
        dotColor: 'bg-zinc-400',
      };
  }
};
