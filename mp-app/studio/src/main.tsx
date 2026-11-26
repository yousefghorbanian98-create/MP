import { StyleProvider } from "@ant-design/cssinjs";
import { ConfigProvider } from "antd";
import faIR from "antd/locale/fa_IR";
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { mpTheme } from "./lib/designTokens";
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
 *   • تم از `mp-app/shared/design-tokens.json` می‌آید تا سطح‌ها، متن و مرزهای
 *     Ant Design با پوستهٔ Tailwind یک منبع رنگ داشته باشند.
 */

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
