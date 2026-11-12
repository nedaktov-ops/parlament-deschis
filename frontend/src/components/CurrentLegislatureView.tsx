import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api, type GroupComposition } from "../api/client";
import ChamberView from "./ChamberView";
import GroupLegend from "./GroupLegend";
import TimelineChart from "./TimelineChart";
import DefectionSankeyCurrent from "./DefectionSankeyCurrent";

interface Props {
  asOf: string;
  onSelect: (id: string) => void;
  currentLegislature: string | null;
}

const LEGISLATURE_START = "2024-12-21";

function diffGroups(
  oldGroups: GroupComposition[],
  newGroups: GroupComposition[],
): { joined: string[]; left: string[]; changed: Array<{ name: string; old: number; new: number; diff: number }> } {
  const oldMap = new Map(oldGroups.map((g) => [g.short_name, g]));
  const newMap = new Map(newGroups.map((g) => [g.short_name, g]));

  const joined: string[] = [];
  const left: string[] = [];
  const changed: Array<{ name: string; old: number; new: number; diff: number }> = [];

  for (const [name, newG] of newMap) {
    const oldG = oldMap.get(name);
    if (!oldG) {
      joined.push(name);
    } else if (oldG.count !== newG.count) {
      changed.push({ name, old: oldG.count, new: newG.count, diff: newG.count - oldG.count });
    }
  }
  for (const [name] of oldMap) {
    if (!newMap.has(name)) {
      left.push(name);
    }
  }
  return { joined, left, changed };
}

