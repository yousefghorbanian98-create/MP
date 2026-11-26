import { Alert, Button, Empty, Input, InputNumber, Modal, Select, Spin, Table, Tag, Upload } from "antd";
import { useCallback, useEffect, useState } from "react";
import {
  EXPENSE_CATEGORIES,
  createExpense,
  deleteExpense,
  fetchExpenseReceiptBlob,
  fetchExpenses,
  updateExpense,
  type ExpenseCategory,
  type ExpensePeriod,
  type ExpenseRow,
  uploadExpenseReceipt,
} from "../lib/api";
import { JalaliDateField } from "../components/ui/JalaliDateField";
import { canSeePage, parseRole } from "../lib/roleNav";
import { fa } from "../lib/useApi";
import { shiftIsoDay, today } from "../lib/clock";

/**
 * هزینه‌های باشگاه (QF-06) — اجاره، حقوق، تجهیزات و بقیهٔ پول‌های خارج‌شده.
 *
 * چرا این صفحه لازم بود: پیش از این فقط **درآمد** دیده می‌شد، پس هر عدد
 * «سود» در بهترین حالت حدس بود. حالا هزینه با دسته و تاریخ ثبت می‌شود و جمع
 * همان دوره از سرور می‌آید.
 *
 * قواعدی که UI رعایت می‌کند و سرور هم جداگانه تحمیل می‌کند:
 * - هر اصلاح و حذف **دلیل** می‌خواهد؛ بدون دلیل درخواست فرستاده نمی‌شود.
 * - حذف نرم است؛ ردیف از جمع بیرون می‌رود ولی تاریخچه‌اش می‌ماند.
 * - مجوز نوشتن `finance.write` و خواندن `finance.read`؛ ۴۰۳ سرور نمایش داده
 *   می‌شود و UI ادعای موفقیت نمی‌کند.
 * - کنترل‌ها از کتابخانهٔ antd/تقویم جلالی می‌آیند (Q11)، نه input دست‌ساز.
 */

const labelOf = (key: string): string =>
  EXPENSE_CATEGORIES.find((c) => c.key === key)?.label ?? key;

const isoDay = (offsetDays = 0): string => shiftIsoDay(today(), offsetDays);

