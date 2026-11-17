import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { get } from "../api/client";

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

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="bg-slate-800 rounded p-3 print:bg-slate-100 print:border print:border-slate-300">
      <div className="text-xs text-slate-400 print:text-slate-600">
        {label}
      </div>
      <div className="text-xl font-bold text-slate-100 print:text-slate-900">
        {typeof value === "number" ? value.toLocaleString() : value}
      </div>
    </div>
  );
}

export default function Report() {
  const { t, i18n } = useTranslation();

  const report = useQuery({
    queryKey: ["transparency-report"],
    queryFn: fetchReport,
  });

  const d = report.data;

  const completenessColor = (c: string): string =>
    c === "full"
      ? "text-emerald-600 print:text-emerald-700"
      : c === "partial"
        ? "text-amber-600 print:text-amber-700"
        : "text-slate-500";

  return (
    <div className="p-6 print:p-0">
      <div className="flex flex-wrap items-start justify-between gap-3 mb-6 print:mb-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 print:text-slate-900">
            {t("report.title", "Transparency Report")}
          </h1>
          <p className="text-slate-400 print:text-slate-600 text-sm mt-1">
            {t(
              "report.subtitle",
              "One-page summary of what the corpus contains — for journalists and citizens.",
            )}
          </p>
          {d && (
            <p className="text-slate-500 print:text-slate-600 text-xs mt-1">
              {t("report.generated", "Generated")}{" "}
              {new Date(d.generated_at).toLocaleString(i18n.language)}
            </p>
          )}
        </div>
        <div className="flex gap-2 print:hidden">
          <button
            type="button"
            onClick={() => window.print()}
            className="bg-sky-600 hover:bg-sky-500 text-white px-4 py-2 rounded focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400"
          >
            {t("report.print", "Print / Save as PDF")}
          </button>
          <a
            href="/api/export/report"
            download="transparency-report.json"
            className="bg-slate-700 hover:bg-slate-600 text-slate-200 px-4 py-2 rounded focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400"
          >
            {t("report.download", "Download JSON")}
          </a>
        </div>
      </div>

      {report.isLoading && (
        <div className="text-slate-500">{t("loading", "Loading…")}</div>
      )}
      {report.isError && (
        <div className="text-red-400">
          {t("report.loadError", "Failed to load the report.")}
        </div>
      )}

      {d && (
        <>
          <section className="mb-6">
            <h2 className="font-semibold text-slate-200 print:text-slate-900 mb-2">
              {t("report.corpus", "Corpus at a glance")}
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
              <Stat
                label={t("report.persons", "Persons")}
                value={d.totals.persons}
              />
              <Stat
                label={t("report.memberships", "Memberships")}
                value={d.totals.memberships}
              />
              <Stat label={t("report.events", "Events")} value={d.totals.events} />
              <Stat
                label={t("report.switches", "Party switches")}
                value={d.totals.switches}
              />
              <Stat
                label={t("report.committees", "Committees")}
                value={d.totals.committees}
              />
              <Stat
                label={t("report.birthDates", "Birth dates")}
                value={`${d.totals.persons_with_birth_date} / ${d.totals.persons}`}
              />
            </div>
          </section>

          <section className="mb-6">
            <h2 className="font-semibold text-slate-200 print:text-slate-900 mb-2">
              {t("report.topSwitchers", "Top party switchers")}
            </h2>
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-slate-400 print:text-slate-600 border-b border-slate-700 print:border-slate-300">
                  <th className="py-1 pr-3">{t("report.col.mp", "MP")}</th>
                  <th className="py-1 pr-3 text-right">
                    {t("report.col.switches", "Switches")}
                  </th>
                  <th className="py-1 pr-3 text-right">
                    {t("report.col.loyalty", "Loyalty")}
                  </th>
                  <th className="py-1 pr-3">{t("report.col.period", "Period")}</th>
                </tr>
              </thead>
              <tbody>
                {d.top_switchers.map((s) => (
                  <tr
                    key={s.person_id}
                    className="border-b border-slate-700/40 print:border-slate-200"
                  >
                    <td className="py-1 pr-3 text-slate-200 print:text-slate-900">
                      {s.name}
                    </td>
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
          </section>

          <section className="mb-6">
            <h2 className="font-semibold text-slate-200 print:text-slate-900 mb-2">
              {t("report.control", "Committee control")}
            </h2>
            <div className="flex flex-wrap gap-3">
              {d.committee_control.parties.map((p) => (
                <span
                  key={p.party}
                  className="bg-slate-800 print:bg-slate-100 print:border print:border-slate-300 rounded px-3 py-1.5 text-sm text-slate-200 print:text-slate-900"
                >
                  {p.party}: {p.chairs}{" "}
                  <span className="text-slate-400 print:text-slate-600">
                    ({p.share_pct}%)
                  </span>
                </span>
              ))}
              <span className="text-slate-500 print:text-slate-600 text-sm self-center">
                {t("report.ofCommittees", "of {{n}} committees", {
                  n: d.committee_control.total_committees,
                })}
              </span>
            </div>
          </section>

          <section className="mb-6">
            <h2 className="font-semibold text-slate-200 print:text-slate-900 mb-2">
              {t("report.waves", "Largest switch waves")}
            </h2>
            <ul className="text-sm space-y-1">
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

          <section className="mb-6">
            <h2 className="font-semibold text-slate-200 print:text-slate-900 mb-2">
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
          </section>

          <section>
            <h2 className="font-semibold text-slate-200 print:text-slate-900 mb-2">
              {t("report.coverage", "Data coverage")}
            </h2>
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-slate-400 print:text-slate-600 border-b border-slate-700 print:border-slate-300">
                  <th className="py-1 pr-3">
                    {t("report.col.chamber", "Chamber")}
                  </th>
                  <th className="py-1 pr-3">
                    {t("report.col.legislature", "Legislature")}
                  </th>
                  <th className="py-1 pr-3">
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
                    <td className="py-1 pr-3 text-slate-300 print:text-slate-700">
                      {c.chamber}
                    </td>
                    <td className="py-1 pr-3 text-slate-300 print:text-slate-700">
                      {c.legislature ?? "—"}
                    </td>
                    <td
                      className={`py-1 pr-3 font-medium ${completenessColor(
                        c.completeness,
                      )}`}
                    >
                      {c.completeness}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <p className="mt-6 text-xs text-slate-500 print:text-slate-600">
            {t(
              "report.footer",
              "Source: parlament-deschis corpus — cdep.ro and senat.ro dated parliamentary ledgers. Every figure above is an observed count; gaps are stated, never filled with estimates. CC-BY 4.0.",
            )}
          </p>
        </>
      )}
    </div>
  );
}
