import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { generationalShift, type GenerationalShiftEntry } from "../api/client";

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

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-slate-100 mb-2">
        {t("demographics.title", "Demographics: Age per Party")}
      </h1>
      <p className="text-slate-400 mb-6">
        {t(
          "demographics.intro",
          "Average and median age of MPs per party, computed from birth dates in the chambers' committee ledgers.",
        )}
        {asOf ? ` (${t("demographics.asOf", "as of")} ${asOf})` : ""}
      </p>

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
