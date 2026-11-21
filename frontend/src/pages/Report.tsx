import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { get } from "../api/client";
import HeroGraphic from "../components/HeroGraphic";
import { InfoStat } from "../components/InfoStat";
import { Sparkline, ProgressRing } from "../components/DataViz";

interface ReportTopSwitcher {
  person_id: string;
  name: string;
  switches: number;
  first_switch: string | null;
  last_switch: string | null;
  loyalty_score: number;
}

interface ReportControl {
  total_committees: number;
  parties: { party: string; chairs: number; share_pct: number }[];
}

interface ReportWave {
  start_date: string | null;
  end_date: string | null;
  switch_count: number;
  trigger_type: string | null;
  trigger_event: string | null;
  chamber: string | null;
  legislature: string | null;
}

interface ReportAge {
  party: string;
  mps_with_birth_dates: number;
  avg_age: number;
  median_age: number;
}

interface TransparencyReport {
  report: string;
  generated_at: string;
  totals: {
    persons: number;
    memberships: number;
    events: number;
    switches: number;
    committees: number;
    persons_with_birth_date: number;
  };
  coverage: {
    chamber: string;
    legislature: string | null;
    completeness: string;
    note: string | null;
  }[];
  top_switchers: ReportTopSwitcher[];
  committee_control: ReportControl;
  switch_waves: ReportWave[];
  party_ages: ReportAge[];
}

function fetchReport(): Promise<TransparencyReport> {
  return get<TransparencyReport>("/export/report");
}

