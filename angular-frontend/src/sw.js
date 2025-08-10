// Custom Service Worker for Dinner First Dating App
// Enhanced offline functionality and background sync

const CACHE_NAME = 'dinner_first-v1.0.0';
const DATA_CACHE_NAME = 'dinner_first-data-v1.0.0';
const BACKGROUND_SYNC_TAG = 'background-sync';

// Files to cache for offline use
const FILES_TO_CACHE = [
  '/',
  '/index.html',
  '/manifest.webmanifest',
  '/assets/icons/icon-192x192.png',
  '/assets/icons/icon-512x512.png',
  '/assets/images/hero-image.jpg',
  // Core app files will be added by Angular CLI
];

// API endpoints that should be cached
const API_CACHE_PATTERNS = [
  /\/api\/v1\/profiles\/me/,
  /\/api\/v1\/soul-connections\/active/,
  /\/api\/v1\/revelations\/timeline/,
  /\/api\/v1\/users\/me/
];

// API endpoints for background sync
const SYNC_ENDPOINTS = [
  /\/api\/v1\/chat\/send/,
  /\/api\/v1\/revelations\/create/,
  /\/api\/v1\/soul-connections\/initiate/,
  /\/api\/v1\/profiles\/me/
];

self.addEventListener('install', (event) => {
  console.log('[SW] Install event');

  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[SW] Pre-caching offline page');
        return cache.addAll(FILES_TO_CACHE);
      })
      .then(() => {
        // Skip waiting to activate immediately
        return self.skipWaiting();
      })
  );
});

self.addEventListener('activate', (event) => {
  console.log('[SW] Activate event');

  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((thisCacheName) => {
          if (thisCacheName !== CACHE_NAME && thisCacheName !== DATA_CACHE_NAME) {
            console.log('[SW] Removing old cache', thisCacheName);
            return caches.delete(thisCacheName);
          }
        })
      );
    }).then(() => {
      // Claim all clients
      return self.clients.claim();
    })
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Handle API requests
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(handleApiRequest(request));
    return;
  }

  // Handle navigation requests
  if (request.mode === 'navigate') {
    event.respondWith(handleNavigationRequest(request));
    return;
  }

  // Handle other requests (static assets)
  event.respondWith(handleStaticRequest(request));
});

