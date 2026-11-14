import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api } from "../api/client";
import { useNavigate, useSearch } from "@tanstack/react-router";
import { useMemo } from "react";
import TimelineChart from "../components/TimelineChart";
import { localISODate } from "../utils/date";

export function ElectoralDynamics() {
  const { t } = useTranslation();
  const navigate = useNavigate({ from: "/electoral" });
  const search = useSearch({ from: "/electoral", select: s => s.date });
  const today = localISODate();
  const asOf = search ?? today;

  const meta = useQuery({ queryKey: ["meta"], queryFn: api.meta });
  const min = useMemo(() => {
    const legs = Object.values(meta.data?.legislatures ?? {})
      .filter((l) => l.start !== null)
      .sort((a, b) => (a.start ?? "").localeCompare(b.start ?? ""));
    return legs[0]?.start ?? "1990-06-18";
  }, [meta.data]);
  const selectedDate = asOf < min ? min : asOf > today ? today : asOf;
  const movements = useQuery({
    queryKey: ["electoral-movements", min, selectedDate],
    queryFn: () => api.movements({ from: min, to: selectedDate, limit: 1000 }),
  });

  if (movements.isLoading) {
    return (
      <div className="card p-4">
        <div className="text-slate-500 text-sm py-8">{t("loading")}</div>
      </div>
    );
  }
  if (movements.isError) {
    return (
      <div className="card p-4" role="alert">
        <p className="text-rose-200 text-sm">{t("electoralLoadError")}</p>
        <button type="button" className="btn mt-3 bg-slate-700 hover:bg-slate-600" onClick={() => movements.refetch()}>
          {t("traseismRetry")}
        </button>
      </div>
    );
  }

  // Aggregate switches by party pair
  const switches = movements.data?.filter(
    (m) => m.type === "switch_group" || m.type === "switch_party"
  ) ?? [];

  const fromPartyCounts: Record<string, number> = {};
  const toPartyCounts: Record<string, number> = {};

  for (const s of switches) {
    const from = s.from_org?.short_name || s.from_org?.name;
    const to = s.to_org?.short_name || s.to_org?.name;
    if (from) fromPartyCounts[from] = (fromPartyCounts[from] || 0) + 1;
    if (to) toPartyCounts[to] = (toPartyCounts[to] || 0) + 1;
  }

  const allParties = new Set([...Object.keys(fromPartyCounts), ...Object.keys(toPartyCounts)]);
  const isLimited = movements.data?.length === 1000;

  return (
    <div className="space-y-4">
      <div className="card p-4">
        <h2 className="font-semibold mb-3">{t("electoralDynamics")}</h2>
        <p className="text-sm text-slate-400 mb-4">{t("electoralDynamicsDesc")}</p>
        <div className="mb-4">
          <label htmlFor="electoral-as-of" className="block text-xs text-slate-300 mb-1">
            {t("asOf")}
          </label>
          <input
            id="electoral-as-of"
            type="date"
            value={selectedDate}
            min={min}
            max={today}
            onChange={(event) => {
              if (event.target.value) {
                navigate({ search: { date: event.target.value }, replace: true });
              }
            }}
            className="bg-slate-800 border border-slate-600 rounded-md px-3 py-2 text-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400"
          />
        </div>
        {isLimited && (
          <p className="text-amber-200 text-sm mb-4" role="status">
            {t("displayedMaxMovements")}
          </p>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="card p-4">
            <h3 className="font-semibold mb-3 text-emerald-400">{t("inflows")}</h3>
            {Object.entries(toPartyCounts).length === 0 ? (
              <div className="text-slate-500 text-sm">{t("noData")}</div>
            ) : (
              <div className="space-y-2">
                {Object.entries(toPartyCounts)
                  .sort((a, b) => b[1] - a[1])
                  .map(([party, count]) => (
                    <div key={party} className="flex items-center justify-between bg-slate-800/50 rounded p-2">
                      <span className="font-medium">{party}</span>
                      <span className="text-emerald-300 font-mono">+{count}</span>
                    </div>
                  ))}
              </div>
            )}
          </div>

          <div className="card p-4">
            <h3 className="font-semibold mb-3 text-rose-400">{t("outflows")}</h3>
            {Object.entries(fromPartyCounts).length === 0 ? (
              <div className="text-slate-500 text-sm">{t("noData")}</div>
            ) : (
              <div className="space-y-2">
                {Object.entries(fromPartyCounts)
                  .sort((a, b) => b[1] - a[1])
                  .map(([party, count]) => (
                    <div key={party} className="flex items-center justify-between bg-slate-800/50 rounded p-2">
                      <span className="font-medium">{party}</span>
                      <span className="text-rose-300 font-mono">−{count}</span>
                    </div>
                  ))}
              </div>
            )}
          </div>
        </div>

        <div className="card p-4">
          <h3 className="font-semibold mb-3">{t("netFlow")}</h3>
          <div className="space-y-2">
            {Array.from(allParties).map((party) => {
              const inCount = toPartyCounts[party] || 0;
              const outCount = fromPartyCounts[party] || 0;
              const net = inCount - outCount;
              return (
                <div key={party} className="flex items-center justify-between bg-slate-800/50 rounded p-2">
                  <span className="font-medium">{party}</span>
                  <span className={`font-mono ${net >= 0 ? "text-emerald-300" : "text-rose-300"}`}>
                    {net >= 0 ? "+" : ""}{net}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4">
        <TimelineChart from={min} to={selectedDate} />
      </div>
    </div>
  );
}