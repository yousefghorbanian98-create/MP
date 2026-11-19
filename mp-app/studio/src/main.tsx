import { StyleProvider } from "@ant-design/cssinjs";
import { ConfigProvider, theme as antdTheme, type ThemeConfig } from "antd";
import faIR from "antd/locale/fa_IR";
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles/index.css";

/**
 * ریشهٔ تم — Q11.
 *
 * چرا این پوسته اینجاست:
 *   • `StyleProvider layer` استایل antd را داخل `@layer antd` می‌گذارد تا
 *     Tailwind preflight آن را نشکند (دستور رسمی antd برای هم‌زیستی با
 *     Tailwind v3). بدون این، دکمه/اینپوت antd رنگ و پدینگ خودش را از دست
 *     می‌داد.
 *   • `direction="rtl"` + `locale={faIR}`: خودِ کامپوننت‌ها (صفحه‌بندی جدول،
 *     متن «بستن» دیالوگ، فرم‌ها) فارسی و راست‌به‌چپ می‌شوند؛ ترجمهٔ دستی
 *     نوشته نمی‌شود.
 *   • `darkAlgorithm` + توکن‌های برند: رنگ‌ها با پوستهٔ فعلی هم‌خوان می‌مانند.
 */
const mpTheme: ThemeConfig = {
  algorithm: antdTheme.darkAlgorithm,
  token: {
    colorPrimary: "#00B86A",
    colorInfo: "#38BDF8",
    colorSuccess: "#34D399",
    colorError: "#F87171",
    colorWarning: "#FBBF24",
    colorBgBase: "#0B0F14",
    colorBgContainer: "#111827",
    colorBorder: "rgba(0, 184, 106, 0.24)",
    colorTextBase: "#F3F6F8",
    borderRadius: 12,
    fontFamily: "'Vazirmatn Variable', Vazirmatn, system-ui, sans-serif",
  },
};

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <StyleProvider layer>
      <ConfigProvider direction="rtl" locale={faIR} theme={mpTheme}>
        <App />
      </ConfigProvider>
    </StyleProvider>
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
