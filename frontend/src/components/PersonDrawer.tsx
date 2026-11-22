import { useEffect, useId, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api, type EventItem } from "../api/client";
import CitationPopover from "./CitationPopover";
import MembershipGantt from "./MembershipGantt";
import RetryButton from "./RetryButton";
import TooltipText from "./ui/TooltipText";

function typeColor(type: string): string {
  switch (type) {
    case "switch_group":
    case "switch_party":
      return "text-amber-400";
    case "join":
    case "committee_join":
      return "text-emerald-400";
    case "leave":
    case "committee_leave":
      return "text-rose-400";
    case "group_founded":
    case "group_renamed":
      return "text-sky-400";
    default:
      return "text-slate-400";
  }
}

export default function PersonDrawer({
  personId,
  onClose,
}: {
  personId: string | null;
  onClose: () => void;
}) {
  const { t, i18n } = useTranslation();
  const tipId = useId().replace(/:/g, "");
  const drawerRef = useRef<HTMLElement>(null);
  const person = useQuery({
    queryKey: ["person", personId],
    queryFn: () => api.person(personId!),
    enabled: !!personId,
  });
  const history = useQuery({
    queryKey: ["personHistory", personId],
    queryFn: () => api.personHistory(personId!),
    enabled: !!personId,
    retry: false,
  });

  useEffect(() => {
    if (!personId) return;
    const previousFocus = document.activeElement instanceof HTMLElement
      ? document.activeElement
      : null;
    drawerRef.current?.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
        return;
      }
      if (event.key !== "Tab") return;
      const items = drawerRef.current?.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])',
      );
      if (!items?.length) return;
      const first = items[0];
      const last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      previousFocus?.focus();
    };
  }, [personId, onClose]);

  if (!personId) return null;

  const summary = (e: EventItem) =>
    i18n.language === "en" ? e.summary_en || e.summary_ro : e.summary_ro || e.summary_en;

  const p = person.data;

  const historyRows = [...(history.data?.history ?? [])].sort((a, b) =>
    (b.date ?? "").localeCompare(a.date ?? ""),
  );

  return (
    <>
      <div aria-hidden="true" className="fixed inset-0 bg-black/70 z-40" onClick={onClose} />
      <aside
        ref={drawerRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="person-drawer-title"
        tabIndex={-1}
        className="fixed right-0 top-0 h-full w-full sm:w-[480px] bg-panel border-l border-slate-700 z-50 overflow-y-auto shadow-2xl"
      >
        <div className="sticky top-0 bg-panel/95 backdrop-blur border-b border-slate-700 px-5 py-4 flex items-start justify-between">
          <div>
            <div className="text-xs uppercase tracking-wide text-slate-500">{t("person")}</div>
            <h2 id="person-drawer-title" className="text-lg font-semibold">{p?.name ?? t("loading")}</h2>
            {p?.birth_date && (
              <div className="text-xs text-slate-400">
                {t("born")} {p.birth_date}
              </div>
            )}
          </div>
          <button type="button"className="btn bg-slate-700 hover:bg-slate-600" onClick={onClose}>
            {t("close")}
          </button>
        </div>

        {person.isLoading && <div className="p-5 text-slate-500 text-sm">{t("loading")}</div>}
        {person.isError && (
          <div className="p-5 text-rose-200 text-sm" role="alert">
            {t("personLoadError")}
            <RetryButton onRetry={() => person.refetch()} className="ml-3" />
          </div>
        )}

        {p && (
          <div className="p-5 space-y-6">
            <div className="flex flex-wrap gap-1.5">
              {p.identifiers.map((id, idx) => (
                <span
                  key={`${id.scheme}-${id.identifier}-${id.legislature}`}
                  className="relative group text-xs bg-slate-800 rounded px-1.5 py-0.5 text-slate-400 font-mono"
                  aria-describedby={`${tipId}-id-${idx}`}
                >
                  {id.scheme}:{id.identifier}
                  {id.legislature ? ` (${id.legislature})` : ""}
                  <TooltipText id={`${tipId}-id-${idx}`}>{t("identifiers")}</TooltipText>
                </span>
              ))}
              {p.wikidata_qid && (
                <a
                  href={`https://www.wikidata.org/wiki/${p.wikidata_qid}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs bg-slate-800 rounded px-1.5 py-0.5 text-sky-400 font-mono hover:underline"
                >
                  {p.wikidata_qid} ↗
                </a>
              )}
            </div>

            <section>
              <h3 className="text-sm font-semibold text-slate-300 mb-2">{t("memberships")}</h3>
              <MembershipGantt memberships={p.memberships} />
            </section>

            <section>
              <h3 className="text-sm font-semibold text-slate-300 mb-2">{t("citations")}</h3>
              <div className="space-y-2">
                {p.memberships.map((m) => {
                  const ev = p.evidence.filter((e) => e.membership_id === m.id);
                  return (
                    <div
                      key={m.id}
                      className="flex items-center justify-between gap-2 bg-slate-800/40 rounded-md px-3 py-2"
                    >
                      <div className="min-w-0">
                        <div className="text-sm truncate">
                          <span
                            className="inline-block w-2 h-2 rounded-full mr-1.5"
                            style={{ background: m.org?.color || "#64748b" }}
                          />
                          {m.org?.short_name || m.org?.name}
                          {m.role && <span className="text-slate-400"> · {m.role}</span>}
                        </div>
                        <div className="text-xs text-slate-500 font-mono">
                          {m.start_date ?? "?"} → {m.end_date ?? t("present")}
                          {m.party && <span className="text-slate-400"> · {m.party.short_name}</span>}
                        </div>
                      </div>
                      <CitationPopover items={ev} />
                    </div>
                  );
                })}
              </div>
            </section>

            <section>
              <h3 className="text-sm font-semibold text-slate-300 mb-2">{t("events")}</h3>
              <div className="space-y-2">
                {p.events.length === 0 && (
                  <div className="text-slate-500 text-sm">{t("noData")}</div>
                )}
                {p.events.map((e) => (
                  <div key={e.id} className="bg-slate-800/40 rounded-md px-3 py-2">
                    <div className="flex items-center gap-2 text-xs">
                      <span className={`font-semibold ${typeColor(e.type)}`}>{e.type}</span>
                      <span className="text-slate-500 font-mono">{e.event_date}</span>
                      {e.reason && <span className="text-slate-600">{e.reason}</span>}
                    </div>
                    <div className="text-sm mt-0.5">{summary(e)}</div>
                    {(e.from_org || e.to_org) && (
                      <div className="text-xs text-slate-500 mt-0.5">
                        {e.from_org?.short_name || e.from_org?.name || "—"} →{" "}
                        {e.to_org?.short_name || e.to_org?.name || "—"}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </section>

            {historyRows.length > 0 && (
              <section>
                <h3 className="text-sm font-semibold text-slate-300 mb-2">
                  {t("changeHistory")}
                </h3>
                <div className="space-y-1.5">
                  {historyRows.map((h, i) => (
                    <div
                      key={`${h.field}-${h.date ?? "undated"}-${i}`}
                      className="bg-slate-800/40 rounded-md px-3 py-2 text-xs"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <span className="font-medium text-slate-300">{h.field}: </span>
                          <span className="text-slate-400 font-mono">
                            {h.from ?? "—"} → {h.to ?? "—"}
                          </span>
                        </div>
                        {h.date && (
                          <span className="text-slate-500 font-mono shrink-0">{h.date}</span>
                        )}
                      </div>
                      {(h.event_type || h.org) && (
                        <div className="text-xs text-slate-500 mt-0.5">
                          {[h.event_type, h.org].filter(Boolean).join(" · ")}
                        </div>
                      )}
                      {h.source_url && (
                        <a
                          href={h.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-block text-xs text-sky-400 hover:underline mt-0.5"
                        >
                          {t("viewOriginal")} ↗
                          <span className="sr-only">
                            {h.date ? ` (${h.date})` : h.org ? ` (${h.org})` : ` (${i + 1})`}
                          </span>
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              </section>
            )}
          </div>
        )}
      </aside>
    </>
  );
}