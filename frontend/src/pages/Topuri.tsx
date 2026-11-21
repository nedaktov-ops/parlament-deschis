import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { useNavigate, useSearch } from "@tanstack/react-router";
import { api, type ScorecardEntry } from "../api/client";
import { useScope } from "../hooks/useScope";
import ScopeControls from "../components/ScopeControls";
import { DataBar, type DataBarTone } from "../components/DataViz";
import AsyncState, { resolveViewState } from "../components/ui/AsyncState";

// Thresholds preserved from the previous loyalty-colour helper; intermediate
// green/yellow steps collapse into the two on-palette semantic tones (success / warning).
const LOYALTY_TONE = (pct: number): DataBarTone => {
  if (pct >= 50) return "success";
  if (pct >= 30) return "warning";
  return "danger";
};

export default function Topuri() {
  const { t } = useTranslation();
  const scope = useScope();
  const navigate = useNavigate({ from: "/topuri" });
  const minVotesRaw = useSearch({
    from: "/topuri",
    select: (s) => Number((s as Record<string, unknown>).minVotes ?? 1),
  });
  const minVotes = Number.isFinite(minVotesRaw) ? Math.max(0, minVotesRaw) : 1;
  const setMinVotes = (value: number) =>
    navigate({ search: scope.searchFor({ minVotes: value }) });

  const scorecardQuery = useQuery({
    queryKey: ["topuri-scorecard", minVotes, ...scope.scopeKey],
    queryFn: () =>
      api.scorecard(scope.legislature, scope.chamber, 100, 0, minVotes),
  });

  const entries = useMemo(() => scorecardQuery.data?.data ?? [], [
    scorecardQuery.data,
  ]);
  const dataExists = scorecardQuery.data?.data_exists ?? false;

  const view = resolveViewState({
    isLoading: scorecardQuery.isLoading,
    isError: scorecardQuery.isError,
    isEmpty: scorecardQuery.isSuccess && (!dataExists || entries.length === 0),
  });
  if (view !== "ready") {
    return (
      <AsyncState
        view={view}
        pageTitle={t("view.topuri.title", "MP behavioural scorecard")}
        onRetry={() => void scorecardQuery.refetch()}
        errorLabel={t("view.topuri.loadError", "The behavioural scorecard could not be loaded.")}
        emptyTitle={dataExists
          ? t("topuri.empty", "No behavioural data available yet for the selected scope.")
          : t("empty.rollcall", "Roll-call vote data is not yet available for this legislature.")}
      />
    );
  }

  return (
    <div className="space-y-6">
      <ScopeControls showChamber showLegislature note={t("scope.note.scorecard")} />
      <section className="py-2" data-enter>
        <h1 className="page-title">
          {t("view.topuri.title", "MP behavioural scorecard")}
        </h1>
        <p className="mt-2 text-sm sm:text-base text-slate-400 max-w-3xl">
          {t(
            "view.topuri.intro",
            "Rank MPs by loyalty / rebellion / participation on roll-call votes.",
          )}
        </p>
      </section>

      <section className="bg-slate-800/30 rounded-xl p-4 sm:p-5" data-enter>
        <div className="flex flex-col sm:flex-row sm:items-end gap-3 sm:gap-4 mb-4">
          <label className="flex-1 min-w-0">
            <span className="block text-xs text-slate-400 mb-1">
              Minimum votes
            </span>
            <input
              type="number"
              value={minVotes}
              onChange={(e) => setMinVotes(Math.max(0, Number(e.target.value) || 0))}
              placeholder="1"
              className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-600 text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500/40 focus:border-sky-500"
            />
          </label>
          <div className="text-xs text-slate-400">
            {entries.length} of {scorecardQuery.data?.total ?? "—"} MPs shown
          </div>
        </div>

        <>
          <div className="overflow-x-auto">
            <table
              role="table"
              aria-label="MP behavioural scorecard: loyalty, rebellion and participation per MP"
              className="min-w-full text-sm data-table"
            >
              <caption className="sr-only">
                MP behavioural scorecard: loyalty, rebellion and participation per MP
              </caption>
              <thead>
                <tr className="text-left text-slate-400 border-b border-slate-700">
                  <th className="py-2.5 pr-4 font-medium" scope="col">
                    MP
                  </th>
                  <th className="py-2.5 pr-4 font-medium text-right" scope="col">
                    Votes
                  </th>
                  <th className="py-2.5 pr-4 font-medium text-right" scope="col">
                    Loyalty
                  </th>
                  <th className="py-2.5 pr-4 font-medium text-right" scope="col">
                    Rebellion
                  </th>
                  <th className="py-2.5 pr-4 font-medium text-right" scope="col">
                    Participation
                  </th>
                  <th className="py-2.5 pr-4 font-medium text-right" scope="col">
                    Party
                  </th>
                </tr>
              </thead>
              <tbody>
                {entries.map((e: ScorecardEntry) => (
                  <tr key={e.person_id} className="border-b border-slate-700/40">
                    <td className="py-2.5 pr-4 text-slate-200">
                      {e.canonical_name ?? e.name_raw ?? "—"}
                    </td>
                    <td className="py-2.5 pr-4 text-right text-slate-300 tabular-nums">
                      {e.total_votes}
                    </td>
                    <td className="py-2.5 pr-4 text-right">
                      {e.loyalty_pct === null ? (
                        <span className="text-slate-400">—</span>
                      ) : (
                        <div className="flex items-center gap-2">
                          <DataBar value={e.loyalty_pct} max={100} tone={LOYALTY_TONE(e.loyalty_pct)} />
                          <span className="text-slate-300 tabular-nums w-8">
                            {e.loyalty_pct}%
                          </span>
                        </div>
                      )}
                    </td>
                    <td className="py-2.5 pr-4 text-right text-slate-300 tabular-nums">
                      {e.rebellion_pct === null ? "—" : `${e.rebellion_pct}%`}
                    </td>
                    <td className="py-2.5 pr-4 text-right text-slate-300 tabular-nums">
                      {e.participation_pct === null ? "—" : `${e.participation_pct}%`}
                    </td>
                    <td className="py-2.5 pr-4 text-slate-300 font-mono text-xs">
                      {e.party ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p role="note" className="mt-2 text-xs text-slate-400">
            {t(
              "topuri.denominators",
              "Loyalty/rebellion denominator: {{alignment}} yes/no positions with a party majority (abstain/not-voting excluded). Participation denominator: {{participation}} votes in scope.",
              {
                alignment: scorecardQuery.data?.data[0]?.denominators.alignment ?? "—",
                participation: scorecardQuery.data?.data[0]?.denominators.participation ?? "—",
              },
            )}
        </p>
        </>
      </section>

      <section className="text-xs text-slate-500 mt-2 max-w-3xl">
        <p>
          {t("view.topuri.note", "Loyalty = share of votes where the MP voted with their party's majority. Rebellion = share against it. Participation = share of all votes in scope the MP cast a position for. Derived from observed roll-call positions only.")}
        </p>
      </section>
    </div>
  );
}
