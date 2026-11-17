import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { useRouter, useSearch } from "@tanstack/react-router";
import {
  api,
  traseismOverview,
  traseismSummary,
  traseismSwitches,
  switchWaves,
  type TraseismCoverage,
  type TraseismScope,
} from "../api/client";
import About from "../components/About";
import SankeyFlow from "../components/SankeyFlow";

/** In-repo methodology document (docs/METHODOLOGY.md). */
const METHODOLOGY_URL =
  "https://github.com/nedaktov-ops/parlament-deschis/blob/main/docs/METHODOLOGY.md";

const PAGE_SIZE = 25;

/**
 * Scope fallback: the legislature election calendar of Romania. It only seeds
 * the selector so every historical legislature stays selectable; the canonical
 * list comes from /api/meta and /api/traseism/overview.
 */
const LEGISLATURE_FALLBACK = [
  "1990",
  "1992",
  "1996",
  "2000",
  "2004",
  "2008",
  "2012",
  "2016",
  "2020",
  "2024",
];

const FOCUS =
  "focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400 focus-visible:outline-offset-2";

function fmtInt(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "—";
  return value.toLocaleString();
}

function fmtDecimal(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "—";
  return value.toLocaleString(undefined, { maximumFractionDigits: digits });
}

/**
 * The API may report the switch rate as a fraction (0.12) or as a percentage
 * (12.0). A rate above 1 cannot be a fraction, so values in [0, 1] are read as
 * fractions; the raw API value is always exposed in the tooltip.
 */
function fmtPercent(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "—";
  const percent = Math.abs(value) <= 1 ? value * 100 : value;
  return `${percent.toLocaleString(undefined, { maximumFractionDigits: 1 })}%`;
}

/** Signed number with an explicit sign glyph (never colour-only). */
function fmtSigned(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "—";
  if (value > 0) return `+${value}`;
  if (value < 0) return `−${Math.abs(value)}`;
  return "0";
}

function chamberLabel(chamber: string, t: (key: string) => string): string {
  return chamber === "deputies" || chamber === "senate" ? t(chamber) : chamber;
}

function completenessKey(value: string): "full" | "partial" | "none" {
  if (value === "full") return "full";
  if (value === "partial") return "partial";
  return "none";
}

function StatCard({
  label,
  value,
  hint,
  title,
}: {
  label: string;
  value: string;
  hint?: string;
  title?: string;
}) {
  return (
    <div className="bg-slate-800/50 rounded p-3">
      <div className="text-slate-500 text-xs">{label}</div>
      <div className="text-2xl font-bold text-slate-100" title={title}>
        {value}
      </div>
      {hint ? <div className="text-[11px] text-slate-500 mt-1">{hint}</div> : null}
    </div>
  );
}

function ErrorState({
  message,
  onRetry,
}: {
  message?: string;
  onRetry?: () => void;
}) {
  const { t } = useTranslation();
  return (
    <div
      className="rounded-lg border border-rose-700/60 bg-rose-950/30 px-4 py-3"
      role="alert"
    >
      <p className="text-sm text-rose-200">
        {message ?? t("traseismLoadError")}
      </p>
      {onRetry ? (
        <button type="button"onClick={onRetry}
          className={`btn mt-2 bg-slate-700 hover:bg-slate-600 ${FOCUS}`}
        >
          {t("traseismRetry")}
        </button>
      ) : null}
    </div>
  );
}

function CoverageBanner({ coverage }: { coverage?: TraseismCoverage }) {
  const { t } = useTranslation();
  const key = completenessKey(coverage?.completeness ?? "none");
  const tone =
    key === "full"
      ? "border-emerald-700/60 bg-emerald-950/30 text-emerald-100"
      : key === "partial"
        ? "border-amber-600/70 bg-amber-950/30 text-amber-100"
        : "border-rose-700/70 bg-rose-950/30 text-rose-100";
  const headline =
    key === "full"
      ? t("traseismCoverageFull")
      : key === "partial"
        ? t("traseismCoveragePartial")
        : t("traseismCoverageNone");

  return (
    <div className={`rounded-lg border px-4 py-3 ${tone}`} role="status">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs uppercase tracking-wide opacity-80">
          {t("coverage")}
        </span>
        <span className="text-sm font-semibold">{t(key)}</span>
      </div>
      <p className="text-sm mt-1">{headline}</p>
      {coverage?.note ? (
        <p className="text-xs mt-1 opacity-90">{coverage.note}</p>
      ) : null}
    </div>
  );
}

