/**
 * صف بازبینی فیش کارت‌به‌کارت — فاز ۶ (QF-08/QF-09).
 *
 * قاعده‌ها:
 *   • فهرست از سرور می‌آید (`GET /payments?status=in_review`)، هیچ ردیف نمونه‌ای
 *     ساخته نمی‌شود.
 *   • تأیید/رد فقط درخواست می‌فرستد و سپس بازخوانی می‌کند؛ اگر سرور ۴۰۳ بدهد
 *     (مجوز `finance.write` نبودن یا تأیید پرداخت خود) همان پیام نمایش داده
 *     می‌شود و ردیف خوش‌بینانه حذف نمی‌شود.
 *   • دلیل رد اجباری است و از کنترل کتابخانه‌ای antd گرفته می‌شود (Q11).
 */
import { Alert, Button, Empty, Input, Modal, Popconfirm, Spin, Table, Tag } from "antd";
import { useCallback, useEffect, useState } from "react";
import {
  approveReceipt,
  AuthError,
  fetchReviewQueue,
  rejectReceipt,
  type PaymentRow,
} from "../lib/api";

const formatRial = (value: number) => `${value.toLocaleString("fa-IR")} ریال`;

export function ReceiptQueue() {
  const [rows, setRows] = useState<PaymentRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [rejecting, setRejecting] = useState<PaymentRow | null>(null);
  const [reason, setReason] = useState("");

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    return fetchReviewQueue()
      .then((data) => setRows(Array.isArray(data) ? data : []))
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "خطا در خواندن صف بازبینی");
        if (err instanceof AuthError) setRows([]);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function approve(row: PaymentRow) {
    setBusyId(row.id);
    setError(null);
    try {
      await approveReceipt(row.id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "تأیید فیش ناموفق بود");
    } finally {
      setBusyId(null);
    }
  }

  async function submitReject() {
    if (!rejecting || reason.trim().length < 3) return;
    const target = rejecting;
    setBusyId(target.id);
    try {
      await rejectReceipt(target.id, reason.trim());
      setRejecting(null);
      setReason("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "رد فیش ناموفق بود");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <section className="glass-card p-5" aria-label="صف بازبینی فیش‌ها">
      <header className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">صف بازبینی فیش کارت‌به‌کارت</h3>
        <Button size="small" onClick={() => void load()} disabled={loading}>
          بازخوانی
        </Button>
      </header>
      <p className="mt-1 text-xs text-ink-dim">
        هر تأیید، پرداخت و (در صورت وجود پلن) اشتراک عضو را در یک تراکنش ثبت می‌کند؛ تأیید
        پرداختی که خودتان ثبت کرده‌اید مجاز نیست.
      </p>

      {error && <Alert className="mt-3" type="error" showIcon message={error} role="alert" />}

      {loading ? (
        <div className="mt-4 flex justify-center">
          <Spin size="small" />
        </div>
      ) : rows.length === 0 ? (
        <Empty className="mt-4" description="فیشی در انتظار بازبینی نیست" />
      ) : (
        <Table<PaymentRow>
          className="mt-4"
          size="small"
          rowKey="id"
          pagination={false}
          dataSource={rows}
          columns={[
            { title: "شناسه", dataIndex: "id", key: "id" },
            { title: "عضو", dataIndex: "member_id", key: "member_id" },
            {
              title: "مبلغ",
              key: "amount_rial",
              render: (_, row) => formatRial(row.amount_rial),
            },
            {
              title: "وضعیت",
              key: "status",
              render: (_, row) => <Tag color="gold">{row.status}</Tag>,
            },
            {
              title: "",
              key: "actions",
              render: (_, row) => (
                <div className="flex gap-2">
                  <Popconfirm
                    title="این فیش تأیید شود؟"
                    okText="تأیید کن"
                    cancelText="انصراف"
                    onConfirm={() => void approve(row)}
                  >
                    <Button type="primary" size="small" loading={busyId === row.id}>
                      تأیید
                    </Button>
                  </Popconfirm>
                  <Button danger size="small" onClick={() => setRejecting(row)}>
                    رد
                  </Button>
                </div>
              ),
            },
          ]}
        />
      )}

      <Modal
        title="رد فیش"
        open={rejecting !== null}
        okText="ثبت رد"
        cancelText="انصراف"
        okButtonProps={{ disabled: reason.trim().length < 3, loading: busyId === rejecting?.id }}
        onOk={() => void submitReject()}
        onCancel={() => {
          setRejecting(null);
          setReason("");
        }}
      >
        <p className="mb-2 text-xs text-ink-dim">
          دلیل رد برای عضو اعلان می‌شود و در لاگ ممیزی می‌ماند.
        </p>
        <Input.TextArea
          aria-label="دلیل رد فیش"
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          rows={3}
          maxLength={500}
        />
      </Modal>
    </section>
  );
}
