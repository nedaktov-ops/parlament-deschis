import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api } from "../api/client";
import { useParams, useSearch } from "@tanstack/react-router";
import TimelineChart from "../components/TimelineChart";
import DefectionSankey from "../components/DefectionSankey";

export function LegislatureDetail() {
  const { t } = useTranslation();
  const params = useParams({ from: "/legislature/$year" });
  const search = useSearch({ from: "/legislature/$year", select: s => s.date });
  const year: string = params.year as string;
  const asOf: string = (search as string) ?? new Date().toISOString().slice(0, 10);

  const meta = useQuery({ queryKey: ["meta"], queryFn: api.meta });
  const chamber = useQuery({
    queryKey: ["chamber", "deputies", asOf],
    queryFn: () => api.chamber("deputies", asOf),
  });
  const movements = useQuery({
    queryKey: ["leg-movements", year, asOf],
    queryFn: () => api.movements(),
  });

  if (chamber.isLoading) {
    return (
      <div className="card p-4">
        <div className="text-slate-500 text-sm py-8">{t("loading")}</div>
      </div>
    );
  }

  const leg = meta.data?.legislatures?.[year];
  const start = leg?.start ?? "2024-12-21";
  const end = leg?.end ?? new Date().toISOString().slice(0, 10);

  return (
    <div className="space-y-4">
      <div className="card p-4">
        <h1 className="text-2xl font-bold">{t("legislature")} {year}</h1>
        <p className="text-sm text-slate-400 mt-1">
          {t("period")}: {start} → {end}
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="card p-4">
          <h3 className="font-semibold mb-3">{t("deputies")}</h3>
          {chamber.isLoading ? (
            <div className="text-slate-500 text-sm">{t("loading")}</div>
          ) : chamber.data?.total === 0 ? (
            <div className="text-slate-500 text-sm">{t("noData")}</div>
          ) : (
            <>
              <div className="space-y-2">
                {chamber.data?.groups?.map((g) => (
                  <div key={g.short_name} className="flex items-center justify-between bg-slate-800/50 rounded p-2">
                    <div className="flex items-center gap-2">
                      <span className="w-3 h-3 rounded-full" style={{ background: g.color || "#64748b" }} />
                      <span className="font-medium">{g.short_name}</span>
                    </div>
                    <span className="text-slate-400">{g.count} {t("members")}</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>

        <div className="card p-4">
          <h3 className="font-semibold mb-3">{t("recentMovements")}</h3>
          {movements.isLoading ? (
            <div className="text-slate-500 text-sm">{t("loading")}</div>
          ) : (
            <div className="space-y-2 max-h-[400px] overflow-y-auto pr-1">
              {movements.data
                ?.filter((m) => m.event_date && m.event_date >= start && m.event_date <= end)
                .slice(0, 20)
                .map((m) => (
                  <button
                    key={m.id}
                    className="w-full text-left bg-slate-800/40 hover:bg-slate-800 rounded-md p-2 transition-colors"
                  >
                    <div className="flex items-center gap-2 text-xs">
                      <span className={`font-semibold ${m.type === "switch_group" || m.type === "switch_party" ? "text-amber-400" : m.type === "join" ? "text-emerald-400" : "text-rose-400"}`}>
                        {m.type}
                      </span>
                      <span className="text-slate-500 font-mono">{m.event_date}</span>
                    </div>
                    <div className="text-sm mt-0.5">
                      {m.person?.name ?? "—"}:
                      {m.from_org?.short_name ?? "—"} → {m.to_org?.short_name ?? "—"}
                    </div>
                  </button>
                ))}
              {movements.data?.filter((m) => m.event_date && m.event_date >= start && m.event_date <= end).length === 0 && (
                <div className="text-slate-500 text-sm py-8 text-center">{t("noData")}</div>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <TimelineChart from={start} to={end} />
        <DefectionSankey />
      </div>
    </div>
  );
}