// Handle API requests with caching strategy
async function handleApiRequest(request) {
  const url = new URL(request.url);

  try {
    // For dating app, we want fresh data for most API calls
    const response = await fetch(request);

    // Cache successful GET requests for offline use
    if (request.method === 'GET' && response.status === 200) {
      const shouldCache = API_CACHE_PATTERNS.some(pattern => pattern.test(url.pathname));

      if (shouldCache) {
        const cache = await caches.open(DATA_CACHE_NAME);
        await cache.put(request, response.clone());
      }
    }

    return response;
  } catch (error) {
    // If offline, try to serve from cache
    if (request.method === 'GET') {
      const cachedResponse = await caches.match(request);
      if (cachedResponse) {
        return cachedResponse;
      }
    }

    // For POST/PUT requests when offline, queue for background sync
    if (['POST', 'PUT', 'DELETE'].includes(request.method)) {
      await queueRequestForSync(request);

      // Return a response indicating the request was queued
      return new Response(
        JSON.stringify({
          queued: true,
          message: 'Request queued for sync when online',
          timestamp: Date.now()
        }),
        {
          status: 202,
          headers: { 'Content-Type': 'application/json' }
        }
      );
    }

    // For unhandled requests, return offline message
    return new Response(
      JSON.stringify({
        error: 'Offline',
        message: 'You are currently offline. Please check your connection.'
      }),
      {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}

// Handle navigation requests
async function handleNavigationRequest(request) {
  try {
    // Try network first
    const response = await fetch(request);
    return response;
  } catch (error) {
    // If offline, serve the cached index.html
    const cache = await caches.open(CACHE_NAME);
    const cachedResponse = await cache.match('/index.html');
    return cachedResponse || new Response('Offline');
  }
}

// Handle static asset requests
async function handleStaticRequest(request) {
  const cache = await caches.open(CACHE_NAME);
  const cachedResponse = await cache.match(request);

  if (cachedResponse) {
    return cachedResponse;
  }

  try {
    const response = await fetch(request);

    // Cache successful responses
    if (response.status === 200) {
      await cache.put(request, response.clone());
    }

    return response;
  } catch (error) {
    // Return offline fallback if available
    return new Response('Offline', { status: 503 });
  }
}

// Background sync for dating app actions
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync event', event.tag);

  if (event.tag === BACKGROUND_SYNC_TAG) {
    event.waitUntil(syncQueuedRequests());
  } else if (event.tag === 'location-sync') {
    event.waitUntil(syncLocation());
  } else if (event.tag === 'message-sync') {
    event.waitUntil(syncMessages());
  }
});

// Queue requests for background sync
async function queueRequestForSync(request) {
  const requestData = {
    url: request.url,
    method: request.method,
    headers: Object.fromEntries(request.headers.entries()),
    body: request.method !== 'GET' ? await request.text() : null,
    timestamp: Date.now()
  };

  // Store in IndexedDB for persistence
  await storeRequestInDB(requestData);

  // Register for background sync
  try {
    await self.registration.sync.register(BACKGROUND_SYNC_TAG);
  } catch (error) {
    console.log('[SW] Background sync registration failed');
  }
}

// Sync queued requests when online
async function syncQueuedRequests() {
  console.log('[SW] Syncing queued requests');

  try {
    const queuedRequests = await getQueuedRequests();

    for (const requestData of queuedRequests) {
      try {
        const request = new Request(requestData.url, {
          method: requestData.method,
          headers: requestData.headers,
          body: requestData.body
        });

        const response = await fetch(request);

        if (response.ok) {
          await removeRequestFromDB(requestData.timestamp);
          console.log('[SW] Successfully synced request:', requestData.url);
        } else {
          console.log('[SW] Sync failed for request:', requestData.url, response.status);
        }
      } catch (error) {
        console.log('[SW] Error syncing request:', requestData.url, error);
      }
    }

    // Notify clients about sync completion
    await notifyClients('sync-complete', {
      synced: queuedRequests.length,
      timestamp: Date.now()
    });

  } catch (error) {
    console.log('[SW] Background sync failed:', error);
  }
}

// Sync location updates for better matching
async function syncLocation() {
  try {
    const position = await getCurrentPosition();

    if (position) {
      const response = await fetch('/api/v1/users/location', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': await getStoredAuthToken()
        },
        body: JSON.stringify({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
          timestamp: Date.now()
        })
      });

      if (response.ok) {
        console.log('[SW] Location synced successfully');
      }
    }
  } catch (error) {
    console.log('[SW] Location sync failed:', error);
  }
}

// Sync pending messages
async function syncMessages() {
  try {
    const pendingMessages = await getPendingMessages();

    for (const message of pendingMessages) {
      try {
        const response = await fetch('/api/v1/chat/send', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': await getStoredAuthToken()
          },
          body: JSON.stringify({ receiverId: message.receiverId, content: message.content, timestamp: message.timestamp })
        });

        if (response.ok) {
          await removePendingMessage(message.id);
        }
      } catch (error) {
        console.log('[SW] Message sync failed:', error);
      }
    }
  } catch (error) {
    console.log('[SW] Messages sync failed:', error);
  }
}

