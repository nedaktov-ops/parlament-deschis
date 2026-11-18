import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api, type CoverageItem } from "../api/client";

const PROJECT_URL = "https://github.com/parlament-deschis";
const CODE_LICENSE_FALLBACK = "AGPL-3.0-or-later";
const DATA_LICENSE_FALLBACK = "CC-BY-4.0";
const CODE_LICENSE_URL_FALLBACK = "https://www.gnu.org/licenses/agpl-3.0.html";
const DATA_LICENSE_URL_FALLBACK = "https://creativecommons.org/licenses/by/4.0/";

const CONFIDENCE_LEVELS = [
  "official_ledger",
  "official_profile",
  "derived",
  "community",
] as const;

function completenessClass(value: string): string {
  if (value === "full") return "bg-emerald-900/50 text-emerald-300";
  if (value === "partial") return "bg-amber-900/50 text-amber-300";
  return "bg-slate-800 text-slate-400";
}

function confidenceClass(value: string): string {
  switch (value) {
    case "official_ledger":
      return "bg-emerald-900/50 text-emerald-300";
    case "official_profile":
      return "bg-sky-900/50 text-sky-300";
    case "derived":
      return "bg-amber-900/50 text-amber-300";
    default:
      return "bg-slate-800 text-slate-400";
  }
}

function renderValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  if (Array.isArray(value)) {
    return value
      .map((item) =>
        item !== null && typeof item === "object" ? JSON.stringify(item) : String(item),
      )
      .join(", ");
  }
  if (typeof value === "object") {
    return Object.entries(value as Record<string, unknown>)
      .map(
        ([key, item]) =>
          `${key}: ${
            item !== null && typeof item === "object" ? JSON.stringify(item) : String(item)
          }`,
      )
      .join(" · ");
  }
  return String(value);
}

function AccordionItem({
  title,
  children,
  open,
  onToggle,
}: {
  title: string;
  children: React.ReactNode;
  open: boolean;
  onToggle: () => void;
}) {
  return (
    <div className="bg-slate-800/30 rounded-lg border border-slate-700/50 overflow-hidden">
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={open}
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-slate-700/50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400 transition-colors"
      >
        <span className="text-sm font-medium text-slate-200">{title}</span>
        <span className={`text-slate-500 ${open ? "rotate-180" : ""}`}>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
          </svg>
        </span>
      </button>
      {open && (
        <div className="px-4 pb-3 border-t border-slate-700/40">{children}</div>
      )}
    </div>
  );
}

