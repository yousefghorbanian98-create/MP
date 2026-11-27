import { fetchMe, fetchMemberMemberships, type MemberMembership } from "../lib/api";
import {
  formatMemberConstraints,
  formatMemberDateTime,
  getMemberMembershipView,
  type MemberMembershipState,
} from "../lib/memberAccount";
import { now } from "../lib/clock";
import { fa, useApi } from "../lib/useApi";

const statusPresentation: Record<MemberMembershipState, { label: string; className: string }> = {
  active: { label: "فعال", className: "pill-green" },
  expiring: { label: "رو به پایان", className: "pill-gold" },
  expired: { label: "منقضی", className: "pill-red" },
  cancelled: { label: "لغوشده", className: "pill-muted" },
  unknown: { label: "نامعلوم", className: "pill-muted" },
};

function RequestState({
  loading,
  error,
  needsSession,
  onRetry,
  loadingLabel,
}: {
  loading: boolean;
  error: string | null;
  needsSession: boolean;
  onRetry: () => void;
  loadingLabel: string;
}) {
  if (loading) {
    return <p role="status" className="py-4 text-sm text-ink-dim">{loadingLabel}</p>;
  }
  if (!error) return null;
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-danger/20 px-4 py-3">
      <p role="alert" className="text-sm text-danger">
        {needsSession ? "نشست معتبر نیست؛ دوباره با کد یک‌بارمصرف وارد شوید." : error}
      </p>
      <button type="button" onClick={onRetry} className="focus-ring rounded-lg px-3 py-2 text-sm text-primary-light underline">
        تلاش دوباره
      </button>
    </div>
  );
}

export function MemberAccount() {
  const profile = useApi((signal) => fetchMe(undefined, signal), []);

  if (profile.loading || profile.error) {
    return (
      <div className="space-y-4" aria-labelledby="member-account-title">
        <h3 id="member-account-title" className="text-lg font-bold">حساب و عضویت</h3>
        <RequestState
          loading={profile.loading}
          error={profile.error}
          needsSession={profile.needsSession}
          onRetry={profile.reload}
          loadingLabel="در حال دریافت حساب عضو…"
        />
      </div>
    );
  }

  if (!profile.data || profile.data.role !== "member") {
    return (
      <div className="space-y-4" aria-labelledby="member-account-title">
        <h3 id="member-account-title" className="text-lg font-bold">حساب و عضویت</h3>
        <p role="alert" className="rounded-xl border border-danger/20 px-4 py-3 text-sm text-danger">
          هویت حساب عضو از پاسخ سرور تأیید نشد؛ اطلاعات شخصی نمایش داده نمی‌شود.
        </p>
        <button type="button" onClick={profile.reload} className="focus-ring rounded-lg px-3 py-2 text-sm text-primary-light underline">
          تلاش دوباره
        </button>
      </div>
    );
  }

  if (!Number.isSafeInteger(profile.data.id) || profile.data.id <= 0) {
    return (
      <div className="space-y-4" aria-labelledby="member-account-title">
        <h3 id="member-account-title" className="text-lg font-bold">حساب و عضویت</h3>
        <p role="alert" className="rounded-xl border border-danger/20 px-4 py-3 text-sm text-danger">
          شناسهٔ پروفایل عضو از سرور معتبر نیست؛ سابقهٔ اشتراک درخواست نشد.
        </p>
      </div>
    );
  }

  const constraints = formatMemberConstraints(profile.data.constraints ?? "");

  return (
    <div className="space-y-5" aria-labelledby="member-account-title">
      <h3 id="member-account-title" className="text-lg font-bold">حساب و عضویت</h3>
      <section className="rounded-xl border border-primary/10 p-4" aria-labelledby="member-profile-title">
        <h4 id="member-profile-title" className="text-base font-semibold">پروفایل من</h4>
        <dl className="mt-4 grid gap-4 sm:grid-cols-2">
          <div>
            <dt className="text-xs text-ink-dim">نام</dt>
            <dd className="mt-1 text-sm">{profile.data.full_name || "نام ثبت نشده"}</dd>
          </div>
          <div>
            <dt className="text-xs text-ink-dim">شمارهٔ همراه</dt>
            <dd className="mt-1 text-sm" dir="ltr">{profile.data.phone || "شماره ثبت نشده"}</dd>
          </div>
          <div>
            <dt className="text-xs text-ink-dim">هدف ثبت‌شده</dt>
            <dd className="mt-1 text-sm">{profile.data.goal || "ثبت نشده"}</dd>
          </div>
          <div>
            <dt className="text-xs text-ink-dim">جنسیت ثبت‌شده</dt>
            <dd className="mt-1 text-sm">{profile.data.gender || "ثبت نشده"}</dd>
          </div>
          <div>
            <dt className="text-xs text-ink-dim">قد ثبت‌شده</dt>
            <dd className="mt-1 text-sm">
              {profile.data.height_cm == null ? "ثبت نشده" : `${fa(profile.data.height_cm)} سانتی‌متر`}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-ink-dim">محدودیت‌ها و آسیب‌های ثبت‌شده</dt>
            <dd className="mt-1 text-sm">
              {constraints.length === 0 ? (
                "محدودیتی ثبت نشده"
              ) : (
                <ul className="list-inside list-disc space-y-1">
                  {constraints.map((constraint, index) => <li key={`${constraint}-${index}`}>{constraint}</li>)}
                </ul>
              )}
            </dd>
          </div>
        </dl>
      </section>
      <MemberMembershipHistory memberId={profile.data.id} />
    </div>
  );
}

