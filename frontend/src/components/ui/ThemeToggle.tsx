// src/components/ui/ThemeToggle.tsx
import { useTranslation } from "react-i18next";

/**
 * Simple theme toggle – adds/removes the `dark` class on the html element.
 * Allows switching between dark (default) and light mode.
 */
export default function ThemeToggle() {
  const { t } = useTranslation();
  const toggleTheme = () => {
    const root = document.documentElement;
    if (root.classList.contains("dark")) {
      root.classList.remove("dark");
    } else {
      root.classList.add("dark");
    }
  };
  return (
    <button
      type="button"
      className="btn bg-slate-700 hover:bg-slate-600"
      onClick={toggleTheme}
    >
      {t("toggleTheme")}
    </button>
  );
}