export default function About({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { t } = useTranslation();
  const closeRef = useRef<HTMLButtonElement | null>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const [coverageOpen, setCoverageOpen] = useState(false);
  const [licensesOpen, setLicensesOpen] = useState(false);
  const [freshnessOpen, setFreshnessOpen] = useState(false);

  const about = useQuery({
    queryKey: ["about"],
    queryFn: api.about,
    enabled: open,
    retry: false,
  });
  const coverage = useQuery({
    queryKey: ["coverage"],
    queryFn: api.coverage,
    enabled: open,
  });

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = previous;
    };
  }, [open, onClose]);

  useEffect(() => {
    if (!open) return;
    const previousFocus = document.activeElement instanceof HTMLElement
      ? document.activeElement
      : null;
    closeRef.current?.focus();
    return () => previousFocus?.focus();
  }, [open]);

  if (!open) return null;

  const data = about.data;
  const coverageRows: CoverageItem[] =
    data?.coverage && data.coverage.length > 0 ? data.coverage : (coverage.data ?? []);
  const freshness = Object.entries(data?.freshness ?? {}).sort(([a], [b]) => {
    const rank = (key: string) => (key === "cdep" ? 0 : key === "senat" ? 1 : 2);
    return rank(a) - rank(b) || a.localeCompare(b);
  });
  const licenses = data?.licenses;
  const codeLicense = licenses?.code || CODE_LICENSE_FALLBACK;
  const dataLicense = licenses?.data || DATA_LICENSE_FALLBACK;
  const codeLicenseUrl = licenses?.code_url || CODE_LICENSE_URL_FALLBACK;
  const dataLicenseUrl = licenses?.data_url || DATA_LICENSE_URL_FALLBACK;

  const chamberLabel = (chamber: string) =>
    chamber === "deputies" || chamber === "senate" ? t(chamber) : chamber;
  const freshnessLabel = (key: string) =>
    key === "cdep" ? t("deputies") : key === "senat" ? t("senate") : key;

  return (
    <div
      className="fixed inset-0 z-[60] flex items-start sm:items-center justify-center bg-black/60 p-4 overflow-y-auto"
      onClick={onClose}
    >
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="about-title"
        className="card w-full max-w-3xl max-h-[85vh] overflow-y-auto p-5 sm:p-6 space-y-6 my-auto"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={(e) => {
          if (e.key !== "Tab") return;
          const items = panelRef.current?.querySelectorAll<HTMLElement>(
            'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])',
          );
          if (!items?.length) return;
          const first = items[0];
          const last = items[items.length - 1];
          if (e.shiftKey && document.activeElement === first) {
            e.preventDefault();
            last.focus();
          } else if (!e.shiftKey && document.activeElement === last) {
            e.preventDefault();
            first.focus();
          }
        }}
      >
        <div className="flex items-start justify-between gap-3 border-b border-slate-700/60 pb-3">
          <div>
            <h2 id="about-title" className="text-lg font-semibold">
              {t("about")} — {data?.name ?? t("title")}
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              {data?.description || t("subtitle")}
            </p>
          </div>
          <button type="button"ref={closeRef}
            className="btn bg-slate-700 hover:bg-slate-600 shrink-0"
            onClick={onClose}
            aria-label={t("close")}
          >
            {t("close")}
          </button>
        </div>

        {about.isError && (
          <div className="text-xs text-amber-300 bg-amber-900/20 border border-amber-800/40 rounded px-3 py-2">
            {t("aboutUnavailable")}
          </div>
        )}

        {/* Featured testimonial — method (ts-4 pattern: single featured quote with attribution) */}
        <section className="relative bg-slate-800/40 rounded-xl p-6 sm:p-8 border border-slate-700/40">
          <span className="absolute top-4 left-4 text-4xl text-slate-600/50 select-none">“</span>
          <h3 className="text-sm font-semibold text-slate-300 mb-2 flex items-center gap-2">
            <span className="text-sky-400">❝</span>
            {t("method")}
          </h3>
          <p className="text-sm text-slate-200 leading-relaxed">
            {t("methodBody")}
          </p>
          <p className="text-xs text-slate-500 mt-3 font-medium">— {t("methodAttribution", "Parlament Deschis methodology")}</p>
          <p className="text-xs text-slate-500 mt-2">{t("methodConfidenceNote")}</p>
          <div className="flex flex-wrap gap-1.5 mt-1.5">
            {CONFIDENCE_LEVELS.map((level) => (
              <span
                key={level}
                className={`text-xs rounded px-2 py-0.5 ${confidenceClass(level)}`}
              >
                {t(`confidence.${level}`)}
              </span>
            ))}
          </div>
        </section>

        {/* Accordion — sources */}
        <AccordionItem title={t("sources")} open={sourcesOpen} onToggle={() => setSourcesOpen(!sourcesOpen)}>
          {(data?.sources?.length ?? 0) === 0 ? (
            <div className="text-sm text-slate-500">
              {about.isLoading ? t("loading") : t("noSources")}
            </div>
          ) : (
            <ul className="space-y-2">
              {data?.sources.map((source) => (
                <li key={`${source.name}-${source.url}`} className="text-sm">
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sky-400 hover:text-sky-300 hover:underline"
                  >
                    {source.name} ↗
                  </a>
                  {source.note && (
                    <div className="text-xs text-slate-500 mt-0.5">{source.note}</div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </AccordionItem>

        {/* Accordion — coverage */}
        <AccordionItem title={t("coverageTable")} open={coverageOpen} onToggle={() => setCoverageOpen(!coverageOpen)}>
          {coverageRows.length === 0 ? (
            <div className="text-sm text-slate-500">
              {about.isLoading || coverage.isLoading ? t("loading") : t("noData")}
            </div>
          ) : (
            <table className="w-full text-xs border-collapse mt-2">
              <thead>
                <tr className="text-left text-slate-500">
                  <th scope="col" className="py-1 pr-2 font-medium">{t("chamber")}</th>
                  <th scope="col" className="py-1 pr-2 font-medium">{t("legislature")}</th>
                  <th scope="col" className="py-1 font-medium">{t("completeness")}</th>
                </tr>
              </thead>
              <tbody>
                {coverageRows.map((row, i) => (
                  <tr
                    key={`${row.chamber}-${row.legislature ?? "none"}-${i}`}
                    className="border-t border-slate-700/60"
                  >
                    <th scope="row" className="py-1.5 pr-2 font-normal text-left">{chamberLabel(row.chamber)}</th>
                    <td className="py-1.5 pr-2 font-mono">{row.legislature ?? "—"}</td>
                    <td className="py-1.5">
                      <span
                        className={`rounded px-2 py-0.5 ${completenessClass(row.completeness)}`}
                      >
                        {t(row.completeness)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </AccordionItem>

        {/* Accordion — licenses */}
        <AccordionItem title={t("licenses")} open={licensesOpen} onToggle={() => setLicensesOpen(!licensesOpen)}>
          <ul className="space-y-1.5 text-sm mt-2">
            <li>
              <span className="text-slate-400">{t("codeLicense")}:</span>{" "}
              <a
                href={codeLicenseUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sky-400 hover:text-sky-300 hover:underline"
              >
                {codeLicense} ↗
              </a>
            </li>
            <li>
              <span className="text-slate-400">{t("dataLicense")}:</span>{" "}
              <a
                href={dataLicenseUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sky-400 hover:text-sky-300 hover:underline"
              >
                {dataLicense} ↗
              </a>
            </li>
          </ul>
        </AccordionItem>

        {/* Accordion — data freshness */}
        <AccordionItem title={t("dataFreshness")} open={freshnessOpen} onToggle={() => setFreshnessOpen(!freshnessOpen)}>
          {freshness.length === 0 ? (
            <div className="text-sm text-slate-500 mt-2">
              {about.isLoading ? t("loading") : t("freshnessUnavailable")}
            </div>
          ) : (
            <div className="space-y-1.5 mt-2">
              {freshness.map(([key, value]) => (
                <div
                  key={key}
                  className="flex flex-col sm:flex-row sm:items-baseline gap-1 bg-slate-800/40 rounded px-3 py-1.5"
                >
                  <span className="text-xs text-slate-400 sm:w-32 shrink-0">
                    {freshnessLabel(key)}
                  </span>
                  <span className="text-xs text-slate-300 font-mono break-all">
                    {renderValue(value)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </AccordionItem>

        <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500 border-t border-slate-700/60 pt-3">
          <span>
            {t("generatedAt")}:{" "}
            <span className="font-mono">{data?.generated_at ?? "—"}</span>
          </span>
          <a
            href={PROJECT_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sky-400 hover:underline"
          >
            {t("project")}: parlament-deschis ↗
          </a>
        </div>
      </div>
    </div>
  );
}
