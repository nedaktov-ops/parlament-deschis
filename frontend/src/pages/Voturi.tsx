import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { useNavigate, useSearch } from "@tanstack/react-router";
import { api, votesForScope, type VoteRow } from "../api/client";
import { useScope } from "../hooks/useScope";
import ScopeControls from "../components/ScopeControls";
import RollCallTable from "../components/RollCallTable";
import AsyncState, { resolveViewState } from "../components/ui/AsyncState";
import ProvenanceStamp from "../components/ProvenanceStamp";

export default function Voturi() {
  const { t } = useTranslation();
  const scope = useScope();
  const navigate = useNavigate({ from: "/Voturi" });
  // Search text and the selected vote are URL-backed so a deep link opens the
  // exact vote and back/forward steps through the filter (FN-7).
  const local = useSearch({ from: "/Voturi", select: (s) => s as Record<string, unknown> });
  const query = typeof local.query === "string" ? local.query : "";
  const selectedVoteId = typeof local.selectedVoteId === "string" ? local.selectedVoteId : null;
  const setQuery = (value: string) => navigate({ search: scope.searchFor({ query: value || undefined }) });
  const setSelectedVoteId = (value: string | null) =>
    navigate({ search: scope.searchFor({ selectedVoteId: value ?? undefined }) });

  const [offset, setOffset] = useState(0);
  const limit = 100;

  // R-08: discover data-bearing scopes from the API instead of hardcoding
  // a chamber/legislature. The probe is tiny; the paged query follows it.
  const scopeProbe = useQuery({
    queryKey: ["votes-scopes"],
    queryFn: () => api.votes({ limit: 1 }),
  });
  const scopes = useMemo(() => scopeProbe.data?.scopes ?? [], [scopeProbe.data]);
  const active = useMemo(() => {
    const candidates = scopes
      .filter((s) => !scope.chamber || s.chamber === scope.chamber)
      .filter((s) => !scope.legislature || s.legislature === scope.legislature)
      .sort((a, b) => b.total - a.total);
    const chosen = candidates[0];
    return chosen
      ? { chamber: chosen.chamber, legislature: chosen.legislature }
      : null;
  }, [scopes, scope.chamber, scope.legislature]);
  const activeKey = active ? `${active.chamber}|${active.legislature ?? ""}` : "";

  useEffect(() => {
    setOffset(0);
  }, [activeKey]);

  // Search is page-local (no API title filter): reset pagination on a new query.
  useEffect(() => setOffset(0), [query]);

  // Title search stays client-side; only the API-supported scope enters the key.
  const votesQuery = useQuery({
    queryKey: ["votes", ...scope.scopeKey, activeKey, offset],
    queryFn: () => api.votes({
      ...votesForScope(scope, { limit, offset }),
      chamber: active?.chamber,
      legislature: active?.legislature ?? undefined,
    }),
    enabled: scopeProbe.isSuccess,
  });

  const voteDetailQuery = useQuery({
    queryKey: ["vote-detail", selectedVoteId],
    queryFn: () => api.voteDetail(selectedVoteId!),
    enabled: Boolean(selectedVoteId),
  });

  const votes = useMemo(() => votesQuery.data?.data ?? [], [votesQuery.data]);
  const total = votesQuery.data?.total ?? 0;
  const shownFrom = total === 0 ? 0 : offset + 1;
  const shownTo = Math.min(offset + limit, total);
  const incompleteOnPage = votes.filter((v: VoteRow) => v.positions_incomplete).length;

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

  const view = resolveViewState({
    isLoading: scopeProbe.isLoading || votesQuery.isLoading,
    isError: scopeProbe.isError || votesQuery.isError,
    isEmpty: scopeProbe.isSuccess && votesQuery.isSuccess && votes.length === 0,
  });
  if (view !== "ready") {
    return (
      <AsyncState
        view={view}
        pageTitle={t("view.voturi.title", "Roll-call votes")}
        onRetry={() => {
          void scopeProbe.refetch();
          void votesQuery.refetch();
        }}
        errorLabel={t("view.voturi.loadError", "Failed to load votes.")}
        emptyTitle={t("view.voturi.empty", "No roll-call votes recorded for this scope.")}
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
          {t("view.voturi.title", "Roll-call votes")}
        </h1>
        <p className="mt-2 text-sm sm:text-base text-slate-400 max-w-3xl">
          {t("view.voturi.intro", "Roll-call votes in the scope selected below. Every published row comes from the official cdep.ro feed and carries its source URL.")}
        </p>
        <p className="mt-2 text-xs text-slate-400 max-w-3xl" aria-live="polite">
          {t("view.voturi.scopeNote", "Scope: {{chamber}} / {{legislature}} — {{total}} votes in this corpus. Showing {{from}}–{{to}}.", {
            chamber: active?.chamber ?? "—",
            legislature: active?.legislature ?? "—",
            total,
            from: shownFrom,
            to: shownTo,
          })}
        </p>
      </section>

      <section className="bg-slate-800/30 rounded-xl p-4 sm:p-5" data-enter>
        <div className="flex flex-col sm:flex-row sm:items-end gap-3 sm:gap-4 mb-4">
          <label className="flex-1 min-w-0">
            <span className="block text-xs text-slate-400 mb-1">
              {t("view.voturi.scopeSelect", "Vote scope (from the corpus)")}
            </span>
            <select
              value={activeKey}
              onChange={(e) => {
                const picked = scopes.find(
                  (s) => `${s.chamber}|${s.legislature ?? ""}` === e.target.value,
                );
                if (picked) {
                  scope.setScope({
                    chamber: picked.chamber === "senate" ? "senate" : "deputies",
                    legislature: picked.legislature ?? undefined,
                  });
                }
              }}
              className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-600 text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500/40 focus:border-sky-500"
            >
              {scopes.map((s) => (
                <option key={`${s.chamber}|${s.legislature ?? ""}`} value={`${s.chamber}|${s.legislature ?? ""}`}>
                  {s.chamber} / {s.legislature ?? "—"} — {s.total}
                </option>
              ))}
            </select>
          </label>
          <label className="flex-1 min-w-0">
            <span className="block text-xs text-slate-400 mb-1">
              {t("filter.search", "Search")}
            </span>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t("view.voturi.searchPlaceholder", "Search by title…")}
              className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-600 text-slate-100 placeholder-slate-400 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500/40 focus:border-sky-500"
            />
            <span className="block text-xs text-slate-500 mt-1">
              {t("view.voturi.searchHint", "Search filters the current page only")}
            </span>
          </label>
          <div className="text-xs text-slate-400" aria-live="polite">
            {t("view.voturi.page", "{{filtered}} of {{total}} votes on this page ({{from}}–{{to}} of corpus)", {
              filtered: filtered.length,
              total,
              from: shownFrom,
              to: shownTo,
            })}
          </div>
        </div>

        {filtered.length === 0 && (
          <div className="text-slate-400 text-sm py-6 text-center">
            {votes.length === 0
              ? t("empty.rollcall", "Roll-call vote data is not yet available for this legislature.")
              : t("view.voturi.noSearchResults", "No votes match this search.")}
          </div>
        )}

        {filtered.length > 0 && (
          <div
            className="overflow-x-auto"
            role="region"
            tabIndex={0}
            aria-label={t("aria.votesScroll", "Scrollable table of plenary votes")}
          >
            <table
              className="min-w-full text-sm data-table"
              aria-label={t("aria.rollcallTable", "Table of plenary votes and each MP's position")}
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
                    {t("view.voturi.col.title", "Title")}
                  </th>
                  <th className="py-2.5 pr-4 font-medium" scope="col">
                    {t("filter.chamber", "Chamber")}
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
                  <th className="py-2.5 pr-4 font-medium text-right" scope="col">
                    {t("mps.source", "Source")}
                  </th>
                  <th className="py-2.5 pr-4 font-medium text-right" scope="col">
                    {t("vote.positionsLabel", "Positions")}
                  </th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((v: VoteRow) => (
                  <tr
                    key={v.native_vote_id}
                    className="border-b border-slate-700/40"
                  >
                    <td className="py-2.5 pr-4 text-slate-200 tabular-nums">
                      {v.vote_time ?? "—"}
                    </td>
                    <td className="py-2.5 pr-4 text-slate-200">
                      <button
                        type="button"
                        onClick={() => goToVote(v.native_vote_id)}
                        className="text-left text-sky-300 hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-500"
                        aria-label={t("view.voturi.positionsTitle", { id: v.title_raw ?? v.native_vote_id })}
                      >
                        {v.title_raw ?? "—"}
                      </button>
                    </td>
                    <td className="py-2.5 pr-4 text-slate-300">
                      {v.chamber === "deputies"
                        ? t("deputies", "Camera Deputaților")
                        : v.chamber === "senate"
                          ? t("senate", "Senat")
                          : "—"}
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
                    <td className="py-2.5 pr-4 text-right text-slate-300 tabular-nums">
                      {v.not_voting ?? "—"}
                    </td>
                    <td className="py-2.5 pr-4 text-right text-xs text-slate-400 tabular-nums">
                      {v.source_url ? (
                        <a
                          href={v.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sky-400 hover:underline"
                        >
                          {v.source_url.split("/")[2] ?? t("mps.source", "Source")}
                        </a>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="py-2.5 pr-4 text-right text-xs">
                      <span
                        className={
                          v.positions_incomplete
                            ? "rounded bg-amber-900/40 px-2 py-0.5 text-amber-300"
                            : "rounded bg-emerald-900/40 px-2 py-0.5 text-emerald-300"
                        }
                      >
                        {v.positions_incomplete
                          ? t("vote.positionsIncomplete", "incomplete")
                          : t("vote.positionsComplete", "complete")}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-400">
          <p role="note">
            {t("view.voturi.positionsNote", "On this page, {{n}} of {{m}} rows have positions_incomplete=true: official yes/no/abstain totals can exceed the number of recorded individual positions. The flag is shown per row.", {
              n: incompleteOnPage,
              m: votes.length,
            })}
          </p>
          <div className="flex items-center gap-3">
            <button
              type="button"
              disabled={offset === 0}
              onClick={() => setOffset((o) => Math.max(0, o - limit))}
              className="rounded border border-slate-600 px-3 py-1.5 disabled:opacity-40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400"
            >
              {t("view.voturi.prev", "Previous")}
            </button>
            <span aria-live="polite">
              {t("view.voturi.pageRange", "{{from}}–{{to}} of {{total}}", { from: shownFrom, to: shownTo, total })}
            </span>
            <button
              type="button"
              disabled={offset + limit >= total}
              onClick={() => setOffset((o) => o + limit)}
              className="rounded border border-slate-600 px-3 py-1.5 disabled:opacity-40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400"
            >
              {t("view.voturi.next", "Next")}
            </button>
          </div>
        </div>
      </section>

      {selectedVoteId && (
        <section className="bg-slate-800/30 rounded-xl p-4 sm:p-5" data-enter>
          <h2 className="text-lg font-semibold text-slate-100 mb-3">
            {t("view.voturi.positionsTitle", { id: selectedVoteId })}
          </h2>
          <button
            type="button"
            onClick={() => setSelectedVoteId(null)}
            className="text-xs text-slate-400 hover:text-slate-200 mb-3 focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-500"
          >
            {t("view.voturi.backToList", "← Back to votes list")}
          </button>
          {voteDetailQuery.data && (
            <ProvenanceStamp
              sourceUrl={voteDetailQuery.data.source_url}
              snapshotHash={voteDetailQuery.data.snapshot_hash}
              note={voteDetailQuery.data.truth_contract_version}
            />
          )}
          <RollCallTable voteId={selectedVoteId} />
        </section>
      )}
    </div>
  );
}
