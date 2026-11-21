import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useSearch } from "@tanstack/react-router";
import { useScope } from "../hooks/useScope";
import ScopeControls from "../components/ScopeControls";
import {
  api,
  generationalShift,
  committeeControl,
  type GenerationalShiftEntry,
  type CommitteeControlParty,
} from "../api/client";
import AsyncState, { resolveViewState } from "../components/ui/AsyncState";

interface PartyRow {
  id: string;
  short_name: string;
  name: string;
  color: string | null;
  total_members: number;
  switches_in: number;
}

interface Metric {
  label: string;
  a: string;
  b: string;
  higherIsBetter?: "a" | "b" | null;
}

function fmtInt(v: number): string {
  return v.toLocaleString();
}

export default function PartyComparison() {
  const { t } = useTranslation();
  const scope = useScope();
  const navigate = useNavigate({ from: "/compare" });
  // Page-local comparison selection is URL-backed too (FN-7).
  const local = useSearch({ from: "/compare", select: (s) => s as Record<string, unknown> });
  const partyA = typeof local.partyA === "string" ? local.partyA : "PSD";
  const partyB = typeof local.partyB === "string" ? local.partyB : "PNL";
  const setPartyA = (value: string) => navigate({ search: scope.searchFor({ partyA: value }) });
  const setPartyB = (value: string) => navigate({ search: scope.searchFor({ partyB: value }) });

  const parties = useQuery({
    queryKey: ["parties"],
    queryFn: () => api.parties(),
  });

  const ages = useQuery({
    queryKey: ["generational-shift", scope.legislature, scope.date, ...scope.scopeKey],
    queryFn: () => generationalShift(scope.legislature, scope.date),
  });

  const control = useQuery({
    queryKey: ["committee-control", scope.legislature, scope.date, ...scope.scopeKey],
    queryFn: () => committeeControl(scope.legislature, scope.date),
  });

  const partyList = parties.data?.data ?? [];

  const ageMap = useMemo(() => {
    const map = new Map<string, GenerationalShiftEntry>();
    for (const row of ages.data?.data ?? []) map.set(row.party, row);
    return map;
  }, [ages.data]);

  const chairMap = useMemo(() => {
    const map = new Map<string, CommitteeControlParty>();
    for (const row of control.data?.data?.parties ?? []) map.set(row.party, row);
    return map;
  }, [control.data]);

  const findParty = (short: string): PartyRow | undefined =>
    partyList.find((p) => p.short_name === short);

  const a = findParty(partyA);
  const b = findParty(partyB);

  const metrics: Metric[] = useMemo(() => {
    if (!a || !b) return [];
    const ageA = ageMap.get(a.short_name);
    const ageB = ageMap.get(b.short_name);
    const chairsA = chairMap.get(a.short_name);
    const chairsB = chairMap.get(b.short_name);
    return [
      {
        label: t("compare.members", "Total members (ever)"),
        a: fmtInt(a.total_members),
        b: fmtInt(b.total_members),
        higherIsBetter: a.total_members === b.total_members ? null : a.total_members > b.total_members ? "a" : "b",
      },
      {
        label: t("compare.switchesIn", "Switches in (observed)"),
        a: fmtInt(a.switches_in),
        b: fmtInt(b.switches_in),
        higherIsBetter: a.switches_in === b.switches_in ? null : a.switches_in > b.switches_in ? "a" : "b",
      },
      {
        label: t("compare.avgAge", "Average age"),
        a: ageA ? `${ageA.avg_age} (${ageA.mps_with_birth_dates} MPs)` : "—",
        b: ageB ? `${ageB.avg_age} (${ageB.mps_with_birth_dates} MPs)` : "—",
        higherIsBetter: null,
      },
      {
        label: t("compare.medianAge", "Median age"),
        a: ageA ? String(ageA.median_age) : "—",
        b: ageB ? String(ageB.median_age) : "—",
        higherIsBetter: null,
      },
      {
        label: t("compare.chairs", "Committee chairs"),
        a: chairsA ? `${chairsA.chairs} (${chairsA.share_pct}%)` : "—",
        b: chairsB ? `${chairsB.chairs} (${chairsB.share_pct}%)` : "—",
        higherIsBetter:
          (chairsA?.chairs ?? 0) === (chairsB?.chairs ?? 0)
            ? null
            : (chairsA?.chairs ?? 0) > (chairsB?.chairs ?? 0)
              ? "a"
              : "b",
      },
    ];
  }, [a, b, ageMap, chairMap, t]);

  const view = resolveViewState({
    isLoading: parties.isLoading || ages.isLoading || control.isLoading,
    isError: parties.isError || ages.isError || control.isError,
    isEmpty: parties.isSuccess && partyList.length === 0,
  });
  if (view !== "ready") {
    return (
      <AsyncState
        view={view}
        pageTitle={t("compare.title", "Party Comparison")}
        onRetry={() => {
          void parties.refetch();
          void ages.refetch();
          void control.refetch();
        }}
        errorLabel={t("compare.loadError", "Failed to load parties.")}
        emptyTitle={t("compare.empty", "There are no parties to compare in this release.")}
      />
    );
  }

  const selectClass =
    "bg-slate-800 border border-slate-700 rounded px-3 py-2 text-slate-200";

  return (
    <div className="py-6">
      <ScopeControls showDate showLegislature note={t("scope.note.parties")} />
      <h1 className="page-title mb-2">
        {t("compare.title", "Party Comparison")}
      </h1>
      <p className="text-slate-400 mb-2">
        {t(
          "compare.intro",
          "Compare any two parties on size, switch activity, demographics and committee control. All figures come from the dated parliamentary ledgers.",
        )}
      </p>
      <p className="text-sm mb-6">
        <Link
          to="/parties"
          search={scope.searchFor()}
          className="text-sky-400 hover:underline"
        >
          {t("compare.viewAllParties", "View all parties →")}
        </Link>
      </p>

      <div className="flex flex-wrap gap-6 mb-8">
        <label className="flex flex-col gap-1 text-sm text-slate-400">
          {t("compare.partyA", "Party A")}
          <select
            value={partyA}
            onChange={(e) => setPartyA(e.target.value)}
            className={selectClass}
          >
            {partyList.map((p) => (
              <option key={p.id} value={p.short_name}>
                {p.short_name}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm text-slate-400">
          {t("compare.partyB", "Party B")}
          <select
            value={partyB}
            onChange={(e) => setPartyB(e.target.value)}
            className={selectClass}
          >
            {partyList.map((p) => (
              <option key={p.id} value={p.short_name}>
                {p.short_name}
              </option>
            ))}
          </select>
        </label>
      </div>

      {a && b && (
        <div className="overflow-x-auto max-w-full" tabIndex={0} role="region" aria-label={t("compare.title", "Party Comparison")}>
          <table className="min-w-full bg-slate-800 rounded-xl overflow-hidden data-table">
            <thead className="bg-slate-700">
              <tr>
                <th scope="col" className="px-4 py-3 text-left text-sm font-medium !text-slate-300">
                  {t("compare.col.metric", "Metric")}
                </th>
                <th scope="col" className="px-4 py-3 text-center text-sm font-semibold !text-slate-100">
                  {a.color && (
                    <span
                      aria-hidden="true"
                      className="inline-block w-2.5 h-2.5 rounded-full mr-1.5 align-middle"
                      style={{ backgroundColor: a.color }}
                    />
                  )}
                  {a.short_name}
                </th>
                <th scope="col" className="px-4 py-3 text-center text-sm font-semibold !text-slate-100">
                  {b.color && (
                    <span
                      aria-hidden="true"
                      className="inline-block w-2.5 h-2.5 rounded-full mr-1.5 align-middle"
                      style={{ backgroundColor: b.color }}
                    />
                  )}
                  {b.short_name}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700">
              {metrics.map((m) => (
                <tr key={m.label} className="hover:bg-slate-700/50">
                  <th scope="row" className="px-4 py-3 text-slate-400 font-normal text-left">{m.label}</th>
                  <td
                    className={`px-4 py-3 text-center font-semibold ${
                      m.higherIsBetter === "a" ? "text-emerald-300" : "text-slate-200"
                    }`}
                    title={m.a === "—" ? t("compare.chairsUnavailable", "No dated chair data in corpus → unavailable, not zero") : undefined}
                  >
                    {m.a}
                    {m.higherIsBetter === "a" && (
                      <span className="ml-1.5 text-xs">
                        <span className="sr-only">{t("compare.higher", "higher")}</span>
                        <span aria-hidden="true">▲</span>
                      </span>
                    )}
                  </td>
                  <td
                    className={`px-4 py-3 text-center font-semibold ${
                      m.higherIsBetter === "b" ? "text-emerald-300" : "text-slate-200"
                    }`}
                    title={m.b === "—" ? t("compare.chairsUnavailable", "No dated chair data in corpus → unavailable, not zero") : undefined}
                  >
                    {m.b}
                    {m.higherIsBetter === "b" && (
                      <span className="ml-1.5 text-xs">
                        <span className="sr-only">{t("compare.higher", "higher")}</span>
                        <span aria-hidden="true">▲</span>
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="mt-6 bg-slate-800/50 rounded p-4 text-sm text-slate-400">
        <h2 className="text-slate-200 font-semibold mb-1">
          {t("compare.notes", "Reading the numbers")}
        </h2>
        <p>
          {t("compare.notes.desc")}
        </p>
      </div>
    </div>
  );
}
