import { Jp7TrendPanel } from "../components/Jp7TrendPanel";
import { RemindersPanel } from "../components/RemindersPanel";
import { SegmentalPanel } from "../components/SegmentalPanel";
import { useAppStore } from "../stores/appStore";

/**
 * ارزیابی — روند شاخص‌های بدنی عضو انتخاب‌شده.
 *
 * مثل صفحهٔ تغذیه، بدون انتخاب عضو هیچ عضوی فرض نمی‌شود: نمایش دادهٔ
 * یک عضو تصادفی، بدتر از نمایش «انتخاب کنید» است.
 */
export function Assessment() {
  const memberId = useAppStore((s) => s.selectedMemberId);

  if (memberId === null) {
    return (
      <div className="glass-card p-10 text-center text-sm text-ink-dim">
        برای دیدن روند ارزیابی، اول یک عضو را از صفحهٔ «اعضا» انتخاب کنید.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <Jp7TrendPanel memberId={memberId} />
      <SegmentalPanel />
      <RemindersPanel />
    </div>
  );
}