function MatrixTable({ scope }: { scope: TraseismScope }) {
  const { t } = useTranslation();

  const { rows, cols, counts } = useMemo(() => {
    const froms = new Set<string>();
    const tos = new Set<string>();
    const map = new Map<string, number>();
    for (const cell of scope.matrix ?? []) {
      if (!cell?.from || !cell?.to) continue;
      froms.add(cell.from);
      tos.add(cell.to);
      map.set(`${cell.from}\u0000${cell.to}`, cell.count ?? 0);
    }
    return {
      rows: [...froms].sort((a, b) => a.localeCompare(b)),
      cols: [...tos].sort((a, b) => a.localeCompare(b)),
      counts: map,
    };
  }, [scope.matrix]);

  if (rows.length === 0 || cols.length === 0) {
    return <div className="text-slate-500 text-sm py-4">{t("noData")}</div>;
  }

  return (
    <div className="overflow-x-auto" tabIndex={0} role="region" aria-label={t("traseismMatrixCaption")}>
      <table className="w-full text-xs border-collapse">
        <caption className="sr-only">{t("traseismMatrixCaption")}</caption>
        <thead>
          <tr className="text-left text-slate-500">
            <th scope="col" className="py-1 pr-3 font-medium">
              {t("traseismFromGroup")}
            </th>
            {cols.map((col) => (
              <th key={col} scope="col" className="py-1 pr-3 font-medium">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row} className="border-t border-slate-700/60">
              <th scope="row" className="py-1.5 pr-3 text-left font-medium text-slate-200">
                {row}
              </th>
              {cols.map((col) => (
                <td key={col} className="py-1.5 pr-3 font-mono text-slate-300">
                  {counts.get(`${row}\u0000${col}`) ?? 0}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function PartyNetTable({ scope }: { scope: TraseismScope }) {
  const { t } = useTranslation();
  const rows = scope.by_party ?? [];

  if (rows.length === 0) {
    return <div className="text-slate-500 text-sm py-4">{t("noData")}</div>;
  }

  return (
    <div className="overflow-x-auto" tabIndex={0} role="region" aria-label={t("traseismPartyNetCaption")}>
      <table className="w-full text-xs border-collapse">
        <caption className="sr-only">{t("traseismPartyNetCaption")}</caption>
        <thead>
          <tr className="text-left text-slate-500">
            <th scope="col" className="py-1 pr-3 font-medium">
              {t("party")}
            </th>
            <th scope="col" className="py-1 pr-3 font-medium">
              {t("traseismGains")}
            </th>
            <th scope="col" className="py-1 pr-3 font-medium">
              {t("traseismLosses")}
            </th>
            <th scope="col" className="py-1 pr-3 font-medium">
              {t("netChange")}
            </th>
            <th scope="col" className="py-1 pr-3 font-medium">
              {t("traseismSeatsStart")}
            </th>
            <th scope="col" className="py-1 font-medium">
              {t("traseismSeatsEnd")}
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const net = row.net ?? 0;
            const netLabel =
              net > 0
                ? t("traseismNetGain")
                : net < 0
                  ? t("traseismNetLoss")
                  : t("traseismNetFlat");
            return (
              <tr
                key={row.party}
                className="border-t border-slate-700/60 align-top"
              >
                <th scope="row" className="py-1.5 pr-3 text-left font-medium text-slate-200">
                  {row.party}
                </th>
                <td className="py-1.5 pr-3 font-mono text-slate-300">
                  {fmtInt(row.gains)}
                </td>
                <td className="py-1.5 pr-3 font-mono text-slate-300">
                  {fmtInt(row.losses)}
                </td>
                <td className="py-1.5 pr-3 font-mono text-slate-200">
                  <span>{fmtSigned(net)}</span>{" "}
                  <span className="text-[11px] text-slate-400">({netLabel})</span>
                </td>
                <td className="py-1.5 pr-3 font-mono text-slate-300">
                  {fmtInt(row.seats_start)}
                </td>
                <td className="py-1.5 font-mono text-slate-300">
                  {fmtInt(row.seats_end)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function SwitchLedger({
  legislature,
  chamber,
}: {
  legislature: string;
  chamber: string;
}) {
  const { t } = useTranslation();
  const [page, setPage] = useState(0);

  useEffect(() => {
    setPage(0);
  }, [legislature, chamber]);

  const query = useQuery({
    queryKey: ["traseism-switches", legislature, chamber, page],
    queryFn: () =>
      traseismSwitches({
        legislature,
        chamber,
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
      }),
  });

  const rows = query.data?.rows ?? [];
  const total = query.data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const from = total === 0 ? 0 : page * PAGE_SIZE + 1;
  const to = Math.min((page + 1) * PAGE_SIZE, total);

  return (
    <section className="card p-4">
      <h2 className="font-semibold">{t("traseismLedgerTitle")}</h2>
      <p className="text-sm text-slate-400 mt-1 mb-3">
        {t("traseismLedgerDesc")}
      </p>

      {query.isLoading ? (
        <div className="text-slate-500 text-sm py-6">{t("loading")}</div>
      ) : query.isError ? (
        <ErrorState onRetry={() => query.refetch()} />
      ) : rows.length === 0 ? (
        <div className="text-slate-500 text-sm py-6">{t("traseismNoRows")}</div>
      ) : (
        <>
          <div className="overflow-x-auto" tabIndex={0} role="region" aria-label={t("traseismLedgerCaption")}>
            <table className="w-full text-xs border-collapse">
              <caption className="sr-only">{t("traseismLedgerCaption")}</caption>
              <thead>
                <tr className="text-left text-slate-500">
                  <th scope="col" className="py-1 pr-3 font-medium">
                    {t("person")}
                  </th>
                  <th scope="col" className="py-1 pr-3 font-medium">
                    {t("traseismFromGroup")}
                  </th>
                  <th scope="col" className="py-1 pr-3 font-medium">
                    {t("traseismToGroup")}
                  </th>
                  <th scope="col" className="py-1 pr-3 font-medium">
                    {t("traseismDate")}
                  </th>
                  <th scope="col" className="py-1 font-medium">
                    {t("sources")}
                  </th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row, index) => (
                  <tr
                    key={`${row.person_id}-${row.date ?? "nd"}-${index}`}
                    className="border-t border-slate-700/60 align-top"
                  >
                    <td className="py-1.5 pr-3 text-slate-200">{row.name}</td>
                    <td className="py-1.5 pr-3 text-slate-300">
                      {row.from_group ?? "—"}
                    </td>
                    <td className="py-1.5 pr-3 text-slate-300">
                      {row.to_group ?? "—"}
                    </td>
                    <td
                      className="py-1.5 pr-3 font-mono text-slate-300"
                      title={
                        row.precision
                          ? t("traseismPrecisionLabel", { value: row.precision })
                          : undefined
                      }
                    >
                      {row.date ? (
                        <>
                          {row.precision && row.precision !== "day" ? "≈ " : ""}
                          {row.date}
                        </>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="py-1.5">
                      {row.source_url ? (
                        <a
                          href={row.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className={`text-sky-400 hover:text-sky-300 hover:underline ${FOCUS}`}
                        >
                          {t("traseismOfficialSource")} ↗
                        </a>
                      ) : (
                        <span className="text-slate-500">
                          {t("traseismNoSource")}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-2 mt-3 text-xs text-slate-400">
            <span>{t("traseismShowing", { from, to, total })}</span>
            <div className="flex items-center gap-2">
              <button type="button"onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className={`btn bg-slate-700 hover:bg-slate-600 text-slate-300 disabled:opacity-40 disabled:cursor-not-allowed ${FOCUS}`}
              >
                {t("traseismPreviousPage")}
              </button>
              <span>{t("traseismPage", { page: page + 1, pages: totalPages })}</span>
              <button type="button"onClick={() => setPage((p) => p + 1)}
                disabled={(page + 1) * PAGE_SIZE >= total}
                className={`btn bg-slate-700 hover:bg-slate-600 text-slate-300 disabled:opacity-40 disabled:cursor-not-allowed ${FOCUS}`}
              >
                {t("traseismNextPage")}
              </button>
            </div>
          </div>
        </>
      )}
    </section>
  );
}

function ScopesOverview({ rows }: { rows: TraseismScope[] }) {
  const { t } = useTranslation();
  type ScopeSortKey =
    | "chamber"
    | "legislature"
    | "members"
    | "switches"
    | "switchers"
    | "switch_rate"
    | "switches_per_100_members";
  const [sortKey, setSortKey] = useState<ScopeSortKey | null>("switch_rate");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const sortedRows = useMemo(() => {
    if (!sortKey) return rows;
    return [...rows].sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (av === null || av === undefined) return 1;
      if (bv === null || bv === undefined) return -1;
      const order =
        typeof av === "string" && typeof bv === "string"
          ? av.localeCompare(bv)
          : typeof av === "number" && typeof bv === "number"
            ? av - bv
            : 0;
      return sortDir === "asc" ? order : -order;
    });
  }, [rows, sortKey, sortDir]);

  if (rows.length === 0) {
    return <div className="text-slate-300 text-sm py-4">{t("noData")}</div>;
  }

  const sortableHeader = (key: ScopeSortKey, label: string) => {
    const isSorted = sortKey === key;
    return (
      <th
        key={key}
        scope="col"
        aria-sort={isSorted ? (sortDir === "asc" ? "ascending" : "descending") : "none"}
        className="py-1 pr-3 font-medium"
      >
        <button type="button"className={`flex items-center gap-1 rounded px-1 py-1 text-left hover:bg-slate-700/50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400 ${
            isSorted ? "text-slate-100" : "text-slate-300"
          }`}
          onClick={() => {
            if (sortKey === key) {
              setSortDir(sortDir === "asc" ? "desc" : "asc");
            } else {
              setSortKey(key);
              setSortDir("desc");
            }
          }}
        >
          {label}
          {isSorted && (
            <span aria-hidden="true" className="text-sky-300">
              {sortDir === "asc" ? "\u25B2" : "\u25BC"}
            </span>
          )}
        </button>
      </th>
    );
  };

  return (
    <div className="overflow-x-auto" tabIndex={0} role="region" aria-label={t("traseismAllScopesCaption")}>
      <table className="w-full text-xs border-collapse">
        <caption className="sr-only">{t("traseismAllScopesCaption")}</caption>
        <thead>
          <tr className="text-left text-slate-500">
            {sortableHeader("chamber", t("chamber"))}
            {sortableHeader("legislature", t("legislature"))}
            {sortableHeader("members", t("traseismMembersDenominator"))}
            {sortableHeader("switches", t("traseismSwitchesCount"))}
            {sortableHeader("switchers", t("traseismSwitchersCount"))}
            {sortableHeader("switch_rate", t("traseismSwitchRate"))}
            {sortableHeader("switches_per_100_members", t("traseismPer100"))}
            <th scope="col" className="py-1 font-medium">
              {t("coverage")}
            </th>
          </tr>
        </thead>
        <tbody>
          {sortedRows.map((row) => {
            const key = completenessKey(row.coverage?.completeness ?? "none");
            const metric = (value: string) =>
              key === "none" ? (
                <>
                  <span className="sr-only">{t("none")}</span>
                  <span aria-hidden="true">—</span>
                </>
              ) : (
                value
              );
            return (
              <tr
                key={`${row.chamber}-${row.legislature}`}
                className="border-t border-slate-700/60 align-top"
              >
                <td className="py-1.5 pr-3 text-slate-200">
                  {chamberLabel(row.chamber, t)}
                </td>
                <td className="py-1.5 pr-3 font-mono text-slate-300">
                  {row.legislature}
                </td>
                <td className="py-1.5 pr-3 font-mono text-slate-300">
                  {metric(fmtInt(row.members))}
                </td>
                <td className="py-1.5 pr-3 font-mono text-slate-300">
                  {metric(fmtInt(row.switches))}
                </td>
                <td className="py-1.5 pr-3 font-mono text-slate-300">
                  {metric(fmtInt(row.switchers))}
                </td>
                <td className="py-1.5 pr-3 font-mono text-slate-300">
                  {metric(fmtPercent(row.switch_rate))}
                </td>
                <td className="py-1.5 pr-3 font-mono text-slate-300">
                  {metric(fmtDecimal(row.switches_per_100_members))}
                </td>
                <td className="py-1.5">
                  <span
                    className={`rounded px-2 py-0.5 ${
                      key === "full"
                        ? "bg-emerald-900/50 text-emerald-300"
                        : key === "partial"
                          ? "bg-amber-900/50 text-amber-300"
                          : "bg-slate-800 text-slate-400"
                    }`}
                  >
                    {t(key)}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

/**
 * Feature 11: switch waves — detected bursts of affiliation change.
 * Read-only view of /analytics/switch-waves; filtered to the active scope.
 */
function SwitchWavesSection({
  chamber,
  legislature,
}: {
  chamber: string;
  legislature: string;
}) {
  const { t } = useTranslation();
  const waves = useQuery({
    queryKey: ["switch-waves", chamber, legislature],
    queryFn: () => switchWaves(chamber, legislature),
  });

  const rows = (waves.data ?? []).slice(0, 10);

  return (
    <section className="card p-4">
      <h2 className="font-semibold">{t("waves.title", "Switch waves")}</h2>
      <p className="text-sm text-slate-400 mt-1 mb-3">
        {t(
          "waves.desc",
          "Periods where affiliation changes clustered (30-day windows, 3+ switches). Election and coalition triggers are annotated when the corpus records them.",
        )}
      </p>
      {waves.isLoading ? (
        <div className="text-slate-500 text-sm py-4">{t("loading")}</div>
      ) : waves.isError ? (
        <div className="text-red-400 text-sm py-4">
          {t("waves.error", "Failed to load waves.")}
        </div>
      ) : rows.length === 0 ? (
        <div className="text-slate-500 text-sm py-4">
          {t("waves.empty", "No waves detected for this scope.")}
        </div>
      ) : (
        <div className="overflow-x-auto" tabIndex={0} role="region" aria-label={t("waves.title", "Switch waves")}>
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-slate-400 border-b border-slate-700">
                <th scope="col" className="py-2 pr-4">{t("waves.col.period", "Period")}</th>
                <th scope="col" className="py-2 pr-4 text-right">
                  {t("waves.col.count", "Switches")}
                </th>
                <th scope="col" className="py-2 pr-4">{t("waves.col.trigger", "Trigger")}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((w) => (
                <tr key={w.id} className="border-b border-slate-700/50">
                  <th scope="row" className="py-2 pr-4 text-slate-300 font-normal text-left">
                    {w.start_date ?? "?"} → {w.end_date ?? "?"}
                  </th>
                  <td className="py-2 pr-4 text-right">
                    <span className="bg-amber-900/40 text-amber-300 px-2 py-0.5 rounded">
                      {w.switch_count}
                    </span>
                  </td>
                  <td className="py-2 pr-4 text-slate-400">
                    {w.trigger_type ?? "—"}
                    {w.trigger_event ? ` (${w.trigger_event})` : ""}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export function Traseism() {
  const { t } = useTranslation();
  const router = useRouter();
  const search = useSearch({ from: "/traseism" });
  const [aboutOpen, setAboutOpen] = useState(false);

  const chamber = search.chamber === "senate" ? "senate" : "deputies";
  const meta = useQuery({ queryKey: ["meta"], queryFn: api.meta });
  const matchingLegislature = Object.entries(meta.data?.legislatures ?? {})
    .filter(([, term]) =>
      term.start !== null &&
      term.start <= search.date &&
      (term.end === null || term.end >= search.date),
    )
    .sort((a, b) => (b[1].start ?? "").localeCompare(a[1].start ?? ""))[0]?.[0];
  const legislature = search.legislature ?? matchingLegislature ?? "2024";

  useEffect(() => {
    if (!search.legislature && matchingLegislature) {
      router.navigate({
        to: "/traseism",
        search: { ...search, legislature: matchingLegislature },
        replace: true,
      });
    }
  }, [matchingLegislature, router, search]);

  const overview = useQuery({
    queryKey: ["traseism-overview"],
    queryFn: traseismOverview,
  });
  const summary = useQuery({
    queryKey: ["traseism-summary", legislature, chamber],
    queryFn: () => traseismSummary(legislature, chamber),
    enabled: Boolean(search.legislature || meta.data || meta.isError),
  });

  const legislatureOptions = useMemo(() => {
    const years = new Set<string>(LEGISLATURE_FALLBACK);
    for (const key of Object.keys(meta.data?.legislatures ?? {})) {
      if (/^\d{4}$/.test(key)) years.add(key);
    }
    for (const row of overview.data ?? []) {
      if (/^\d{4}$/.test(row.legislature)) years.add(row.legislature);
    }
    return [...years].sort((a, b) => b.localeCompare(a));
  }, [meta.data, overview.data]);

  const scope = summary.data;
  const coverageKey = completenessKey(scope?.coverage?.completeness ?? "none");
  const hasRecord = coverageKey !== "none";

  const setScope = (next: { chamber?: string; legislature?: string }) => {
    router.navigate({ to: "/traseism", search: { ...search, ...next } });
  };

  return (
    <div className="space-y-4">
      <section className="card p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="max-w-3xl">
            <h1 className="text-2xl font-bold">{t("traseismTitle")}</h1>
            <p className="text-sm text-slate-300 mt-2">
              {t("traseismHeadline")}
            </p>
            <p className="text-sm text-slate-400 mt-1">{t("traseismIntro")}</p>
            <p className="text-sm text-slate-200 mt-2 font-medium">
              {t("traseismNotMotive")}
            </p>
          </div>
          <button type="button"onClick={() => setAboutOpen(true)}
            className={`btn bg-slate-700 hover:bg-slate-600 shrink-0 ${FOCUS}`}
          >
            {t("traseismAboutButton")}
          </button>
        </div>
        <div className="mt-4 text-sm">
          <a
            href={METHODOLOGY_URL}
            target="_blank"
            rel="noopener noreferrer"
            className={`text-sky-400 hover:text-sky-300 hover:underline ${FOCUS}`}
          >
            {t("traseismMethodologyLink")} ↗
          </a>
        </div>
      </section>

      <section className="card p-4">
        <h2 className="font-semibold mb-3">{t("traseismScopeTitle")}</h2>
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <div
              id="traseism-chamber-label"
              className="text-xs text-slate-500 mb-1"
            >
              {t("chamber")}
            </div>
            <div
              className="flex gap-1"
              role="group"
              aria-labelledby="traseism-chamber-label"
            >
              {(["deputies", "senate"] as const).map((c) => (
                <button type="button"key={c}onClick={() => setScope({ chamber: c })}
                  aria-pressed={chamber === c}
                  className={`btn ${
                    chamber === c
                      ? "bg-sky-700 text-white"
                      : "bg-slate-700 hover:bg-slate-600 text-slate-200"
                  } ${FOCUS}`}
                >
                  {t(c)}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label
              htmlFor="traseism-legislature"
              className="block text-xs text-slate-500 mb-1"
            >
              {t("legislature")}
            </label>
            <select
              id="traseism-legislature"
              value={legislature}
              onChange={(e) => setScope({ legislature: e.target.value })}
              className={`bg-slate-800 border border-slate-700 rounded-md px-3 py-1.5 text-sm ${FOCUS}`}
            >
              {legislatureOptions.map((year) => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </select>
          </div>
          {scope?.period ? (
            <div className="text-xs text-slate-400">
              {t("period")}: {scope.period.start ?? "—"} →{" "}
              {scope.period.end ?? t("present")}
            </div>
          ) : null}
        </div>
      </section>

      {summary.isLoading ? (
        <div className="card p-4">
          <div className="text-slate-500 text-sm py-8">{t("loading")}</div>
        </div>
      ) : summary.isError || !scope ? (
        <ErrorState onRetry={() => summary.refetch()} />
      ) : (
        <>
          <CoverageBanner coverage={scope.coverage} />

          {hasRecord ? (
            <>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
                <StatCard
                  label={t("traseismMembersDenominator")}
                  value={fmtInt(scope.members)}
                />
                <StatCard
                  label={t("traseismSwitchesCount")}
                  value={fmtInt(scope.switches)}
                />
                <StatCard
                  label={t("traseismSwitchersCount")}
                  value={fmtInt(scope.switchers)}
                />
                <StatCard
                  label={t("traseismSwitchRate")}
                  value={fmtPercent(scope.switch_rate)}
                  title={t("traseismRawValue", { value: scope.switch_rate })}
                />
                <StatCard
                  label={t("traseismPer100")}
                  value={fmtDecimal(scope.switches_per_100_members)}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <StatCard
                  label={t("traseismRepeatSwitchers")}
                  value={fmtInt(scope.repeat_switchers?.people)}
                />
                <StatCard
                  label={t("traseismMaxSwitches")}
                  value={fmtInt(scope.repeat_switchers?.max_switches)}
                />
                <StatCard
                  label={t("traseismMedianMonths")}
                  value={fmtDecimal(scope.timing?.median_months)}
                />
              </div>

              <section className="card p-4">
                <h2 className="font-semibold">{t("defections")}</h2>
                <p className="text-sm text-slate-400 mt-1 mb-3">
                  {t("traseismFlowDesc")}
                </p>
                <SankeyFlow chamber={chamber} legislature={legislature} />
              </section>

              <section className="card p-4">
                <h2 className="font-semibold">{t("traseismMatrixTitle")}</h2>
                <p className="text-sm text-slate-400 mt-1 mb-3">
                  {t("traseismMatrixDesc")}
                </p>
                <MatrixTable scope={scope} />
              </section>

              <section className="card p-4">
                <h2 className="font-semibold">{t("traseismPartyNetTitle")}</h2>
                <p className="text-sm text-slate-400 mt-1 mb-3">
                  {t("traseismPartyNetDesc")}
                </p>
                <PartyNetTable scope={scope} />
              </section>
            </>
          ) : null}

          <SwitchLedger legislature={legislature} chamber={chamber} />

          <SwitchWavesSection chamber={chamber} legislature={legislature} />
        </>
      )}

      <section className="card p-4">
        <h2 className="font-semibold">{t("traseismAllScopes")}</h2>
        <p className="text-sm text-slate-400 mt-1 mb-3">
          {t("traseismAllScopesDesc")}
        </p>
        {overview.isLoading ? (
          <div className="text-slate-500 text-sm py-4">{t("loading")}</div>
        ) : overview.isError ? (
          <ErrorState onRetry={() => overview.refetch()} />
        ) : (
          <ScopesOverview rows={overview.data ?? []} />
        )}
      </section>

      <section className="card p-4">
        <h2 className="font-semibold">{t("traseismMethodology")}</h2>
        <p className="text-sm text-slate-400 mt-2 leading-relaxed">
          {t("traseismMethodologyBody")}
        </p>
        <a
          href={METHODOLOGY_URL}
          target="_blank"
          rel="noopener noreferrer"
          className={`inline-block mt-3 text-sm text-sky-400 hover:text-sky-300 hover:underline ${FOCUS}`}
        >
          {t("traseismMethodologyLink")} ↗
        </a>
      </section>

      <About open={aboutOpen} onClose={() => setAboutOpen(false)} />
    </div>
  );
}
