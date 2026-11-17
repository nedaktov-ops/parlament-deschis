import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { get } from "../api/client";

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

  const timeline = useQuery({
    queryKey: ["party-timeline"],
    queryFn: fetchTimeline,
  });

  const rows = timeline.data?.data ?? [];
  const gaps = timeline.data?.gaps;
  // Derive the dated-join total from the rows already fetched by this page.
  const datedJoins = rows.reduce((sum, p) => sum + p.dated_joins, 0);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-slate-100 mb-2">
        {t("ptimeline.title", "Party Timeline")}
      </h1>
      <p className="text-slate-400 mb-6">
        {t(
          "ptimeline.intro",
          "When each party is observed in parliament: first and last dated join on behalf of the party. Bars show observed presence in the record — not official founding or dissolution dates.",
        )}
      </p>

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
          className="bg-slate-800 rounded-lg p-4 overflow-x-auto"
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
