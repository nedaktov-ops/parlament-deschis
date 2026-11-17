import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { Link } from "@tanstack/react-router";
import { switchLeaderboard, type SwitchLeaderboardEntry } from "../api/client";
import { localISODate } from "../utils/date";

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

function fmtDate(value: string | null): string {
  if (!value) return "—";
  return value;
}

export default function SwitchLeaderboard() {
  const { t } = useTranslation();
  const [legislature, setLegislature] = useState<string>("");
  const [limit, setLimit] = useState<number>(20);

  const leaderboard = useQuery({
    queryKey: ["switch-leaderboard", legislature, limit],
    queryFn: () => switchLeaderboard(limit, legislature || undefined),
  });

  const rows = leaderboard.data?.data ?? [];

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-slate-100 mb-2">
        {t("leaderboard.title", "Party Switching Leaderboard")}
      </h1>
      <p className="text-slate-400 mb-6">
        {t(
          "leaderboard.intro",
          "MPs ranked by the number of observed party/group switches. Every count comes from the chambers' own dated group ledgers.",
        )}
      </p>

      <div className="flex gap-4 mb-6 flex-wrap">
        <label className="flex flex-col gap-1 text-sm text-slate-400">
          {t("leaderboard.filter.legislature", "Legislature")}
          <select
            value={legislature}
            onChange={(e) => setLegislature(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded px-3 py-2 text-slate-200"
          >
            <option value="">{t("leaderboard.filter.all", "All")}</option>
            {LEGISLATURES.map((leg) => (
              <option key={leg} value={leg}>
                {leg}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm text-slate-400">
          {t("leaderboard.filter.limit", "Show top")}
          <select
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
            className="bg-slate-800 border border-slate-700 rounded px-3 py-2 text-slate-200"
          >
            {[10, 20, 50, 100].map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </label>
      </div>

      {legislature && (
        <p role="note" className="mb-4 text-amber-300 text-sm">
          {t("leaderboard.scope.note")}
        </p>
      )}

      {leaderboard.isLoading && (
        <div className="text-slate-500">{t("loading", "Loading…")}</div>
      )}
      {leaderboard.isError && (
        <div className="text-red-400">
          {t("leaderboard.error", "Failed to load leaderboard.")}
        </div>
      )}

      {rows.length > 0 && (
        <div className="overflow-x-auto" tabIndex={0} role="region" aria-label={t("leaderboard.title", "Party Switching Leaderboard")}>
          <table className="min-w-full bg-slate-800 rounded-lg overflow-hidden">
            <thead className="bg-slate-700">
              <tr>
                <th scope="col" className="px-4 py-3 text-left text-sm font-medium text-slate-300">
                  #
                </th>
                <th scope="col" className="px-4 py-3 text-left text-sm font-medium text-slate-300">
                  {t("leaderboard.col.name", "MP")}
                </th>
                <th scope="col" className="px-4 py-3 text-right text-sm font-medium text-slate-300">
                  {t("leaderboard.col.switches", "Switches")}
                </th>
                <th scope="col" className="px-4 py-3 text-right text-sm font-medium text-slate-300">
                  {t("leaderboard.col.loyalty", "Loyalty")}
                </th>
                <th scope="col" className="px-4 py-3 text-left text-sm font-medium text-slate-300">
                  {t("leaderboard.col.parties", "Parties joined")}
                </th>
                <th scope="col" className="px-4 py-3 text-left text-sm font-medium text-slate-300">
                  {t("leaderboard.col.first", "First")}
                </th>
                <th scope="col" className="px-4 py-3 text-left text-sm font-medium text-slate-300">
                  {t("leaderboard.col.last", "Last")}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700">
              {rows.map((row: SwitchLeaderboardEntry, index: number) => (
                <tr key={row.person_id} className="hover:bg-slate-700/50">
                  <th scope="row" className="px-4 py-3 text-slate-500 font-normal text-left">{index + 1}</th>
                  <td className="px-4 py-3">
                    <Link
                      to="/person/$id"
                      params={{ id: row.person_id }}
                      search={{ date: localISODate() }}
                      className="text-sky-400 hover:text-sky-300 hover:underline"
                    >
                      {row.name}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="inline-block bg-amber-900/40 text-amber-300 px-2 py-1 rounded text-sm font-semibold">
                      {row.switch_count}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span
                      className={`inline-block px-2 py-1 rounded text-sm font-semibold ${
                        row.loyalty_score >= 70
                          ? "bg-emerald-900/40 text-emerald-300"
                          : row.loyalty_score >= 40
                            ? "bg-amber-900/40 text-amber-300"
                            : "bg-red-900/40 text-red-300"
                      }`}
                      title={t("leaderboard.loyalty.hint", {
                        switches: row.switch_count,
                        events: row.total_events,
                        years: row.tenure_years,
                      })}
                    >
                      {row.loyalty_score}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-400 text-sm">
                    {row.parties.join(" → ")}
                  </td>
                  <td className="px-4 py-3 text-slate-400 text-sm">
                    {fmtDate(row.first_switch)}
                  </td>
                  <td className="px-4 py-3 text-slate-400 text-sm">
                    {fmtDate(row.last_switch)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {rows.length === 0 && !leaderboard.isLoading && !leaderboard.isError && (
        <div className="text-slate-500">
          {t("leaderboard.empty", "No switch data available for this scope.")}
        </div>
      )}

      <div className="mt-6 bg-slate-800/50 rounded p-4 text-sm text-slate-400">
        <h2 className="text-slate-200 font-semibold mb-1">
          {t("leaderboard.methodology", "Methodology")}
        </h2>
        <p>
          {t(
            "leaderboard.methodology.desc",
            "A switch is one observed switch_group event between two parliamentary groups. Counts come from cdep.ro and senat.ro dated group ledgers. Unaffiliated periods (NEAFILIATI) are counted as a destination group.",
          )}
        </p>
        <p className="mt-2">
          {t(
            "leaderboard.methodology.loyalty",
            "Loyalty = 100 × (1 − (switches ÷ total events) × tenure weight), where tenure weight = min(1, career years ÷ 4). 100 means no observed switch in the record.",
          )}
        </p>
        <p className="mt-2">
          {t("leaderboard.scope.career")}
        </p>
        <p className="mt-2">
          <a
            href="https://github.com/nedaktov-ops/parlament-deschis/blob/main/docs/METHODOLOGY.md"
            target="_blank"
            rel="noreferrer"
            className="text-sky-400 hover:underline"
          >
            {t("leaderboard.methodology.link", "Full methodology →")}
          </a>
        </p>
      </div>
    </div>
  );
}
