/**
 * منطق آپدیت تفاضلی وب (M20) — قابل تست: مقایسهٔ نسخه + تصمیم به‌روزرسانی.
 */
import { useEffect, useState } from "react";

export interface UpdateManifest {
  update_available: boolean;
  force?: boolean;
  latest: string;
  current: string;
  min_supported: string;
  notes: string;
  mode?: "delta" | "full";
}

export function parseVersion(v: string): number[] {
  const parts = v
    .trim()
    .split(".")
    .map((c) => parseInt(c.replace(/\D/g, ""), 10) || 0);
  while (parts.length < 3) parts.push(0);
  return parts.slice(0, 3);
}

export function isNewer(candidate: string, current: string): boolean {
  const a = parseVersion(candidate);
  const b = parseVersion(current);
  for (let i = 0; i < 3; i++) {
    if (a[i] !== b[i]) return a[i] > b[i];
  }
  return false;
}

export async function checkUpdate(
  platform: "web" | "kiosk" | "android",
  current: string,
  base = "/api/v1"
): Promise<UpdateManifest> {
  const resp = await fetch(`${base}/updates/manifest?platform=${platform}&current=${current}`);
  return (await resp.json()) as UpdateManifest;
}

/** Activate a waiting worker only on explicit user action, then reload after takeover. */
export function applyWaitingWorkerUpdate(
  registration: Pick<ServiceWorkerRegistration, "waiting"> | undefined,
  serviceWorker: Pick<ServiceWorkerContainer, "addEventListener" | "removeEventListener">,
  reload: () => void,
): void {
  const waiting = registration?.waiting;
  if (!waiting) {
    reload();
    return;
  }

  let reloaded = false;
  const cleanup = () => {
    waiting.removeEventListener("statechange", reloadAfterActivation);
    serviceWorker.removeEventListener("controllerchange", reloadAfterActivation);
  };
  const reloadAfterActivation = () => {
    if (waiting.state !== "activated" || reloaded) return;
    reloaded = true;
    cleanup();
    reload();
  };

  waiting.addEventListener("statechange", reloadAfterActivation);
  serviceWorker.addEventListener("controllerchange", reloadAfterActivation);
  waiting.postMessage("SKIP_WAITING");
  reloadAfterActivation();
}

/** قلاب React: بررسی دوره‌ای مانیفست + وضعیت آمادهٔ به‌روزرسانی. */
export function useUpdateCheck(current: string, platform: "web" | "kiosk" = "web", intervalMs = 30 * 60_000) {
  const [manifest, setManifest] = useState<UpdateManifest | null>(null);

  useEffect(() => {
    let alive = true;
    const tick = () =>
      checkUpdate(platform, current)
        .then((m) => alive && m.update_available && setManifest(m))
        .catch(() => undefined);
    tick();
    const id = setInterval(tick, intervalMs);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [current, platform, intervalMs]);

  const apply = () => {
    if (!("serviceWorker" in navigator)) {
      window.location.reload();
      return;
    }

    const serviceWorker = navigator.serviceWorker;
    void serviceWorker
      .getRegistration()
      .then((registration) =>
        applyWaitingWorkerUpdate(registration, serviceWorker, () => window.location.reload()),
      )
      .catch(() => window.location.reload());
  };

  return { manifest, apply };
}
