import { useState, type FormEvent } from "react";
import { Modal } from "antd";
import {
  confirmPhoneChange,
  requestPhoneChange,
  verifyOldPhoneChange,
} from "../lib/session";

interface PhoneChangeDialogProps {
  currentPhone?: string;
  onClose: () => void;
  onCompleted: (phone: string) => void | Promise<void>;
}

type PhoneChangeStep = "request" | "verify-current" | "verify-new";

function asciiDigits(value: string): string {
  return value.replace(/[۰-۹٠-٩]/g, (digit) => {
    const code = digit.charCodeAt(0);
    const zero = code >= 0x06f0 ? 0x06f0 : 0x0660;
    return String(code - zero);
  });
}

export function PhoneChangeDialog({
  currentPhone,
  onClose,
  onCompleted,
}: PhoneChangeDialogProps) {
  const [step, setStep] = useState<PhoneChangeStep>("request");
  const [newPhone, setNewPhone] = useState("");
  const [code, setCode] = useState("");
  const [challengeId, setChallengeId] = useState<string | null>(null);
  const [devCode, setDevCode] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function restart(): void {
    setStep("request");
    setCode("");
    setChallengeId(null);
    setDevCode(null);
    setError(null);
  }

  async function submit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      if (step === "request") {
        const phone = asciiDigits(newPhone.trim());
        if (!/^09\d{9}$/.test(phone)) {
          throw new Error("شمارهٔ موبایل معتبر نیست (مثال: 09121234567)");
        }
        const result = await requestPhoneChange(phone);
        if (!result.challenge_id) throw new Error("شناسهٔ درخواست از سرور دریافت نشد");
        setChallengeId(result.challenge_id);
        setDevCode(result.dev_code ?? null);
        setCode("");
        setStep("verify-current");
      } else if (step === "verify-current") {
        const normalizedCode = asciiDigits(code.trim());
        if (!/^\d{6}$/.test(normalizedCode)) throw new Error("کد باید شش رقم باشد");
        if (!challengeId) throw new Error("درخواست تغییر شماره معتبر نیست؛ دوباره آغاز کنید");
        const result = await verifyOldPhoneChange(challengeId, normalizedCode);
        setDevCode(result.dev_code ?? null);
        setCode("");
        setStep("verify-new");
      } else {
        const normalizedCode = asciiDigits(code.trim());
        if (!/^\d{6}$/.test(normalizedCode)) throw new Error("کد باید شش رقم باشد");
        if (!challengeId) throw new Error("درخواست تغییر شماره معتبر نیست؛ دوباره آغاز کنید");
        const result = await confirmPhoneChange(challengeId, normalizedCode);
        if (result.status !== "phone_changed") throw new Error("تغییر شماره از سوی سرور تأیید نشد");
        await onCompleted(result.phone);
      }
    } catch (caught) {
      setError((caught as Error).message ?? String(caught));
    } finally {
      setBusy(false);
    }
  }

  const title =
    step === "request"
      ? "تغییر شمارهٔ موبایل"
      : step === "verify-current"
        ? "تأیید شمارهٔ فعلی"
        : "تأیید شمارهٔ جدید";
  const submitLabel =
    step === "request"
      ? "ارسال کد به شمارهٔ فعلی"
      : step === "verify-current"
        ? "تأیید کد فعلی و ارسال کد جدید"
        : "تأیید و تغییر شماره";

  return (
    <Modal
      centered
      cancelText="انصراف"
      closable={!busy}
      keyboard={!busy}
      maskClosable={false}
      open
      title={title}
      footer={null}
      onCancel={onClose}
    >
      <div className="space-y-4">
        <p className="text-sm text-ink-dim">
          {step === "request"
            ? "برای امنیت، ابتدا کد شمارهٔ فعلی و سپس کد شمارهٔ جدید لازم است. اگر به شمارهٔ فعلی دسترسی ندارید، این مسیر بازیابی قابل استفاده نیست."
            : step === "verify-current"
              ? `کد تأیید به شمارهٔ فعلی ${currentPhone ?? "حساب"} فرستاده شد.`
              : `شمارهٔ فعلی تأیید شد؛ کد جداگانه به ${asciiDigits(newPhone)} فرستاده شد.`}
        </p>

        <form className="space-y-4" onSubmit={(event) => void submit(event)}>
          {step === "request" ? (
            <label className="block space-y-1 text-sm">
              <span>شمارهٔ جدید</span>
              <input
                autoComplete="tel-national"
                className="focus-ring w-full rounded-xl border border-primary/20 bg-surface/70 px-3 py-2 text-left"
                dir="ltr"
                inputMode="tel"
                maxLength={11}
                onChange={(event) => setNewPhone(event.target.value)}
                placeholder="09xxxxxxxxx"
                value={newPhone}
              />
            </label>
          ) : (
            <label className="block space-y-1 text-sm">
              <span>{step === "verify-current" ? "کد شمارهٔ فعلی" : "کد شمارهٔ جدید"}</span>
              <input
                autoComplete="one-time-code"
                autoFocus
                className="focus-ring w-full rounded-xl border border-primary/20 bg-surface/70 px-3 py-2 text-left"
                dir="ltr"
                inputMode="numeric"
                maxLength={6}
                onChange={(event) => setCode(event.target.value)}
                value={code}
              />
              {devCode && <span className="block text-xs text-amber-300">کد آزمایشی: {devCode}</span>}
            </label>
          )}

          {error && <p className="text-sm text-rose-300" role="alert">{error}</p>}

          <div className="flex flex-wrap justify-end gap-2">
            {step !== "request" && (
              <button
                className="focus-ring rounded-xl px-3 py-2 text-sm text-ink-dim hover:bg-surface"
                disabled={busy}
                onClick={restart}
                type="button"
              >
                شروع دوباره
              </button>
            )}
            <button
              className="focus-ring rounded-xl px-3 py-2 text-sm text-ink-dim hover:bg-surface"
              disabled={busy}
              onClick={onClose}
              type="button"
            >
              انصراف
            </button>
            <button
              className="focus-ring rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
              disabled={busy}
              type="submit"
            >
              {busy ? "لطفاً صبر کنید…" : submitLabel}
            </button>
          </div>
        </form>
      </div>
    </Modal>
  );
}
