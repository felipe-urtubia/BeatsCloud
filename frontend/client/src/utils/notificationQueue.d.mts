export type QueueNotification = {
  id: number;
  kind: 'success' | 'error';
  message: string;
};

export function enqueueNotification(
  queue: QueueNotification[],
  notification: QueueNotification,
  limit?: number,
): QueueNotification[];

export function dismissNotification(
  queue: QueueNotification[],
  id: number,
): QueueNotification[];
