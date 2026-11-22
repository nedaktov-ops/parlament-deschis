import { useMemo } from "react";
import { useQueries, useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api, votesForScope, type VotePositionRow } from "../api/client";
import { useScope } from "../hooks/useScope";
import ScopeControls from "../components/ScopeControls";
import PartyAgreementMatrix from "../components/PartyAgreementMatrix";
import AsyncState, { resolveViewState } from "../components/ui/AsyncState";

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

  // R-08: discover data-bearing scopes from the API (W8), never hardcode
  // a chamber/legislature. URL scope takes precedence over the corpus default.
  const scopeProbe = useQuery({
    queryKey: ["votes-scopes"],
    queryFn: () => api.votes({ limit: 1 }),
  });
  const active = useMemo(() => {
    const candidates = (scopeProbe.data?.scopes ?? [])
      .filter((s) => !scope.chamber || s.chamber === scope.chamber)
      .filter((s) => !scope.legislature || s.legislature === scope.legislature)
      .sort((a, b) => b.total - a.total);
    const chosen = candidates[0];
    return chosen
      ? { chamber: chosen.chamber, legislature: chosen.legislature, total: chosen.total }
      : null;
  }, [scopeProbe.data, scope.chamber, scope.legislature]);
  const total = active?.total ?? 0;

  const votesQuery = useQuery({
    queryKey: ["radar-votes", ...scope.scopeKey, active?.chamber ?? "*", active?.legislature ?? "*"],
    queryFn: () => api.votes({
      ...votesForScope(scope, { limit: 30, offset: 0 }),
      chamber: active?.chamber,
      legislature: active?.legislature ?? undefined,
    }),
    enabled: scopeProbe.isSuccess,
  });

  const votes = useMemo(() => votesQuery.data?.data ?? [], [votesQuery.data]);

  const positionQueries = useQueries({
    queries: votes.map((v) => ({
      queryKey: ["radar-positions", v.native_vote_id],
      queryFn: () => api.votePositions(v.native_vote_id, { limit: 500 }),
      enabled: votesQuery.isSuccess && !!v.native_vote_id,
      retry: 1,
    })),
  });

  // Only successful position queries contribute cells; failures are counted
  // and disclosed separately instead of blanking the whole matrix.
  const failedPositions = positionQueries.reduce((n, q) => n + (q.isError ? 1 : 0), 0);
  const positionsData = useMemo(() => {
    const map = new Map<string, VotePositionRow[]>();
    positionQueries.forEach((q, i) => {
      const vote = votes[i];
      if (q.isSuccess && q.data?.data && vote) {
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

  const view = resolveViewState({
    isLoading: scopeProbe.isLoading || votesQuery.isLoading
      || positionQueries.some((q) => q.isLoading && q.fetchStatus !== "idle"),
    // A failed positions query is an excluded column, not a page-level error.
    isError: scopeProbe.isError || votesQuery.isError,
    isEmpty: votesQuery.isSuccess && votes.length === 0,
  });
  if (view !== "ready") {
    return (
      <AsyncState
        view={view}
        pageTitle={t("view.radar.title", "Roll-call alignment matrix")}
        onRetry={() => {
          void scopeProbe.refetch();
          void votesQuery.refetch();
          positionQueries.forEach((q) => void q.refetch());
        }}
        errorLabel={t("view.radar.loadError", "The roll-call alignment matrix could not be loaded.")}
        emptyTitle={t("empty.rollcall", "Roll-call vote data is not yet available for this legislature.")}
      />
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
      </section>

      <section className="text-xs text-slate-500 mt-2 max-w-3xl">
        <p role="note">
          {t("view.radar.sampleNote", "Sample of {{shown}} of {{total}} votes in scope {{legislature}}. Colour = dominant party choice; number = count of MPs with that choice.", {
            shown: votes.length,
            total,
            legislature: active?.legislature ?? "—",
          })}
        </p>
        {failedPositions > 0 && (
          <p role="note" className="mt-2 text-amber-300">
            {t("view.radar.failedPositions", "{{failed}} vote(s) had positions that could not be loaded and are excluded from the matrix — this is an error, not an empty result.", { failed: failedPositions })}
          </p>
        )}
        <p className="mt-2">
          {t("view.radar.note", "Each cell shows how many MPs of a party voted a given way in a roll-call vote. Colour = dominant party choice; number = count of MPs with that choice.")}
        </p>
        {votes.some((v) => v.positions_incomplete) && (
          <p role="note" className="mt-2">
            {t("scope.note.positionsIncomplete")}{" "}
            {t("view.radar.positionsNote", "In this sample, {{n}} of {{m}} votes are flagged positions_incomplete=true; official yes/no/abstain totals can exceed the number of recorded individual positions.", {
              n: votes.filter((v) => v.positions_incomplete).length,
              m: votes.length,
            })}
          </p>
        )}
      </section>

      <section className="bg-slate-800/30 rounded-xl p-4 sm:p-5" data-enter>
        <PartyAgreementMatrix votes={votes} positionsByVote={positionsData} />
      </section>
    </div>
  );
}