export default function CurrentLegislatureView({
  asOf,
  onSelect,
  currentLegislature,
}: Props) {
  const { t } = useTranslation();

  // Current composition (as of selected date)
  const deputiesNow = useQuery({
    queryKey: ["chamber", "deputies", asOf],
    queryFn: () => api.chamber("deputies", asOf),
  });
  const senateNow = useQuery({
    queryKey: ["chamber", "senate", asOf],
    queryFn: () => api.chamber("senate", asOf),
  });

  // Composition at start of legislature
  const deputiesStart = useQuery({
    queryKey: ["chamber", "deputies", LEGISLATURE_START],
    queryFn: () => api.chamber("deputies", LEGISLATURE_START),
    enabled: asOf !== LEGISLATURE_START,
  });
  const senateStart = useQuery({
    queryKey: ["chamber", "senate", LEGISLATURE_START],
    queryFn: () => api.chamber("senate", LEGISLATURE_START),
    enabled: asOf !== LEGISLATURE_START,
  });

  // Movements in current legislature
  const movements = useQuery({
    queryKey: ["current-leg-movements", asOf],
    queryFn: () => api.movements(),
  });

  const isCurrentLeg = currentLegislature === "2024";
  const showDiff = asOf !== LEGISLATURE_START;

  if (deputiesNow.isLoading || senateNow.isLoading) {
    return (
      <div className="card p-4">
        <div className="text-slate-500 text-sm py-8">{t("loading")}</div>
      </div>
    );
  }

  const deputiesDiff = showDiff ? diffGroups(
    deputiesStart.data?.groups ?? [],
    deputiesNow.data?.groups ?? [],
  ) : null;
  const senateDiff = showDiff ? diffGroups(
    senateStart.data?.groups ?? [],
    senateNow.data?.groups ?? [],
  ) : null;

  return (
    <div className="space-y-4">
      {/* Header with legislature info */}
      <div className="card p-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold">
              {t("currentLegislature")}: {currentLegislature ?? "—"}
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              {t("period")}: {LEGISLATURE_START} → {asOf}
              {isCurrentLeg ? "" : ` (${t("historicalView")})`}
            </p>
          </div>
          {showDiff && (
            <button
              onClick={() => window.location.search = window.location.search.replace(/date=[^&]*/, `date=${LEGISLATURE_START}`)}
              className="btn bg-slate-700 hover:bg-slate-600 text-xs"
            >
              {t("viewStartOfLegislature")}
            </button>
          )}
        </div>
      </div>

      {/* Chamber comparison: Start vs Now */}
      {showDiff && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="card p-4">
            <h3 className="font-semibold mb-3 flex items-center gap-2">
              {t("deputies")} — {t("compositionChange")}
            </h3>
            <CompositionDiff
              joined={deputiesDiff?.joined ?? []}
              left={deputiesDiff?.left ?? []}
              changed={deputiesDiff?.changed ?? []}
              nowGroups={deputiesNow.data?.groups ?? []}
              startGroups={deputiesStart.data?.groups ?? []}
            />
          </div>
          <div className="card p-4">
            <h3 className="font-semibold mb-3 flex items-center gap-2">
              {t("senate")} — {t("compositionChange")}
            </h3>
            <CompositionDiff
              joined={senateDiff?.joined ?? []}
              left={senateDiff?.left ?? []}
              changed={senateDiff?.changed ?? []}
              nowGroups={senateNow.data?.groups ?? []}
              startGroups={senateStart.data?.groups ?? []}
            />
          </div>
        </div>
      )}

      {/* Current chamber composition (as of selected date) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="card p-4 flex flex-col">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold">{t("deputies")} ({t("asOf")} {asOf})</h3>
            <span className="text-xs text-slate-400">
              {deputiesNow.data?.total ?? 0} {t("totalSeats")}
            </span>
          </div>
          {deputiesNow.isLoading && <div className="text-slate-500 text-sm py-8">{t("loading")}</div>}
          {deputiesNow.data && deputiesNow.data.total === 0 && (
            <div className="text-slate-500 text-sm py-8">{t("noData")}</div>
          )}
          {deputiesNow.data && deputiesNow.data.total > 0 && (
            <>
              <ChamberView chamber="deputies" asOf={asOf} onSelect={onSelect} />
              <div className="mt-3">
                <GroupLegend groups={deputiesNow.data.groups} />
              </div>
            </>
          )}
        </div>

        <div className="card p-4 flex flex-col">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold">{t("senate")} ({t("asOf")} {asOf})</h3>
            <span className="text-xs text-slate-400">
              {senateNow.data?.total ?? 0} {t("totalSeats")}
            </span>
          </div>
          {senateNow.isLoading && <div className="text-slate-500 text-sm py-8">{t("loading")}</div>}
          {senateNow.data && senateNow.data.total === 0 && (
            <div className="text-slate-500 text-sm py-8">{t("noData")}</div>
          )}
          {senateNow.data && senateNow.data.total > 0 && (
            <>
              <ChamberView chamber="senate" asOf={asOf} onSelect={onSelect} />
              <div className="mt-3">
                <GroupLegend groups={senateNow.data.groups} />
              </div>
            </>
          )}
        </div>

        {/* Movements in current legislature */}
        <div className="card p-4 flex flex-col">
          <h3 className="font-semibold mb-3">{t("movementsInLegislature")}</h3>
          {movements.isLoading && <div className="text-slate-500 text-sm py-4">{t("loading")}</div>}
          {movements.data && (
            <div className="space-y-2 max-h-[420px] overflow-y-auto pr-1">
              {movements.data
                .filter((m) => {
                  if (!m.event_date) return false;
                  return m.event_date >= LEGISLATURE_START;
                })
                .slice(0, 25)
                .map((m) => (
                  <button
                    key={m.id}
                    onClick={() => m.person && onSelect(m.person.id)}
                    className="w-full text-left bg-slate-800/40 hover:bg-slate-800 rounded-md p-2 transition-colors"
                  >
                    <div className="flex items-center gap-2 text-xs">
                      <span className={`font-semibold ${
                        m.type === "switch_group" || m.type === "switch_party"
                          ? "text-amber-400"
                          : m.type === "join"
                          ? "text-emerald-400"
                          : "text-rose-400"
                      }`}>
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
              {movements.data.filter((m) => m.event_date && m.event_date >= LEGISLATURE_START).length === 0 && (
                <div className="text-slate-500 text-sm py-8 text-center">{t("noData")}</div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Group timeline and defection sankey for current legislature only */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <TimelineChart
          from={LEGISLATURE_START}
          to={asOf}
          groups={deputiesNow.data?.groups.map((g) => g.org).filter((o): o is NonNullable<typeof o> => o !== null)}
        />
        <DefectionSankeyCurrent fromDate={LEGISLATURE_START} />
      </div>
    </div>
  );
}

function CompositionDiff({
  joined,
  left,
  changed,
  nowGroups,
  startGroups,
}: {
  joined: string[];
  left: string[];
  changed: Array<{ name: string; old: number; new: number; diff: number }>;
  nowGroups: GroupComposition[];
  startGroups: GroupComposition[];
}) {
  const { t } = useTranslation();

  const nowMap = new Map(nowGroups.map((g) => [g.short_name, g]));
  const startMap = new Map(startGroups.map((g) => [g.short_name, g]));

  if (joined.length === 0 && left.length === 0 && changed.length === 0) {
    return <div className="text-slate-500 text-sm py-4">{t("noChange")}</div>;
  }

  return (
    <div className="space-y-3">
      {joined.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-emerald-400 mb-2">{t("groupsJoined")} (+{joined.length})</h4>
          <div className="flex flex-wrap gap-1.5">
            {joined.map((name) => {
              const g = nowMap.get(name);
              return (
                <span
                  key={name}
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-emerald-900/30 border border-emerald-800 text-xs"
                  style={{ borderColor: g?.color || "#64748b" }}
                >
                  <span className="w-2 h-2 rounded-full" style={{ background: g?.color || "#64748b" }} />
                  {name} ({g?.count ?? 0})
                </span>
              );
            })}
          </div>
        </div>
      )}

      {left.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-rose-400 mb-2">{t("groupsDissolved")} (−{left.length})</h4>
          <div className="flex flex-wrap gap-1.5">
            {left.map((name) => {
              const g = startMap.get(name);
              return (
                <span
                  key={name}
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-rose-900/30 border border-rose-800 text-xs"
                  style={{ borderColor: g?.color || "#64748b" }}
                >
                  <span className="w-2 h-2 rounded-full" style={{ background: g?.color || "#64748b" }} />
                  {name} (era: {g?.count ?? 0})
                </span>
              );
            })}
          </div>
        </div>
      )}

      {changed.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-amber-400 mb-2">{t("groupsChanged")} ({changed.length})</h4>
          <div className="space-y-1">
            {changed
              .sort((a, b) => Math.abs(b.diff) - Math.abs(a.diff))
              .map((c) => {
                const g = nowMap.get(c.name);
                return (
                  <div
                    key={c.name}
                    className={`flex items-center gap-2 text-xs bg-slate-800/40 rounded p-1.5 ${
                      c.diff > 0 ? "text-emerald-400" : "text-rose-400"
                    }`}
                    style={{ borderLeftColor: g?.color || "#64748b" }}
                  >
                    <span className="w-2 h-2 rounded-full" style={{ background: g?.color || "#64748b" }} />
                    <span className="font-medium truncate">{c.name}</span>
                    <span className="text-slate-500">{c.old}</span>
                    <span className="text-slate-500">→</span>
                    <span className="font-mono">
                      {c.new} ({c.diff > 0 ? "+" : ""}{c.diff})
                    </span>
                  </div>
                );
              })}
          </div>
        </div>
      )}
    </div>
  );
}