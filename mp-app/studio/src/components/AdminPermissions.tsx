/**
 * ماتریس مجوز شخصی ادمین — فاز ۵ (QF-03/QF-04).
 *
 * هر کلید یک تصمیم **سرورمحور** است: UI فقط درخواست می‌فرستد و سپس از سرور
 * بازخوانی می‌کند؛ هیچ سوییچی در `useState` محلی «سبز» نمی‌ماند. کنترل‌ها از
 * antd هستند (Q11: صفر کنترل دست‌ساز) و فقط مالک سیستم این بخش را می‌بیند —
 * سرور هم مستقل از UI همان را اعمال می‌کند (۴۰۳ برای ادمین).
 */
import { Alert, Button, Empty, Popconfirm, Select, Spin, Table, Tag } from "antd";
import { useCallback, useEffect, useMemo, useState } from "react";
import { roleFromToken } from "../lib/roleNav";
import {
  AuthError,
  fetchPermissionGrants,
  fetchPermissionKeys,
  fetchUsers,
  grantPermission,
  revokePermission,
  type PermissionGrant,
  type PermissionKey,
  type UserRow,
} from "../lib/adminApi";

const STATUS_LABEL: Record<PermissionGrant["status"], { label: string; color: string }> = {
  active: { label: "فعال", color: "green" },
  expired: { label: "منقضی", color: "gold" },
  revoked: { label: "سلب‌شده", color: "red" },
};

const EXPIRY_OPTIONS = [
  { value: 0, label: "بدون انقضا" },
  { value: 24, label: "۲۴ ساعت" },
  { value: 24 * 7, label: "۷ روز" },
  { value: 24 * 30, label: "۳۰ روز" },
  { value: 24 * 90, label: "۹۰ روز" },
];

function formatWhen(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "نامشخص";
  return d.toISOString().replace("T", " ").slice(0, 16) + " UTC";
}

