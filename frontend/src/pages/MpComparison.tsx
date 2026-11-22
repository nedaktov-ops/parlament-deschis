import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { Link } from "@tanstack/react-router";
import { mpsCards, type MpCard } from "../api/client";
import { useScope } from "../hooks/useScope";
import ScopeControls from "../components/ScopeControls";
import HeroGraphic from "../components/HeroGraphic";
import InfoStat from "../components/InfoStat";
import AsyncState, { resolveViewState } from "../components/ui/AsyncState";

interface CompareRow {
  label: string;
  values: (string | number)[];
  highlight?: boolean;
}

export default function MpComparison() {
  const { t } = useTranslation();
  const scope = useScope();
  const [searches, setSearches] = useState<string[]>(["", "", ""]);
  const [selected, setSelected] = useState<(MpCard | null)[]>([
    null,
    null,
    null,
  ]);

  // Load a wide pool; selection is client-side over the pool.
  const pool = useQuery({
    queryKey: ["mps-pool", ...scope.scopeKey],
    queryFn: () => mpsCards({
      limit: 200, sort: "name",
      asOf: scope.date, chamber: scope.chamber, legislature: scope.legislature,
    }),
  });

  const poolList = useMemo(() => pool.data?.data ?? [], [pool.data]);

  const setSearch = (i: number, value: string) => {
    setSearches((prev) => {
      const next = [...prev];
      next[i] = value;
      return next;
    });
    // Clear the slot when the search text no longer matches the selection.
    setSelected((prev) => {
      const next = [...prev];
      if (next[i] && !value.trim()) next[i] = null;
      return next;
    });
  };

  const pick = (i: number, card: MpCard) => {
    setSelected((prev) => {
      const next = [...prev];
      next[i] = card;
      return next;
    });
    setSearches((prev) => {
      const next = [...prev];
      next[i] = card.name;
      return next;
    });
  };

  const clearSlot = (i: number) => {
    setSelected((prev) => {
      const next = [...prev];
      next[i] = null;
      return next;
    });
    setSearches((prev) => {
      const next = [...prev];
      next[i] = "";
      return next;
    });
  };

  const chosen = selected.filter((s): s is MpCard => s !== null);

  const suggestions = useMemo(() => {
    return searches.map((text, i) => {
      if (selected[i]) return [];
      const q = text.trim().toLowerCase();
      if (!q) return [];
      return poolList
        .filter((p) => p.name.toLowerCase().includes(q))
        .slice(0, 6);
    });
  }, [searches, poolList, selected]);

  const rows: CompareRow[] = useMemo(() => {
    if (chosen.length < 2) return [];
    return [
      {
        label: t("mpc.party", "Party"),
        values: chosen.map((c) => c.party ?? "—"),
      },
      {
        label: t("mpc.birth", "Birth date"),
        values: chosen.map((c) => c.birth_date ?? t("mpc.unknown", "unknown")),
      },
      {
        label: t("mpc.age", "Age"),
        values: chosen.map((c) =>
          c.age !== null ? `${c.age}` : t("mpc.unknown", "unknown"),
        ),
      },
      {
        label: t("mpc.switches", "Observed switches"),
        values: chosen.map((c) => c.switches),
        highlight: true,
      },
      {
        label: t("mpc.committees", "Committee seats"),
        values: chosen.map((c) => c.committees),
        highlight: true,
      },
    ];
  }, [chosen, t]);

  const view = resolveViewState({
    isLoading: pool.isLoading,
    isError: pool.isError,
    isEmpty: pool.isSuccess && poolList.length === 0,
  });
  if (view !== "ready") {
    return (
      <AsyncState
        view={view}
        pageTitle={t("mpc.title", "MP Comparison")}
        onRetry={() => void pool.refetch()}
        errorLabel={t("mpc.loadError", "Failed to load MP list.")}
        emptyTitle={t("mpc.pickTwo", "Pick at least two MPs to compare.")}
      />
    );
  }

  const maxSwitches = Math.max(...chosen.map((c) => c.switches), 0);
  const maxCommittees = Math.max(...chosen.map((c) => c.committees), 0);

  return (
    <div className="space-y-6">
      <ScopeControls showDate showChamber showLegislature note={t("scope.note.mpc")} />
      <section className="hero-section" data-enter>
        <div>
          <div className="flex flex-col md:flex-row md:items-center gap-8">
            <div className="flex-1 space-y-4">
              <h1 className="page-title">{t("mpc.title", "MP Comparison")}</h1>
              <p className="text-sm text-slate-300 mt-2">
                {t("mpc.intro")}
              </p>
            </div>
            <div className="w-full md:w-auto max-w-[260px]">
              <HeroGraphic variant="people" className="mx-auto" />
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
            <InfoStat
              label={t("mpcTotalMps", "MPs in corpus (search pool capped at 200)")}
              value={pool.data?.total ?? "--"}
              accent="sky"
            />
            <InfoStat
              label={t("mpcComparisonSlots", "Comparison slots")}
              value="3"
              accent="emerald"
            />
            <InfoStat
              label={t("mpcSelectedMps", "Selected MPs")}
              value={chosen.length}
              accent="amber"
            />
          </div>
          <div className="mt-8 flex items-center gap-4" data-moment>
            <span className="moment-value block">
              {pool.data?.total ?? "--"}
            </span>
            <span className="text-sm text-slate-400">
              {t("mpcTotalMpsLabel", "persons in corpus")}
            </span>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        {[0, 1, 2].map((i) => (
          <div key={i} className="bg-slate-800 rounded-lg p-4 relative">
            <div className="text-xs text-slate-500 mb-2">
              {t("mpc.slot", "Slot {{n}}", { n: i + 1 })}
            </div>
            {selected[i] ? (
              <div>
                <Link
                  to="/person/$id"
                  params={{ id: selected[i]!.id }}
                  search={scope.searchFor()}
                  className="text-slate-100 font-semibold hover:text-sky-300 hover:underline"
                >
                  {selected[i]!.name}
                </Link>
                <div className="mt-1 text-sm text-slate-400">
                  {selected[i]!.party ?? "—"} ·{" "}
                  {selected[i]!.age !== null
                    ? t("mpc.ageYears", "{{age}} yrs", { age: selected[i]!.age })
                    : t("mpc.unknown", "unknown")}
                </div>
                <button
                  type="button"
                  onClick={() => clearSlot(i)}
                  className="mt-2 text-xs text-slate-500 hover:text-slate-300 underline"
                >
                  {t("mpc.clear", "clear")}
                </button>
              </div>
            ) : (
              <div>
                <input
                  type="search"
                  value={searches[i]}
                  onChange={(e) => setSearch(i, e.target.value)}
                  placeholder={t("mpc.search", "Search name…")}
                  aria-label={t("mpc.searchSlot", "Search MP for slot {{n}}", {
                    n: i + 1,
                  })}
                  className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-slate-200"
                />
                {suggestions[i].length > 0 && (
                  <ul className="mt-2 bg-slate-900 rounded border border-slate-700 divide-y divide-slate-700/60">
                    {suggestions[i].map((s) => (
                      <li key={s.id}>
                        <button
                          type="button"
                          onClick={() => pick(i, s)}
                          className="w-full text-left px-3 py-2 text-sm text-slate-300 hover:bg-slate-800 focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400"
                        >
                          {s.name}
                          <span className="text-slate-500 ml-2">
                            {s.party ?? ""}
                          </span>
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {chosen.length >= 2 && (
        <div className="overflow-x-auto max-w-full" tabIndex={0} role="region" aria-label={t("mpc.title", "MP Comparison")}>
          <table className="min-w-full bg-slate-800 rounded-xl overflow-hidden data-table">
            <thead className="bg-slate-700">
              <tr>
                <th scope="col" className="px-4 py-3 text-left text-sm font-medium text-slate-300">
                  {t("mpc.col.metric", "Metric")}
                </th>
                {chosen.map((c) => (
                  <th
                    key={c.id}
                    scope="col"
                    className="px-4 py-3 text-center text-sm font-semibold text-slate-100"
                  >
                    {c.name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700">
              {rows.map((row) => (
                <tr key={row.label}>
                  <th scope="row" className="px-4 py-3 text-slate-400 font-normal text-left">{row.label}</th>
                  {row.values.map((v, idx) => (
                    <td
                      key={idx}
                      className={`px-4 py-3 text-center ${
                        row.highlight
                          ? "text-slate-100 font-semibold"
                          : "text-slate-200"
                      }`}
                    >
                      {v}
                      {row.label === t("mpc.switches", "Observed switches") &&
                        typeof v === "number" &&
                        maxSwitches > 0 && (
                          <div className="mt-1 bg-slate-700 rounded-full h-1.5 mx-auto max-w-[120px]">
                            <div
                              className="bg-amber-500 rounded-full h-1.5"
                              style={{ width: `${(v / maxSwitches) * 100}%` }}
                            />
                          </div>
                        )}
                      {row.label === t("mpc.committees", "Committee seats") &&
                        typeof v === "number" &&
                        maxCommittees > 0 && (
                          <div className="mt-1 bg-slate-700 rounded-full h-1.5 mx-auto max-w-[120px]">
                            <div
                              className="bg-sky-500 rounded-full h-1.5"
                              style={{
                                width: `${(v / maxCommittees) * 100}%`,
                              }}
                            />
                          </div>
                        )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {chosen.length < 2 && (
        <div className="text-slate-500">
          {t("mpc.pickTwo", "Pick at least two MPs to compare.")}
        </div>
      )}

      <div className="mt-6 bg-slate-800/50 rounded p-4 text-sm text-slate-400">
        <h2 className="text-slate-200 font-semibold mb-1">
          {t("mpc.notes", "Reading the numbers")}
        </h2>
        <p>
          {t(
            "mpc.notes.desc",
            "Switches are observed switch_group events from the chambers' ledgers. Committee seats count distinct committees in the 2024 legislature ingestion. Age is computed from the recorded birth date; 'unknown' means the source never published one.",
          )}
        </p>
      </div>
    </div>
  );
}
