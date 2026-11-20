import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api, type ScorecardEntry } from "../api/client";
import { DataBar } from "../components/DataViz";
import Skeleton from "../components/ui/Skeleton";

const LOYALTY_COLOR = (pct: number) => {
  if (pct >= 90) return "#10b981"; // emerald
  if (pct >= 70) return "#22c55e"; // green
  if (pct >= 50) return "#eab308"; // yellow
  if (pct >= 30) return "#f59e0b"; // amber
  return "#ef4444"; // rose
};

export default function Topuri() {
  const { t } = useTranslation();
  const [minVotes, setMinVotes] = useState(1);

  const scorecardQuery = useQuery({
    queryKey: ["topuri-scorecard", minVotes],
    queryFn: () =>
      api.scorecard(undefined, undefined, 100, 0, minVotes),
  });

  const entries = useMemo(() => scorecardQuery.data?.data ?? [], [
    scorecardQuery.data,
  ]);
  const dataExists = scorecardQuery.data?.data_exists ?? false;

  if (scorecardQuery.isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Skeleton className="h-8 w-32" />
        <Skeleton className="mt-2 h-4 w-64" />
        <p className="mt-2 text-sm text-slate-500">{t("loading", "Loading…")}</p>
      </div>
    );
  }

  if (scorecardQuery.isError) {
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
            {entries.length} MPs shown
          </div>
        </div>

        {scorecardQuery.isLoading && (
          <div className="text-slate-500 text-sm py-6">
            {t("loading", "Loading…")}
          </div>
        )}
        {scorecardQuery.isError && (
          <div className="text-red-400 text-sm py-6">
            {t("view.voturi.loadError", "Failed to load votes.")}
          </div>
        )}

        {!scorecardQuery.isLoading && !scorecardQuery.isError && entries.length === 0 && (
          <div className="text-slate-500 text-sm py-6 text-center">
            {dataExists
              ? t("topuri.empty", "No behavioural data available yet for the selected scope.")
              : t("empty.rollcall", "Roll-call vote data is not yet available for this legislature.")}
          </div>
        )}

        {!scorecardQuery.isLoading && !scorecardQuery.isError && entries.length > 0 && (
          <div className="overflow-x-auto">
            <table
              role="table"
              aria-label="MP behavioural scorecard: loyalty, rebellion and participation per MP"
              className="min-w-full text-sm"
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
                      <div className="flex items-center gap-2">
                        <DataBar value={e.loyalty_pct} max={100} color={LOYALTY_COLOR(e.loyalty_pct)} />
                        <span className="text-slate-300 tabular-nums w-8">
                          {e.loyalty_pct}%
                        </span>
                      </div>
                    </td>
                    <td className="py-2.5 pr-4 text-right text-slate-300 tabular-nums">
                      {e.rebellion_pct}%
                    </td>
                    <td className="py-2.5 pr-4 text-right text-slate-300 tabular-nums">
                      {e.participation_pct}%
                    </td>
                    <td className="py-2.5 pr-4 text-slate-300 font-mono text-xs">
                      {e.party ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="text-xs text-slate-500 mt-2 max-w-3xl">
        <p>
          {t("view.topuri.note", "Loyalty = share of votes where the MP voted with their party's majority. Rebellion = share against it. Participation = share of all votes in scope the MP cast a position for. Derived from observed roll-call positions only.")}
        </p>
      </section>
    </div>
  );
}
