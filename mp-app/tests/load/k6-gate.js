// سناریوی بار k6 (M14) — SLO: p95 چک‌این < 2s و خطای 5xx < 5%
// اجرا در CI/M11 پس از deploy: k6 run k6-gate.js --env BASE_URL=https://...
import http from "k6/http";
import { check, sleep } from "k6";
import { Rate } from "k6/metrics";

const errors = new Rate("errors");
const BASE = __ENV.BASE_URL || "http://localhost:8751";

export const options = {
  stages: [
    { duration: "1m", target: 20 }, // گرم‌کردن
    { duration: "3m", target: 20 }, // بار پایدار — ظرفیت واقعی باشگاه
    { duration: "1m", target: 60 }, // اوج (ساعت شلوغ)
    { duration: "1m", target: 0 },
  ],
  thresholds: {
    http_req_duration: ["p(95)<2000"], // SLO گیت ورود (NFR-2)
    errors: ["rate<0.05"],
  },
};

export default function () {
  // health + metrics
  const ready = http.get(`${BASE}/api/v1/health/ready`);
  check(ready, { "ready ok": (r) => r.status === 200 });
  errors.add(ready.status >= 500);

  // چرخهٔ OTP (auth بار)
  const phone = `0912${__VU}${__ITER}`.slice(0, 11);
  const req = http.post(`${BASE}/api/v1/auth/otp/request`, JSON.stringify({ phone }), {
    headers: { "Content-Type": "application/json" },
  });
  check(req, { "otp request ok": (r) => r.status === 200 || r.status === 429 });
  errors.add(req.status >= 500);
  sleep(1);
}
