// ESLint 9 (flat) برای استودیو — WP 0.5 / F-10.
// قوانین خطا فقط در کد واقعی اعمال می‌شود؛ هیچ قاعده‌ای خاموش نشده است.
import js from "@eslint/js";
import tseslint from "typescript-eslint";
import hooks from "eslint-plugin-react-hooks";
import a11y from "eslint-plugin-jsx-a11y";
import globals from "globals";

export default tseslint.config(
  { ignores: ["**/dist/**", "**/node_modules/**", "**/coverage/**"] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ["**/*.{ts,tsx}"],
    plugins: { "react-hooks": hooks, "jsx-a11y": a11y },
    languageOptions: { globals: { ...globals.browser } },
    rules: {
      ...hooks.configs.recommended.rules,
      ...a11y.configs.recommended.rules,
      // کنترل‌های antd (Input/InputNumber/Select) داخل <label> هستند؛ بدون این تنظیم
      // قاعده آن‌ها را نمی‌بیند و برچسب‌های درست را خطا می‌گیرد.
      "jsx-a11y/label-has-associated-control": [
        "error",
        {
          controlComponents: ["Input", "InputNumber", "Select", "Checkbox", "DatePicker"],
          assert: "either",
          depth: 3,
        },
      ],
      "@typescript-eslint/no-explicit-any": "warn",
      "@typescript-eslint/no-unused-vars": ["warn", { argsIgnorePattern: "^_" }],
    },
  },
  // P‑1: ساعت یکتا — هیچ کد src جز src/lib/clock.ts نباید new Date() یا Date.now() بزند.
  {
    files: ["src/**/*.{ts,tsx}"],
    ignores: ["src/lib/clock.ts"],
    rules: {
      "no-restricted-syntax": [
        "error",
        {
          selector: "NewExpression[callee.name='Date']",
          message: "از src/lib/clock.ts استفاده کنید (now/today/toDate/fromParts).",
        },
        {
          selector: "CallExpression[callee.object.name='Date'][callee.property.name='now']",
          message: "از now() در src/lib/clock.ts استفاده کنید.",
        },
      ],
    },
  },
  {
    files: ["electron/**/*.cjs"],
    languageOptions: { sourceType: "commonjs", globals: { ...globals.node } },
    rules: { "@typescript-eslint/no-require-imports": "off" },
  },
  {
    files: ["public/sw.js"],
    languageOptions: { globals: { ...globals.serviceworker } },
  },
  {
    files: ["tests/**/*.{ts,tsx}"],
    languageOptions: { globals: { ...globals.browser, ...globals.node } },
  },
);
