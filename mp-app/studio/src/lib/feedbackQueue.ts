/**
 * MEM-05 / PWA-34 — کلید idempotent نوشتن بازخورد ست.
 *
 * چرا این فایل جدا است: قاعدهٔ «دوباره‌ارسال نباید رکورد تکراری بسازد» یک قاعدهٔ
 * منطقی است، نه یک جزئیات UI. سرور کلیدش را `device_id:client_id` می‌گیرد و با
 * `updated_at` (LWW) تصمیم می‌گیرد. پس:
 *   - `client_id` یک بار ساخته می‌شود و **در همهٔ تلاش‌های همان ست ثابت می‌ماند**؛
 *   - `updated_at` هم همان تلاش ثابت می‌ماند؛ اگر timestamp عوض شود، سرور آن را
 *     نوشتهٔ تازه‌تری می‌بیند و همان کلید را بازنویسی می‌کند (که برای «همان ست»
 *     پذیرفتنی است ولی دیگر «unchanged» گزارش نمی‌شود)؛
 *   - تغییر مقدار فرم = نوشتهٔ منطقی تازه ⇒ `client_id` تازه.
 */
import type { SetFeedbackSyncItem } from "./api";
import { now as clockNow } from "./clock";

export const DEVICE_ID_KEY = "mp_device_id";

export interface PendingSetWrite {
  clientId: string;
  updatedAt: string;
  /** مقادیر همان نوشته؛ برای تشخیص «تغییر فرم ⇒ کلید تازه». */
  values: SetValues;
  item: SetFeedbackSyncItem;
}

function randomId(): string {
  const cryptoApi = globalThis.crypto;
  if (cryptoApi && typeof cryptoApi.randomUUID === "function") return cryptoApi.randomUUID();
  // jsdom قدیمی/مرورگر بدون randomUUID: شناسهٔ کافی برای یکتا بودن در صف همان دستگاه.
  const bytes = new Uint8Array(16);
  if (cryptoApi && typeof cryptoApi.getRandomValues === "function") {
    cryptoApi.getRandomValues(bytes);
  } else {
    for (let i = 0; i < bytes.length; i += 1) bytes[i] = Math.floor(Math.random() * 256);
  }
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
}

/**
 * شناسهٔ دستگاه در همین مرورگر نگه داشته می‌شود تا کلید سرور
 * (`device_id:client_id`) بین reloadها یکی بماند.
 */
export function getDeviceId(storage: Storage | undefined = safeStorage()): string {
  if (!storage) return `device-${randomId()}`;
  const existing = storage.getItem(DEVICE_ID_KEY);
  if (existing && existing.trim().length > 0) return existing;
  const created = `device-${randomId()}`.slice(0, 64);
  storage.setItem(DEVICE_ID_KEY, created);
  return created;
}

function safeStorage(): Storage | undefined {
  try {
    return globalThis.localStorage ?? undefined;
  } catch {
    return undefined;
  }
}

export interface SetValues {
  movementId: string;
  weight: number;
  targetReps: number;
  repsDone: number;
  rir: number | null;
  soreness: number | null;
  setsDone: number | null;
  notes: string;
}

const FIELD_ORDER: (keyof SetValues)[] = [
  "movementId",
  "weight",
  "targetReps",
  "repsDone",
  "rir",
  "soreness",
  "setsDone",
  "notes",
];

/** آیا مقدار فعلی فرم همان نوشتهٔ معلق قبلی است؟ (برای تصمیم «همان کلید» یا «کلید تازه») */
export function sameValues(a: SetValues, b: SetValues): boolean {
  return FIELD_ORDER.every((field) => a[field] === b[field]);
}

export function buildPendingWrite(
  values: SetValues,
  programId: number | null,
  options: { deviceId: string; at?: Date; clientId?: string },
): PendingSetWrite {
  const clientId = options.clientId ?? `set-${randomId()}`.slice(0, 64);
  const updatedAt = (options.at ?? clockNow()).toISOString();
  return {
    clientId,
    updatedAt,
    values,
    item: {
      client_id: clientId,
      device_id: options.deviceId,
      // ساعت کلاینت تنها مبنای LWW است؛ صادقانه همان چیزی است که دستگاه می‌داند.
      updated_at: updatedAt,
      program_id: programId,
      movement_id: values.movementId,
      weight: values.weight,
      target_reps: values.targetReps,
      reps_done: values.repsDone,
      rir: values.rir ?? undefined,
      soreness: values.soreness ?? undefined,
      notes: values.notes,
    },
  };
}
