import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { generationalShift, type GenerationalShiftEntry } from "../api/client";
import HeroGraphic from "../components/HeroGraphic";
import InfoStat from "../components/InfoStat";
import { Sparkline, ProgressRing } from "../components/DataViz";

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
  const [legislature, setLegislature] = useState<string>("");

  const shift = useQuery({
    queryKey: ["generational-shift", legislature],
    queryFn: () => generationalShift(legislature || undefined),
  });

  const rows = shift.data?.data ?? [];
  const asOf = shift.data?.as_of;
  // Derive the in-scope coverage figure from what this page already fetches.
  const birthDated = rows.reduce((sum, r) => sum + r.mps_with_birth_dates, 0);

  // Find min/max avg age for a simple visual scale.
  const ages = rows.map((r) => r.avg_age);
  const minAge = ages.length > 0 ? Math.min(...ages) : 0;
  const maxAge = ages.length > 0 ? Math.max(...ages) : 0;
  const span = maxAge - minAge || 1;

  // Headline stats for the hero info-graphic cards.
  const totalMPs = birthDated;
  const avgAge =
    rows.length > 0
      ? Math.round((rows.reduce((s, r) => s + r.avg_age, 0) / rows.length) * 10) /
        10
      : 0;
  const medianAges = rows.map((r) => r.median_age).sort((a, b) => a - b);
  const medianAge =
    medianAges.length > 0
      ? medianAges.length % 2 === 1
        ? medianAges[Math.floor(medianAges.length / 2)]
        : (medianAges[medianAges.length / 2 - 1] +
            medianAges[medianAges.length / 2]) /
          2
      : 0;
  const partiesWithData = rows.filter((r) => r.mps_with_birth_dates > 0).length;
  const coveragePct =
    rows.length > 0 ? Math.round((partiesWithData / rows.length) * 100) : 0;

  return (
    <div className="wrap space-y-6">
      {/* Hero section — fills the first screen alone */}
      <section className="hero-section" data-enter>
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row md:items-center gap-8">
            <div className="flex-1 space-y-4">
              <h1 className="text-3xl font-bold tracking-tight text-slate-100">
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
                <span className="text-5xl font-black block tracking-tight text-slate-200">
                  {totalMPs.toLocaleString()}
                </span>
                <span className="text-sm text-slate-400">
                  {t("demographics.moment.totalMPs", "members with birth dates")}
                </span>
              </div>
              {/* InfoStat cards — key metrics at a glance. */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
                <InfoStat
                  label={t("demographics.stat.totalMPs", "Total MPs")}
                  value={totalMPs}
                  accent="sky"
                />
                <InfoStat
                  label={t("demographics.stat.avgAge", "Average age")}
                  value={avgAge}
                  accent="emerald"
                />
                <InfoStat
                  label={t("demographics.stat.medianAge", "Median age")}
                  value={medianAge}
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
              {rows.length > 0 && (
                <ProgressRing value={coveragePct} size={56} color="stroke-emerald-400" />
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Legislature selector (unchanged). */}
      <div className="mb-6">
        <label className="flex flex-col gap-1 text-sm text-slate-400 max-w-xs">
          {t("demographics.filter.legislature", "Legislature")}
          <select
            value={legislature}
            onChange={(e) => setLegislature(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded px-3 py-2 text-slate-200"
          >
            <option value="">{t("demographics.filter.all", "Current / all")}</option>
            {LEGISLATURES.map((leg) => (
              <option key={leg} value={leg}>
                {leg}
              </option>
            ))}
          </select>
        </label>
      </div>

      {shift.isLoading && (
        <div className="text-slate-500">{t("loading", "Loading…")}</div>
      )}
      {shift.isError && (
        <div className="text-red-400">
          {t("demographics.error", "Failed to load demographics.")}
        </div>
      )}

      {rows.length > 0 && (
        <div className="overflow-x-auto" tabIndex={0} role="region" aria-label={t("demographics.title", "Demographics: Age per Party")}>
          <table className="min-w-full bg-slate-800 rounded-lg overflow-hidden">
            <thead className="bg-slate-700">
              <tr>
                <th scope="col" className="px-4 py-3 text-left text-sm font-medium text-slate-300">
                  {t("demographics.col.party", "Party")}
                </th>
                <th scope="col" className="px-4 py-3 text-right text-sm font-medium text-slate-300">
                  {t("demographics.col.mps", "MPs with birth date")}
                </th>
                <th scope="col" className="px-4 py-3 text-right text-sm font-medium text-slate-300">
                  {t("demographics.col.avg", "Average age")}
                </th>
                <th scope="col" className="px-4 py-3 text-right text-sm font-medium text-slate-300">
                  {t("demographics.col.median", "Median age")}
                </th>
                <th scope="col" className="px-4 py-3 text-left text-sm font-medium text-slate-300">
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

      {rows.length === 0 && !shift.isLoading && !shift.isError && (
        <div className="text-slate-500">
          {t(
            "demographics.empty",
            "No birth-date data available for this scope.",
          )}
        </div>
      )}

      <div className="mt-6 bg-slate-800/50 rounded p-4 text-sm text-slate-400">
        <h2 className="text-slate-200 font-semibold mb-1">
          {t("demographics.coverage", "Data coverage")}
        </h2>
        <p>
          {t("demographics.coverage.desc", { birthDated })}
        </p>
      </div>
    </div>
  );
}
