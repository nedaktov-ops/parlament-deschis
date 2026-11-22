import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api, type CoverageDimension } from "../api/client";
import { useScope } from "../hooks/useScope";
import ScopeControls from "../components/ScopeControls";
import HeroGraphic from "../components/HeroGraphic";
import InfoStat from "../components/InfoStat";
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

function DimensionCell({
  d,
  labelT,
}: {
  d: CoverageDimension;
  labelT: (key: string) => string;
}) {
  return (
    <td className="py-1.5 pr-3 align-top">
      <span className={`rounded px-2 py-0.5 ${completenessClass(d.status)}`}>{labelT(d.status)}</span>
      <span className="ml-2 tabular-nums">
        {d.count}{d.total != null ? ` / ${d.total}` : ""}
      </span>
      <div className="text-slate-500 text-xs">{d.note ?? "—"}</div>
    </td>
  );
}

export default function CoverageView() {
  const { t } = useTranslation();
  const scope = useScope();

  const coverage = useQuery({
    queryKey: ["coverage-detailed", ...scope.scopeKey],
    queryFn: () => api.coverage_detailed(),
  });

  // R-08: the dimensions endpoint is the primary view. Mandates, votes and
  // biographies are independent; no overall percentage is averaged or inferred.
  const dimensions = useQuery({
    queryKey: ["coverage-dimensions", ...scope.scopeKey],
    queryFn: api.coverageDimensions,
  });

  // Chamber/legislature are client-side row filters on the data-availability
  // matrix; the endpoint itself takes no scope params.
  const rows = useMemo(
    () => (coverage.data ?? []).filter(
      (r) =>
        (!scope.chamber || r.chamber === scope.chamber) &&
        (!scope.legislature || r.legislature === scope.legislature),
    ),
    [coverage.data, scope.chamber, scope.legislature],
  );
  const dimRows = useMemo(
    () => (dimensions.data ?? []).filter(
      (r) =>
        (!scope.chamber || r.chamber === scope.chamber) &&
        (!scope.legislature || r.legislature === scope.legislature),
    ),
    [dimensions.data, scope.chamber, scope.legislature],
  );

  // R-04: corpus-wide aggregates stay backed by the API's raw integer counts,
  // never by back-computing rows from rounded percentages.
  const summary = useQuery({
    queryKey: ["coverage-summary"],
    queryFn: () => api.coverageSummary(),
  });
  const totals = useMemo(
    () => ({
      totalCount: summary.data?.totals?.memberships ?? null,
      datedCount: summary.data?.totals?.memberships_dated ?? null,
      switchesCount: summary.data?.totals?.switches_all ?? null,
      sourcedCount: summary.data?.totals?.switches_sourced ?? null,
    }),
    [summary.data],
  );

  const chamberCount = useMemo(() => new Set(dimRows.map((r) => r.chamber)).size, [dimRows]);
  const legislatureCount = useMemo(
    () => new Set(dimRows.map((r) => r.legislature).filter(Boolean)).size,
    [dimRows],
  );
  const fullMandateCount = dimRows.filter((r) => r.mandates.status === "full").length;
  const partialMandateCount = dimRows.filter((r) => r.mandates.status === "partial").length;
  const voteScopeCount = dimRows.filter((r) => r.votes.status !== "none").length;
  const entryCount = dimRows.length;

  const view = resolveViewState({
    isLoading: coverage.isLoading || dimensions.isLoading,
    isError: coverage.isError || dimensions.isError,
    isEmpty: coverage.isSuccess && dimensions.isSuccess && dimRows.length === 0,
  });
  if (view !== "ready") {
    return (
      <AsyncState
        view={view}
        pageTitle={t("coverageTitle")}
        onRetry={() => {
          void coverage.refetch();
          void dimensions.refetch();
        }}
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

              {/* Count-only headline cards: no derived percentage is shown. */}
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
                  label={t("coverageStatFullCoverage", "Scopes with full mandates")}
                  value={fullMandateCount}
                  accent="emerald"
                />
                <InfoStat
                  label={t("coverageStatPartialCoverage", "Scopes with votes recorded")}
                  value={voteScopeCount}
                  accent="amber"
                />
              </div>

              <p role="note" className="mt-6 text-xs text-slate-400 max-w-3xl">
                {t(
                  "coverageDimensionsNote",
                  "Dimensions are reported separately. A scope with full mandates is not claimed to have full votes or biographies. Counts and notes come from /api/coverage/dimensions; no overall percentage is averaged or inferred.",
                )}
              </p>
              <p role="note" className="mt-2 text-xs text-slate-400">
                {t("coverageRawCounts", "Members with a start date: {{dated}} / {{total}}; switch events with a source: {{sourced}} / {{switches}}.", {
                  dated: totals.datedCount ?? "—",
                  total: totals.totalCount ?? "—",
                  sourced: totals.sourcedCount ?? "—",
                  switches: totals.switchesCount ?? "—",
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
              {entryCount}
            </span>
            <span className="text-sm text-slate-400">
              {t("coverageStatEntries", "coverage entries")}
            </span>
          </div>
        </div>
      </section>

      {/* Section 2: per-dimension table (primary view) */}
      <section className="space-y-4">
        <div className="card p-4">
          <h2 className="text-lg font-semibold text-slate-100 mb-3">
            {t("coverageDimensionsTitle", "Coverage by dimension")}
          </h2>
          <div
            className="overflow-x-auto max-w-full"
            tabIndex={0}
            role="region"
            aria-label={t("coverageDimensionsTitle", "Coverage by dimension")}
          >
            <table className="w-full data-table border-collapse">
              <caption className="sr-only">{t("coverageDimensionsTitle", "Coverage by dimension")}</caption>
              <thead>
                <tr className="text-left text-slate-500">
                  <th scope="col" className="py-1 pr-3 font-medium">{t("chamber")}</th>
                  <th scope="col" className="py-1 pr-3 font-medium">{t("legislature")}</th>
                  <th scope="col" className="py-1 pr-3 font-medium">{t("period")}</th>
                  <th scope="col" className="py-1 pr-3 font-medium">{t("coverageDimMandates", "Mandates")}</th>
                  <th scope="col" className="py-1 pr-3 font-medium">{t("coverageDimVotes", "Votes")}</th>
                  <th scope="col" className="py-1 pr-3 font-medium">{t("coverageDimBiographies", "Biographies")}</th>
                </tr>
              </thead>
              <tbody>
                {dimRows.map((row) => (
                  <tr
                    key={`dim-${row.chamber}-${row.legislature}`}
                    className="border-t border-slate-700/60 align-top"
                  >
                    <td className="py-1.5 pr-3 text-slate-200">
                      {row.chamber === "deputies" ? t("deputies") : t("senate")}
                    </td>
                    <td className="py-1.5 pr-3 font-mono text-slate-300">{row.legislature ?? "—"}</td>
                    <td className="py-1.5 pr-3 font-mono text-slate-300">
                      {fmtDate(row.period_start)} → {fmtDate(row.period_end)}
                    </td>
                    <DimensionCell d={row.mandates} labelT={t} />
                    <DimensionCell d={row.votes} labelT={t} />
                    <DimensionCell d={row.biographies} labelT={t} />
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-xs text-slate-500">
            {t("coverageDimensionsNote", "Dimensions are reported separately. A scope with full mandates is not claimed to have full votes or biographies. Counts and notes come from /api/coverage/dimensions; no overall percentage is averaged or inferred.")}
          </p>
          <p className="mt-1 text-xs text-slate-500">
            {t("coveragePartialMandateCount", "Scopes with partial mandates: {{n}}.", { n: partialMandateCount })}
          </p>
        </div>
      </section>

      {/* Section 3: existing mandate detail table */}
      <section className="space-y-4">
        <div className="card p-4">
          <h2 className="text-lg font-semibold text-slate-100 mb-3">
            {t("coverageMandateDetail", "Mandate detail")}
          </h2>
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
                  <th scope="col" className="py-1 pr-3 font-medium text-right">
                    {t("prov.note")}
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
                      <td className="py-1.5 pr-3 text-xs text-slate-400 text-right">
                        {row.note ?? "—"}
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
