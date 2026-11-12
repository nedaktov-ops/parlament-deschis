import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import type { EvidenceItem } from "../api/client";

const TYPE_LABEL: Record<string, string> = {
  official_ledger: "confidence.official_ledger",
  profile: "confidence.official_profile",
  jo: "confidence.official_ledger",
  intervention: "confidence.official_profile",
  scrutin: "confidence.official_ledger",
  other: "confidence.derived",
};

function LinkIcon() {
  return (
    <svg viewBox="0 0 24 24" className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M10 13a5 5 0 0 0 7.5.5l3-3a5 5 0 0 0-7-7l-1.5 1.5" strokeLinecap="round" />
      <path d="M14 11a5 5 0 0 0-7.5-.5l-3 3a5 5 0 0 0 7 7l1.5-1.5" strokeLinecap="round" />
    </svg>
  );
}

export default function CitationPopover({ items }: { items: EvidenceItem[] }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  if (items.length === 0) return null;

  return (
    <div className="relative inline-block" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="inline-flex items-center gap-1 text-xs text-sky-400 hover:text-sky-300 transition-colors"
        title={t("citations")}
        aria-expanded={open}
      >
        <LinkIcon />
        <span>
          {items.length} {t("evidenceCount")}
        </span>
      </button>
      {open && (
        <div className="absolute right-0 z-50 mt-1 w-72 card p-3 text-left shadow-xl">
          <div className="text-xs font-semibold text-slate-300 mb-2">{t("citations")}</div>
          <div className="space-y-3">
            {items.map((ev) => (
              <div key={ev.id} className="border-l-2 border-slate-600 pl-2">
                <div className="flex items-center gap-2 text-xs">
                  <span className="font-medium text-emerald-400">
                    {t(TYPE_LABEL[ev.type] ?? "confidence.derived")}
                  </span>
                  {ev.observed_at && (
                    <span className="text-slate-500 font-mono">{ev.observed_at.slice(0, 10)}</span>
                  )}
                </div>
                {ev.note && <div className="text-xs text-amber-400/90 mt-0.5">{ev.note}</div>}
                <div className="flex flex-col gap-1 mt-1">
                  {ev.source_url && (
                    <a
                      href={ev.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-sky-400 hover:underline"
                    >
                      {t("viewOriginal")} ↗
                    </a>
                  )}
                  {ev.snapshot_url && (
                    <a
                      href={ev.snapshot_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-slate-400 hover:underline"
                    >
                      {t("viewArchive")} ↗
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}