export function AdminPermissions() {
  const isOwner = roleFromToken() === "super_admin";
  const [users, setUsers] = useState<UserRow[]>([]);
  const [keys, setKeys] = useState<PermissionKey[]>([]);
  const [grants, setGrants] = useState<PermissionGrant[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [permission, setPermission] = useState<string | null>(null);
  const [expiryHours, setExpiryHours] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [forbidden, setForbidden] = useState(false);

  const loadUsersAndKeys = useCallback(() => {
    setLoading(true);
    setError(null);
    return Promise.all([fetchUsers(), fetchPermissionKeys()])
      .then(([u, k]) => {
        setUsers(u);
        setKeys(k);
        // هدف پیش‌فرض اولین کاربر غیرمالک است؛ مالک به مجوز شخصی نیاز ندارد.
        setSelectedUserId((current) => current ?? u.find((row) => row.role !== "super_admin")?.id ?? null);
      })
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : "خطا در خواندن دادهٔ مدیریتی";
        if (err instanceof AuthError) setError(message);
        else if (message.includes("اجازه")) setForbidden(true);
        else setError(message);
      })
      .finally(() => setLoading(false));
  }, []);

  const loadGrants = useCallback((userId: number) => {
    return fetchPermissionGrants(userId)
      .then(setGrants)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "خطا"));
  }, []);

  useEffect(() => {
    if (isOwner) void loadUsersAndKeys();
  }, [isOwner, loadUsersAndKeys]);

  useEffect(() => {
    if (isOwner && selectedUserId !== null) void loadGrants(selectedUserId);
  }, [isOwner, selectedUserId, loadGrants]);

  const targets = useMemo(() => users.filter((u) => u.role !== "super_admin"), [users]);

  async function submit() {
    if (selectedUserId === null || !permission) return;
    setBusy(true);
    setError(null);
    try {
      await grantPermission(selectedUserId, permission, expiryHours > 0 ? expiryHours : null);
      await loadGrants(selectedUserId);
      setPermission(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "اعطای مجوز ناموفق بود");
    } finally {
      setBusy(false);
    }
  }

  async function revoke(row: PermissionGrant) {
    setBusy(true);
    setError(null);
    try {
      await revokePermission(row.id);
      await loadGrants(row.user_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "سلب مجوز ناموفق بود");
    } finally {
      setBusy(false);
    }
  }

  // همان قاعدهٔ RoleManager: برای غیرمالک هیچ درخواستی فرستاده نمی‌شود و بخش
  // رندر نمی‌شود؛ اما مرجع نهایی همچنان سرور است (۴۰۳ مستقل از UI).
  if (!isOwner) return null;

  if (forbidden) {
    return (
      <section className="glass-card p-5" aria-label="مجوزهای شخصی">
        <h3 className="text-sm font-semibold">مجوزهای شخصی</h3>
        <p className="mt-2 text-xs text-ink-dim">
          سرور این حساب را برای مدیریت مجوز مجاز نمی‌داند — فقط مالک سیستم مجاز است.
        </p>
      </section>
    );
  }

  return (
    <section className="glass-card p-5" aria-label="مجوزهای شخصی">
      <header className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">مجوزهای شخصی ادمین</h3>
        <Button size="small" onClick={() => void loadUsersAndKeys()} disabled={loading}>
          بازخوانی
        </Button>
      </header>
      <p className="mt-1 text-xs text-ink-dim">
        مالی و گزارش محرمانه برای ادمین/مدیر به‌طور پیش‌فرض بسته است؛ هر مجوز با مدت و وضعیت
        مؤثرش از سرور خوانده می‌شود.
      </p>

      {error && (
        <Alert className="mt-3" type="error" showIcon message={error} role="alert" />
      )}

      {loading ? (
        <div className="mt-4 flex justify-center">
          <Spin size="small" />
        </div>
      ) : (
        <>
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <label className="text-xs text-ink-dim">
              کاربر
              <Select
                className="mt-1 w-full"
                value={selectedUserId ?? undefined}
                onChange={(value: number) => setSelectedUserId(value)}
                options={targets.map((u) => ({
                  value: u.id,
                  label: `${u.full_name} — ${u.role}`,
                }))}
                placeholder="کاربر را انتخاب کنید"
                data-testid="permission-user"
              />
            </label>
            <label className="text-xs text-ink-dim">
              کلید مجوز
              <Select
                className="mt-1 w-full"
                value={permission ?? undefined}
                onChange={(value: string) => setPermission(value)}
                options={keys.map((k) => ({ value: k.key, label: k.key }))}
                placeholder="کلید مجوز"
                data-testid="permission-key"
              />
            </label>
            <label className="text-xs text-ink-dim">
              مدت
              <Select
                className="mt-1 w-full"
                value={expiryHours}
                onChange={(value: number) => setExpiryHours(value)}
                options={EXPIRY_OPTIONS}
                data-testid="permission-expiry"
              />
            </label>
          </div>

          <Button
            className="mt-3"
            type="primary"
            onClick={() => void submit()}
            loading={busy}
            disabled={selectedUserId === null || !permission}
          >
            اعطای مجوز
          </Button>

          <div className="mt-5">
            {grants.length === 0 ? (
              <Empty description="برای این کاربر مجوزی ثبت نشده" />
            ) : (
              <Table<PermissionGrant>
                size="small"
                rowKey="id"
                pagination={false}
                dataSource={grants}
                columns={[
                  { title: "کلید", dataIndex: "permission", key: "permission" },
                  {
                    title: "وضعیت",
                    key: "status",
                    render: (_, row) => (
                      <Tag color={STATUS_LABEL[row.status].color}>{STATUS_LABEL[row.status].label}</Tag>
                    ),
                  },
                  {
                    title: "انقضا",
                    key: "expires_at",
                    render: (_, row) => formatWhen(row.expires_at),
                  },
                  {
                    title: "ثبت",
                    key: "granted_at",
                    render: (_, row) => formatWhen(row.granted_at),
                  },
                  {
                    title: "",
                    key: "actions",
                    render: (_, row) =>
                      row.status === "active" ? (
                        <Popconfirm
                          title="این مجوز سلب شود؟"
                          okText="سلب کن"
                          cancelText="انصراف"
                          onConfirm={() => void revoke(row)}
                        >
                          <Button danger size="small" loading={busy}>
                            سلب
                          </Button>
                        </Popconfirm>
                      ) : null,
                  },
                ]}
              />
            )}
          </div>
        </>
      )}
    </section>
  );
}
