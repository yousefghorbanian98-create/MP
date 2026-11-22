// WP 4.6 / F‑16: fixture for mp-ts-float-money (semgrep --test).
// ruleid: mp-ts-float-money
const a = parseFloat(row.total_paid_rial);
// ruleid: mp-ts-float-money
const b = Number(order.total_amount);
// ruleid: mp-ts-float-money
const c = Number(priceRial);
// ruleid: mp-ts-float-money
const d = Number(wallet.balance);
// ruleid: mp-ts-float-money
const e = Number(feeAmount);
// ok: mp-ts-float-money
const f = Number(row.total_minutes);
// ok: mp-ts-float-money
const g = Number(row.visits);
// ok: mp-ts-float-money
const h = Number(row.avg_axis_score);
// ok: mp-ts-float-money
const i = Number(row.total_kcal);
