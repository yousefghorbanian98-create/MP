/*
 * Service Worker برای shell استاتیک Studio/PWA.
 * مرز cache: فقط GETهای same-origin، assetهای Vite هش‌دار و app shell عمومی.
 * API، فرم‌های نوشتنی، query string، پاسخ private/no-store و cacheهای اپ‌های دیگر
 * هرگز از این worker خوانده/ذخیره/حذف نمی‌شوند.
 */
const CACHE_PREFIX = "mp-studio-";
const CACHE_NAME = "mp-studio-v2";
const APP_SHELL_KEY = new URL("/", self.location.origin).href;
const HASHED_STATIC_ASSET =
  /^\/assets\/[A-Za-z0-9_.-]+-[A-Za-z0-9_-]{8,}\.(?:css|js|svg|png|webp|woff2?|ttf)$/i;

function isCacheableResponse(response) {
  if (!response || response.status !== 200 || response.type !== "basic") return false;
  const cacheControl = response.headers?.get?.("cache-control") ?? "";
  return !/\b(?:private|no-store)\b/i.test(cacheControl);
}

function isApiPath(pathname) {
  return pathname === "/api" || pathname.startsWith("/api/");
}

// Leave an update in the waiting state until the user chooses to apply it.
// First installation still activates normally because there is no prior worker.
self.addEventListener("install", () => {});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => key.startsWith(CACHE_PREFIX) && key !== CACHE_NAME)
            .map((key) => caches.delete(key)),
        ),
      )
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("message", (event) => {
  // پیام فقط از بنر update بعد از انتخاب کاربر فرستاده می‌شود.
  if (event.data === "SKIP_WAITING") self.skipWaiting();
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin || url.search || isApiPath(url.pathname)) return;

  if (HASHED_STATIC_ASSET.test(url.pathname)) {
    event.respondWith(
      (async () => {
        const cache = await caches.open(CACHE_NAME);
        const hit = await cache.match(request);
        if (hit) return hit;

        const response = await fetch(request);
        if (isCacheableResponse(response)) await cache.put(request, response.clone());
        return response;
      })(),
    );
    return;
  }

  if (request.mode !== "navigate") return;

  event.respondWith(
    (async () => {
      const cache = await caches.open(CACHE_NAME);
      try {
        const response = await fetch(request);
        // Only the stable public app entry is persisted, never a deep-link URL.
        if (
          (url.pathname === "/" || url.pathname === "/index.html") &&
          isCacheableResponse(response)
        ) {
          await cache.put(APP_SHELL_KEY, response.clone());
        }
        return response;
      } catch {
        return (await cache.match(APP_SHELL_KEY)) ?? Response.error();
      }
    })(),
  );
});
