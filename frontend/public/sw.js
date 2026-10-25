// Service worker for Web Push notifications.
// Registered once from the Settings page after the user opts in.

self.addEventListener('push', (event) => {
  let data = { title: 'AIHMS', body: 'You have a new notification.', url: '/' };
  try {
    if (event.data) data = event.data.json();
  } catch (e) {
    // fall back to default text if payload isn't JSON
  }

  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: '/icon-192.png',
      badge: '/icon-192.png',
      data: { url: data.url || '/' },
    })
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const url = event.notification.data?.url || '/';
  event.waitUntil(
    self.clients.matchAll({ type: 'window' }).then((clients) => {
      for (const client of clients) {
        if (client.url.includes(url) && 'focus' in client) return client.focus();
      }
      if (self.clients.openWindow) return self.clients.openWindow(url);
    })
  );
});
