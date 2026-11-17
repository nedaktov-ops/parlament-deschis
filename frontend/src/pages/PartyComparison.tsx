import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import {
  api,
  generationalShift,
  committeeControl,
  type GenerationalShiftEntry,
  type CommitteeControlParty,
} from "../api/client";

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
  const [partyA, setPartyA] = useState<string>("PSD");
  const [partyB, setPartyB] = useState<string>("PNL");

  const parties = useQuery({
    queryKey: ["parties"],
    queryFn: () => api.parties(),
  });

  const ages = useQuery({
    queryKey: ["generational-shift"],
    queryFn: () => generationalShift(),
  });

  const control = useQuery({
    queryKey: ["committee-control"],
    queryFn: () => committeeControl(),
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
        a: chairsA ? `${chairsA.chairs} (${chairsA.share_pct}%)` : "0",
        b: chairsB ? `${chairsB.chairs} (${chairsB.share_pct}%)` : "0",
        higherIsBetter:
          (chairsA?.chairs ?? 0) === (chairsB?.chairs ?? 0)
            ? null
            : (chairsA?.chairs ?? 0) > (chairsB?.chairs ?? 0)
              ? "a"
              : "b",
      },
    ];
  }, [a, b, ageMap, chairMap, t]);

  const selectClass =
    "bg-slate-800 border border-slate-700 rounded px-3 py-2 text-slate-200";

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-slate-100 mb-2">
        {t("compare.title", "Party Comparison")}
      </h1>
      <p className="text-slate-400 mb-6">
        {t(
          "compare.intro",
          "Compare any two parties on size, switch activity, demographics and committee control. All figures come from the dated parliamentary ledgers.",
        )}
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

      {parties.isLoading && (
        <div className="text-slate-500">{t("loading", "Loading…")}</div>
      )}
      {parties.isError && (
        <div className="text-red-400">
          {t("compare.loadError", "Failed to load parties.")}
        </div>
      )}

      {a && b && (
        <div className="overflow-x-auto">
          <table className="min-w-full bg-slate-800 rounded-lg overflow-hidden">
            <thead className="bg-slate-700">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-slate-300">
                  {t("compare.col.metric", "Metric")}
                </th>
                <th
                  className="px-4 py-3 text-center text-sm font-semibold"
                  style={{ color: a.color || "#e2e8f0" }}
                >
                  {a.short_name}
                </th>
                <th
                  className="px-4 py-3 text-center text-sm font-semibold"
                  style={{ color: b.color || "#e2e8f0" }}
                >
                  {b.short_name}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700">
              {metrics.map((m) => (
                <tr key={m.label} className="hover:bg-slate-700/50">
                  <td className="px-4 py-3 text-slate-400">{m.label}</td>
                  <td
                    className={`px-4 py-3 text-center font-semibold ${
                      m.higherIsBetter === "a" ? "text-emerald-300" : "text-slate-200"
                    }`}
                  >
                    {m.a}
                    {m.higherIsBetter === "a" && (
                      <span className="ml-1.5 text-xs" aria-label={t("compare.higher", "higher")}>
                        ▲
                      </span>
                    )}
                  </td>
                  <td
                    className={`px-4 py-3 text-center font-semibold ${
                      m.higherIsBetter === "b" ? "text-emerald-300" : "text-slate-200"
                    }`}
                  >
                    {m.b}
                    {m.higherIsBetter === "b" && (
                      <span className="ml-1.5 text-xs" aria-label={t("compare.higher", "higher")}>
                        ▲
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
          {t(
            "compare.notes.desc",
            "Members counts distinct persons with a membership on behalf of the party across all legislatures. Switches in counts observed switch_group events into a group carrying the party acronym. Ages cover MPs with a birth date (92% of the corpus). Chairs count active committee presidents.",
          )}
        </p>
      </div>
    </div>
  );
}
