import React from "react";
import ReactDOM from "react-dom/client";
import { AppRoot } from "./router";
import "./i18n";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AppRoot />
  </React.StrictMode>,
);// Force Vercel deploy - Thu Nov 19 12:34:54 AM EET 2026
