import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { api, type EventItem } from "../api/client";
import { useParams } from "@tanstack/react-router";
import MembershipGantt from "../components/MembershipGantt";
import CitationPopover from "../components/CitationPopover";
import HeroGraphic from "../components/HeroGraphic";
import InfoStat from "../components/InfoStat";
import { Sparkline } from "../components/DataViz";

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

export function PersonDeepDive() {
  const { t, i18n } = useTranslation();
  const params = useParams({ from: "/person/$id" });
  const personId = params.id;

  const person = useQuery({
    queryKey: ["person", personId],
    queryFn: () => api.person(personId),
    enabled: !!personId,
  });

  const summary = (e: EventItem) =>
    i18n.language === "en" ? e.summary_en || e.summary_ro : e.summary_ro || e.summary_en;

  const p = person.data;
  const personEvents = p?.events;

  // All hooks must be declared before any early return (React #310).
  // `personEvents` may be undefined while loading/on error; optional chaining
  // inside the memo keeps the hook unconditional and safe.
  const sparklineData = useMemo(() => {
    const counts = new Map<string, number>();
    let first: string | null = null;
    let last: string | null = null;
    for (const e of personEvents ?? []) {
      if (!e.event_date) continue;
      const d = e.event_date.slice(0, 10);
      counts.set(d, (counts.get(d) ?? 0) + 1);
      if (first === null || d < first) first = d;
      if (last === null || d > last) last = d;
    }
    if (!first || !last) return [];
    const out: number[] = [];
    let cur = first;
    while (cur <= last) {
      out.push(counts.get(cur) ?? 0);
      const [y, m, day] = cur.split("-").map(Number);
      const nd = new Date(Date.UTC(y, m - 1, day));
      nd.setUTCDate(nd.getUTCDate() + 1);
      cur = nd.toISOString().slice(0, 10);
    }
    return out;
  }, [personEvents]);

  if (person.isLoading) {
    return (
      <div className="card p-4">
        <h1 className="sr-only">{t("personDeepDive.title", "Parliamentary profile")}</h1>
        <div className="text-slate-500 text-sm py-8">{t("loading")}</div>
      </div>
    );
  }

  if (person.isError || !p) {
    return (
      <div className="card p-4" role="alert">
        <h1 className="sr-only">{t("personDeepDive.title", "Parliamentary profile")}</h1>
        <p className="text-rose-200 text-sm py-4">{t("personLoadError")}</p>
        <button type="button"className="btn bg-slate-700 hover:bg-slate-600" onClick={() => person.refetch()}>
          {t("traseismRetry")}
        </button>
      </div>
    );
  }

  const totalEvents = p.events.length;
  const switches = p.events.filter(
    (e) => e.type === "switch_group" || e.type === "switch_party",
  ).length;
  const chambersCovered = new Set(
    p.events.map((e) => e.chamber).filter(Boolean),
  ).size;
  const legislaturesCovered = new Set(
    p.events.map((e) => e.legislature).filter(Boolean),
  ).size;

  return (
    <div className="space-y-6">
      {/* Section 1: Hero — MP biography graphic, fills the first screen alone */}
      <section className="hero-section" data-enter>
        <div>
          <div className="flex flex-col md:flex-row md:items-center gap-8">
            <div className="flex-1 space-y-4">
              <h1 className="page-title">{p.name}</h1>
              <p className="text-sm text-slate-400">{t("personDeepDive.subtitle")}</p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
                <InfoStat
                  label={t("personStatEvents")}
                  value={totalEvents}
                  accent="sky"
                />
                <InfoStat
                  label={t("personStatSwitches")}
                  value={switches}
                  accent="amber"
                />
                <InfoStat
                  label={t("personStatChambers")}
                  value={chambersCovered}
                  accent="emerald"
                />
                <InfoStat
                  label={t("personStatLegislatures")}
                  value={legislaturesCovered}
                  accent="rose"
                />
              </div>
              {sparklineData.length > 0 && (
                <div className="mt-4 flex items-center gap-2">
                  <span className="text-xs text-slate-500">
                    {t("personStatEventsTimeline")}
                  </span>
                  <Sparkline data={sparklineData} height={36} color="stroke-sky-400" />
                </div>
              )}
              <div className="mt-6 flex items-center gap-4" data-moment>
                <span className="moment-value block">
                  {totalEvents}
                </span>
                <span className="text-sm text-slate-400">{t("personDeepDive.moment")}</span>
              </div>
            </div>
            <div className="w-full md:w-auto max-w-[260px]">
              <HeroGraphic variant="people" className="mx-auto" />
            </div>
          </div>
        </div>
      </section>

      <div className="card p-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h2 className="text-2xl font-bold">{p.name}</h2>
            <p className="text-sm text-slate-400">
              {p.birth_date && `${t("born")} ${p.birth_date}`}
              {p.wikidata_qid && (
                <>
                  {" · "}
                  <a href={`https://www.wikidata.org/wiki/${p.wikidata_qid}`} target="_blank" rel="noopener noreferrer" className="text-sky-400 hover:underline">
                    Wikidata: {p.wikidata_qid} ↗
                  </a>
                </>
              )}
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="card p-4">
          <h2 className="font-semibold mb-3">{t("memberships")}</h2>
          <MembershipGantt memberships={p.memberships} />
        </div>

        <div className="card p-4">
          <h2 className="font-semibold mb-3">{t("events")}</h2>
          {p.events.length === 0 ? (
            <div className="text-slate-500 text-sm py-4">{t("noData")}</div>
          ) : (
            <div className="space-y-2 max-h-[400px] overflow-y-auto pr-1">
              {p.events.map((e) => (
                <div key={e.id} className="bg-slate-800/40 rounded-md p-2">
                  <div className="flex items-center gap-2 text-xs">
                    <span className={`font-semibold ${typeColor(e.type)}`}>{e.type}</span>
                    <span className="text-slate-500 font-mono">{e.event_date}</span>
                    {e.chamber && (
                      <span className="text-xs text-slate-500 px-1.5 py-0.5 bg-slate-800 rounded">
                        {e.chamber}
                      </span>
                    )}
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
          )}
        </div>
      </div>

      {(p.committee_memberships?.length ?? 0) > 0 && (
        <div className="card p-4">
          <h2 className="font-semibold mb-3">
            {t("committeeService", "Committee service")}
          </h2>
          <p className="text-xs text-slate-500 mb-3">
            {t(
              "committeeService.desc",
              "Dated committee tenures from the official cdep.ro ledgers (separate from party/group membership).",
            )}
          </p>
          <div className="space-y-2 max-h-[400px] overflow-y-auto pr-1">
            {(p.committee_memberships ?? []).map((m) => (
              <div key={m.id} className="bg-slate-800/40 rounded-md p-2">
                <div className="text-sm">
                  {m.org?.name || m.org?.short_name || "—"}
                  {m.role && (
                    <span className="text-sky-400 ml-1.5">· {m.role}</span>
                  )}
                </div>
                <div className="text-xs text-slate-500 mt-0.5">
                  {m.start_date ?? "—"} → {m.end_date ?? "present"}
                </div>
                {m.source_url && (
                  <a
                    href={m.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-sky-400 hover:underline"
                  >
                    {t("source", "source")} ↗
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="card p-4">
        <h2 className="font-semibold mb-3">{t("citations")}</h2>
        <div className="space-y-3">
          {p.memberships.map((m) => {
            const ev = p.evidence.filter((e) => e.membership_id === m.id);
            return (
              <div key={m.id} className="flex items-center justify-between gap-2 bg-slate-800/40 rounded-md px-3 py-2">
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
      </div>
    </div>
  );
}