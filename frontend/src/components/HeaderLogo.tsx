import { useEffect, useState } from "react";
import BrandMark from "./BrandMark";

/** Sky accents with >= 3:1 contrast against each theme's header background:
 *  dark #0f172a → #38bdf8 (8.33:1); light #f8fafc → #0369a1 (5.67:1). */
const COLORS = { dark: "#38bdf8", light: "#0369a1" } as const;

function currentTheme(): keyof typeof COLORS {
  return document.documentElement.dataset.theme === "light" ? "light" : "dark";
}

/**
 * Header brand mark. The authoritative file is stored by the back end and
 * served at /api/logo with a theme-appropriate accent. If no logo has been
 * uploaded (or the API is offline), fall back to the inline SVG so the header
 * is never blank.
 */
export default function HeaderLogo() {
  const [failed, setFailed] = useState(false);
  const [theme, setTheme] = useState<keyof typeof COLORS>(currentTheme);

  useEffect(() => {
    setTheme(currentTheme());
    const observer = new MutationObserver(() => setTheme(currentTheme()));
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    return () => observer.disconnect();
  }, []);

  if (failed) {
    return (
      <svg viewBox="0 0 200 200" fill="none" aria-hidden="true" focusable="false" className="w-9 h-9 shrink-0 text-sky-400">
        <BrandMark />
      </svg>
    );
  }

  return (
    <img
      src={`/api/logo?color=${encodeURIComponent(COLORS[theme])}`}
      alt=""
      aria-hidden="true"
      width={40}
      height={40}
      className="w-10 h-10 shrink-0 object-contain"
      onError={() => setFailed(true)}
    />
  );
}
