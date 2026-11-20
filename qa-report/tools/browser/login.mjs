// ورود واقعی از طریق API (OTP با dev_code در محیط development) و برگرداندن توکن‌ها
export async function login(phone, base = 'http://127.0.0.1:8000/api/v1') {
  const r1 = await fetch(`${base}/auth/otp/request`, {method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify({phone})});
  const j1 = await r1.json();
  const code = j1.dev_code;
  const r2 = await fetch(`${base}/auth/otp/verify`, {method:'POST', headers:{'content-type':'application/json'}, body: JSON.stringify({phone, code})});
  if (!r2.ok) throw new Error('verify ' + r2.status + ' ' + await r2.text());
  return r2.json();
}
