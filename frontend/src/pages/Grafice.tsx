import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api, traseismSummary } from "../api/client";
import { DataBar } from "../components/DataViz";
import Skeleton from "../components/ui/Skeleton";

export default function Grafice() {
  const { t } = useTranslation();

  const summaryQuery = useQuery({
    queryKey: ["grafice-summary"],
    queryFn: () => traseismSummary("2024", "deputies"),
  });

  const cohesionQuery = useQuery({
    queryKey: ["grafice-cohesion"],
    queryFn: () => api.voteCohesion("deputies", "2024"),
  });

  const summary = summaryQuery.data;
  const cohesion = cohesionQuery.data?.data ?? [];
  const cohesionExists = cohesionQuery.data?.data_exists ?? false;

  if (summaryQuery.isLoading || cohesionQuery.isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Skeleton className="h-8 w-32" />
        <Skeleton className="mt-2 h-4 w-64" />
        <p className="mt-2 text-sm text-slate-500">{t("loading", "Loading…")}</p>
      </div>
    );
  }

  if (summaryQuery.isError || cohesionQuery.isError) {
    return (
      <div className="text-red-400 text-sm py-6 text-center">
        {t("view.voturi.loadError", "Failed to load votes.")}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <section className="py-2" data-enter>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-100">
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
        {!cohesionExists || cohesion.length === 0 ? (
          <div className="text-slate-500 text-sm py-12 text-center">
            {t("empty.rollcall", "Roll-call vote data is not yet available for this legislature.")}
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table
                role="table"
                aria-label={t("aria.rollcallTable", "Table of plenary votes and each MP's position")}
                className="min-w-full text-sm"
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
                          <DataBar value={c.yes_pct} max={100} color="#10b981" />
                          <span className="text-slate-300 tabular-nums w-8">
                            {c.yes_pct}%
                          </span>
                        </div>
                      </td>
                      <td className="py-2.5 pr-4 text-right">
                        <div className="flex items-center gap-2">
                          <DataBar value={c.no_pct} max={100} color="#ef4444" />
                          <span className="text-slate-300 tabular-nums w-8">
                            {c.no_pct}%
                          </span>
                        </div>
                      </td>
                      <td className="py-2.5 pr-4 text-right">
                        <div className="flex items-center gap-2">
                          <DataBar value={c.abstain_pct} max={100} color="#f59e0b" />
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
                    <div className="text-xs text-slate-400">Switches</div>
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
        )}
      </section>

      <section className="text-xs text-slate-500 mt-2 max-w-3xl">
        <p>
          {t("view.grafice.note", "Cohesion bars show each party's share of roll-call positions by choice. Switch statistics come from observed switch_group events in the chamber ledgers.")}
        </p>
      </section>
    </div>
  );
}
