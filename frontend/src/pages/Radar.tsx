import { useMemo } from "react";
import { useQueries, useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api, votesForScope, type VotePositionRow } from "../api/client";
import { useScope } from "../hooks/useScope";
import ScopeControls from "../components/ScopeControls";
import PartyAgreementMatrix from "../components/PartyAgreementMatrix";
import Skeleton from "../components/ui/Skeleton";

const CHOICE_COLOR: Record<string, string> = {
  yes: "#10b981", // emerald-500
  no: "#f87171", // red-400: rose-500 (#ef4444) is only 4.03:1 on the row background
  abstain: "#f59e0b", // amber-500
  not_voting: "#94a3b8", // slate-400
};

interface PartyVoteCell {
  party: string;
  choice: string | null;
  count: number;
  total: number;
}

export default function Radar() {
  const { t } = useTranslation();
  const scope = useScope();

  const votesQuery = useQuery({
    queryKey: ["radar-votes", ...scope.scopeKey],
    queryFn: () => api.votes(votesForScope(scope, { limit: 30 })),
  });

  const votes = useMemo(() => votesQuery.data?.data ?? [], [votesQuery.data]);
  const dataExists = votesQuery.data?.data_exists ?? false;

  const positionQueries = useQueries({
    queries: votes.map((v) => ({
      queryKey: ["radar-positions", v.native_vote_id],
      queryFn: () => api.votePositions(v.native_vote_id, { limit: 500 }),
      enabled: votesQuery.isSuccess && !!v.native_vote_id,
    })),
  });

  const positionsData = useMemo(() => {
    const map = new Map<string, VotePositionRow[]>();
    positionQueries.forEach((q, i) => {
      const vote = votes[i];
      if (q.data?.data && vote) {
        map.set(vote.native_vote_id, q.data.data);
      }
    });
    return map;
  }, [positionQueries, votes]);

  // Build alignment matrix: parties x votes
  const matrix = useMemo(() => {
    const parties = new Set<string>();
    const cells = new Map<string, PartyVoteCell>(); // key: "${party}|${vote_id}"

    votes.forEach((vote) => {
      const positions = positionsData.get(vote.native_vote_id) ?? [];
      const byParty = new Map<string, Record<string, number>>();
      positions.forEach((p) => {
        if (!p.group_raw) return;
        parties.add(p.group_raw);
        const choiceCounts = byParty.get(p.group_raw) ?? {};
        choiceCounts[p.choice] = (choiceCounts[p.choice] || 0) + 1;
        byParty.set(p.group_raw, choiceCounts);
      });
      byParty.forEach((choiceCounts, party) => {
        const total = Object.values(choiceCounts).reduce((a, b) => a + b, 0);
        const dominant = Object.entries(choiceCounts).sort(
          (a, b) => b[1] - a[1],
        )[0];
        cells.set(
          `${party}|${vote.native_vote_id}`,
          {
            party,
            choice: dominant ? dominant[0] : null,
            count: dominant ? dominant[1] : 0,
            total,
          },
        );
      });
    });

    return { parties: Array.from(parties).sort(), votes, cells };
  }, [votes, positionsData]);

  if (votesQuery.isLoading || positionQueries.some((q) => q.isLoading)) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <h1 className="sr-only">{t("view.radar.title", "Roll-call alignment matrix")}</h1>
        <Skeleton className="h-8 w-32" />
        <Skeleton className="mt-2 h-4 w-64" />
        <p className="mt-2 text-sm text-slate-500">{t("loading", "Loading…")}</p>
      </div>
    );
  }

  if (votesQuery.isError || positionQueries.some((q) => q.isError)) {
    return (
      <div className="text-red-400 text-sm py-6 text-center">
        <h1 className="sr-only">{t("view.radar.title", "Roll-call alignment matrix")}</h1>
        {t("view.voturi.loadError", "Failed to load votes.")}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <ScopeControls
        showDate showChamber showLegislature
        note={t("scope.note.votesUpTo", { date: scope.date })}
      />
      <section className="py-2" data-enter>
        <h1 className="page-title">
          {t("view.radar.title", "Roll-call alignment matrix")}
        </h1>
        <p className="mt-2 text-sm sm:text-base text-slate-400 max-w-3xl">
          {t(
            "view.radar.intro",
            "How parliamentary groups align on roll-call votes: yes / no / abstain / did-not-vote heatmap by party.",
          )}
        </p>
      </section>

      <section className="bg-slate-800/30 rounded-xl p-4 sm:p-5" data-enter>
        {!dataExists || votes.length === 0 || matrix.parties.length === 0 ? (
          <div className="text-slate-500 text-sm py-12 text-center">
            {t("empty.rollcall", "Roll-call vote data is not yet available for this legislature.")}
          </div>
        ) : (
          <div
            className="overflow-x-auto"
            tabIndex={0}
            role="region"
            aria-label={t("aria.votesScroll", "Scrollable table of plenary votes")}
          >
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
                  {matrix.votes.map((v) => (
                    <th
                      key={v.native_vote_id}
                      className="py-2.5 pr-4 font-medium text-center text-slate-400 border-b border-slate-700"
                      scope="col"
                      title={v.title_raw ?? ""}
                    >
                      {v.vote_time?.split(" ")[0] ?? "—"}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {matrix.parties.map((party) => (
                  <tr key={party} className="border-b border-slate-700/40">
                    <td className="py-2.5 pr-4 text-slate-200 font-medium">
                      {party}
                    </td>
                    {matrix.votes.map((vote) => {
                      const cell = matrix.cells.get(`${party}|${vote.native_vote_id}`);
                      const choice = cell?.choice ?? null;
                      const count = cell?.count ?? 0;
                      const total = cell?.total ?? 0;
                      const pct = total > 0 ? Math.round((count / total) * 100) : 0;
                      return (
                        <td
                          key={vote.native_vote_id}
                          className="py-2.5 pr-4 text-center border-b border-slate-700/40"
                          title={`${party}: ${choice ?? "—"} ${count}/${total} (${pct}%)`}
                          style={{
                            backgroundColor: choice
                              ? CHOICE_COLOR[choice as keyof typeof CHOICE_COLOR] + "20"
                              : "transparent",
                          }}
                        >
                          {count > 0 ? (
                            <span className="text-xs font-mono tabular-nums" style={{ color: (choice && CHOICE_COLOR[choice as keyof typeof CHOICE_COLOR]) || "#94a3b8" }}>
                              {count}
                            </span>
                          ) : (
                            <span className="text-xs text-slate-600">—</span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="text-xs text-slate-500 mt-2 max-w-3xl">
        <p>
          {t("view.radar.note", "Each cell shows how many MPs of a party voted a given way in a roll-call vote. Colour = dominant party choice; number = count of MPs with that choice.")}
        </p>
        {votes.some((v) => v.positions_incomplete) && (
          <p role="note" className="mt-2">
            {t("scope.note.positionsIncomplete")}
          </p>
        )}
      </section>

      <section className="bg-slate-800/30 rounded-xl p-4 sm:p-5" data-enter>
        <PartyAgreementMatrix votes={votes} positionsByVote={positionsData} />
      </section>
    </div>
  );
}
