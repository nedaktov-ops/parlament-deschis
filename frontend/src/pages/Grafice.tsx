import { useMemo } from "react";
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

  // R-08/W10: derive scope from the data-bearing scopes published by /votes
  // (W8). No chamber/legislature is hardcoded; URL scope wins over the default.
  const scopeProbe = useQuery({
    queryKey: ["votes-scopes"],
    queryFn: () => api.votes({ limit: 1 }),
  });
  const active = useMemo(() => {
    const candidates = (scopeProbe.data?.scopes ?? [])
      .filter((s) => !scope.chamber || s.chamber === scope.chamber)
      .filter((s) => !scope.legislature || s.legislature === scope.legislature)
      .sort((a, b) => b.total - a.total);
    return candidates[0] ?? null;
  }, [scopeProbe.data, scope.chamber, scope.legislature]);
  const legislature = active?.legislature ?? undefined;
  const chamber = active?.chamber ?? "deputies";

  const summaryQuery = useQuery({
    queryKey: ["grafice-summary", chamber, legislature ?? "*"],
    queryFn: () => traseismSummary(legislature ?? "", chamber),
    enabled: scopeProbe.isSuccess && !!legislature,
  });
  const cohesionQuery = useQuery({
    queryKey: ["grafice-cohesion", chamber, legislature ?? "*"],
    queryFn: () => api.voteCohesion(chamber, legislature),
    enabled: scopeProbe.isSuccess && !!legislature,
  });

  const summary = summaryQuery.data;
  const cohesion = cohesionQuery.data?.data ?? [];
  const cohesionExists = cohesionQuery.data?.data_exists ?? false;

  // Page-level state only when neither independent block can render.
  const view = resolveViewState({
    isLoading: scopeProbe.isLoading || (summaryQuery.isLoading && cohesionQuery.isLoading),
    isError: scopeProbe.isError || (summaryQuery.isError && cohesionQuery.isError),
    isEmpty: scopeProbe.isSuccess && (!legislature
      || (summaryQuery.isSuccess && cohesionQuery.isSuccess && !summary && !cohesionExists)),
  });
  if (view !== "ready") {
    return (
      <AsyncState
        view={view}
        pageTitle={t("view.grafice.title", "Party cohesion & defection timeline")}
        onRetry={() => {
          void scopeProbe.refetch();
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
            'Party cohesion from observed roll-call positions and switch_group events in the selected scope. "Cohesion" here is the share of recorded positions by choice, not a party-discipline score.',
          )}
        </p>
        <p className="mt-2 text-xs text-slate-400" aria-live="polite">
          {t("view.grafice.scopeNote", "Scope: {{chamber}} / {{legislature}} — {{total}} votes in this corpus.", {
            chamber: active?.chamber ?? "—",
            legislature: legislature ?? "—",
            total: active?.total ?? 0,
          })}
        </p>
      </section>

      {/* Cohesion block: its own state, independent of switch statistics. */}
      <section className="bg-slate-800/30 rounded-xl p-4 sm:p-5" data-enter>
        <h2 className="text-lg font-semibold text-slate-100 mb-3">
          {t("view.grafice.cohesionTitle", "Roll-call positions by party")}
        </h2>
        {cohesionQuery.isError ? (
          <p role="alert" className="text-sm text-rose-300">
            {t("view.grafice.cohesionLoadError", "Cohesion data could not be loaded.")}
          </p>
        ) : cohesionQuery.isSuccess && !cohesionExists ? (
          <p role="note" className="text-sm text-slate-400">
            {t("empty.rollcall", "Roll-call vote data is not yet available for this legislature.")}
          </p>
        ) : cohesionQuery.isSuccess && cohesion.length === 0 ? (
          <p role="note" className="text-sm text-slate-400">
            {t("view.grafice.cohesionEmpty", "No cohesion rows are published for this scope.")}
          </p>
        ) : (
          <div className="overflow-x-auto max-w-full" tabIndex={0} role="region"
               aria-label={t("view.grafice.cohesionTitle", "Roll-call positions by party")}>
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
                        <span className="text-slate-300 tabular-nums w-8">{c.yes_pct}%</span>
                      </div>
                    </td>
                    <td className="py-2.5 pr-4 text-right">
                      <div className="flex items-center gap-2">
                        <DataBar value={c.no_pct} max={100} tone="danger" />
                        <span className="text-slate-300 tabular-nums w-8">{c.no_pct}%</span>
                      </div>
                    </td>
                    <td className="py-2.5 pr-4 text-right">
                      <div className="flex items-center gap-2">
                        <DataBar value={c.abstain_pct} max={100} tone="warning" />
                        <span className="text-slate-300 tabular-nums w-8">{c.abstain_pct}%</span>
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
        )}
      </section>

      {/* Switch statistics: independent of cohesion success. */}
      <section className="bg-slate-800/30 rounded-xl p-4 sm:p-5" data-enter>
        <h2 className="text-lg font-semibold text-slate-100 mb-3">
          {t("view.grafice.switchStatsTitle", "Switch statistics")}
        </h2>
        {summaryQuery.isError ? (
          <p role="alert" className="text-sm text-rose-300">
            {t("view.grafice.summaryLoadError", "Switch statistics could not be loaded.")}
          </p>
        ) : summaryQuery.isSuccess && !summary ? (
          <p role="note" className="text-sm text-slate-400">
            {t("view.grafice.summaryEmpty", "No switch statistics are published for this scope.")}
          </p>
        ) : summary ? (
          <>
            <p className="text-xs text-slate-400 mb-3">
              {summary.legislature} / {summary.chamber}
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
              <div className="bg-slate-900/50 p-3 rounded min-w-0">
                <div className="text-xs text-slate-400">{t("view.grafice.members", "Members")}</div>
                <div className="text-xl text-slate-100 tabular-nums">{summary.members}</div>
              </div>
              <div className="bg-slate-900/50 p-3 rounded min-w-0">
                <div className="text-xs text-slate-400">{t("view.grafice.groupSwitches", "Group switches")}</div>
                <div className="text-xl text-slate-100 tabular-nums">{summary.switches}</div>
              </div>
              <div className="bg-slate-900/50 p-3 rounded min-w-0">
                <div className="text-xs text-slate-400">{t("view.grafice.switchers", "Switchers")}</div>
                <div className="text-xl text-slate-100 tabular-nums">{summary.switchers}</div>
              </div>
              <div className="bg-slate-900/50 p-3 rounded min-w-0">
                <div className="text-xs text-slate-400">{t("view.grafice.rate", "Rate — switchers / members")}</div>
                {/* W1 residual: a raw float overflowed the grid at 320/768.
                    Render a bounded percentage instead. */}
                <div className="text-xl text-slate-100 tabular-nums break-words">
                  {(summary.switch_rate * 100).toFixed(1)}%
                </div>
              </div>
            </div>
          </>
        ) : null}
      </section>

      <section className="bg-slate-800/30 rounded-xl p-4 sm:p-5" data-enter>
        <VoteActivityChart chamber={chamber} legislature={legislature} />
      </section>

      <section className="text-xs text-slate-500 mt-2 max-w-3xl">
        <p>
          {t("view.grafice.note", 'Cohesion bars show each party\'s share of recorded roll-call positions by choice, not a discipline score. Switch statistics come from observed switch_group events in the chamber ledgers.')}
        </p>
        {active?.total != null && (
          <p role="note" className="mt-2">
            {t("scope.note.positionsIncomplete")}
          </p>
        )}
      </section>
    </div>
  );
}
