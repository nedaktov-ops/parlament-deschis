import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { generationalShift, type GenerationalShiftEntry } from "../api/client";
import { useScope } from "../hooks/useScope";
import ScopeControls from "../components/ScopeControls";
import HeroGraphic from "../components/HeroGraphic";
import InfoStat from "../components/InfoStat";
import { Sparkline, ProgressRing } from "../components/DataViz";
import AsyncState, { resolveViewState } from "../components/ui/AsyncState";

const LEGISLATURES = [
  "1990",
  "1992",
  "1996",
  "2000",
  "2004",
  "2008",
  "2012",
  "2016",
  "2020",
  "2024",
];

export default function Demographics() {
  const { t } = useTranslation();
  const scope = useScope();

  const shift = useQuery({
    queryKey: ["generational-shift", scope.legislature, scope.date, ...scope.scopeKey],
    queryFn: () => generationalShift(scope.legislature, scope.date),
  });

  const rows = shift.data?.data ?? [];
  const asOf = shift.data?.as_of;
  const totals = shift.data?.totals;
  const knownBirthDates = totals?.mps_with_birth_date ?? null;
  const inScope = totals?.mps_in_scope ?? null;

  // Find min/max avg age for a simple visual scale.
  const ages = rows.map((r) => r.avg_age);
  const minAge = ages.length > 0 ? Math.min(...ages) : 0;
  const maxAge = ages.length > 0 ? Math.max(...ages) : 0;
  const span = maxAge - minAge || 1;

  // R-04: population-level figures from the API totals — never a mean of
  // per-party means and never parties-with-data / parties as "coverage".
  const totalMPs = inScope;
  const avgAge = totals?.population_avg_age ?? null;
  const medianAge = totals?.population_median_age ?? null;
  const coveragePct = totals?.coverage_pct ?? null;

  const view = resolveViewState({
    isLoading: shift.isLoading,
    isError: shift.isError,
    isEmpty: shift.isSuccess && rows.length === 0,
  });
  if (view !== "ready") {
    return (
      <AsyncState
        view={view}
        pageTitle={t("demographics.title", "Demographics: Age per Party")}
        onRetry={() => void shift.refetch()}
        errorLabel={t("demographics.error", "Failed to load demographics.")}
        emptyTitle={t("demographics.empty", "No birth-date data available for this scope.")}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Hero section — fills the first screen alone */}
      <section className="hero-section" data-enter>
        <div>
          <div className="flex flex-col md:flex-row md:items-center gap-8">
            <div className="flex-1 space-y-4">
              <h1 className="page-title">
                {t("demographics.title", "Demographics: Age per Party")}
              </h1>
              <p className="text-sm text-slate-400">
                {t(
                  "demographics.intro",
                  "Average and median age of MPs per party, computed from birth dates in the chambers' committee ledgers.",
                )}
                {asOf ? ` (${t("demographics.asOf", "as of")} ${asOf})` : ""}
              </p>
              {/* Dealt moment: headline figure for the page. */}
              <div className="mt-4 flex items-center gap-4" data-moment>
                <span className="moment-value block">
                  {totalMPs === null ? "—" : totalMPs.toLocaleString()}
                </span>
                <span className="text-sm text-slate-400">
                  {t("demographics.moment.totalMPs", "MPs in scope")}
                </span>
              </div>
              {/* InfoStat cards — key metrics at a glance. */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
                <InfoStat
                  label={t("demographics.stat.totalMPs", "MPs in scope")}
                  value={totalMPs === null ? "—" : totalMPs}
                  accent="sky"
                />
                <InfoStat
                  label={t("demographics.stat.avgAge", "Average age")}
                  value={avgAge === null ? "—" : avgAge}
                  accent="emerald"
                />
                <InfoStat
                  label={t("demographics.stat.medianAge", "Median age")}
                  value={medianAge === null ? "—" : medianAge}
                  accent="amber"
                />
                <InfoStat
                  label={t("demographics.stat.legislatures", "Legislatures covered")}
                  value={LEGISLATURES.length}
                  accent="rose"
                />
              </div>
              {/* Age distribution sparkline (when data is available). */}
              {rows.length > 0 && (
                <div className="mt-6 flex flex-col gap-1">
                  <span className="text-xs font-medium text-slate-400 uppercase tracking-wide">
                    {t("demographics.sparkline.label", "Age distribution by party")}
                  </span>
                  <Sparkline data={ages} height={40} color="stroke-sky-400" />
                </div>
              )}
            </div>
            <div className="w-full md:w-auto max-w-[260px] flex flex-col items-center gap-4">
              <HeroGraphic variant="people" className="mx-auto" />
              {coveragePct !== null ? (
                <ProgressRing value={coveragePct} size={56} color="stroke-emerald-400" />
              ) : (
                <span className="text-2xl font-bold text-slate-400">—</span>
              )}
            </div>
          </div>
        </div>
      </section>

      <div className="mb-6">
        <ScopeControls showDate showLegislature note={t("scope.note.chamber")} />
      </div>

      {rows.length > 0 && (
        <div className="overflow-x-auto max-w-full" tabIndex={0} role="region" aria-label={t("demographics.title", "Demographics: Age per Party")}>
          <table className="min-w-full bg-slate-800 rounded-xl overflow-hidden data-table">
            <thead className="bg-slate-700">
              <tr>
                <th scope="col" className="px-4 py-3 text-left text-sm font-medium !text-slate-300">
                  {t("demographics.col.party", "Party")}
                </th>
                <th scope="col" className="px-4 py-3 text-right text-sm font-medium !text-slate-300">
                  {t("demographics.col.mps", "MPs with birth date")}
                </th>
                <th scope="col" className="px-4 py-3 text-right text-sm font-medium !text-slate-300">
                  {t("demographics.col.avg", "Average age")}
                </th>
                <th scope="col" className="px-4 py-3 text-right text-sm font-medium !text-slate-300">
                  {t("demographics.col.median", "Median age")}
                </th>
                <th scope="col" className="px-4 py-3 text-left text-sm font-medium !text-slate-300">
                  {t("demographics.col.dist", "Distribution")}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700">
              {rows.map((row: GenerationalShiftEntry) => {
                const width = ((row.avg_age - minAge) / span) * 100;
                return (
                  <tr key={row.party} className="hover:bg-slate-700/50">
                    <th scope="row" className="px-4 py-3 text-slate-200 font-medium text-left">
                      {row.party}
                    </th>
                    <td className="px-4 py-3 text-right text-slate-300">
                      {row.mps_with_birth_dates}
                    </td>
                    <td className="px-4 py-3 text-right text-slate-200 font-semibold">
                      {row.avg_age}
                    </td>
                    <td className="px-4 py-3 text-right text-slate-300">
                      {row.median_age}
                    </td>
                    <td className="px-4 py-3">
                      <div className="bg-slate-700 rounded-full h-2 w-full min-w-[120px]">
                        <div
                          className="bg-sky-500 rounded-full h-2"
                          style={{ width: `${Math.max(width, 4)}%` }}
                        />
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <div className="mt-6 bg-slate-800/50 rounded p-4 text-sm text-slate-400">
        <h2 className="text-slate-200 font-semibold mb-1">
          {t("demographics.coverage", "Data coverage")}
        </h2>
        <p>
          {t(
            "demographics.coverage.desc",
            "Birth date known: {{known}} / {{total}} ({{pct}}%).",
            {
              known: knownBirthDates ?? "—",
              total: inScope ?? "—",
              pct: coveragePct === null ? "—" : `${coveragePct}%`,
            },
          )}
        </p>
      </div>
    </div>
  );
}
