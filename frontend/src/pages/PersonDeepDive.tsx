import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api, type EventItem } from "../api/client";
import { useParams } from "@tanstack/react-router";
import MembershipGantt from "../components/MembershipGantt";
import CitationPopover from "../components/CitationPopover";

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

  if (person.isLoading) {
    return (
      <div className="card p-4">
        <div className="text-slate-500 text-sm py-8">{t("loading")}</div>
      </div>
    );
  }

  if (person.isError || !p) {
    return (
      <div className="card p-4" role="alert">
        <p className="text-rose-200 text-sm py-4">{t("personLoadError")}</p>
        <button type="button" className="btn bg-slate-700 hover:bg-slate-600" onClick={() => person.refetch()}>
          {t("traseismRetry")}
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="card p-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold">{p.name}</h1>
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
                      <span className="text-[10px] text-slate-500 px-1.5 py-0.5 bg-slate-800 rounded">
                        {e.chamber}
                      </span>
                    )}
                  </div>
                  <div className="text-sm mt-0.5">{summary(e)}</div>
                  {(e.from_org || e.to_org) && (
                    <div className="text-[11px] text-slate-500 mt-0.5">
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
                  <div className="text-[11px] text-slate-500 font-mono">
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