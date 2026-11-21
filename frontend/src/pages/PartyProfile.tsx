import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api } from "../api/client";
import { useParams } from "@tanstack/react-router";
import { useCallback, useMemo, useState } from "react";
import { useScope } from "../hooks/useScope";
import ScopeControls from "../components/ScopeControls";
import PersonDrawer from "../components/PersonDrawer";
import HeroGraphic from "../components/HeroGraphic";
import InfoStat from "../components/InfoStat";
import { Sparkline } from "../components/DataViz";
import AsyncState, { resolveViewState } from "../components/ui/AsyncState";

function formatCount(value: number | null): string {
  return value === null ? "—" : value.toLocaleString();
}

export function PartyProfile() {
  const { t } = useTranslation();
  const params = useParams({ from: "/party/$shortName" });
  const scope = useScope();
  const shortName = params.shortName;
  const asOf = scope.date;
  const [personId, setPersonId] = useState<string | null>(null);
  const closePerson = useCallback(() => setPersonId(null), []);

  const party = useQuery({
    queryKey: ["party", shortName, asOf, ...scope.scopeKey],
    queryFn: () => api.partyProfile(shortName, asOf),
    enabled: !!shortName,
  });

  const movements = useQuery({
    queryKey: ["party-movements", shortName, asOf, ...scope.scopeKey],
    queryFn: () => api.partyMovements(shortName, asOf),
    enabled: !!shortName,
  });

  // All hooks must be declared before any early return (React #310).
  // Both memos depend only on movements.data, so they are safe to compute
  // before the party loading/error guards below.
  const chambersCovered = useMemo(() => {
    const chambers = new Set<string>();
    for (const m of movements.data ?? []) {
      if (m.chamber) chambers.add(m.chamber);
    }
    return chambers.size;
  }, [movements.data]);

  const switchTimeline = useMemo(() => {
    const counts = new Map<string, number>();
    for (const m of movements.data ?? []) {
      const previous = counts.get(m.event_date);
      counts.set(m.event_date, previous === undefined ? 1 : previous + 1);
    }
    return [...counts.entries()]
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([, c]) => c);
  }, [movements.data]);

  const view = resolveViewState({
    isLoading: party.isLoading,
    isError: party.isError,
    isEmpty: party.isSuccess && !party.data,
  });
  if (view !== "ready") {
    return (
      <AsyncState
        view={view}
        pageTitle={t("party", "Party")}
        onRetry={() => void party.refetch()}
        errorLabel={t("partyLoadError")}
        emptyTitle={t("partyProfile.empty", "There are no data for this party.")}
      />
    );
  }

  const p = party.data!;

  const movementsView = resolveViewState({
    isLoading: movements.isLoading,
    isError: movements.isError,
    isEmpty: movements.isSuccess && (movements.data?.length ?? 0) === 0,
  });

  // R-04: backend null means "no dated data", not zero. Never fabricate a sum.
  const totalSwitches =
    p.switches_in === null || p.switches_out === null
      ? null
      : p.switches_in + p.switches_out;

  const hasSwitchTimeline = switchTimeline.length > 0;

  return (
    <div className="space-y-6">
      <ScopeControls showDate />
      {/* Section 1: Hero — fills the first screen alone */}
      <section className="hero-section" data-enter>
        <div>
          <div className="flex flex-col md:flex-row md:items-center gap-8">
            <div className="flex-1 space-y-4">
              <HeroGraphic variant="committee" className="mx-auto md:mx-0 mb-6 md:mb-0" />
              <h1 className="page-title">{p.name}</h1>
              <p className="text-sm text-slate-400">{p.short_name} · {t("party")}</p>
              {p.wikidata_qid && (
                <a
                  href={`https://www.wikidata.org/wiki/${p.wikidata_qid}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-sky-400 hover:underline"
                >
                  Wikidata: {p.wikidata_qid} ↗
                </a>
              )}
              {/* Dealt moment: party membership count */}
              <div className="mt-6 flex items-center gap-3 px-3 py-2 rounded bg-slate-800/50 border border-slate-700/50" data-moment>
                <span className="moment-badge">{t("currentMembers")}</span>
                <span className="moment-value">{formatCount(p.current_members)}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Section 2: Info-graphic stat cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <InfoStat
          label={t("pp.totalMembers", "Total members")}
          value={p.current_members ?? "--"}
          accent="emerald"
        />
        <InfoStat
          label={t("pp.totalSwitches", "Party switches (in + out)")}
          value={totalSwitches === null ? "—" : totalSwitches}
          accent="sky"
        />
        <InfoStat
          label={t("pp.activeMembers", "Active members")}
          value={p.current_members ?? "--"}
          accent="sky"
        />
        <InfoStat
          label={t("committees.chambersCovered", "Chambers covered")}
          value={chambersCovered}
          max={2}
          accent="sky"
          showBar
        />
      </div>

      {/* Section 3: Switch timeline sparkline (when movement data is available) */}
      {hasSwitchTimeline && (
        <section className="card p-4">
          <h2 className="font-semibold mb-3">{t("pp.switchTimeline", "Switch timeline")}</h2>
          <div className="h-24 w-full flex items-center">
            <Sparkline data={switchTimeline} color="stroke-sky-400" />
          </div>
          <p className="text-xs text-slate-500 mt-2">
            {t("pp.switchTimelineNote", "Switch events per day across recorded movements")}
          </p>
        </section>
      )}

      {/* Section 4: Recent movements (existing) */}
      <div className="card p-4">
        <h2 className="font-semibold mb-3">{t("recentMovements")}</h2>
        <AsyncState
          view={movementsView}
          variant="inline"
          onRetry={() => void movements.refetch()}
          errorLabel={t("electoralLoadError")}
          emptyTitle={t("noData")}
        >
          <div className="space-y-2 max-h-[400px] overflow-y-auto pr-1">
            {movements.data?.map((m) => (
              <button type="button" key={m.id}
                onClick={() => m.person && setPersonId(m.person.id)}
                className="w-full text-left bg-slate-800/40 hover:bg-slate-800 rounded-md p-2 transition-colors"
              >
                <div className="flex items-center gap-2 text-xs">
                  <span className={`font-semibold ${m.type === "switch_party" || m.type === "switch_group" ? "text-amber-400" : m.type === "join" ? "text-emerald-400" : "text-rose-400"}`}>
                    {m.type}
                  </span>
                  <span className="text-slate-500 font-mono">{m.event_date}</span>
                  {m.chamber && (
                    <span className="text-xs text-slate-500 px-1.5 py-0.5 bg-slate-800 rounded">
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
        </AsyncState>
      </div>

      <PersonDrawer personId={personId} onClose={closePerson} />
    </div>
  );
}
