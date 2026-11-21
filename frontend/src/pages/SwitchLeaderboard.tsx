import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useSearch } from "@tanstack/react-router";
import { switchLeaderboard, type SwitchLeaderboardEntry } from "../api/client";
import { useScope } from "../hooks/useScope";
import ScopeControls from "../components/ScopeControls";
import HeroGraphic from "../components/HeroGraphic";
import InfoStat from "../components/InfoStat";
import AsyncState, { resolveViewState } from "../components/ui/AsyncState";

function fmtDate(value: string | null): string {
  if (!value) return "—";
  return value;
}

export default function SwitchLeaderboard() {
  const { t } = useTranslation();
  const scope = useScope();
  const navigate = useNavigate({ from: "/leaderboard" });
  // Page-local filter lives in the URL too (FN-7); scope reads stay in useScope.
  const rawLimit = useSearch({
    from: "/leaderboard",
    select: (s) => Number((s as Record<string, unknown>).limit ?? 20),
  });
  const limit = [10, 20, 50, 100].includes(rawLimit) ? rawLimit : 20;
  const setLimit = (value: number) => navigate({ search: scope.searchFor({ limit: value }) });

  const leaderboard = useQuery({
    queryKey: ["switch-leaderboard", scope.legislature, scope.chamber, limit, ...scope.scopeKey],
    queryFn: () => switchLeaderboard(limit, scope.legislature, scope.chamber),
  });

  const rows = leaderboard.data?.data ?? [];

  // R-04: top-N sum of the displayed rows, NOT a corpus total.
  const totalSwitches = rows.reduce((sum, row) => sum + row.switch_count, 0);
  const uniqueSwitchers = rows.length;
  const topSwitcherCount = rows.length > 0 ? rows[0].switch_count : 0;

  const view = resolveViewState({
    isLoading: leaderboard.isLoading,
    isError: leaderboard.isError,
    isEmpty: leaderboard.isSuccess && rows.length === 0,
  });
  if (view !== "ready") {
    return (
      <AsyncState
        view={view}
        pageTitle={t("leaderboard.title", "Party Switching Leaderboard")}
        onRetry={() => void leaderboard.refetch()}
        errorLabel={t("leaderboard.error", "Failed to load leaderboard.")}
        emptyTitle={t("leaderboard.empty", "No switch data available for this scope.")}
      />
    );
  }

  return (
    <div className="py-6">
      {/* Hero section — H2-D: min-h-screen, data-enter, HeroGraphic, dealt moment */}
      <section className="hero-section" data-enter>
        <div>
          <div className="flex flex-col lg:flex-row lg:items-start gap-8">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-4">
                <HeroGraphic variant="switches" className="w-10 h-10" />
                <h1 className="page-title">
                  {t("leaderboard.title", "Party Switching Leaderboard")}
                </h1>
              </div>
              <p className="text-slate-400 text-lg mb-6">
                {t(
                  "leaderboard.intro",
                  "MPs ranked by observed group switch count (switch_group) within the reported scope.",
                )}
              </p>
              {/* Dealt moment: InfoStat cards */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
                <InfoStat
                  label={t("leaderboard.stat.total_switches", "Group switches in top N")}
                  value={totalSwitches}
                  accent="amber"
                />
                <InfoStat
                  label={t("leaderboard.stat.unique_switchers", "Unique switchers")}
                  value={uniqueSwitchers}
                  accent="sky"
                />
                <InfoStat
                  label={t("leaderboard.stat.top_switcher", "Top switcher")}
                  value={topSwitcherCount}
                  accent="sky"
                />
              </div>
            </div>
            <div className="w-full lg:w-72 shrink-0">
              <div className="flex flex-col gap-4">
                <ScopeControls showChamber showLegislature />
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
            </div>
          </div>
        </div>
      </section>

      {scope.legislature && (
        <p role="note" className="mb-4 text-amber-300 text-sm">
          {t("leaderboard.scope.note")}
        </p>
      )}

      {rows.length > 0 && (
        <div className="overflow-x-auto max-w-full" tabIndex={0} role="region" aria-label={t("leaderboard.title", "Party Switching Leaderboard")}>
          <table className="min-w-full bg-slate-800 rounded-xl overflow-hidden data-table">
            <thead className="bg-slate-700">
              <tr>
                <th scope="col" className="px-4 py-3 text-left text-sm font-medium !text-slate-300">
                  #
                </th>
                <th scope="col" className="px-4 py-3 text-left text-sm font-medium !text-slate-300">
                  {t("leaderboard.col.name", "MP")}
                </th>
                <th scope="col" className="px-4 py-3 text-right text-sm font-medium !text-slate-300">
                  {t("leaderboard.col.switches", "Switches")}
                </th>
                <th scope="col" className="px-4 py-3 text-right text-sm font-medium !text-slate-300">
                  {t("leaderboard.col.loyalty", "Loyalty")}
                </th>
                <th scope="col" className="px-4 py-3 text-left text-sm font-medium !text-slate-300">
                  {t("leaderboard.col.parties", "Parties joined")}
                </th>
                <th scope="col" className="px-4 py-3 text-left text-sm font-medium !text-slate-300">
                  {t("leaderboard.col.first", "First")}
                </th>
                <th scope="col" className="px-4 py-3 text-left text-sm font-medium !text-slate-300">
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
                      search={scope.searchFor()}
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
                        row.loyalty_score === null
                          ? "bg-slate-700/40 text-slate-400"
                          : row.loyalty_score >= 70
                            ? "bg-emerald-900/40 text-emerald-300"
                            : row.loyalty_score >= 40
                              ? "bg-amber-900/40 text-amber-300"
                              : "bg-red-900/40 text-red-300"
                      }`}
                      title={t("leaderboard.loyalty.denominators", {
                        switches: row.loyalty_inputs.switch_count,
                        events: row.loyalty_inputs.total_events_in_scope,
                        years: row.loyalty_inputs.tenure_years,
                        weight: row.loyalty_inputs.tenure_weight ?? "—",
                        status: row.loyalty_status,
                      })}
                    >
                      {row.loyalty_score === null ? "—" : row.loyalty_score}
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
            "Loyalty = 100 × (1 − (switches ÷ total events in scope) × min(1, tenure years ÷ 4)). 100 is the maximum proxy value; any MP with an observed group switch is capped below 100; — means no observed event span in scope.",
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