function MemberMembershipHistory({ memberId }: { memberId: number }) {
  const history = useApi(
    (signal) => fetchMemberMemberships(memberId, undefined, signal),
    [memberId],
  );

  return (
    <section className="space-y-3" aria-labelledby="member-membership-title">
      <div>
        <h4 id="member-membership-title" className="text-base font-semibold">وضعیت و تاریخچهٔ عضویت</h4>
        <p className="mt-1 text-xs text-ink-dim">تاریخ‌ها به تقویم فارسی و به وقت تهران نمایش داده می‌شوند.</p>
      </div>
      <RequestState
        loading={history.loading}
        error={history.error}
        needsSession={history.needsSession}
        onRetry={history.reload}
        loadingLabel="در حال دریافت سابقهٔ عضویت از سرور…"
      />
      {!history.loading && !history.error && history.data?.length === 0 && (
        <p role="status" className="rounded-xl border border-primary/10 px-4 py-4 text-sm text-ink-dim">
          سابقهٔ اشتراکی در حساب شما ثبت نشده است؛ این وضعیت به معنی «منقضی» نیست.
        </p>
      )}
      {!history.loading && !history.error && history.data && history.data.length > 0 && (
        <div className="space-y-3">
          {history.data.map((membership) => (
            <MembershipCard key={membership.id} membership={membership} />
          ))}
        </div>
      )}
    </section>
  );
}

function MembershipCard({ membership }: { membership: MemberMembership }) {
  const view = getMemberMembershipView(membership, now());
  const presentation = statusPresentation[view.state];

  return (
    <article className="rounded-xl border border-primary/10 p-4" aria-label={`اشتراک ${membership.plan_name || "بدون نام"}`}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h5 className="font-semibold">{membership.plan_name || "نام پلن ثبت نشده"}</h5>
        <span className={presentation.className}>{presentation.label}</span>
      </div>
      <dl className="mt-4 grid gap-4 sm:grid-cols-2">
        <div>
          <dt className="text-xs text-ink-dim">شروع</dt>
          <dd className="mt-1 text-sm">
            <time dateTime={membership.started_at}>{formatMemberDateTime(membership.started_at)}</time>
          </dd>
        </div>
        <div>
          <dt className="text-xs text-ink-dim">اعتبار تا</dt>
          <dd className="mt-1 text-sm">
            <time dateTime={membership.expires_at}>{formatMemberDateTime(membership.expires_at)}</time>
          </dd>
        </div>
      </dl>
      {(view.state === "active" || view.state === "expiring") && view.daysLeft !== null && (
        <p className="mt-3 text-xs text-ink-dim">{fa(view.daysLeft)} روز تا پایان اعتبار</p>
      )}
    </article>
  );
}
