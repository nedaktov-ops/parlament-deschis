import { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import type { MetaResponse } from "../api/client";
import { useReducedMotion } from "../hooks/useReducedMotion";
import { legislatureStops, stopIndexForDate } from "../utils/legislatureStops";
import ChamberView from "./ChamberView";

/**
 * Legislature start-year slider plus the two chamber hemicycles it drives.
 * The slider snaps to the `start` of each legislature from `/api/meta`, writes
 * both `date` and `legislature` into the route scope, and re-samples both
 * chamber composition charts at that date.
 */
export default function LegislatureSeatExplorer({
  legislatures,
  date,
  onSelectLegislature,
  onOpenPerson,
}: {
  legislatures: MetaResponse["legislatures"];
  date: string;
  onSelectLegislature: (date: string, legislature: string) => void;
  onOpenPerson: (id: string) => void;
}) {
  const { t } = useTranslation();
  const reducedMotion = useReducedMotion();
  const stops = useMemo(() => legislatureStops(legislatures), [legislatures]);
  const index = stopIndexForDate(stops, date);
  const active = index >= 0 ? stops[index] : undefined;
  const [playing, setPlaying] = useState(false);

  // Refs keep the autoplay interval stable while the selected date changes.
  const indexRef = useRef(index);
  const stopsRef = useRef(stops);
  indexRef.current = index;
  stopsRef.current = stops;

  const selectIndex = (next: number) => {
    const list = stopsRef.current;
    if (next < 0 || next >= list.length) return;
    onSelectLegislature(list[next].start, list[next].id);
  };

  useEffect(() => {
    if (!playing || reducedMotion || stops.length < 2) return;
    const timer = window.setInterval(() => {
      const current = indexRef.current;
      selectIndex(current >= stops.length - 1 ? 0 : current + 1);
    }, 1200);
    return () => window.clearInterval(timer);
    // selectIndex is intentionally read from refs, so it need not be a dep.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [playing, reducedMotion, stops.length]);

  return (
    <div className="card p-4 sm:p-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-100">
            {t("chamberEvolutionTitle", "Compoziția camerelor pe legislaturi")}
          </h2>
          <p className="text-sm text-slate-300/90 mt-1 max-w-2xl">
            {t(
              "chamberEvolutionIntro",
              "Mută cursorul la anul de start al fiecărei legislaturi pentru a vedea cum se schimbă locurile din ambele camere între 1990 și azi.",
            )}
          </p>
        </div>
        <div className="text-sm whitespace-nowrap">
          <span className="text-slate-300">{t("chamberEvolutionStartYear", "An de start")}: </span>
          <output className="font-mono font-semibold text-sky-300" aria-live="polite">
            {active ? active.year : "—"}
          </output>
        </div>
      </div>

      {stops.length === 0 ? (
        <p role="status" className="text-sm text-slate-300 py-8">{t("loading")}</p>
      ) : (
        <>
          <div className="flex flex-wrap items-center gap-3 mt-4">
            <button
              type="button"
              className="btn btn-hover bg-slate-700 hover:bg-slate-600 min-h-11 sm:min-h-0"
              onClick={() => setPlaying((p) => !p)}
              aria-pressed={playing}
              disabled={reducedMotion || stops.length < 2}
            >
              {playing ? t("pause") : t("play")}
            </button>
            <button
              type="button"
              className="btn btn-hover bg-slate-700 hover:bg-slate-600 min-h-11 sm:min-h-0"
              onClick={() => selectIndex(index - 1)}
              disabled={index <= 0}
              aria-label={t("chamberEvolutionPrev", "Legislatura anterioară")}
            >
              ←
            </button>
            <div className="flex-1 min-w-[180px]">
              <label htmlFor="legislature-start-slider" className="sr-only">
                {t("chamberEvolutionSelect", "Selectează legislatura după anul de start")}
              </label>
              <input
                id="legislature-start-slider"
                type="range"
                min={0}
                max={stops.length - 1}
                step={1}
                value={index < 0 ? 0 : index}
                onChange={(e) => selectIndex(Number(e.target.value))}
                aria-valuetext={active ? String(active.year) : ""}
                className="w-full accent-sky-500"
              />
              <div className="relative h-4 mt-1" aria-hidden="true">
                {stops.map((stop, i) => {
                  const pct = stops.length === 1 ? 0 : (i / (stops.length - 1)) * 100;
                  return (
                    <span
                      key={stop.id}
                      className="absolute text-[10px] sm:text-xs text-slate-300 -translate-x-1/2 whitespace-nowrap"
                      style={{ left: `${pct}%` }}
                    >
                      {stop.year}
                    </span>
                  );
                })}
              </div>
            </div>
            <button
              type="button"
              className="btn btn-hover bg-slate-700 hover:bg-slate-600 min-h-11 sm:min-h-0"
              onClick={() => selectIndex(index + 1)}
              disabled={index < 0 || index >= stops.length - 1}
              aria-label={t("chamberEvolutionNext", "Legislatura următoare")}
            >
              →
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-5 mt-5">
            {(["deputies", "senate"] as const).map((chamber) => (
              <ChamberView
                key={`${chamber}-${active ? active.start : date}`}
                chamber={chamber}
                asOf={active ? active.start : date}
                onSelect={onOpenPerson}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
