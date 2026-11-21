import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api, type HealthResponse } from "../api/client";

// Footer #5 "Status indicator footer" (vibeui.online Footer category):
// live system status indicator alongside grouped links, logo and copyright.
// Status data reuses the existing health/freshness pattern from LiveFeed.tsx
// (api.health, source status dots, lastDataRefresh label).
type SourceHealth = Exclude<HealthResponse["sources"][string], string>;

export default function Footer() {
  const { t, i18n } = useTranslation();
  const health = useQuery({
    queryKey: ["health"],
    queryFn: api.health,
  });

  const sourceRuns = Object.values(health.data?.sources ?? {}).filter(
    (value): value is SourceHealth => typeof value === "object" && value !== null,
  );
  const refreshFailed = sourceRuns.some((source) => source.status === "FAILURE");
  const lastRefresh = sourceRuns
    .map((source) => source.finished_at)
    .filter((value): value is string => !!value)
    .sort();
  const mostRecentRefresh = lastRefresh[lastRefresh.length - 1];
  const refreshLabel = health.isError
    ? t("dataHealthLoadError")
    : refreshFailed
      ? t("dataRefreshFailed")
      : mostRecentRefresh
        ? t("lastDataRefresh", {
            date: Number.isNaN(Date.parse(mostRecentRefresh))
              ? mostRecentRefresh
              : new Date(mostRecentRefresh).toLocaleString(i18n.language),
          })
        : t("dataRefreshUnavailable");
  const statusDot =
    refreshFailed ? "bg-rose-400" : mostRecentRefresh ? "bg-emerald-400" : "bg-slate-400";

  return (
    <footer className="border-t border-slate-700/60 bg-panel mt-auto">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Footer #1 multi-column sitemap: logo + link groups */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 sm:gap-8 mb-6">
          <div className="col-span-2 md:col-span-1">
            <h2 className="text-sm font-semibold text-slate-100 mb-3">{t("title")}</h2>
            <p className="text-xs text-slate-400 leading-relaxed">{t("subtitle")}</p>
          </div>
          <div>
            <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider mb-3">
              {t("nav.product")}
            </h3>
            <ul className="space-y-2 text-xs text-slate-400 list-none p-0 m-0">
              <li>
                <a
                  href="/"
                  className="hover:text-slate-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400 rounded"
                >
                  {t("overview")}
                </a>
              </li>
              <li>
                <a
                  href="/traseism"
                  className="hover:text-slate-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400 rounded"
                >
                  {t("traseismShort")}
                </a>
              </li>
              <li>
                <a
                  href="/report"
                  className="hover:text-slate-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400 rounded"
                >
                  {t("nav.report")}
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider mb-3">
              {t("nav.company")}
            </h3>
            <ul className="space-y-2 text-xs text-slate-400 list-none p-0 m-0">
              <li>
                <a
                  href="https://github.com/nedaktov-ops/parlament-deschis"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-slate-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400 rounded"
                >
                  {t("about")}
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/nedaktov-ops/parlament-deschis"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-slate-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400 rounded"
                >
                  {t("sources")}
                </a>
              </li>
            </ul>
          </div>
          <div>
            <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider mb-3">
              {t("nav.resources")}
            </h3>
            <ul className="space-y-2 text-xs text-slate-400 list-none p-0 m-0">
              <li>
                <a
                  href="/coverage"
                  className="hover:text-slate-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400 rounded"
                >
                  {t("coverage")}
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Footer #5 status indicator: live freshness alongside copyright */}
        <div
          className="border-t border-slate-700/60 pt-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
        >
          <div className="flex items-center gap-2 text-xs">
            <span
              aria-hidden="true"
              className={`w-2 h-2 rounded-full ${statusDot}`}
            />
            <span className="text-slate-400">{refreshLabel}</span>
          </div>
          <p className="text-xs text-slate-400">
            © {new Date().getFullYear()} Parlament Deschis — CC-BY 4.0
          </p>
        </div>
      </div>
    </footer>
  );
}
