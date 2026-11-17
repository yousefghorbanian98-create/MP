import { useEffect, useState } from "react";
import { roleFromToken } from "../lib/roleNav";
import {
  AuthError,
  fetchAudit,
  fetchUsers,
  revokeUserRole,
  setUserRole,
  type AuditRow,
  type UserRow,
} from "../lib/adminApi";

const roleLabels: Record<string, string> = {
  member: "عضو",
  reception: "پذیرش",
  coach: "مربی",
  manager: "مدیر",
  admin: "ادمین",
  super_admin: "مالک",
};

/** مدیریت نقش‌ها = «admin pass» (M43-c2) — فقط مالک سیستم؛ هر تغییر در لاگ ممیزی. */
export function RoleManager() {
  const isOwner = roleFromToken() === "super_admin";
  const [users, setUsers] = useState<UserRow[]>([]);
  const [audit, setAudit] = useState<AuditRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = () => {
    setError(null);
    Promise.all([fetchUsers(), fetchAudit("role_grant")])
      .then(([u, a]) => {
        setUsers(u);
        setAudit(a);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "خطا"));
  };

  useEffect(() => {
    if (isOwner) load();
  }, [isOwner]);

  const change = async (id: number, role: string) => {
    setBusy(true);
    setError(null);
    try {
      await setUserRole(id, role);
      load();
    } catch (e) {
      setError(e instanceof AuthError ? e.message : e instanceof Error ? e.message : "خطا");
    } finally {
      setBusy(false);
    }
  };

  if (!isOwner) return null;

  return (
    <div className="glass-card p-5">
      <h3 className="text-sm font-bold">admin pass — نقش‌های کاربران</h3>
      <p className="mt-0.5 text-[11px] text-ink-dim">
        فقط مالک سیستم (super_admin) می‌تواند نقش بدهد؛ تغییر نقش خودتان ممنوع است؛ هر تغییر در لاگ ممیزی ثبت می‌شود
      </p>
      {error && (
        <p className="mt-2 rounded-lg bg-rose-500/10 px-3 py-2 text-xs text-rose-300" role="alert">
          {error}
          <span className="mt-1 block text-[11px] text-ink-dim">
            این بخش فقط برای مالک سیستم (super_admin) باز است؛ مدیر معمولی ۴۰۳ می‌گیرد و
            لیست خالی نشان داده نمی‌شود.
          </span>
        </p>
      )}
      <div className="mt-3 space-y-2">
        {users.map((u) => (
          <div key={u.id} className="flex items-center gap-3 rounded-xl bg-surface/60 px-3 py-2">
            <span className="flex-1 truncate text-sm">{u.full_name} · {u.phone}</span>
            <select
              className="rounded-lg bg-surface px-2 py-1 text-xs"
              value={u.role}
              disabled={busy}
              onChange={(e) => change(u.id, e.target.value)}
            >
              {Object.entries(roleLabels).map(([key, label]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>
            {u.role !== "member" && (
              <button
                className="rounded-lg bg-red-500/10 px-2 py-1 text-[11px] text-red-400 disabled:opacity-50"
                disabled={busy}
                onClick={() => revokeUserRole(u.id).then(load).catch((e) => setError(e.message))}
              >
                ابطال
              </button>
            )}
          </div>
        ))}
        {users.length === 0 && !error && <p className="text-xs text-ink-dim">کاربری نمایش داده نمی‌شود</p>}
      </div>
      <h4 className="mt-5 text-xs font-semibold">آخرین تغییرات نقش (لاگ ممیزی)</h4>
      <div className="mt-2 space-y-1">
        {audit.slice(0, 6).map((row) => (
          <p key={row.id} className="text-[11px] text-ink-dim">
            #{row.id} · کاربر {row.entity_id} · {row.detail} · {row.created_at?.slice(0, 16).replace("T", " ")}
          </p>
        ))}
        {audit.length === 0 && <p className="text-[11px] text-ink-dim">تغییری ثبت نشده</p>}
      </div>
    </div>
  );
}
