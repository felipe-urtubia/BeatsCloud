export function enqueueNotification(queue, notification, limit = 3) {
  if (queue.some((item) => item.message === notification.message && item.kind === notification.kind)) {
    return queue;
  }
  return [...queue, notification].slice(-limit);
}

export function dismissNotification(queue, id) {
  return queue.filter((item) => item.id !== id);
}
