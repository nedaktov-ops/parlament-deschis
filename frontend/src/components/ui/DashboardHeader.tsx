// src/components/ui/DashboardHeader.tsx
import { useTranslation } from "react-i18next";
import ThemeToggle from "../ThemeToggle";

/**
 * Header for the LiveDashboard page – shows the main title and theme toggle.
 */
export default function DashboardHeader() {
  const { t } = useTranslation();
  return (
    <div className="flex items-center justify-between mb-4">
      <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-slate-100">
        {t("overview")}
      </h1>
      <ThemeToggle />
    </div>
  );
}