export default function Report() {
  const { t, i18n } = useTranslation();

  const report = useQuery({
    queryKey: ["transparency-report"],
    queryFn: fetchReport,
  });

  const d = report.data;

  const statMax = d
    ? Math.max(
        d.totals.persons,
        d.totals.memberships,
        d.totals.events,
        d.totals.switches,
        d.totals.committees,
        d.totals.persons_with_birth_date,
      )
    : 0;

  const completenessColor = (c: string): string =>
    c === "full"
      ? "text-emerald-600 print:text-emerald-700"
      : c === "partial"
        ? "text-amber-600 print:text-amber-700"
        : "text-slate-500";

  const completenessValue = (c: string): number =>
    c === "full" ? 100 : c === "partial" ? 60 : 0;

  const completenessRingColor = (c: string): string =>
    c === "full"
      ? "stroke-emerald-400"
      : c === "partial"
        ? "stroke-amber-400"
        : "stroke-slate-400";

  return (
    <div className="py-6 print:p-0">
      <div
        className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6 lg:gap-10 mb-8 sm:mb-10 print:mb-4 print:block"
        data-enter
      >
        <div className="flex-1 min-w-0 space-y-3">
          <h1 className="page-title print:text-slate-900">
            {t("report.title", "Transparency Report")}
          </h1>
          <p className="text-slate-400 print:text-slate-600 text-sm sm:text-base mt-1 max-w-2xl leading-relaxed">
            {t(
              "report.subtitle",
              "One-page summary of what the corpus contains — for journalists and citizens.",
            )}
          </p>
          {d && (
            <p className="text-slate-500 print:text-slate-600 text-xs sm:text-sm mt-1">
              {t("report.generated", "Generated")}{" "}
              {new Date(d.generated_at).toLocaleString(i18n.language)}
            </p>
          )}
          {d && (
            <div className="mt-6 sm:mt-8 pt-6 border-t border-slate-800/80 print:border-slate-200" data-moment>
              <span className="moment-value block print:text-slate-900">
                {d.totals.persons.toLocaleString()}
              </span>
              <span className="text-sm sm:text-base text-slate-400 print:text-slate-600 mt-1 block">
                {t("report.deputiesCount", "deputies in the corpus")}
              </span>
            </div>
          )}
        </div>
        <div className="flex flex-col sm:flex-row lg:flex-col items-start sm:items-center lg:items-end gap-4 sm:gap-5 print:hidden shrink-0">
          <HeroGraphic variant="report" className="max-w-[260px] w-full sm:w-auto" />
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => window.print()}
              className="bg-sky-700 hover:bg-sky-800 text-white px-4 py-2 rounded btn-hover focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400"
            >
              {t("report.print", "Print / Save as PDF")}
            </button>
            <a
              href="/api/export/report"
              download="transparency-report.json"
              className="bg-slate-700 hover:bg-slate-600 text-slate-200 px-4 py-2 rounded btn-hover focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400"
            >
              {t("report.download", "Download JSON")}
            </a>
          </div>
        </div>
      </div>

      {report.isLoading && (
        <div
          role="status"
          aria-label={t("report.loadingTitle", "Loading report…")}
          className="flex flex-col items-center justify-center gap-3 py-12 text-slate-400"
        >
          <svg
            className="w-12 h-12 text-sky-400"
            aria-hidden="true"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth="1.5"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            ></path>
          </svg>
          <h2 className="font-semibold text-slate-200">
            {t("report.loadingTitle", "Loading report…")}
          </h2>
          <p className="text-sm text-slate-500 text-center max-w-xs">
            {t(
              "report.loadingDesc",
              "Compiling the transparency corpus. This may take a moment.",
            )}
          </p>
          <button
            type="button"
            onClick={() => report.refetch()}
            className="mt-3 bg-slate-700 hover:bg-slate-600 text-slate-200 px-4 py-2 rounded text-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400"
          >
            {t("report.refresh", "Refresh")}
          </button>
        </div>
      )}
      {report.isError && (
        <div
          role="alert"
          aria-label={t("report.errorTitle", "Failed to load report")}
          className="flex flex-col items-center justify-center gap-3 py-12 text-slate-400"
        >
          <svg
            className="w-12 h-12 text-red-400"
            aria-hidden="true"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth="1.5"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            ></path>
          </svg>
          <h2 className="font-semibold text-slate-200">
            {t("report.errorTitle", "Failed to load report")}
          </h2>
          <p className="text-sm text-slate-500 text-center max-w-xs">
            {t("report.errorDesc", "We couldn't load the transparency report.")}
          </p>
          <button
            type="button"
            onClick={() => report.refetch()}
            className="mt-3 bg-sky-700 hover:bg-sky-800 text-white px-4 py-2 rounded text-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400"
          >
            {t("report.retry", "Retry")}
          </button>
        </div>
      )}

      {d && (
        <>
          <div className="bg-slate-800/30 rounded-xl p-4 sm:p-5 mb-6 print:bg-transparent print:p-0">
            <section className="mb-6 sm:mb-8">
              <h2 className="font-semibold text-slate-200 print:text-slate-900 mb-3 sm:mb-4 tracking-tight">
                {t("report.corpus", "Corpus at a glance")}
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
                <InfoStat
                  label={t("report.persons", "Persons")}
                  value={d.totals.persons}
                  max={statMax}
                />
                <InfoStat
                  label={t("report.memberships", "Memberships")}
                  value={d.totals.memberships}
                  max={statMax}
                />
                <InfoStat
                  label={t("report.events", "Events")}
                  value={d.totals.events}
                  max={statMax}
                />
                <InfoStat
                  label={t("report.switches", "Party switches")}
                  value={d.totals.switches}
                  max={statMax}
                />
                <InfoStat
                  label={t("report.committees", "Committees")}
                  value={d.totals.committees}
                  max={statMax}
                />
                <InfoStat
                  label={t("report.birthDates", "Birth dates")}
                  value={`${d.totals.persons_with_birth_date} / ${d.totals.persons}`}
                  max={statMax}
                  barValue={d.totals.persons_with_birth_date}
                />
              </div>
            </section>

            <section className="mb-0">
              <h2 className="font-semibold text-slate-200 print:text-slate-900 mb-3 sm:mb-4 tracking-tight">
                {t("report.topSwitchers", "Top party switchers")}
              </h2>
              <div
                className="overflow-x-auto max-w-full"
                tabIndex={0}
                role="region"
                aria-label={t("report.topSwitchers", "Top party switchers")}
              >
                <table className="min-w-full text-sm data-table">
                  <thead>
                    <tr className="text-left text-slate-400 print:text-slate-600 border-b border-slate-700 print:border-slate-300">
                      <th scope="col" className="py-1 pr-3">{t("report.col.mp", "MP")}</th>
                      <th scope="col" className="py-1 pr-3 text-right">
                        {t("report.col.switches", "Switches")}
                      </th>
                      <th scope="col" className="py-1 pr-3 text-right">
                        {t("report.col.loyalty", "Loyalty")}
                      </th>
                      <th scope="col" className="py-1 pr-3">{t("report.col.period", "Period")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {d.top_switchers.map((s) => (
                      <tr
                        key={s.person_id}
                        className="border-b border-slate-700/40 print:border-slate-200"
                      >
                        <th scope="row" className="py-1 pr-3 text-slate-200 print:text-slate-900 font-normal text-left">
                          {s.name}
                        </th>
                        <td className="py-1 pr-3 text-right text-slate-300 print:text-slate-700">
                          {s.switches}
                        </td>
                        <td className="py-1 pr-3 text-right text-slate-300 print:text-slate-700">
                          {s.loyalty_score}
                        </td>
                        <td className="py-1 pr-3 text-slate-400 print:text-slate-600 text-xs">
                          {s.first_switch ?? "—"} → {s.last_switch ?? "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </div>

          <div className="bg-slate-800/30 rounded-xl p-4 sm:p-5 mb-6 print:bg-transparent print:p-0">
            <section className="mb-6 sm:mb-8">
              <h2 className="font-semibold text-slate-200 print:text-slate-900 mb-3 sm:mb-4 tracking-tight">
                {t("report.control", "Committee control")}
              </h2>
              <div className="flex flex-wrap gap-3 sm:gap-4">
                {d.committee_control.parties.map((p) => (
                  <InfoStat
                    key={p.party}
                    label={p.party}
                    value={p.chairs}
                    max={100}
                    barValue={p.share_pct}
                  />
                ))}
                <span className="text-slate-500 print:text-slate-600 text-sm self-center">
                  {t("report.ofCommittees", "of {{n}} committees", {
                    n: d.committee_control.total_committees,
                  })}
                </span>
              </div>
            </section>

            <section className="mb-0">
              <h2 className="font-semibold text-slate-200 print:text-slate-900 mb-3 sm:mb-4 tracking-tight">
                {t("report.waves", "Largest switch waves")}
              </h2>
              {d.switch_waves.length > 0 && (
                <div className="mt-3 h-10 w-64 max-w-full">
                  <Sparkline
                    data={d.switch_waves.slice(0, 6).map((w) => w.switch_count)}
                    height={36}
                  />
                </div>
              )}
              <ul className="text-sm space-y-1.5">
                {d.switch_waves.slice(0, 6).map((w, i) => (
                  <li
                    key={`${w.start_date}-${i}`}
                    className="text-slate-300 print:text-slate-700"
                  >
                    <span className="text-slate-500 print:text-slate-600 font-mono text-xs">
                      {w.start_date} → {w.end_date}
                    </span>{" "}
                    — {w.switch_count}{" "}
                    {t("report.switchesUnit", "switches")}
                    {w.trigger_event ? ` · ${w.trigger_event}` : ""}
                  </li>
                ))}
              </ul>
            </section>
          </div>

          <div className="bg-slate-800/30 rounded-xl p-4 sm:p-5 mb-6 print:bg-transparent print:p-0">
            <section className="mb-4">
              <h2 className="font-semibold text-slate-200 print:text-slate-900 mb-3 sm:mb-4 tracking-tight">
                {t("report.ages", "Average age by party")}
              </h2>
              <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm">
                {d.party_ages.slice(0, 12).map((a) => (
                  <span
                    key={a.party}
                    className="text-slate-300 print:text-slate-700"
                  >
                    {a.party}:{" "}
                    <span className="font-semibold">{a.avg_age}</span>{" "}
                    <span className="text-slate-500 print:text-slate-600 text-xs">
                      (n={a.mps_with_birth_dates})
                    </span>
                  </span>
                ))}
              </div>
              {d.party_ages.length > 0 && (
                <div className="mt-3 h-10 w-64">
                  <Sparkline
                    data={d.party_ages.slice(0, 12).map((a) => a.avg_age)}
                    height={36}
                  />
                </div>
              )}
            </section>

            <section className="mb-0">
              <h2 className="font-semibold text-slate-200 print:text-slate-900 mb-2">
                {t("report.coverage", "Data coverage")}
              </h2>
              <div
                className="overflow-x-auto max-w-full"
                tabIndex={0}
                role="region"
                aria-label={t("report.coverage", "Data coverage")}
              >
                <table className="min-w-full text-sm data-table">
                  <thead>
                    <tr className="text-left text-slate-400 print:text-slate-600 border-b border-slate-700 print:border-slate-300">
                      <th scope="col" className="py-1 pr-3">
                        {t("report.col.chamber", "Chamber")}
                      </th>
                      <th scope="col" className="py-1 pr-3">
                        {t("report.col.legislature", "Legislature")}
                      </th>
                      <th scope="col" className="py-1 pr-3">
                        {t("report.col.completeness", "Completeness")}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {d.coverage.map((c) => (
                      <tr
                        key={`${c.chamber}-${c.legislature}`}
                        className="border-b border-slate-700/40 print:border-slate-200"
                      >
                        <th scope="row" className="py-1 pr-3 text-slate-300 print:text-slate-700 font-normal text-left">
                          {c.chamber}
                        </th>
                        <td className="py-1 pr-3 text-slate-300 print:text-slate-700">
                          {c.legislature ?? "—"}
                        </td>
                        <td className="py-1 pr-3">
                          <div className="flex items-center gap-2">
                            <span
                              className={`font-medium text-xs text-nowrap ${completenessColor(
                                c.completeness,
                              )}`}
                            >
                              {c.completeness}
                            </span>
                            <ProgressRing
                              value={completenessValue(c.completeness)}
                              max={100}
                              size={22}
                              color={completenessRingColor(c.completeness)}
                            />
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </div>

          <p className="mt-6 text-xs text-slate-500 print:text-slate-600">
            {t("report.footer")}
          </p>
        </>
      )}
    </div>
  );
}
