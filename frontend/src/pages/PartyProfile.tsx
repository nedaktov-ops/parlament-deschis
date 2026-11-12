import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api } from "../api/client";
import { useParams, useSearch } from "@tanstack/react-router";
import { useState } from "react";
import TimelineChart from "../components/TimelineChart";
import DefectionSankey from "../components/DefectionSankey";
import PersonDrawer from "../components/PersonDrawer";

export function PartyProfile() {
  const { t } = useTranslation();
  const params = useParams({ from: "/party/$shortName" });
  const search = useSearch({ from: "/party/$shortName", select: s => s.date });
  const shortName: string = params.shortName as string;
  const asOf: string = (search as string) ?? new Date().toISOString().slice(0, 10);
  const [personId, setPersonId] = useState<string | null>(null);

  const party = useQuery({
    queryKey: ["party", shortName, asOf],
    queryFn: () => api.partyProfile(shortName, asOf),
    enabled: !!shortName,
  });

  const movements = useQuery({
    queryKey: ["party-movements", shortName, asOf],
    queryFn: () => api.partyMovements(shortName, asOf),
    enabled: !!shortName,
  });

  if (party.isLoading) {
    return (
      <div className="card p-4">
        <div className="text-slate-500 text-sm py-8">{t("loading")}</div>
      </div>
    );
  }

  if (party.isError || !party.data) {
    return (
      <div className="card p-4">
        <div className="text-rose-400 text-sm py-8">{t("noData")}</div>
      </div>
    );
  }

  const p = party.data;
  const partyColor = p.color || "#64748b";

  return (
    <div className="space-y-4">
      <div className="card p-4">
        <div className="flex items-center gap-3">
          <span className="w-8 h-8 rounded-full" style={{ background: partyColor }} />
          <div>
            <h1 className="text-2xl font-bold">{p.name}</h1>
            <p className="text-sm text-slate-400">{p.short_name} · {t("party")}</p>
            {p.wikidata_qid && (
              <a href={`https://www.wikidata.org/wiki/${p.wikidata_qid}`} target="_blank" rel="noopener noreferrer" className="text-xs text-sky-400 hover:underline">
                Wikidata: {p.wikidata_qid} ↗
              </a>
            )}
          </div>
        </div>
        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
          <div className="bg-slate-800/50 rounded p-3">
            <div className="text-slate-500">{t("currentMembers")}</div>
            <div className="text-2xl font-bold text-emerald-300">{p.current_members ?? 0}</div>
          </div>
          <div className="bg-slate-800/50 rounded p-3">
            <div className="text-slate-500">{t("switchesIn")}</div>
            <div className="text-2xl font-bold text-emerald-300">{p.switches_in ?? 0}</div>
          </div>
          <div className="bg-slate-800/50 rounded p-3">
            <div className="text-slate-500">{t("switchesOut")}</div>
            <div className="text-2xl font-bold text-rose-300">{p.switches_out ?? 0}</div>
          </div>
          <div className="bg-slate-800/50 rounded p-3">
            <div className="text-slate-500">{t("netChange")}</div>
            <div className={`text-2xl font-bold ${(p.net_change ?? 0) >= 0 ? "text-emerald-300" : "text-rose-300"}`}>
              {(p.net_change ?? 0) >= 0 ? "+" : ""}{p.net_change ?? 0}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <TimelineChart
          from="2024-12-21"
          to={new Date().toISOString().slice(0, 10)}
        />
        <DefectionSankey />
      </div>

      <div className="card p-4">
        <h2 className="font-semibold mb-3">{t("recentMovements")}</h2>
        {movements.isLoading ? (
          <div className="text-slate-500 text-sm py-4">{t("loading")}</div>
        ) : movements.data?.length === 0 ? (
          <div className="text-slate-500 text-sm py-4">{t("noData")}</div>
        ) : (
          <div className="space-y-2 max-h-[400px] overflow-y-auto pr-1">
            {movements.data?.map((m) => (
              <button
                key={m.id}
                onClick={() => m.person && setPersonId(m.person.id)}
                className="w-full text-left bg-slate-800/40 hover:bg-slate-800 rounded-md p-2 transition-colors"
              >
                <div className="flex items-center gap-2 text-xs">
                  <span className={`font-semibold ${m.type === "switch_party" || m.type === "switch_group" ? "text-amber-400" : m.type === "join" ? "text-emerald-400" : "text-rose-400"}`}>
                    {m.type}
                  </span>
                  <span className="text-slate-500 font-mono">{m.event_date}</span>
                  {m.chamber && (
                    <span className="text-[10px] text-slate-500 px-1.5 py-0.5 bg-slate-800 rounded">
                      {m.chamber}
                    </span>
                  )}
                </div>
                <div className="text-sm mt-0.5">
                  {m.person?.name ?? "—"}:
                  {m.from_org?.short_name ?? "—"} → {m.to_org?.short_name ?? "—"}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      <PersonDrawer personId={personId} onClose={() => setPersonId(null)} />
    </div>
  );
}