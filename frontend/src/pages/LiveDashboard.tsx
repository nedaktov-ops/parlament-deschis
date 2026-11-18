import { Suspense, lazy, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api, type OrgBrief } from "../api/client";
import { useNavigate, useSearch } from "@tanstack/react-router";
import ChamberView from "../components/ChamberView";
import LiveFeed from "../components/LiveFeed";
import TimeSlider from "../components/TimeSlider";
import { localISODate } from "../utils/date";

// Lazy-load TimelineChart (bundles ECharts ~220 KB) so it doesn't block initial paint
const TimelineChart = lazy(() => import("../components/TimelineChart"));

const TODAY = localISODate();

export function LiveDashboard() {
  const { t } = useTranslation();
  const navigate = useNavigate({ from: "/" });
  const search = useSearch({ from: "/", select: s => s.date });
  const asOf = search ?? TODAY;

  const meta = useQuery({ queryKey: ["meta"], queryFn: api.meta });
  const coverage = useQuery({ queryKey: ["coverage"], queryFn: api.coverage });

  const { min, ticks } = useMemo(() => {
    const legs = Object.values(meta.data?.legislatures ?? {})
      .filter((l) => l.start !== null)
      .sort((a, b) => (a.start ?? "").localeCompare(b.start ?? ""));
    const start = legs[0]?.start ?? null;
    const earliest = start !== null && start <= TODAY ? start : "1990-06-18";
    return {
      min: earliest,
      ticks: legs.map((l) => ({ label: l.label, start: l.start ?? "" })),
    };
  }, [meta.data]);

  const clamped = asOf < min ? min : asOf > TODAY ? TODAY : asOf;

  const currentCoverage = useMemo(() => {
    const matched = (coverage.data ?? []).filter(
      (c) =>
        c.period_start !== null &&
        c.period_start <= clamped &&
        (c.period_end === null || clamped < c.period_end),
    );
    if (matched.length === 0) return undefined;
    const rank = (value: string) =>
      value === "full" ? 2 : value === "partial" ? 1 : 0;
    return matched.reduce((worst, row) =>
      rank(row.completeness) < rank(worst.completeness) ? row : worst,
    );
  }, [coverage.data, clamped]);

  const selectedLegislature = useMemo(() => {
    const legs = Object.values(meta.data?.legislatures ?? {})
      .filter((l) => l.start !== null)
      .sort((a, b) => (a.start ?? "").localeCompare(b.start ?? ""));
    return (
      legs.find(
        (l) =>
          (l.start ?? "") <= clamped &&
          (l.end === null || clamped < l.end),
      )?.label ?? null
    );
  }, [meta.data, clamped]);

  const changeDate = (iso: string) => {
    navigate({ search: { date: iso }, replace: true });
  };

  const openPerson = (id: string) => {
    navigate({
      to: "/person/$id",
      params: { id },
      search: { date: clamped },
    });
  };

  function completenessClass(value: string): string {
    if (value === "full") return "bg-emerald-900/50 text-emerald-300";
    if (value === "partial") return "bg-amber-900/50 text-amber-300";
    return "bg-slate-800 text-slate-400";
  }

  return (
    <div className="wrap space-y-6">
      {/* Section 1: Hero — fills the first screen alone */}
      <section className="min-h-screen flex flex-col justify-center py-8" data-enter>
        <div className="max-w-3xl">
          <h1 className="text-2xl font-bold">{t("overview")}</h1>
          <p className="text-sm text-slate-400 mt-1">{t("dashboardIntro")}</p>
          {meta.isError && (
            <div className="text-rose-200 text-sm mt-4" role="alert">
              {t("metaLoadError")}
              <button type="button"className="ml-3 underline" onClick={() => meta.refetch()}>
                {t("traseismRetry")}
              </button>
            </div>
          )}
          {coverage.isError && (
            <div className="text-rose-200 text-sm mt-4" role="alert">
              {t("coverageLoadError")}
              <button type="button"className="ml-3 underline" onClick={() => coverage.refetch()}>
                {t("traseismRetry")}
              </button>
            </div>
          )}
          {!meta.isError && !coverage.isError && (
            <div className="flex flex-wrap items-center gap-2 text-xs mt-4">
              <span className="text-slate-300">{t("coverageNote")}:</span>
              {currentCoverage ? (
                <>
                  <span className="bg-slate-800 rounded px-2 py-0.5 text-slate-200">
                    {currentCoverage.legislature ?? selectedLegislature ?? t("currentTerm")}
                  </span>
                  <span
                    className={`rounded px-2 py-0.5 ${completenessClass(
                      currentCoverage.completeness,
                    )}`}
                  >
                    {t(currentCoverage.completeness)}
                  </span>
                </>
              ) : (
                <div className="flex items-center gap-2 px-2 py-1 rounded bg-slate-800/50 border border-slate-700/50">
                  <span className="text-slate-400 text-xs">{t("coverageNoData")}</span>
                  <button
                    type="button"
                    className="text-xs underline text-sky-400 hover:text-sky-300"
                    onClick={() => coverage.refetch()}
                  >
                    {t("traseismRetry")}
                  </button>
                </div>
              )}
            </div>
          )}
            {meta.data && (
              <p className="mt-6 text-slate-200" data-moment>
                <span className="text-4xl font-bold block tracking-tight">
                  {Object.keys(meta.data.legislatures).length}
                </span>
                <span className="text-sm text-slate-400 mt-1">
                  {t("dashboardLegislatures", "legislatures in the corpus")}
                </span>
              </p>
            )}
        </div>
      </section>

      {/* Section 2: Bento grid — main visualizations (TimelineChart + chambers) */}
      <section className="wrap space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Large tile — TimelineChart, most important visualization */}
          <TimelineChartTile
            from={min}
            to={clamped}
            groups={meta.data?.groups}
          />
          {/* Medium tile — deputies chamber */}
          <ChamberViewTile chamber="deputies" asOf={clamped} onSelect={openPerson} />
          {/* Medium tile — senate chamber */}
          <ChamberViewTile chamber="senate" asOf={clamped} onSelect={openPerson} />
        </div>
      </section>

      {/* Section 3: Bento grid — live feed and time controls */}
      <section className="wrap space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Medium tile — LiveFeed */}
          <div className="md:col-span-2 card p-4 flex flex-col h-full">
            <LiveFeed onSelect={openPerson} legislature={selectedLegislature} />
          </div>
          {/* Medium tile — TimeSlider */}
          <div className="md:col-span-2 card p-4 flex flex-col h-full">
            <TimeSlider value={clamped} min={min} max={TODAY} onChange={changeDate} ticks={ticks} />
          </div>
        </div>
      </section>
    </div>
  );
}

function TimelineChartTile({
  from,
  to,
  groups,
}: {
  from: string;
  to: string;
  groups: OrgBrief[] | undefined;
}) {
  return (
    <div className="md:col-span-2 card p-4 flex flex-col h-full">
      <Suspense fallback={<div className="card p-4 h-64 animate-pulse bg-slate-800/50 rounded-xl" aria-busy="true" aria-label="Loading…" />}>
        <TimelineChart from={from} to={to} groups={groups} />
      </Suspense>
    </div>
  );
}

function ChamberViewTile({
  chamber,
  asOf,
  onSelect,
}: {
  chamber: "deputies" | "senate";
  asOf: string;
  onSelect: (id: string) => void;
}) {
  return (
    <div className="md:col-span-1 card p-4 flex flex-col h-full">
      <ChamberView chamber={chamber} asOf={asOf} onSelect={onSelect} />
    </div>
  );
}
