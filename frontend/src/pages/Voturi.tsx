import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api, type VoteRow } from "../api/client";
import RollCallTable from "../components/RollCallTable";
import Skeleton from "../components/ui/Skeleton";

export default function Voturi() {
  const { t } = useTranslation();
  const [query, setQuery] = useState<string>("");
  const [selectedVoteId, setSelectedVoteId] = useState<string | null>(null);

  const votesQuery = useQuery({
    queryKey: ["votes", query],
    queryFn: () =>
      api.votes({
        chamber: undefined,
        legislature: undefined,
        limit: 100,
      }),
  });

  const votes = useMemo(() => votesQuery.data?.data ?? [], [votesQuery.data]);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return votes;
    return votes.filter(
      (v: VoteRow) => (v.title_raw ?? "").toLowerCase().includes(needle),
    );
  }, [votes, query]);

  const goToVote = (nativeVoteId: string) => {
    setSelectedVoteId(nativeVoteId);
  };

  if (votesQuery.isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Skeleton className="h-8 w-32" />
        <Skeleton className="mt-2 h-4 w-64" />
        <p className="mt-2 text-sm text-slate-500">
          {t("loading", "Loading…")}
        </p>
      </div>
    );
  }

  if (votesQuery.isError) {
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
          {t("view.voturi.title", "Roll-call votes")}
        </h1>
        <p className="mt-2 text-sm sm:text-base text-slate-400 max-w-3xl">
          {t("view.voturi.intro", "Every vote in the Chamber of Deputies and the Senate, with MP names and the official source.")}
        </p>
        <p className="mt-2 text-xs text-slate-500 max-w-3xl">
          {t(
            "view.voturi.scopeNote",
            "Roll-call vote data comes from the official cdep.ro feed. Each row carries its source URL.",
          )}
        </p>
      </section>

      <section className="bg-slate-800/30 rounded-xl p-4 sm:p-5" data-enter>
        <div className="flex flex-col sm:flex-row sm:items-end gap-3 sm:gap-4 mb-4">
          <label className="flex-1 min-w-0">
            <span className="block text-xs text-slate-400 mb-1">
              {t("filter.search", "Search")}
            </span>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t("filter.search", "Search by title…")}
              className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-600 text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500/40 focus:border-sky-500"
            />
          </label>
          <div className="text-xs text-slate-400">
            {filtered.length} / {votes.length}
          </div>
        </div>

        {votesQuery.isLoading && (
          <div className="text-slate-500 text-sm py-6">
            {t("loading", "Loading…")}
          </div>
        )}
        {votesQuery.isError && (
          <div className="text-red-400 text-sm py-6">
            {t("view.voturi.loadError", "Failed to load votes.")}
          </div>
        )}

        {!votesQuery.isLoading && !votesQuery.isError && filtered.length === 0 && (
          <div className="text-slate-500 text-sm py-6 text-center">
            {votes.length === 0
              ? t("empty.rollcall", "Roll-call vote data is not yet available for this legislature.")
              : t("mps.empty", "No votes match this search.")}
          </div>
        )}

        {!votesQuery.isLoading && !votesQuery.isError && filtered.length > 0 && (
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
                    {t("filter.date", "Date")}
                  </th>
                  <th className="py-2.5 pr-4 font-medium" scope="col">
                    {t("mps.search", "Title")}
                  </th>
                  <th className="py-2.5 pr-4 font-medium" scope="col">
                    Chamber
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
                {filtered.map((v: VoteRow) => (
                  <tr
                    key={v.native_vote_id}
                    className="border-b border-slate-700/40 hover:bg-slate-800/40 cursor-pointer"
                    role="button"
                    tabIndex={0}
                    onClick={() => goToVote(v.native_vote_id)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        goToVote(v.native_vote_id);
                      }
                    }}
                  >
                    <td className="py-2.5 pr-4 text-slate-200 tabular-nums">
                      {v.vote_time ?? "—"}
                    </td>
                    <td className="py-2.5 pr-4 text-slate-200">
                      {v.title_raw ?? "—"}
                    </td>
                    <td className="py-2.5 pr-4 text-slate-300">
                      {v.chamber === "deputies" ? "Camera Deputaților" : v.chamber === "senate" ? "Senatul" : "—"}
                    </td>
                    <td className="py-2.5 pr-4 text-right text-slate-300 tabular-nums">
                      {v.yes ?? "—"}
                    </td>
                    <td className="py-2.5 pr-4 text-right text-slate-300 tabular-nums">
                      {v.no ?? "—"}
                    </td>
                    <td className="py-2.5 pr-4 text-right text-slate-300 tabular-nums">
                      {v.abstain ?? "—"}
                    </td>
                    <td className="py-2.5 pr-4 text-right text-xs text-slate-500 tabular-nums">
                      {v.source_url ? v.source_url.split("/")[2] : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {selectedVoteId && (
        <section className="bg-slate-800/30 rounded-xl p-4 sm:p-5" data-enter>
          <h2 className="text-lg font-semibold text-slate-100 mb-3">
            Vote positions — {selectedVoteId}
          </h2>
          <button
            type="button"
            onClick={() => setSelectedVoteId(null)}
            className="text-xs text-slate-400 hover:text-slate-200 mb-3"
          >
            ← Back to votes list
          </button>
          <RollCallTable voteId={selectedVoteId} />
        </section>
      )}
    </div>
  );
}
