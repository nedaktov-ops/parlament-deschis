import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api, traseismSummary } from "../api/client";
import { useScope } from "../hooks/useScope";
import ScopeControls from "../components/ScopeControls";
import { DataBar } from "../components/DataViz";
import VoteActivityChart from "../components/VoteActivityChart";
import AsyncState, { resolveViewState } from "../components/ui/AsyncState";

export default function Grafice() {
  const { t } = useTranslation();
  const scope = useScope();

  const summaryQuery = useQuery({
    queryKey: ["grafice-summary", ...scope.scopeKey],
    queryFn: () => traseismSummary(scope.legislature ?? "2024", scope.chamber ?? "deputies"),
  });

  const cohesionQuery = useQuery({
    queryKey: ["grafice-cohesion", ...scope.scopeKey],
    queryFn: () => api.voteCohesion(scope.chamber, scope.legislature),
  });

  const summary = summaryQuery.data;
  const cohesion = cohesionQuery.data?.data ?? [];
  const cohesionExists = cohesionQuery.data?.data_exists ?? false;

  const view = resolveViewState({
    isLoading: summaryQuery.isLoading || cohesionQuery.isLoading,
    isError: summaryQuery.isError || cohesionQuery.isError,
    isEmpty: cohesionQuery.isSuccess && (!cohesionExists || cohesion.length === 0),
  });
  if (view !== "ready") {
    return (
      <AsyncState
        view={view}
        pageTitle={t("view.grafice.title", "Party cohesion & defection timeline")}
        onRetry={() => {
          void summaryQuery.refetch();
          void cohesionQuery.refetch();
        }}
        errorLabel={t("view.grafice.loadError", "Cohesion and vote-activity data could not be loaded.")}
        emptyTitle={t("empty.rollcall", "Roll-call vote data is not yet available for this legislature.")}
      />
    );
  }

  return (
    <div className="space-y-6">
      <ScopeControls showChamber showLegislature note={t("scope.note.cohesion")} />
      <section className="py-2" data-enter>
        <h1 className="page-title">
          {t("view.grafice.title", "Party cohesion & defection timeline")}
        </h1>
        <p className="mt-2 text-sm sm:text-base text-slate-400 max-w-3xl">
          {t(
            "view.grafice.intro",
            "Party cohesion score over time, with defection markers. Based on observed switch_group events and roll-call positions.",
          )}
        </p>
      </section>

      <section className="bg-slate-800/30 rounded-xl p-4 sm:p-5" data-enter>
        <>
            <div className="overflow-x-auto">
              <table
                role="table"
                aria-label={t("aria.rollcallTable", "Table of plenary votes and each MP's position")}
                className="min-w-full text-sm data-table"
              >
                <caption className="sr-only">
                  {t("aria.rollcallTable", "Table of plenary votes and each MP's position")}
                </caption>
                <thead>
                  <tr className="text-left text-slate-400 border-b border-slate-700">
                    <th className="py-2.5 pr-4 font-medium" scope="col">
                      {t("filter.party", "Party")}
                    </th>
                    <th className="py-2.5 pr-4 font-medium text-right" scope="col">
                      {t("vote.yes", "Yes")}
                    </th>
                    <th className="py-2.5 pr-4 font-medium text-right" scope="col">
                      {t("vote.no", "No")}
                    </th>
                    <th className="py-2.5 pr-4 font-medium text-right" scope="col">
                      {t("vote.abstain", "Abstain")}
                    </th>
                    <th className="py-2.5 pr-4 font-medium text-right" scope="col">
                      {t("vote.not_voting", "Present, did not vote")}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {cohesion.map((c) => (
                    <tr key={c.party} className="border-b border-slate-700/40">
                      <td className="py-2.5 pr-4 text-slate-200 font-medium">
                        {c.party}
                      </td>
                      <td className="py-2.5 pr-4 text-right">
                        <div className="flex items-center gap-2">
                          <DataBar value={c.yes_pct} max={100} tone="success" />
                          <span className="text-slate-300 tabular-nums w-8">
                            {c.yes_pct}%
                          </span>
                        </div>
                      </td>
                      <td className="py-2.5 pr-4 text-right">
                        <div className="flex items-center gap-2">
                          <DataBar value={c.no_pct} max={100} tone="danger" />
                          <span className="text-slate-300 tabular-nums w-8">
                            {c.no_pct}%
                          </span>
                        </div>
                      </td>
                      <td className="py-2.5 pr-4 text-right">
                        <div className="flex items-center gap-2">
                          <DataBar value={c.abstain_pct} max={100} tone="warning" />
                          <span className="text-slate-300 tabular-nums w-8">
                            {c.abstain_pct}%
                          </span>
                        </div>
                      </td>
                      <td className="py-2.5 pr-4 text-right text-slate-300 tabular-nums">
                        {c.not_voting}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {summary && (
              <section className="bg-slate-800/30 rounded-xl p-4 sm:p-5 mt-6" data-enter>
                <h2 className="text-lg font-semibold text-slate-100 mb-3">
                  Switch statistics — {summary.legislature} / {summary.chamber}
                </h2>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
                  <div className="bg-slate-900/50 p-3 rounded">
                    <div className="text-xs text-slate-400">Members</div>
                    <div className="text-xl text-slate-100 tabular-nums">
                      {summary.members}
                    </div>
                  </div>
                  <div className="bg-slate-900/50 p-3 rounded">
                    <div className="text-xs text-slate-400">Group switches</div>
                    <div className="text-xl text-slate-100 tabular-nums">
                      {summary.switches}
                    </div>
                  </div>
                  <div className="bg-slate-900/50 p-3 rounded">
                    <div className="text-xs text-slate-400">Switchers</div>
                    <div className="text-xl text-slate-100 tabular-nums">
                      {summary.switchers}
                    </div>
                  </div>
                  <div className="bg-slate-900/50 p-3 rounded">
                    <div className="text-xs text-slate-400">Rate</div>
                    <div className="text-xl text-slate-100 tabular-nums">
                      {summary.switch_rate}
                    </div>
                  </div>
                </div>
              </section>
          )}
        </>
      </section>

      <section className="bg-slate-800/30 rounded-xl p-4 sm:p-5" data-enter>
        <VoteActivityChart chamber={scope.chamber ?? "deputies"} legislature={scope.legislature ?? "2024"} />
      </section>

      <section className="text-xs text-slate-500 mt-2 max-w-3xl">
        <p>
          {t("view.grafice.note", "Cohesion bars show each party's share of roll-call positions by choice. Switch statistics come from observed switch_group events in the chamber ledgers.")}
        </p>
      </section>
    </div>
  );
}
