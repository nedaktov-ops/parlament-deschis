import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api } from "../api/client";
import HeroGraphic from "../components/HeroGraphic";
import InfoStat from "../components/InfoStat";

interface CoverageRow {
  chamber: string;
  legislature: string | null;
  period_start: string | null;
  period_end: string | null;
  completeness: string;
  note: string | null;
  persons: number;
  total_memberships: number;
  dated_pct: number | null;
  sourced_pct: number | null;
  total_switches: number;
  sourced_switches_pct: number | null;
  last_refresh: string | null;
}

function completenessBadge(value: string) {
  if (value === "full") return "bg-emerald-900/50 text-emerald-300";
  if (value === "partial") return "bg-amber-900/50 text-amber-300";
  return "bg-slate-800 text-slate-400";
}

function formatDate(value: string | null): string {
  if (!value) return "—";
  return value;
}

export default function SenateHistory() {
  const { t } = useTranslation();

  const coverage = useQuery({
    queryKey: ["coverage-detailed"],
    queryFn: () => api.coverage_detailed(),
  });

  const rows = coverage.data ?? [];

  // Never fall back to all-chamber rows: deputy data must not be presented
  // under a Senate heading. If Senate coverage is empty, the table says so.
  const allRows = rows.filter((r) => r.chamber === "senate");

  return (
    <div className="space-y-6">
      <section className="hero-section" data-enter>
        <div>
          <div className="flex flex-col md:flex-row md:items-center gap-8">
            <div className="flex-1 space-y-4">
              <h1 className="page-title">
                {t("senate.history", "Senate Historical Coverage")}
              </h1>
              <p className="text-sm text-slate-300 mt-2">
                {t("senate.history.intro")}
              </p>
            </div>
            <div className="w-full md:w-auto max-w-[260px]">
              <HeroGraphic variant="people" className="mx-auto" />
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
            <InfoStat
              label={t("senateStatMembers", "Senate Members")}
              value={coverage.data?.reduce((acc, r) => acc + r.persons, 0) ?? "--"}
              accent="sky"
            />
            <InfoStat
              label={t("senateStatChambers", "Chambers")}
              value="1"
              accent="emerald"
            />
            <InfoStat
              label={t("senateStatLegislatures", "Legislatures")}
              value={new Set(rows.map((r) => r.legislature)).size}
              accent="amber"
            />
            <InfoStat
              label={t("senateStatCoverage", "Full Coverage %")}
              value={
                rows.filter((r) => r.completeness === "full").length
              }
              accent="rose"
              showBar={false}
            />
          </div>
          <div className="mt-8 flex items-center gap-4" data-moment>
            <span className="moment-value block">
              {coverage.data?.reduce((acc, r) => acc + r.persons, 0) ?? "--"}
            </span>
            <span className="text-sm text-slate-400">
              {t("senateStatMembersLabel", "senate members in corpus")}
            </span>
          </div>
        </div>
      </section>
        <div className="bg-slate-800/50 rounded p-4 mb-4">
          <h2 className="text-lg font-semibold text-slate-200 mb-2">
            {t("senate.history.gaps", "Known Gaps")}
          </h2>
          <ul className="text-slate-400 list-disc list-inside space-y-1">
            <li>
              {t(
                "senate.history.gap.pre1990",
                "Pre-1990: Different regime; outside project scope"
              )}
            </li>
            <li>
              {t(
                "senate.history.gap.current",
                "Current legislature (2024): Only sitemap data available (134 GUIDs)"
              )}
            </li>
            <li>
              {t(
                "senate.history.gap.methodology",
                "Data collected via two-step POST flow from senat.ro"
              )}
            </li>
          </ul>
      </div>

      <div className="overflow-x-auto max-w-full" tabIndex={0} role="region" aria-label={t("senate.history", "Senate Historical Coverage")}>
        <table className="min-w-full bg-slate-800 rounded-xl overflow-hidden data-table">
          <thead className="bg-slate-700">
            <tr>
              <th scope="col" className="px-4 py-3 text-left text-sm font-medium !text-slate-300">
                {t("senate.history.legislature", "Legislature")}
              </th>
              <th scope="col" className="px-4 py-3 text-left text-sm font-medium !text-slate-300">
                {t("senate.history.period", "Period")}
              </th>
              <th scope="col" className="px-4 py-3 text-left text-sm font-medium !text-slate-300">
                {t("senate.history.completeness", "Completeness")}
              </th>
              <th scope="col" className="px-4 py-3 text-left text-sm font-medium !text-slate-300">
                {t("senate.history.notes", "Notes")}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700">
            {allRows.map((row: CoverageRow) => (
              <tr key={`${row.chamber}-${row.legislature}`} className="hover:bg-slate-700/50">
                <th scope="row" className="px-4 py-3 text-slate-200 font-normal text-left">{row.legislature ?? "—"}</th>
                <td className="px-4 py-3 text-slate-300">
                  {formatDate(row.period_start)} — {formatDate(row.period_end)}
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`px-2 py-1 rounded text-xs font-medium ${completenessBadge(row.completeness)}`}
                  >
                    {row.completeness}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-400 text-sm">{row.note ?? "—"}</td>
              </tr>
            ))}
            {allRows.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-slate-500">
                  {t("senate.history.noData", "No coverage data available")}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="mt-6 bg-slate-800/50 rounded p-4">
        <h2 className="text-lg font-semibold text-slate-200 mb-2">
          {t("senate.history.methodology", "Data Collection Methodology")}
        </h2>
        <p className="text-slate-400 text-sm mb-2">
          {t(
            "senate.history.methodology.desc",
            "Senate data is collected using a two-step POST flow from senat.ro:"
          )}
        </p>
        <ol className="text-slate-400 list-decimal list-inside space-y-1 text-sm">
          <li>
            {t(
              "senate.history.methodology.step1",
              "Discover GUIDs for each legislature via POST requests"
            )}
          </li>
          <li>
            {t(
              "senate.history.methodology.step2",
              "Fetch detailed profile data for each GUID"
            )}
          </li>
          <li>
            {t(
              "senate.history.methodology.step3",
              "HistoricalDiscoveryError guard prevents empty/duplicate data"
            )}
          </li>
        </ol>
        <p className="text-slate-500 text-xs mt-3">
          {t(
            "senate.history.methodology.source",
            "Source: senat.ro public data, CC-BY 4.0"
          )}
        </p>
      </div>
    </div>
  );
}
