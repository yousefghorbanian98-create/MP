/**
 * تست منطق آپدیت تفاضلی وب (M20).
 */
import { describe, expect, it, vi } from "vitest";
import { applyWaitingWorkerUpdate, isNewer, parseVersion } from "../src/lib/update";

describe("update logic", () => {
  it("مقایسهٔ نسخه قطعی است", () => {
    expect(parseVersion("1.1.0")).toEqual([1, 1, 0]);
    expect(parseVersion("1.0")).toEqual([1, 0, 0]); // نرمال‌سازی
    expect(isNewer("1.1.0", "1.0.9")).toBe(true);
    expect(isNewer("1.0.0", "1.0.0")).toBe(false);
    expect(isNewer("2.0.0", "1.9.9")).toBe(true);
    expect(isNewer("1.0.1", "1.0.10")).toBe(false); // 10 > 1 در جزء سوم
  });

  it("waits for an explicit activation to finish before reloading", () => {
    let state: ServiceWorkerState = "installed";
    const createTarget = () => {
      const listeners = new Map<string, Set<EventListener>>();
      return {
        addEventListener: vi.fn((type: string, listener: EventListener) => {
          const registered = listeners.get(type) ?? new Set<EventListener>();
          registered.add(listener);
          listeners.set(type, registered);
        }),
        removeEventListener: vi.fn((type: string, listener: EventListener) => {
          listeners.get(type)?.delete(listener);
        }),
        dispatch: (type: string) => {
          for (const listener of listeners.get(type) ?? []) listener(new Event(type));
        },
      };
    };
    const workerEvents = createTarget();
    const serviceWorkerEvents = createTarget();
    const waiting = {
      get state() {
        return state;
      },
      postMessage: vi.fn(),
      ...workerEvents,
    } as unknown as ServiceWorker;
    const serviceWorker = serviceWorkerEvents as unknown as ServiceWorkerContainer;
    const reload = vi.fn();

    applyWaitingWorkerUpdate({ waiting } as Pick<ServiceWorkerRegistration, "waiting">, serviceWorker, reload);
    expect(waiting.postMessage).toHaveBeenCalledWith("SKIP_WAITING");
    expect(reload).not.toHaveBeenCalled();

    state = "activating";
    workerEvents.dispatch("statechange");
    expect(reload).not.toHaveBeenCalled();

    state = "activated";
    workerEvents.dispatch("statechange");
    serviceWorkerEvents.dispatch("controllerchange");
    expect(reload).toHaveBeenCalledOnce();
    expect(workerEvents.removeEventListener).toHaveBeenCalled();
    expect(serviceWorkerEvents.removeEventListener).toHaveBeenCalled();
  });

  it("reloads directly when no service worker is waiting", () => {
    const events = {
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    } as unknown as ServiceWorkerContainer;
    const reload = vi.fn();

    applyWaitingWorkerUpdate({ waiting: null }, events, reload);

    expect(reload).toHaveBeenCalledOnce();
    expect(events.addEventListener).not.toHaveBeenCalled();
  });
});
