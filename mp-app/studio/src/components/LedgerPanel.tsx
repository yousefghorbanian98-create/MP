/**
 * دفتر پول عضو (QF-05) — موجودی، تطبیق و معکوس‌سازی با دلیل.
 *
 * چرا این پنل: API دفتر و معکوس‌سازی وجود داشت ولی هیچ مصرف‌کنندهٔ واقعی در
 * Studio نداشت؛ یعنی «قابلیت» فقط در تست بود. این‌جا همان کار از UI انجام
 * می‌شود و هر ردیف فقط با **ردیف جبرانی** و دلیل اصلاح می‌شود، نه ویرایش مبلغ.
 *
 * رفتار عمدی: هیچ درخواستی هنگام mount فرستاده نمی‌شود. کاربر اول شناسهٔ عضو
 * را می‌دهد؛ این‌طور صفحهٔ مالی با یک درخواست اضافی و بدون مقصد شلوغ نمی‌شود.
 */
import { Alert, Button, Empty, Input, InputNumber, Modal, Spin, Table, Tag } from "antd";
import { useState } from "react";
import {
  fetchMemberLedger,
  reverseLedgerEntry,
  type LedgerRow,
  type MemberLedger,
} from "../lib/api";

const KIND_LABELS: Record<LedgerRow["kind"], string> = {
  charge: "شارژ",
  pay: "پرداخت",
  refund: "بازگشت",
  reversal: "معکوس‌سازی",
};

const rial = (value: number) => `${value.toLocaleString("fa-IR")} ریال`;

export function LedgerPanel() {
  const [memberId, setMemberId] = useState<number | null>(null);
  const [ledger, setLedger] = useState<MemberLedger | null>(null);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [reversing, setReversing] = useState<LedgerRow | null>(null);
  const [reason, setReason] = useState("");

  async function load(id = memberId) {
    if (id === null || !Number.isFinite(id) || id < 1) {
      setError("شناسهٔ عضو باید عدد مثبت باشد");
      return;
    }
    setLoading(true);
    setError("");
    try {
      setLedger(await fetchMemberLedger(id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "خواندن دفتر ناموفق بود");
    } finally {
      setLoading(false);
    }
  }

  async function submitReverse() {
    if (!reversing) return;
    if (reason.trim().length < 3) {
      setError("دلیل معکوس‌سازی اجباری است (حداقل ۳ نویسه)");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await reverseLedgerEntry(reversing.id, reason.trim());
      setReversing(null);
      setReason("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "معکوس‌سازی ناموفق بود");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="glass-card space-y-3 p-5" aria-label="دفتر پول عضو">
      <header>
        <h2 className="text-sm font-bold">دفتر پول عضو</h2>
        <p className="mt-1 text-xs text-ink-dim">
          هر حرکت کیف‌پول یک ردیف فقط-افزودنی است. اشتباه با ردیف جبرانی و دلیل اصلاح
          می‌شود؛ ردیف اصلی هرگز تغییر نمی‌کند.
        </p>
      </header>

      <div className="flex flex-wrap items-end gap-3">
        <label className="text-xs text-ink-dim">
          شناسهٔ عضو
          <InputNumber<number>
            aria-label="شناسهٔ عضو برای دفتر"
            className="mt-1 block w-36"
            min={1}
            controls={false}
            value={memberId}
            onChange={(value) => setMemberId(value)}
          />
        </label>
        <Button type="primary" onClick={() => void load()} loading={loading}>
          نمایش دفتر
        </Button>
      </div>

      {error && <Alert type="error" showIcon message={error} role="alert" />}

      {loading && !ledger ? (
        <div className="flex justify-center p-4">
          <Spin size="small" />
        </div>
      ) : ledger ? (
        <div className="space-y-3">
          <div className="grid gap-2 sm:grid-cols-3">
            <div className="rounded-xl bg-primary/10 p-3 text-center">
              <p className="text-xs text-ink-dim">موجودی کیف‌پول</p>
              <p className="text-sm font-bold">{rial(ledger.balance_rial)}</p>
            </div>
            <div className="rounded-xl bg-primary/10 p-3 text-center">
              <p className="text-xs text-ink-dim">مجموع دفتر</p>
              <p className="text-sm font-bold">{rial(ledger.reconcile.ledger_balance_rial)}</p>
            </div>
            <div className="rounded-xl bg-primary/10 p-3 text-center">
              <p className="text-xs text-ink-dim">تطبیق</p>
              <Tag color={ledger.reconcile.matches ? "green" : "red"}>
                {ledger.reconcile.matches
                  ? "منطبق"
                  : `اختلاف ${rial(ledger.reconcile.difference_rial)}`}
              </Tag>
            </div>
          </div>

          {ledger.entries.length === 0 ? (
            <Empty description="رویدادی برای این عضو ثبت نشده است" />
          ) : (
            <Table<LedgerRow>
              size="small"
              rowKey="id"
              pagination={false}
              dataSource={ledger.entries}
              columns={[
                { title: "شناسه", dataIndex: "id", key: "id" },
                {
                  title: "نوع",
                  key: "kind",
                  render: (_, row) => <Tag>{KIND_LABELS[row.kind] ?? row.kind}</Tag>,
                },
                {
                  title: "مبلغ",
                  key: "amount_rial",
                  render: (_, row) => rial(row.amount_rial),
                },
                {
                  title: "وضعیت",
                  key: "status",
                  render: (_, row) =>
                    row.reversed_by_entry_id ? (
                      <Tag color="orange">معکوس‌شده</Tag>
                    ) : row.reverses_entry_id ? (
                      <Tag color="purple">جبرانی</Tag>
                    ) : (
                      <Tag color="green">فعال</Tag>
                    ),
                },
                {
                  title: "",
                  key: "actions",
                  render: (_, row) => (
                    <Button
                      size="small"
                      disabled={row.reversed_by_entry_id !== null || row.kind === "reversal"}
                      onClick={() => {
                        setReversing(row);
                        setReason("");
                      }}
                    >
                      معکوس‌سازی
                    </Button>
                  ),
                },
              ]}
            />
          )}
        </div>
      ) : null}

      <Modal
        title="معکوس‌سازی ردیف دفتر"
        open={reversing !== null}
        okText="ثبت معکوس"
        cancelText="انصراف"
        confirmLoading={busy}
        onOk={() => void submitReverse()}
        onCancel={() => {
          setReversing(null);
          setReason("");
        }}
      >
        <p className="text-xs text-ink-dim">
          ردیف جبرانی با علامت مخالف ساخته می‌شود و در ممیزی با نام شما ثبت است. دلیل
          اجباری است.
        </p>
        <Input
          aria-label="دلیل معکوس‌سازی"
          className="mt-3"
          placeholder="دلیل (اجباری)"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
        />
      </Modal>
    </section>
  );
}