// Push notification handling for dating app
self.addEventListener('push', (event) => {
  console.log('[SW] Push received');

  let data = {};

  if (event.data) {
    try {
      data = event.data.json();
    } catch (error) {
      data = { title: 'Dinner First', body: event.data.text() };
    }
  }

  const options = {
    title: data.title || 'Dinner First',
    body: data.body || 'You have a new notification',
    icon: '/assets/icons/icon-192x192.png',
    badge: '/assets/icons/badge-72x72.png',
    image: data.image,
    tag: data.tag || 'general',
    data: data.data || {},
    actions: getNotificationActions(data.type),
    requireInteraction: data.type === 'new_match' || data.type === 'photo_reveal',
    silent: false,
    vibrate: getVibrationPattern(data.type)
  };

  event.waitUntil(
    self.registration.showNotification(options.title, options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification clicked');

  event.notification.close();

  const data = event.notification.data;
  let url = '/';

  // Handle action button clicks
  if (event.action) {
    switch (event.action) {
      case 'reply':
        url = `/messages/${data.connectionId}`;
        break;
      case 'view_profile':
        url = `/profile/${data.userId}`;
        break;
      case 'view_revelation':
        url = `/revelations/${data.connectionId}`;
        break;
      default:
        url = '/';
    }
  } else {
    // Handle notification click based on type
    switch (data.type) {
      case 'new_message':
        url = `/messages/${data.connectionId}`;
        break;
      case 'new_match':
        url = '/discover';
        break;
      case 'new_revelation':
        url = `/revelations/${data.connectionId}`;
        break;
      case 'photo_reveal':
        url = `/connections/${data.connectionId}`;
        break;
      default:
        url = '/';
    }
  }

  event.waitUntil(
    clients.openWindow(url)
  );
});

// Notification action buttons based on type
function getNotificationActions(type) {
  switch (type) {
    case 'new_message':
      return [
        { action: 'reply', title: 'Reply' },
        { action: 'view_profile', title: 'View Profile' }
      ];
    case 'new_revelation':
      return [
        { action: 'view_revelation', title: 'View Revelation' },
        { action: 'reply', title: 'Respond' }
      ];
    case 'new_match':
      return [
        { action: 'view_profile', title: 'View Profile' }
      ];
    default:
      return [];
  }
}

// Vibration patterns for different notification types
function getVibrationPattern(type) {
  switch (type) {
    case 'new_message':
      return [100, 50, 100];
    case 'new_match':
      return [200, 100, 200, 100, 200];
    case 'new_revelation':
      return [300, 200, 100, 200, 300];
    case 'photo_reveal':
      return [500];
    default:
      return [200];
  }
}

// IndexedDB helper functions for persistent storage
async function storeRequestInDB(requestData) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('dinner_first-sync', 1);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction(['requests'], 'readwrite');
      const store = transaction.objectStore('requests');
      store.add(requestData);
      transaction.oncomplete = () => resolve();
    };

    request.onupgradeneeded = () => {
      const db = request.result;
      const store = db.createObjectStore('requests', { keyPath: 'timestamp' });
      store.createIndex('url', 'url', { unique: false });
    };
  });
}

async function getQueuedRequests() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('dinner_first-sync', 1);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction(['requests'], 'readonly');
      const store = transaction.objectStore('requests');
      const getAllRequest = store.getAll();

      getAllRequest.onsuccess = () => resolve(getAllRequest.result);
    };
  });
}

async function removeRequestFromDB(timestamp) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('dinner_first-sync', 1);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction(['requests'], 'readwrite');
      const store = transaction.objectStore('requests');
      store.delete(timestamp);
      transaction.oncomplete = () => resolve();
    };
  });
}

// Utility functions
async function getCurrentPosition() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocation not supported'));
      return;
    }

    navigator.geolocation.getCurrentPosition(resolve, reject, {
      enableHighAccuracy: true,
      timeout: 10000,
      maximumAge: 300000
    });
  });
}

async function getStoredAuthToken() {
  // This would retrieve the auth token from storage
  // Implementation depends on your auth storage strategy
  return ''; // Placeholder
}

async function getPendingMessages() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('dinner_first-sync', 1);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction(['pending-messages'], 'readonly');
      const store = transaction.objectStore('pending-messages');
      const getAllRequest = store.getAll();
      getAllRequest.onsuccess = () => resolve(getAllRequest.result || []);
    };
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains('pending-messages')) {
        db.createObjectStore('pending-messages', { keyPath: 'id' });
      }
    };
  });
}

async function removePendingMessage(messageId) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('dinner_first-sync', 1);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction(['pending-messages'], 'readwrite');
      const store = transaction.objectStore('pending-messages');
      store.delete(messageId);
      transaction.oncomplete = () => resolve();
    };
  });
}

async function notifyClients(type, data) {
  const clients = await self.clients.matchAll();

  clients.forEach(client => {
    client.postMessage({
      type: type,
      data: data
    });
  });
}
