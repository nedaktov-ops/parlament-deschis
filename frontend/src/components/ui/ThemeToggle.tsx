import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

type Theme = "dark" | "light";

const STORAGE_KEY = "parlament-deschis-theme";

function readTheme(): Theme {
  return document.documentElement.dataset.theme === "light" ? "light" : "dark";
}

/** Switches the whole app between the dark default and the light theme. */
export default function ThemeToggle() {
  const { t } = useTranslation();
  const [theme, setTheme] = useState<Theme>(readTheme);

  // index.html applies the saved theme before React mounts, so there is no
  // flash of the wrong theme. Here we keep the DOM and storage in sync.
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try {
      localStorage.setItem(STORAGE_KEY, theme);
    } catch {
      // Storage can be disabled (private mode); the toggle still works.
    }
  }, [theme]);

  const nextTheme: Theme = theme === "dark" ? "light" : "dark";
  const label = t("toggleTheme", "Toggle colour theme");

  return (
    <button
      type="button"
      className="btn bg-slate-700 hover:bg-slate-600 inline-flex items-center gap-2 shrink-0"
      onClick={() => setTheme(nextTheme)}
      aria-label={label}
      aria-pressed={theme === "light"}
      title={label}
    >
      {theme === "dark" ? (
        <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <circle cx="12" cy="12" r="4" />
          <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" strokeLinecap="round" />
        </svg>
      ) : (
        <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79Z" strokeLinejoin="round" />
        </svg>
      )}
      <span>{theme === "dark" ? t("themeLight", "Light") : t("themeDark", "Dark")}</span>
    </button>
  );
}
