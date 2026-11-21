import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { Link } from "@tanstack/react-router";
import { get } from "../api/client";
import { useScope } from "../hooks/useScope";
import ScopeControls from "../components/ScopeControls";
import HeroGraphic from "../components/HeroGraphic";
import InfoStat from "../components/InfoStat";
import { Sparkline } from "../components/DataViz";

interface PartySpan {
  party: string;
  name: string;
  founding_date: string | null;
  first_join: string | null;
  last_join: string | null;
  dated_joins: number;
}

interface PartyTimelineResponse {
  status: string;
  data: PartySpan[];
  gaps: {
    predecessor_links: number;
    successor_links: number;
    dissolution_dates: number;
    note: string;
  };
}

const MIN_YEAR = 1990;
const MAX_YEAR = 2027;

function yearOf(iso: string | null): number | null {
  if (!iso) return null;
  const y = Number(iso.slice(0, 4));
  return Number.isFinite(y) ? y : null;
}

function pct(year: number): number {
  return ((year - MIN_YEAR) / (MAX_YEAR - MIN_YEAR)) * 100;
}

function fetchTimeline(): Promise<PartyTimelineResponse> {
  return get<PartyTimelineResponse>("/analytics/party-timeline");
}

export default function PartyTimeline() {
  const { t } = useTranslation();
  const scope = useScope();

  const timeline = useQuery({
    queryKey: ["party-timeline", ...scope.scopeKey],
    queryFn: fetchTimeline,
  });

  const rows = useMemo(() => timeline.data?.data ?? [], [timeline.data]);
  const gaps = timeline.data?.gaps;
  // Derive the dated-join total from the rows already fetched by this page.
  const datedJoins = rows.reduce((sum, p) => sum + p.dated_joins, 0);

  // Distinct first-join years observed across parties (legislature proxy).
  const legislaturesCovered = new Set(
    rows.map((p) => yearOf(p.first_join)).filter((y): y is number => y !== null),
  ).size;

  // Total declared gap events (predecessor + successor links + dissolution dates).
  const gapsCount = gaps
    ? gaps.predecessor_links + gaps.successor_links + gaps.dissolution_dates
    : 0;

  // Party count observed per year across the full span (sparkline source).
  const sparklineData = useMemo(() => {
    if (rows.length === 0) return [];
    const years = Array.from(
      { length: MAX_YEAR - MIN_YEAR + 1 },
      (_, i) => MIN_YEAR + i,
    );
    return years.map((y) =>
      rows.filter((p) => {
        const start = yearOf(p.first_join);
        const end = yearOf(p.last_join) ?? MAX_YEAR;
        return start !== null && start <= y && y <= end;
      }).length,
    );
  }, [rows]);

  return (
    <div className="py-6">
      <ScopeControls note={t("scope.note.partyTimeline")} />
      {/* H2-O Hero section — fills the first screen alone */}
      <section className="hero-section" data-enter>
        <div>
          <div className="flex flex-col md:flex-row md:items-center gap-8">
            <div className="flex-1 space-y-4">
              <h1 className="page-title">
                {t("ptimeline.title", "Party Timeline")}
              </h1>
              <p className="text-sm text-slate-400">
                {t(
                  "ptimeline.intro",
                  "When each party is observed in parliament: first and last dated join on behalf of the party. Bars show observed presence in the record — not official founding or dissolution dates.",
                )}
              </p>
              <p className="text-sm">
                <Link
                  to="/parties"
                  search={scope.searchFor()}
                  className="text-sky-400 hover:underline"
                >
                  {t("ptimeline.viewAllParties", "View all parties →")}
                </Link>
              </p>
              <div
                className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-6"
              >
                <InfoStat
                  label={t("ptimeline.statParties", "Total parties")}
                  value={rows.length}
                  accent="sky"
                />
                <InfoStat
                  label={t("ptimeline.statSwitches", "Dated joins in range")}
                  value={datedJoins}
                  accent="emerald"
                />
                <InfoStat
                  label={
                    t("ptimeline.statLegislatures", "Legislatures covered")
                  }
                  value={legislaturesCovered}
                  accent="amber"
                />
                <InfoStat
                  label={t("ptimeline.statGaps", "Gap events")}
                  value={gapsCount}
                  accent="rose"
                  showBar={false}
                />
              </div>
              <div className="mt-8 flex items-center gap-4" data-moment>
                <span className="moment-value block">
                  {rows.length}
                </span>
                <span className="text-sm text-slate-400">
                  {t("ptimeline.parties", "parties in the corpus")}
                </span>
              </div>
            </div>
            <div className="w-full md:w-auto max-w-[260px]">
              <HeroGraphic variant="wave" className="mx-auto" />
              {sparklineData.length > 0 && (
                <div className="mt-6 sparkline">
                  <Sparkline
                    data={sparklineData}
                    height={40}
                    color="stroke-sky-400"
                  />
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {gaps && (
        <div
          role="note"
          className="mb-6 bg-amber-950/30 border border-amber-700/50 rounded p-4 text-sm text-amber-200"
        >
          <h2 className="font-semibold mb-1">
            {t("ptimeline.gapTitle", "Declared-data gap")}
          </h2>
          <p>
            {t(
              "ptimeline.gapBody",
              "Predecessor/successor links: {{pred}} · dissolution dates: {{diss}}. Mergers and splits are NOT machine-declared in this corpus — where one party's span ends and another's begins (e.g. PDSR → PSD), the succession is visible but never asserted.",
              { pred: gaps.predecessor_links, diss: gaps.dissolution_dates },
            )}
          </p>
        </div>
      )}

      {timeline.isLoading && (
        <div className="text-slate-500">{t("loading", "Loading…")}</div>
      )}
      {timeline.isError && (
        <div className="text-red-400">
          {t("ptimeline.loadError", "Failed to load the timeline.")}
        </div>
      )}

      {rows.length > 0 && (
        <div
          className="bg-slate-800 rounded-lg p-4 overflow-x-auto max-w-full"
          tabIndex={0}
          role="region"
          aria-label={t("ptimeline.title", "Party Timeline")}
        >
          {/* Year axis */}
          <div className="relative h-6 mb-2 min-w-[720px]">
            {[1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025].map((y) => (
              <span
                key={y}
                className="absolute top-0 text-xs text-slate-500 -translate-x-1/2"
                style={{ left: `${pct(y)}%` }}
              >
                {y}
              </span>
            ))}
          </div>

          <div className="space-y-1.5 min-w-[720px]">
            {rows.map((p) => {
              const start = yearOf(p.first_join);
              const end = yearOf(p.last_join);
              if (start === null) return null;
              const endYear = end ?? start;
              const left = pct(start);
              const width = Math.max(pct(endYear) - pct(start), 0.6);
              const ongoing = end !== null && end >= 2026;
              return (
                <div key={p.party} className="flex items-center gap-3">
                  <span
                    className="w-24 shrink-0 text-sm text-slate-300 text-right truncate"
                    title={p.name}
                  >
                    {p.party}
                  </span>
                  <div className="relative flex-1 h-5 bg-slate-900/60 rounded">
                    <div
                      className={`absolute inset-y-1 rounded ${
                        ongoing ? "bg-sky-500" : "bg-slate-500"
                      }`}
                      style={{ left: `${left}%`, width: `${width}%` }}
                      title={`${p.first_join} → ${p.last_join} (${p.dated_joins} dated joins)`}
                    />
                  </div>
                  <span className="w-40 shrink-0 text-xs text-slate-500 font-mono">
                    {p.first_join} → {p.last_join}
                  </span>
                  <span className="w-16 shrink-0 text-xs text-slate-400 text-right">
                    {p.dated_joins}
                  </span>
                </div>
              );
            })}
          </div>

          <div className="mt-3 flex gap-4 text-xs text-slate-500">
            <span className="flex items-center gap-1.5">
              <span className="inline-block w-3 h-3 rounded bg-sky-500" />
              {t("ptimeline.ongoing", "join observed through 2026")}
            </span>
            <span className="flex items-center gap-1.5">
              <span className="inline-block w-3 h-3 rounded bg-slate-500" />
              {t("ptimeline.ended", "no join observed after last date")}
            </span>
          </div>
        </div>
      )}

      {rows.length === 0 && !timeline.isLoading && !timeline.isError && (
        <div className="text-slate-500">{t("ptimeline.empty", "No dated party spans.")}</div>
      )}

      <div className="mt-6 bg-slate-800/50 rounded p-4 text-sm text-slate-400">
        <h2 className="text-slate-200 font-semibold mb-1">
          {t("ptimeline.methodology", "Methodology")}
        </h2>
        <p>
          {t("ptimeline.methodology.desc", { datedJoins })}
        </p>
      </div>
    </div>
  );
}
