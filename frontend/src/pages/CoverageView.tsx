import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api } from "../api/client";
import { useScope } from "../hooks/useScope";
import ScopeControls from "../components/ScopeControls";
import HeroGraphic from "../components/HeroGraphic";
import InfoStat from "../components/InfoStat";
import { ProgressRing } from "../components/DataViz";
import AsyncState, { resolveViewState } from "../components/ui/AsyncState";

function completenessClass(value: string): string {
  if (value === "full") return "bg-emerald-900/50 text-emerald-300";
  if (value === "partial") return "bg-amber-900/50 text-amber-300";
  return "bg-slate-800 text-slate-400";
}

function fmtPct(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "—";
  return `${value}%`;
}

function fmtDate(value: string | null | undefined): string {
  if (!value) return "—";
  return value;
}

export default function CoverageView() {
  const { t } = useTranslation();
  const scope = useScope();

  const coverage = useQuery({
    queryKey: ["coverage-detailed", ...scope.scopeKey],
    queryFn: () => api.coverage_detailed(),
  });

  // Chamber/legislature are client-side row filters on a data-availability
  // matrix; the endpoint itself takes no scope params.
  const rows = useMemo(
    () => (coverage.data ?? []).filter(
      (r) =>
        (!scope.chamber || r.chamber === scope.chamber) &&
        (!scope.legislature || r.legislature === scope.legislature),
    ),
    [coverage.data, scope.chamber, scope.legislature],
  );
  // R-04: corpus-wide aggregates come from the API's raw integer counts,
  // never from back-computing rows via rounded percentages.
  const summary = useQuery({
    queryKey: ["coverage-summary"],
    queryFn: () => api.coverageSummary(),
  });
  const totals = useMemo(
    () => ({
      totalMemberships: summary.data?.totals?.memberships ?? null,
      datedMemberships: summary.data?.totals?.memberships_dated ?? null,
      totalSwitches: summary.data?.totals?.switches_all ?? null,
      sourcedSwitches: summary.data?.totals?.switches_sourced ?? null,
    }),
    [summary.data],
  );

  const chamberCount = useMemo(() => new Set(rows.map((r) => r.chamber)).size, [rows]);
  const legislatureCount = useMemo(
    () => new Set(rows.map((r) => r.legislature).filter(Boolean)).size,
    [rows],
  );
  const fullCount = rows.filter((r) => r.completeness === "full").length;
  const partialCount = rows.filter((r) => r.completeness === "partial").length;
  const fullPct = rows.length > 0 ? (fullCount / rows.length) * 100 : 0;
  const partialPct = rows.length > 0 ? (partialCount / rows.length) * 100 : 0;
  // R-04: derived by the backend from raw counts; null at a zero denominator.
  const overallPct: number | null = summary.data?.percentages?.dated ?? null;

  const view = resolveViewState({
    isLoading: coverage.isLoading,
    isError: coverage.isError,
    isEmpty: coverage.isSuccess && rows.length === 0,
  });
  if (view !== "ready") {
    return (
      <AsyncState
        view={view}
        pageTitle={t("coverageTitle")}
        onRetry={() => void coverage.refetch()}
        errorLabel={t("coverageLoadError")}
        emptyTitle={t("coverage.empty", "There are no coverage records for this scope.")}
      />
    );
  }

  return (
    <div className="space-y-6">
      <ScopeControls showChamber showLegislature note={t("scope.note.coverage")} />
      {/* Section 1: Hero — fills the first screen alone */}
      <section className="hero-section" data-enter>
        <div>
          <div className="flex flex-col md:flex-row md:items-center gap-8">
            <div className="flex-1 space-y-4">
              <h1 className="page-title">{t("coverageTitle")}</h1>
              <p className="text-sm text-slate-400">{t("coverageDesc")}</p>

              {/* InfoStat cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
                <InfoStat
                  label={t("coverageStatChambers", "Chambers")}
                  value={chamberCount}
                  accent="sky"
                />
                <InfoStat
                  label={t("coverageStatLegislatures", "Legislatures")}
                  value={legislatureCount}
                  accent="emerald"
                />
                <InfoStat
                  label={t("coverageStatFullCoverage", "Full coverage")}
                  value={fullPct}
                  max={100}
                  accent="emerald"
                />
                <InfoStat
                  label={t("coverageStatPartialCoverage", "Partial coverage")}
                  value={partialPct}
                  max={100}
                  accent="amber"
                />
              </div>

              {/* Progress ring — overall coverage */}
              <div className="mt-6 flex items-center gap-4">
                {overallPct === null ? (
                  <span className="text-2xl font-bold text-slate-400">—</span>
                ) : (
                  <ProgressRing value={overallPct} size={56} />
                )}
                <div>
                  <div className="text-sm font-bold text-slate-100">
                    {fmtPct(overallPct)}
                  </div>
                  <div className="text-xs text-slate-400">
                    {t("coverageOverallLabel", "Overall coverage")}
                  </div>
                </div>
              </div>
              <p role="note" className="mt-2 text-xs text-slate-400">
                {t("coverageRawCounts", "Members with a start date: {{dated}} / {{total}}; switch events with a source: {{sourced}} / {{switches}}.", {
                  dated: totals.datedMemberships ?? "—",
                  total: totals.totalMemberships ?? "—",
                  sourced: totals.sourcedSwitches ?? "—",
                  switches: totals.totalSwitches ?? "—",
                })}
              </p>
            </div>
            <div className="w-full md:w-auto max-w-[260px]">
              <HeroGraphic variant="overview" className="mx-auto" />
            </div>
          </div>

          {/* Dealt moment — total coverage entries */}
          <div className="mt-8 flex items-center gap-4" data-moment>
            <span className="moment-value block">
              {rows.length}
            </span>
            <span className="text-sm text-slate-400">
              {t("coverageStatEntries", "coverage entries")}
            </span>
          </div>
        </div>
      </section>

      {/* Section 2: Coverage table (existing) */}
      <section className="space-y-4">
        <div className="card p-4">
          {/* Per-scope table */}
          <div
            className="overflow-x-auto max-w-full"
            tabIndex={0}
            role="region"
            aria-label={t("coverageTableCaption")}
          >
            <table className="w-full data-table border-collapse">
              <caption className="sr-only">{t("coverageTableCaption")}</caption>
              <thead>
                <tr className="text-left text-slate-500">
                  <th scope="col" className="py-1 pr-3 font-medium">
                    {t("chamber")}
                  </th>
                  <th scope="col" className="py-1 pr-3 font-medium">
                    {t("legislature")}
                  </th>
                  <th scope="col" className="py-1 pr-3 font-medium">
                    {t("period")}
                  </th>
                  <th scope="col" className="py-1 pr-3 font-medium">
                    {t("completeness")}
                  </th>
                  <th scope="col" className="py-1 pr-3 font-medium text-right">
                    {t("persons")}
                  </th>
                  <th scope="col" className="py-1 pr-3 font-medium text-right">
                    {t("datedPct")}
                  </th>
                  <th scope="col" className="py-1 pr-3 font-medium text-right">
                    {t("sourcedPct")}
                  </th>
                  <th scope="col" className="py-1 pr-3 font-medium text-right">
                    {t("sourcedSwitchesPct")}
                  </th>
                  <th scope="col" className="py-1 pr-3 font-medium text-right">
                    {t("lastRefresh")}
                  </th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => {
                  const key = row.completeness;
                  return (
                    <tr
                      key={`${row.chamber}-${row.legislature}`}
                      className="border-t border-slate-700/60 align-top"
                    >
                      <td className="py-1.5 pr-3 text-slate-200">
                        {row.chamber === "deputies" ? t("deputies") : t("senate")}
                      </td>
                      <td className="py-1.5 pr-3 font-mono text-slate-300">
                        {row.legislature ?? "—"}
                      </td>
                      <td className="py-1.5 pr-3 font-mono text-slate-300">
                        {fmtDate(row.period_start)} →{" "}
                        {fmtDate(row.period_end)}
                      </td>
                      <td className="py-1.5">
                        <span
                          className={`rounded px-2 py-0.5 ${completenessClass(key)}`}
                        >
                          {t(key)}
                        </span>
                      </td>
                      <td className="py-1.5 pr-3 font-mono text-slate-300 text-right">
                        {row.persons.toLocaleString()}
                      </td>
                      <td className="py-1.5 pr-3 font-mono text-slate-300 text-right">
                        {fmtPct(row.dated_pct)}
                      </td>
                      <td className="py-1.5 pr-3 font-mono text-slate-300 text-right">
                        {fmtPct(row.sourced_pct)}
                      </td>
                      <td className="py-1.5 pr-3 font-mono text-slate-300 text-right">
                        {fmtPct(row.sourced_switches_pct)}
                      </td>
                      <td className="py-1.5 pr-3 font-mono text-slate-300 text-right">
                        {fmtDate(row.last_refresh)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="mt-3 text-xs text-slate-500">
            {t("coverageNoteText", {
              datedPct: t("datedPctShort"),
              sourcedPct: t("sourcedPctShort"),
              sourcedSwitchesPct: t("sourcedSwitchesPctShort"),
            })}
          </div>
        </div>
      </section>
    </div>
  );
}
