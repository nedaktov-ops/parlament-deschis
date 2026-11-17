import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api } from "../api/client";

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

  const coverage = useQuery({
    queryKey: ["coverage-detailed"],
    queryFn: () => api.coverage_detailed(),
  });

  const rows = coverage.data ?? [];
  const totals = useMemo(() => {
    const totalMemberships = rows.reduce((sum, r) => sum + r.total_memberships, 0);
    const datedMemberships = rows.reduce(
      (sum, r) => sum + Math.round(((r.dated_pct ?? 0) / 100) * r.total_memberships),
      0,
    );
    const totalSwitches = rows.reduce((sum, r) => sum + r.total_switches, 0);
    const sourcedSwitches = rows.reduce(
      (sum, r) =>
        sum + Math.round(((r.sourced_switches_pct ?? 0) / 100) * r.total_switches),
      0,
    );
    return {
      totalMemberships,
      datedMemberships,
      totalSwitches,
      sourcedSwitches,
    };
  }, [rows]);

  if (coverage.isLoading) {
    return (
      <div className="card p-4">
        <div className="text-slate-500 text-sm py-8">{t("loading")}</div>
      </div>
    );
  }

  if (coverage.isError) {
    return (
      <div className="card p-4">
        <div role="alert" className="text-rose-200 text-sm py-8">
          {t("coverageLoadError")}
          <button type="button"className="ml-3 underline" onClick={() => coverage.refetch()}>
            {t("traseismRetry")}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="card p-4">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-bold">{t("coverageTitle")}</h1>
        </div>
        <p className="text-sm text-slate-400 mb-4">
          {t("coverageDesc")}
        </p>

        {/* Summary cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
          <div className="bg-slate-800/50 rounded p-3">
            <div className="text-slate-500 text-xs">{t("totalMemberships")}</div>
            <div className="text-2xl font-bold text-slate-100">
              {totals.totalMemberships.toLocaleString()}
            </div>
          </div>
          <div className="bg-slate-800/50 rounded p-3">
            <div className="text-slate-500 text-xs">{t("datedMemberships")}</div>
            <div className="text-2xl font-bold text-emerald-300">
              {fmtPct(
                totals.totalMemberships > 0
                  ? (totals.datedMemberships / totals.totalMemberships) * 100
                  : null,
              )}
            </div>
          </div>
          <div className="bg-slate-800/50 rounded p-3">
            <div className="text-slate-500 text-xs">{t("totalSwitchesLabel")}</div>
            <div className="text-2xl font-bold text-slate-100">
              {totals.totalSwitches.toLocaleString()}
            </div>
          </div>
          <div className="bg-slate-800/50 rounded p-3">
            <div className="text-slate-500 text-xs">{t("sourcedSwitches")}</div>
            <div className="text-2xl font-bold text-emerald-300">
              {fmtPct(
                totals.totalSwitches > 0
                  ? (totals.sourcedSwitches / totals.totalSwitches) * 100
                  : null,
              )}
            </div>
          </div>
        </div>

        {/* Per-scope table */}
        <div className="overflow-x-auto">
          <table className="w-full text-xs border-collapse">
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
    </div>
  );
}