export function Expenses() {
  const role = parseRole();
  const [from, setFrom] = useState(isoDay(-30));
  const [to, setTo] = useState(isoDay(0));
  const [period, setPeriod] = useState<ExpensePeriod | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const [amount, setAmount] = useState<number | null>(null);
  const [category, setCategory] = useState<ExpenseCategory>("rent");
  const [spentOn, setSpentOn] = useState(isoDay(0));
  const [payee, setPayee] = useState("");
  const [note, setNote] = useState("");

  // اصلاح مبلغ: مودال کتابخانه‌ای با دلیل اجباری
  const [editing, setEditing] = useState<ExpenseRow | null>(null);
  const [editAmount, setEditAmount] = useState<number | null>(null);
  const [editReason, setEditReason] = useState("");
  // حذف نرم: مودال با دلیل اجباری
  const [removing, setRemoving] = useState<ExpenseRow | null>(null);
  const [removeReason, setRemoveReason] = useState("");

  const load = useCallback(
    (start = from, end = to) => {
      setLoading(true);
      setError("");
      return fetchExpenses(start, end)
        .then((data) => setPeriod(data))
        .catch((err: unknown) =>
          setError(err instanceof Error ? err.message : "خطا در خواندن هزینه‌ها"),
        )
        .finally(() => setLoading(false));
    },
    [from, to],
  );

  useEffect(() => {
    void load(from, to);
    // یک‌بار در باز شدن صفحه؛ تغییر بازه با دکمهٔ «نمایش دوره» انجام می‌شود.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function uploadReceipt(id: number, file: File) {
    setError("");
    try {
      await uploadExpenseReceipt(id, file);
    } catch (e) {
      setError(e instanceof Error ? e.message : "خطای ناشناخته");
    }
  }

  async function openReceipt(id: number) {
    setError("");
    try {
      const blob = await fetchExpenseReceiptBlob(id);
      const url = URL.createObjectURL(blob);
      window.open(url, "_blank", "noopener");
      // فایل خصوصی است؛ آدرس موقت پس از باز شدن پاک می‌شود.
      setTimeout(() => URL.revokeObjectURL(url), 60_000);
    } catch (e) {
      setError(e instanceof Error ? e.message : "خطای ناشناخته");
    }
  }

  async function submit() {
    if (amount === null || !Number.isFinite(amount) || amount < 1000) {
      setError("مبلغ هزینه باید عددی و حداقل ۱٬۰۰۰ ریال باشد");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await createExpense({
        amount_rial: amount,
        category,
        spent_on: spentOn,
        payee: payee.trim(),
        note: note.trim(),
      });
      setAmount(null);
      setNote("");
      setPayee("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "ثبت هزینه ناموفق بود");
    } finally {
      setBusy(false);
    }
  }

  async function submitEdit() {
    if (!editing) return;
    if (editAmount === null || editAmount < 1000) {
      setError("مبلغ اصلاح‌شده باید حداقل ۱٬۰۰۰ ریال باشد");
      return;
    }
    if (editReason.trim().length < 3) {
      setError("دلیل اصلاح اجباری است (حداقل ۳ نویسه)");
      return;
    }
    if (editAmount === editing.amount_rial) {
      setError("مبلغ تغییری نکرده است");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await updateExpense(editing.id, {
        amount_rial: editAmount,
        reason: editReason.trim(),
      });
      setEditing(null);
      setEditReason("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "اصلاح هزینه ناموفق بود");
    } finally {
      setBusy(false);
    }
  }

  async function submitRemove() {
    if (!removing) return;
    if (removeReason.trim().length < 3) {
      setError("برای حذف، دلیل حداقل ۳ نویسه لازم است");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await deleteExpense(removing.id, removeReason.trim());
      setRemoving(null);
      setRemoveReason("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "حذف هزینه ناموفق بود");
    } finally {
      setBusy(false);
    }
  }

  if (role && !canSeePage("expenses", role)) {
    return (
      <div className="glass-card p-5 text-sm text-ink-dim" role="alert">
        هزینه‌ها برای نقش شما مجاز نیست. سرور هم این را رد می‌کند (۴۰۳) — این پیام فقط
        توضیح می‌دهد چرا صفحه خالی است.
      </div>
    );
  }

  return (
    <section className="space-y-4" aria-label="هزینه‌های باشگاه">
      <div className="glass-card space-y-4 p-5">
        <h2 className="text-sm font-bold">هزینه‌های باشگاه</h2>
        <div className="flex flex-wrap items-end gap-3">
          <JalaliDateField label="از تاریخ" value={from} onChange={setFrom} />
          <JalaliDateField label="تا تاریخ" value={to} onChange={setTo} />
          <Button type="primary" onClick={() => void load()} loading={loading}>
            نمایش دوره
          </Button>
        </div>

        {loading && !period ? (
          <div className="flex justify-center p-4">
            <Spin size="small" />
          </div>
        ) : period ? (
          <div className="space-y-3">
            <p className="text-sm">
              جمع هزینهٔ دوره: <b className="text-primary-light">{fa(period.total_rial)}</b> ریال —{" "}
              {fa(period.count)} ردیف
            </p>
            {period.by_category.length > 0 ? (
              <div className="grid gap-2 sm:grid-cols-3">
                {period.by_category.map((row) => (
                  <div key={row.category} className="rounded-xl bg-primary/10 p-3 text-center">
                    <p className="text-xs text-ink-dim">{row.label}</p>
                    <p className="text-sm font-bold">{fa(row.total_rial)}</p>
                    <p className="text-xs text-ink-dim">{fa(row.count)} مورد</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-ink-dim">
                در این دوره هزینه‌ای ثبت نشده است — «صفر» یعنی ثبت نشده، نه اینکه رایگان بوده.
              </p>
            )}
          </div>
        ) : null}
      </div>

      <div className="glass-card space-y-3 p-5">
        <h2 className="text-sm font-bold">ثبت هزینهٔ تازه</h2>
        <div className="flex flex-wrap items-end gap-3">
          <label className="text-xs text-ink-dim">
            مبلغ (ریال)
            <InputNumber<number>
              aria-label="مبلغ هزینه"
              className="mt-1 block w-40"
              min={1000}
              step={1000}
              controls={false}
              value={amount}
              onChange={(value) => setAmount(value)}
            />
          </label>
          <label className="text-xs text-ink-dim">
            دسته
            <Select<ExpenseCategory>
              aria-label="دستهٔ هزینه"
              className="mt-1 block w-40"
              value={category}
              onChange={(value) => setCategory(value)}
              options={EXPENSE_CATEGORIES.map((c) => ({ value: c.key, label: c.label }))}
            />
          </label>
          <JalaliDateField label="تاریخ هزینه" value={spentOn} onChange={setSpentOn} />
          <label className="text-xs text-ink-dim">
            طرف‌حساب (اختیاری)
            <Input
              aria-label="طرف‌حساب"
              className="mt-1 block w-44"
              value={payee}
              onChange={(e) => setPayee(e.target.value)}
            />
          </label>
          <label className="text-xs text-ink-dim">
            توضیح (اختیاری)
            <Input
              aria-label="توضیح هزینه"
              className="mt-1 block w-56"
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </label>
          <Button type="primary" onClick={() => void submit()} loading={busy}>
            ثبت هزینه
          </Button>
        </div>
      </div>

      <div className="glass-card space-y-3 p-5">
        <h2 className="text-sm font-bold">ریز هزینه‌های دوره</h2>
        {period && period.items.length > 0 ? (
          <Table<ExpenseRow>
            size="small"
            rowKey="id"
            pagination={false}
            dataSource={period.items}
            columns={[
              { title: "دسته", key: "category", render: (_, row) => labelOf(row.category) },
              {
                title: "مبلغ",
                key: "amount_rial",
                render: (_, row) => `${fa(row.amount_rial)} ریال`,
              },
              { title: "تاریخ", dataIndex: "spent_on", key: "spent_on" },
              { title: "طرف‌حساب", dataIndex: "payee", key: "payee" },
              {
                title: "وضعیت",
                key: "status",
                render: (_, row) => (
                  <Tag color="green">{row.deleted_at ? "حذف‌شده" : "ثبت‌شده"}</Tag>
                ),
              },
              {
                title: "",
                key: "actions",
                render: (_, row) => (
                  <div className="flex gap-2">
                    <Button
                      size="small"
                      onClick={() => {
                        setEditing(row);
                        setEditAmount(row.amount_rial);
                        setEditReason("");
                      }}
                    >
                      اصلاح
                    </Button>
                    <Upload
                      accept="image/jpeg,image/png,image/webp"
                      showUploadList={false}
                      beforeUpload={(file) => {
                        void uploadReceipt(row.id, file);
                        return false;
                      }}
                    >
                      <Button size="small">فیش</Button>
                    </Upload>
                    <Button size="small" onClick={() => void openReceipt(row.id)}>
                      مشاهدهٔ فیش
                    </Button>
                    <Button size="small" danger onClick={() => setRemoving(row)}>
                      حذف
                    </Button>
                  </div>
                ),
              },
            ]}
          />
        ) : (
          <Empty description="هزینه‌ای در این دوره ثبت نشده است" />
        )}
      </div>

      {error && <Alert type="error" showIcon message={error} role="alert" />}

      <Modal
        title="اصلاح مبلغ هزینه"
        open={editing !== null}
        okText="ثبت اصلاح"
        cancelText="انصراف"
        confirmLoading={busy}
        onOk={() => void submitEdit()}
        onCancel={() => {
          setEditing(null);
          setEditReason("");
        }}
      >
        <p className="text-xs text-ink-dim">
          هر اصلاح در تاریخچه با دلیل ثبت می‌شود؛ مقدار قبلی حذف نمی‌شود.
        </p>
        <InputNumber<number>
          aria-label="مبلغ اصلاح‌شده"
          className="mt-3 block w-40"
          min={1000}
          step={1000}
          controls={false}
          value={editAmount}
          onChange={(value) => setEditAmount(value)}
        />
        <Input
          aria-label="دلیل اصلاح"
          className="mt-3"
          placeholder="دلیل اصلاح (اجباری)"
          value={editReason}
          onChange={(e) => setEditReason(e.target.value)}
        />
      </Modal>

      <Modal
        title="حذف هزینه"
        open={removing !== null}
        okText="حذف کن"
        cancelText="انصراف"
        okButtonProps={{ danger: true }}
        confirmLoading={busy}
        onOk={() => void submitRemove()}
        onCancel={() => {
          setRemoving(null);
          setRemoveReason("");
        }}
      >
        <p className="text-xs text-ink-dim">
          حذف نرم است: ردیف از جمع‌ها بیرون می‌رود ولی تاریخچه و ممیزی می‌ماند.
        </p>
        <Input
          aria-label="دلیل حذف"
          className="mt-3"
          placeholder="دلیل حذف (اجباری)"
          value={removeReason}
          onChange={(e) => setRemoveReason(e.target.value)}
        />
      </Modal>
    </section>
  );
}
