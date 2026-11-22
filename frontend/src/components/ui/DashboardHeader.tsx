// src/components/ui/DashboardHeader.tsx
import { useTranslation } from "react-i18next";
import ThemeToggle from "./ThemeToggle";

/**
 * Header for the LiveDashboard page – shows the main title and theme toggle.
 */
export default function DashboardHeader() {
  const { t } = useTranslation();
  return (
    <div className="flex items-center justify-between gap-3">
      <h1 className="page-title">
        {t("overview")}
      </h1>
      <ThemeToggle />
    </div>
  );
}
