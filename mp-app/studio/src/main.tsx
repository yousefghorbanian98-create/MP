import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles/index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// ثبت Service Worker — آپدیت تفاضلی بدون نصب مجدد (M20)
//
// D-024 (نسخهٔ وب/PWA): ثبت دیگر فقط در PROD نیست. اگر PWA فقط در build
// نهایی نصب‌پذیر باشد، تا لحظهٔ تحویل هرگز آزموده نمی‌شود. در dev هم
// ثبت می‌شود تا «نصب روی موبایل» واقعاً بررسی شده باشد.
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch(() => undefined);
  });
}
