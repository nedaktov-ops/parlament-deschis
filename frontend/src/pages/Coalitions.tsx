import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { switchWaves, type SwitchWave } from "../api/client";
import HeroGraphic from "../components/HeroGraphic";
import InfoStat from "../components/InfoStat";
import { Sparkline } from "../components/DataViz";

interface NamedEvent {
  date: string;
  name: string;
  switchCount: number;
  waveId: string;
}

function toNamedEvents(waves: SwitchWave[], triggerType: string): NamedEvent[] {
  return waves
    .filter((w) => w.trigger_type === triggerType && w.trigger_event)
    .map((w) => ({
      date: w.start_date ?? "?",
      name: w.trigger_event as string,
      switchCount: w.switch_count,
      waveId: w.id,
    }))
    .sort((a, b) => a.date.localeCompare(b.date));
}

export default function Coalitions() {
  const { t } = useTranslation();

  const waves = useQuery({
    queryKey: ["switch-waves-all"],
    queryFn: () => switchWaves(),
  });

  const all = waves.data ?? [];
  const formations = toNamedEvents(all, "government_formation");
  const breakups = toNamedEvents(all, "coalition_breakup");
  const congresses = toNamedEvents(all, "party_congress");

  // Observed span: for each named breakup, the most recent prior formation
  // (evidence of duration, not a claim about the government's official life).
  const spans = breakups.map((b) => {
    const prior = formations.filter((f) => f.date <= b.date);
    const last = prior.length > 0 ? prior[prior.length - 1] : null;
    const days =
      last && b.date !== "?"
        ? Math.round(
            (new Date(b.date).getTime() - new Date(last.date).getTime()) /
              86_400_000,
          )
        : null;
    return { breakup: b, formation: last, days };
  });

  return (
    <div className="space-y-6">
      {/* Section 1: Hero — fills the first screen alone (H2-G recipe). */}
      <section className="hero-section" data-enter>
        <div>
          <div className="flex flex-col md:flex-row md:items-center gap-8">
            <div className="flex-1 space-y-4">
              <h1 className="page-title">
                {t("coalitions.title", "Coalition Stability")}
              </h1>
              <p className="text-sm text-slate-400">
                {t(
                  "coalitions.intro",
                  "Government formations, coalition breakups and party congresses that coincide with detected switch waves. Each event is a burst of affiliation change the corpus links to a named political moment.",
                )}
              </p>
              {waves.isLoading && (
                <div className="text-slate-500" role="status" aria-live="polite">
                  {t("loading", "Loading…")}
                </div>
              )}
              {waves.isError && (
                <div className="text-rose-400" role="alert">
                  {t("coalitions.loadError", "Failed to load wave data.")}
                </div>
              )}
              {!waves.isLoading && !waves.isError && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6">
                  <InfoStat
                    label={t("coalitions.statWaves", "Total waves")}
                    value={all.length}
                    accent="sky"
                  />
                  <InfoStat
                    label={t("coalitions.statFormations", "Formations")}
                    value={formations.length}
                    accent="emerald"
                  />
                  <InfoStat
                    label={t("coalitions.statBreakups", "Breakups")}
                    value={breakups.length}
                    accent="amber"
                  />
                  <InfoStat
                    label={t("coalitions.statCongresses", "Congresses")}
                    value={congresses.length}
                    accent="rose"
                  />
                </div>
              )}
            </div>
            <div className="w-full md:w-auto max-w-[260px]">
              <HeroGraphic variant="wave" className="mx-auto" />
            </div>
          </div>
          {!waves.isLoading && !waves.isError && (
            <>
              <div className="mt-8 flex items-center gap-4" data-moment>
                <span className="moment-value block">
                  {all.length}
                </span>
                <span className="text-sm text-slate-400">
                  {t("coalitions.wavesInCorpus", "switch waves in the corpus")}
                </span>
              </div>
              {all.length > 0 && (
                <div className="mt-6">
                  <p className="text-xs text-slate-500 mb-2">
                    {t(
                      "coalitions.waveTimeline",
                      "Wave timeline — switches per detected wave",
                    )}
                  </p>
                  <Sparkline
                    data={all.map((w) => w.switch_count ?? 0)}
                    color="stroke-sky-400"
                  />
                </div>
              )}
            </>
          )}
        </div>
      </section>

      {/* Coalition breakups with observed prior formation span */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-slate-100 mb-3">
          {t("coalitions.breakups", "Coalition breakups")}
        </h2>
        {breakups.length === 0 ? (
          <div className="text-slate-500">
            {t("coalitions.noBreakups", "No coalition breakups recorded.")}
          </div>
        ) : (
          <div className="overflow-x-auto max-w-full" tabIndex={0} role="region" aria-label={t("coalitions.breakups", "Coalition breakups")}>
            <table className="min-w-full bg-slate-800 rounded-xl overflow-hidden data-table">
              <thead className="bg-slate-700">
                <tr>
                  <th scope="col" className="px-4 py-3 text-left text-sm font-medium !text-slate-300">
                    {t("coalitions.col.event", "Event")}
                  </th>
                  <th scope="col" className="px-4 py-3 text-left text-sm font-medium !text-slate-300">
                    {t("coalitions.col.date", "Date")}
                  </th>
                  <th scope="col" className="px-4 py-3 text-right text-sm font-medium !text-slate-300">
                    {t("coalitions.col.switches", "Switches in wave")}
                  </th>
                  <th scope="col" className="px-4 py-3 text-left text-sm font-medium !text-slate-300">
                    {t("coalitions.col.since", "Since prior formation")}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700">
                {spans.map(({ breakup, formation, days }) => (
                  <tr key={breakup.waveId} className="hover:bg-slate-700/50">
                    <th scope="row" className="px-4 py-3 text-slate-200 font-normal text-left">{breakup.name}</th>
                    <td className="px-4 py-3 text-slate-300">{breakup.date}</td>
                    <td className="px-4 py-3 text-right">
                      <span className="bg-amber-900/40 text-amber-300 px-2 py-0.5 rounded text-sm">
                        {breakup.switchCount}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-400 text-sm">
                      {days !== null ? (
                        <>
                          {days} {t("coalitions.days", "days")}
                          {formation ? (
                            <span className="text-slate-500">
                              {" "}
                              ({t("coalitions.after", "after")} {formation.name},{" "}
                              {formation.date})
                            </span>
                          ) : null}
                        </>
                      ) : (
                        "—"
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Government formations */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold text-slate-100 mb-3">
          {t("coalitions.formations", "Government formations")}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {formations.map((f) => (
            <div
              key={f.waveId}
              className="bg-slate-800 rounded p-3 flex items-center justify-between gap-3"
            >
              <div>
                <div className="text-slate-200 text-sm">{f.name}</div>
                <div className="text-slate-500 text-xs">{f.date}</div>
              </div>
              <span className="bg-sky-900/40 text-sky-300 px-2 py-0.5 rounded text-sm shrink-0">
                {f.switchCount}
              </span>
            </div>
          ))}
          {formations.length === 0 && !waves.isLoading && (
            <div className="text-slate-500">
              {t("coalitions.noFormations", "No formations recorded.")}
            </div>
          )}
        </div>
      </section>

      {/* Party congresses */}
      <section>
        <h2 className="text-lg font-semibold text-slate-100 mb-3">
          {t("coalitions.congresses", "Party congresses")}
        </h2>
        <div className="flex flex-wrap gap-3">
          {congresses.map((c) => (
            <div key={c.waveId} className="bg-slate-800 rounded px-3 py-2 text-sm">
              <span className="text-slate-200">{c.name}</span>
              <span className="text-slate-500 ml-2">{c.date}</span>
              <span className="bg-purple-900/40 text-purple-300 px-2 py-0.5 rounded ml-2">
                {c.switchCount}
              </span>
            </div>
          ))}
          {congresses.length === 0 && !waves.isLoading && (
            <div className="text-slate-500">
              {t("coalitions.noCongresses", "No congresses recorded.")}
            </div>
          )}
        </div>
      </section>

      <div className="mt-8 bg-slate-800/50 rounded p-4 text-sm text-slate-400">
        <h2 className="text-slate-200 font-semibold mb-1">
          {t("coalitions.methodology", "Methodology")}
        </h2>
        <p>
          {t(
            "coalitions.methodology.desc",
            "Switch waves are 30-day clusters of 3+ observed switch_group events. A wave is linked to a named event (government, coalition breakup, congress) when the corpus records that trigger at the wave's date. 'Since prior formation' measures days between the most recent formation wave and the breakup wave — an observation about switch bursts, not an official government lifetime.",
          )}
        </p>
      </div>
    </div>
  );
}
