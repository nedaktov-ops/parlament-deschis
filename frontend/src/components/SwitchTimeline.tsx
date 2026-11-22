import { useId, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { activateOnKey } from "../utils/a11y";
import TooltipText from "./ui/TooltipText";

export interface SwitchWaveData {
  id: string;
  label: string | null;
  start_date: string | null;
  end_date: string | null;
  switch_count: number;
  trigger_type: string | null;
  legislature: string | null;
  chamber: string | null;
}

export interface LegislationData {
  label: string;
  start: string | null;
  end: string | null;
}

export interface SwitchTimelineProps {
  waves: SwitchWaveData[];
  legislatures: Record<string, { label: string; start: string | null; end: string | null }>;
  onWaveClick?: (wave: SwitchWaveData) => void;
  height?: number;
}

/** The SVG canvas keeps its aspect ratio (`w-full h-auto`). A 480-unit width
 *  gives ten four-digit legislature labels room to breathe in a wide dashboard
 *  card; at ~475px rendered width a fontSize of 14 stays above 11px. The old
 *  200-unit canvas squashed those labels into an unreadable string, and the
 *  older 500×120 viewBox used preserveAspectRatio="none" to distort 7px text. */
const WIDTH = 480;
const AXIS_Y = 20;
const ROW_TOP = 38;
const ROW_H = 26;
const BAR_H = 18;
const BAR_W = 10;

export default function SwitchTimeline({
  waves,
  legislatures,
  onWaveClick,
  height = 120,
}: SwitchTimelineProps) {
  const { t } = useTranslation();
  const uid = useId().replace(/:/g, "");
  const timelineData = useMemo(() => {
    const sortedLegs = Object.values(legislatures)
      .filter((l) => l.start)
      .sort((a, b) => (a.start ?? "").localeCompare(b.start ?? ""));

    const startDate = sortedLegs[0]?.start || "1990-06-18";
    const startDateObj = new Date(startDate);
    const endDate = new Date();
    const durationMs = endDate.getTime() - startDateObj.getTime();

    return {
      legs: sortedLegs,
      startDate,
      totalSwitches: waves.reduce((sum, w) => sum + w.switch_count, 0),
      wavesByDate: waves.map((wave) => ({
        ...wave,
        daysFromStart: wave.start_date
          ? Math.round(
              (new Date(wave.start_date).getTime() - startDateObj.getTime()) /
                (durationMs / 100),
            )
          : 0,
      })),
      durationMs,
    };
  }, [legislatures, waves]);

  const xScale = (days: number) => 8 + (days / 100) * (WIDTH - 16);

  if (!waves?.length) {
    return (
      <div className="w-full bg-slate-800/30 rounded-xl p-4 overflow-hidden">
        <div className="text-xs text-slate-400 mb-2">Switch Waves</div>
        <div
          role="status"
          className="flex h-32 flex-col items-center justify-center gap-1 text-center"
        >
          <span className="text-sm font-medium text-slate-300">No switch waves</span>
          <span className="text-xs text-slate-400">
            Wave activity will appear here when available.
          </span>
        </div>
      </div>
    );
  }

  const activeWaves = timelineData.wavesByDate
    .filter((w) => w.daysFromStart >= 0 && w.daysFromStart <= 100)
    .sort((a, b) => b.switch_count - a.switch_count)
    .slice(0, 8);

  const canvasHeight = Math.max(
    height,
    ROW_TOP + activeWaves.length * ROW_H + 6,
  );

  return (
    <div className="w-full bg-slate-800/30 rounded-xl p-4 overflow-hidden">
      <div className="text-xs text-slate-400 mb-2">Switch Waves</div>
      <div className="relative w-full">
        {/* No preserveAspectRatio="none": the viewBox keeps its aspect ratio,
            so bars, ticks and labels stay proportional and legible. */}
        {/* No role="img" here: that would flatten the focusable wave <rect>s
            out of the accessibility tree. Each rect carries its own name. */}
        <svg
          className="block h-auto w-full overflow-visible"
          viewBox={`0 0 ${WIDTH} ${canvasHeight}`}
        >
          {/* Time axis */}
          <line
            x1={8}
            y1={AXIS_Y}
            x2={WIDTH - 8}
            y2={AXIS_Y}
            strokeWidth={0.6}
            className="stroke-slate-500 opacity-60"
          />

          {/* Legislature markers */}
          {timelineData.legs
            .filter((_, i) => i % 2 === 0 || i === timelineData.legs.length - 1)
            .map((leg) => {
            const legDate = leg.start ? new Date(leg.start).getTime() : null;
            if (!legDate) return null;
            const days = Math.round(
              (legDate - new Date(timelineData.startDate).getTime()) /
                (timelineData.durationMs / 100),
            );
            const x = xScale(days);
            const anchor = x < 40 ? "start" : x > WIDTH - 40 ? "end" : "middle";
            return (
              <g key={leg.label}>
                <line
                  x1={x}
                  y1={AXIS_Y - 5}
                  x2={x}
                  y2={AXIS_Y + 5}
                  strokeWidth={0.6}
                  className="stroke-slate-500 opacity-70"
                />
                <text
                  x={x}
                  y={AXIS_Y - 10}
                  textAnchor={anchor}
                  fontSize={14}
                  className="fill-slate-400"
                >
                  {leg.label}
                </text>
              </g>
            );
          })}

          {/* Switch wave bars — one row per wave, positioned by start date */}
          {activeWaves.map((wave, idx) => {
            const x = Math.max(8, Math.min(WIDTH - BAR_W - 24, xScale(wave.daysFromStart)));
            const y = ROW_TOP + idx * ROW_H;
            const intensity = Math.min(1, wave.switch_count / 100);
            const waveLabel = `${wave.start_date ?? "unknown date"}: ${wave.switch_count} switches`;
            return (
              <g key={wave.id}>
                <rect
                  x={x}
                  y={y}
                  width={BAR_W}
                  height={BAR_H}
                  rx={2}
                  style={{ fill: "rgb(var(--danger-rgb))" }}
                  opacity={0.4 + intensity * 0.6}
                  role="button"
                  tabIndex={0}
                  aria-label={t("a11y.switchWave", "Switch wave on {{date}}: {{count}} switches", {
                    count: wave.switch_count,
                    date: wave.start_date ?? "",
                  })}
                  aria-describedby={`${uid}-wave-${wave.id}`}
                  onClick={() => onWaveClick?.(wave)}
                  onKeyDown={(e) => activateOnKey(e, () => onWaveClick?.(wave))}
                  className="cursor-pointer transition-opacity duration-150 motion-reduce:transition-none hover:opacity-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-400"
                >
                  <title>{waveLabel}</title>
                </rect>
                <text
                  x={x + BAR_W + 4}
                  y={y + BAR_H / 2 + 4}
                  fontSize={14}
                  dominantBaseline="middle"
                  className="fill-slate-300 tabular-nums"
                >
                  {wave.switch_count}
                </text>
              </g>
            );
          })}
        </svg>
        {activeWaves.map((wave) => (
          <TooltipText key={wave.id} id={`${uid}-wave-${wave.id}`}>
            {`${wave.start_date ?? "unknown date"}: ${wave.switch_count} switches`}
          </TooltipText>
        ))}
      </div>

      <div className="mt-2 flex items-center justify-between gap-2 text-xs">
        <span className="text-slate-500">{waves.length} events</span>
        <button
          type="button"
          className="btn btn-hover min-h-11 text-sky-400 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-400"
          onClick={() =>
            onWaveClick?.({
              id: "all",
              label: null,
              start_date: null,
              end_date: null,
              switch_count: timelineData.totalSwitches,
              trigger_type: null,
              legislature: null,
              chamber: null,
            } as SwitchWaveData)
          }
        >
          View all →
        </button>
      </div>
    </div>
  );
}
