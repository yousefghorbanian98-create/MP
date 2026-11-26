import React from "react";
import ReactDOM from "react-dom/client";
import { StyleProvider } from "@ant-design/cssinjs";
import { ConfigProvider, theme as antdTheme, type ThemeConfig } from "antd";
import faIR from "antd/locale/fa_IR";
import VisualConcepts from "./VisualConcepts";
import "./visual-concepts.css";

const mpPreviewTheme: ThemeConfig = {
  algorithm: antdTheme.darkAlgorithm,
  token: {
    colorPrimary: "#00B86A",
    colorInfo: "#38BDF8",
    colorSuccess: "#34D399",
    colorWarning: "#FBBF24",
    colorError: "#F87171",
    colorBgBase: "#0B0F14",
    colorBgContainer: "#111827",
    colorBorder: "rgba(0, 184, 106, 0.24)",
    colorTextBase: "#F3F6F8",
    borderRadius: 12,
    fontFamily: "'Vazirmatn Variable', Vazirmatn, system-ui, sans-serif",
  },
};

ReactDOM.createRoot(document.getElementById("concept-root")!).render(
  <React.StrictMode>
    <StyleProvider layer>
      <ConfigProvider direction="rtl" locale={faIR} theme={mpPreviewTheme}>
        <VisualConcepts />
      </ConfigProvider>
    </StyleProvider>
  </React.StrictMode>
);
