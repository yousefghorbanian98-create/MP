import { existsSync, readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";
import { resolve } from "node:path";
import { describe, expect, it, vi } from "vitest";

/**
 * D-024 — نسخهٔ وب به‌عنوان PWA قابل نصب.
 *
 * «نصب‌پذیر» ادعایی است که باید بررسی شود، نه فرض. اگر مانیفست آیکون‌هایش
 * را نداشته باشد یا `start_url` نباشد، مرورگر دکمهٔ نصب را نشان نمی‌دهد
 * و کاربر فکر می‌کند خراب است.
 */

const root = resolve(__dirname, "..");
const pub = (f: string) => resolve(root, "public", f);

type FakeResponse = {
  ok: boolean;
  status: number;
  type: string;
  headers: { get: (name: string) => string | null };
  clone: () => FakeResponse;
};

type CacheKey = string | { url: string };
const cacheKey = (key: CacheKey) => (typeof key === "string" ? key : key.url);

function response(status = 200, cacheControl: string | null = null): FakeResponse {
  const result: FakeResponse = {
    ok: status >= 200 && status < 300,
    status,
    type: "basic",
    headers: { get: (name) => (name.toLowerCase() === "cache-control" ? cacheControl : null) },
    clone: () => result,
  };
  return result;
}

function loadServiceWorker(initialCaches: string[] = ["mp-studio-v1", "unrelated-app-v1"]) {
  type Listener = (event: Record<string, unknown>) => void;
  const listeners = new Map<string, Listener>();
  const cacheNames = new Set(initialCaches);
  const deleted: string[] = [];
  const entries = new Map<string, Map<string, FakeResponse>>();
  const caches = {
    keys: vi.fn(async () => [...cacheNames]),
    delete: vi.fn(async (name: string) => {
      deleted.push(name);
      return cacheNames.delete(name);
    }),
    open: vi.fn(async (name: string) => {
      cacheNames.add(name);
      if (!entries.has(name)) entries.set(name, new Map());
      const values = entries.get(name)!;
      return {
        match: vi.fn(async (key: CacheKey) => values.get(cacheKey(key)) ?? null),
        put: vi.fn(async (key: CacheKey, value: FakeResponse) => {
          values.set(cacheKey(key), value);
        }),
      };
    }),
  };
  const fetchMock = vi.fn(async (_request: unknown) => response());
  const self = {
    location: { origin: "https://pwa.example" },
    addEventListener: (type: string, listener: Listener) => listeners.set(type, listener),
    skipWaiting: vi.fn(() => Promise.resolve()),
    clients: { claim: vi.fn(() => Promise.resolve()) },
  };
  const responseApi = { error: () => ({ type: "error", ok: false, status: 0 }) };
  const script = readFileSync(pub("sw.js"), "utf8");
  runInNewContext(script, { self, caches, fetch: fetchMock, URL, Response: responseApi, Promise });

  return {
    self,
    caches,
    fetchMock,
    deleted,
    entries,
    dispatchInstall: () => listeners.get("install")?.({}),
    dispatchMessage: (data: string) => listeners.get("message")?.({ data }),
    dispatchActivate: async () => {
      let pending: Promise<unknown> | undefined;
      listeners.get("activate")?.({ waitUntil: (value: Promise<unknown>) => (pending = Promise.resolve(value)) });
      await pending;
    },
    dispatchFetch: (request: { url: string; method: string; mode: string }) => {
      let pending: Promise<unknown> | undefined;
      listeners.get("fetch")?.({
        request,
        respondWith: (value: Promise<unknown>) => (pending = Promise.resolve(value)),
      });
      return { intercepted: pending !== undefined, response: pending };
    },
  };
}

describe("PWA installability (D-024)", () => {
  const raw = readFileSync(pub("manifest.webmanifest"), "utf8");
  const manifest = JSON.parse(raw) as Record<string, unknown>;

  it("declares a shared member-and-staff identity and install metadata", () => {
    expect(manifest.name).toBe("Muscle Paradise — باشگاه");
    expect(manifest.short_name).toBe("Muscle Paradise");
    expect(manifest.description).toContain("عضو و کادر");
    expect(manifest.start_url).toBe("/");
    expect(manifest.scope).toBe("/");
    expect(manifest.display).toBe("standalone");
  });

  it("is a Persian RTL app, not a mislabelled English one", () => {
    expect(manifest.lang).toBe("fa");
    expect(manifest.dir).toBe("rtl");
  });

  it("points at icons that actually exist on disk", () => {
    const icons = manifest.icons as { src: string; sizes: string }[];
    expect(icons.length).toBeGreaterThanOrEqual(2);
    for (const icon of icons) {
      const file = pub(icon.src.replace(/^\//, ""));
      expect(existsSync(file), `missing icon file ${icon.src}`).toBe(true);
      const bytes = readFileSync(file);
      // امضای PNG — فایل خالی یا متنی پذیرفته نمی‌شود
      expect(bytes.subarray(0, 8)).toEqual(
        Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
      );
    }
  });

  it("has a 512x512 maskable icon — Android requires it", () => {
    const icons = manifest.icons as { src: string; sizes: string; purpose?: string }[];
    expect(icons.some((i) => i.sizes === "512x512" && i.purpose === "maskable")).toBe(true);
  });

  it("links the manifest from index.html", () => {
    const html = readFileSync(resolve(root, "index.html"), "utf8");
    expect(html).toContain('rel="manifest"');
    expect(html).toContain("/manifest.webmanifest");
    expect(html).toContain("apple-touch-icon");
    expect(html).toContain(`<title>${manifest.name}</title>`);
    expect(html).toContain('name="apple-mobile-web-app-title" content="Muscle Paradise"');
  });

  it("does not auto-activate a waiting update before the user chooses it", () => {
    const worker = loadServiceWorker();
    worker.dispatchInstall();
    expect(worker.self.skipWaiting).not.toHaveBeenCalled();

    worker.dispatchMessage("UNRELATED_MESSAGE");
    expect(worker.self.skipWaiting).not.toHaveBeenCalled();

    worker.dispatchMessage("SKIP_WAITING");
    expect(worker.self.skipWaiting).toHaveBeenCalledOnce();
  });

  it("deletes only its own older cache versions on activation", async () => {
    const worker = loadServiceWorker(["mp-studio-v1", "another-app-shell", "http-cache"]);
    await worker.dispatchActivate();

    expect(worker.deleted).toEqual(["mp-studio-v1"]);
    expect(worker.caches.delete).toHaveBeenCalledTimes(1);
    expect(worker.caches.delete).toHaveBeenCalledWith("mp-studio-v1");
    expect(worker.self.clients.claim).toHaveBeenCalledOnce();
  });

  it("leaves API, writes, cross-origin, and query-string requests untouched", () => {
    const worker = loadServiceWorker();
    const requests = [
      { url: "https://pwa.example/api/v1/members/me", method: "GET", mode: "cors" },
      { url: "https://pwa.example/api", method: "GET", mode: "cors" },
      { url: "https://pwa.example/assets/index-AbCdef12.js", method: "POST", mode: "cors" },
      { url: "https://cdn.example/assets/index-AbCdef12.js", method: "GET", mode: "cors" },
      { url: "https://pwa.example/?token=private", method: "GET", mode: "navigate" },
    ];

    for (const request of requests) {
      expect(worker.dispatchFetch(request).intercepted).toBe(false);
    }
    expect(worker.fetchMock).not.toHaveBeenCalled();
    expect(worker.caches.open).not.toHaveBeenCalled();
  });

  it("caches only hashed same-origin static assets with public successful responses", async () => {
    const worker = loadServiceWorker();
    const publicAsset = response();
    worker.fetchMock.mockResolvedValueOnce(publicAsset);
    const result = worker.dispatchFetch({
      url: "https://pwa.example/assets/vendor-AbCdef123.css",
      method: "GET",
      mode: "cors",
    });

    expect(result.intercepted).toBe(true);
    await result.response;
    expect(worker.fetchMock).toHaveBeenCalledOnce();
    const appCache = worker.entries.get("mp-studio-v2");
    expect(appCache?.get("https://pwa.example/assets/vendor-AbCdef123.css")).toBe(publicAsset);

    const notHashed = worker.dispatchFetch({
      url: "https://pwa.example/assets/runtime.js",
      method: "GET",
      mode: "cors",
    });
    expect(notHashed.intercepted).toBe(false);

    const privateAsset = response(200, "private, max-age=0");
    worker.fetchMock.mockResolvedValueOnce(privateAsset);
    const privateResult = worker.dispatchFetch({
      url: "https://pwa.example/assets/private-AbCdef123.css",
      method: "GET",
      mode: "cors",
    });
    await privateResult.response;
    expect(appCache?.has("https://pwa.example/assets/private-AbCdef123.css")).toBe(false);

    const forbiddenAssets = [
      { url: "https://pwa.example/assets/not-found-AbCdef123.js", response: response(404) },
      { url: "https://pwa.example/assets/partial-AbCdef123.js", response: response(206) },
      { url: "https://pwa.example/assets/opaque-AbCdef123.js", response: { ...response(), type: "opaque" } },
      { url: "https://pwa.example/assets/no-store-AbCdef123.js", response: response(200, "no-store") },
    ];
    for (const asset of forbiddenAssets) {
      worker.fetchMock.mockResolvedValueOnce(asset.response);
      const uncached = worker.dispatchFetch({ url: asset.url, method: "GET", mode: "cors" });
      await uncached.response;
      expect(appCache?.has(asset.url)).toBe(false);
    }
  });

  it("uses one public app-shell cache entry as an offline fallback for deep links", async () => {
    const worker = loadServiceWorker();
    const shell = response();
    worker.fetchMock.mockResolvedValueOnce(shell);

    const online = worker.dispatchFetch({
      url: "https://pwa.example/",
      method: "GET",
      mode: "navigate",
    });
    await online.response;
    const appCache = worker.entries.get("mp-studio-v2");
    expect(appCache?.size).toBe(1);
    expect(appCache?.get("https://pwa.example/")).toBe(shell);

    worker.fetchMock.mockRejectedValueOnce(new TypeError("offline"));
    const offline = worker.dispatchFetch({
      url: "https://pwa.example/members/42",
      method: "GET",
      mode: "navigate",
    });
    await expect(offline.response).resolves.toBe(shell);
    expect(appCache?.size).toBe(1);
    expect(appCache?.has("https://pwa.example/members/42")).toBe(false);
  });

  it("reserves only /api and slash-delimited API paths, not /apix", () => {
    const nginx = readFileSync(resolve(root, "nginx.conf"), "utf8");
    const bareApiLocation = "location = /api {";
    const apiTreeLocation = "location ^~ /api/ {";
    const bareApiIndex = nginx.indexOf(bareApiLocation);
    const apiTreeIndex = nginx.indexOf(apiTreeLocation);
    const blockFor = (start: number) => nginx.slice(start, nginx.indexOf("\n    }", start));

    expect(bareApiIndex).toBeGreaterThanOrEqual(0);
    expect(apiTreeIndex).toBeGreaterThanOrEqual(0);
    expect(nginx).not.toContain("location ^~ /api {");
    for (const apiBlock of [blockFor(bareApiIndex), blockFor(apiTreeIndex)]) {
      expect(apiBlock).toContain("proxy_pass http://backend:8000;");
      expect(apiBlock).toContain("proxy_set_header X-Forwarded-For $remote_addr;");
    }

    // Static contract mirror: exact /api plus a segment-boundary /api/ prefix.
    const matchesApiNamespace = (path: string) => path === "/api" || path.startsWith("/api/");
    for (const path of ["/api", "/api/", "/api/v1/members/me"]) {
      expect(matchesApiNamespace(path), path).toBe(true);
    }
    for (const path of ["/apix", "/apiary", "/apix/v1/members/me"]) {
      expect(matchesApiNamespace(path), path).toBe(false);
    }

    expect(nginx).toContain("location / {");
    expect(nginx).toContain("try_files $uri $uri/ /index.html;");
  });

  it("registers the service worker outside production too", () => {
    // اگر فقط در PROD ثبت شود، تا لحظهٔ تحویل هرگز آزموده نمی‌شود
    const main = readFileSync(resolve(root, "src/main.tsx"), "utf8");
    const block = main.slice(main.indexOf("serviceWorker"));
    expect(block).toContain('register("/sw.js")');
    expect(block).not.toContain("import.meta.env.PROD");
  });
});
