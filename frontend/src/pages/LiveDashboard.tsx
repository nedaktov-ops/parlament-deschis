import { Suspense, lazy, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api } from "../api/client";
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
    <div className="space-y-4">
      <div>
        <h2 className="text-2xl font-bold">{t("overview")}</h2>
        <p className="text-sm text-slate-400 mt-1">{t("dashboardIntro")}</p>
      </div>
      <div className="space-y-4">
        {meta.isError && (
          <div className="text-rose-200 text-sm" role="alert">
            {t("metaLoadError")}
            <button type="button" className="ml-3 underline" onClick={() => meta.refetch()}>
              {t("traseismRetry")}
            </button>
          </div>
        )}
        {coverage.isError ? (
          <div className="text-rose-200 text-sm" role="alert">
            {t("coverageLoadError")}
            <button type="button" className="ml-3 underline" onClick={() => coverage.refetch()}>
              {t("traseismRetry")}
            </button>
          </div>
        ) : (
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="text-slate-300">{t("coverageNote")}:</span>
            <span className="bg-slate-800 rounded px-2 py-0.5 text-slate-200">
              {currentCoverage?.legislature ?? selectedLegislature ?? t("currentTerm")}
            </span>
            <span
              className={`rounded px-2 py-0.5 ${completenessClass(
                currentCoverage?.completeness ?? "none",
              )}`}
            >
              {t(currentCoverage?.completeness ?? "none")}
            </span>
          </div>
        )}

        <TimeSlider value={clamped} min={min} max={TODAY} onChange={changeDate} ticks={ticks} />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <ChamberView chamber="deputies" asOf={clamped} onSelect={openPerson} />
          <ChamberView chamber="senate" asOf={clamped} onSelect={openPerson} />
          <LiveFeed onSelect={openPerson} legislature={selectedLegislature} />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4">
        <Suspense fallback={<div className="card p-4 h-64 animate-pulse bg-slate-800/50 rounded-xl" aria-busy="true" aria-label={t("loading")} />}>
          <TimelineChart from={min} to={clamped} groups={meta.data?.groups} />
        </Suspense>
      </div>
    </div>
  );
}