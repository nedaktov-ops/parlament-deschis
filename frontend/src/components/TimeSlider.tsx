import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useReducedMotion } from "../hooks/useReducedMotion";

function toISO(d: Date) {
  return d.toISOString().slice(0, 10);
}

export default function TimeSlider({
  value,
  min,
  max,
  onChange,
  ticks,
}: {
  value: string;
  min: string;
  max: string;
  onChange: (iso: string) => void;
  ticks: { label: string; start: string }[];
}) {
  const { t } = useTranslation();
  const reducedMotion = useReducedMotion();
  const [playing, setPlaying] = useState(false);
  const timer = useRef<number | null>(null);
  // Keep the latest value/onChange in refs so the interval can read them
  // without being torn down and recreated on every tick (value changes each tick).
  const valueRef = useRef(value);
  const onChangeRef = useRef(onChange);
  valueRef.current = value;
  onChangeRef.current = onChange;
  const minMs = new Date(min).getTime();
  const maxMs = new Date(max).getTime();
  const valMs = new Date(value).getTime();
  const spanMs = Math.max(1, maxMs - minMs);
  const tickStride = Math.max(1, Math.ceil(ticks.length / 5));
  const visibleTicks = ticks.filter(
    (_, index) => index % tickStride === 0 || index === ticks.length - 1,
  );

  useEffect(() => {
    if (!playing || reducedMotion) return;
    timer.current = window.setInterval(() => {
      const cur = new Date(valueRef.current).getTime();
      const next = cur + 7 * 86400_000;
      if (next >= maxMs) {
        // Loop back to the beginning of the timeline so play is a continuous
        // animation instead of stopping immediately when already at the latest
        // date (which is the default "as of" value).
        onChangeRef.current(toISO(new Date(minMs)));
      } else {
        onChangeRef.current(toISO(new Date(next)));
      }
    }, 300);
    return () => {
      if (timer.current) window.clearInterval(timer.current);
    };
  }, [playing, minMs, maxMs, reducedMotion]);

  return (
    <div className="card p-4">
      <div className="flex flex-col sm:flex-row sm:items-center gap-3">
        <button type="button"className="btn btn-hover bg-slate-700 hover:bg-slate-600 min-h-11 sm:min-h-0"
          onClick={() => setPlaying((p) => !p)}
          aria-pressed={playing}
          disabled={reducedMotion}
        >
          {playing ? t("pause") : t("play")}
        </button>
        {reducedMotion ? (
          <span className="sr-only">
            {t("a11y.reducedMotionNote", "Animation disabled by your reduced-motion setting.")}
          </span>
        ) : null}
        <div className="flex-1">
          <label htmlFor="as-of-date" className="sr-only">{t("selectDate")}</label>
          <input
            id="as-of-date"
            type="range"
            min={minMs}
            max={maxMs}
            step={86400_000}
            value={valMs}
            onChange={(e) => onChange(toISO(new Date(Number(e.target.value))))}
            aria-valuetext={value}
            className="w-full accent-sky-500"
          />
          <div className="relative h-4 mt-1">
            {visibleTicks.map((tk) => {
              const ms = new Date(tk.start).getTime();
              if (!Number.isFinite(ms) || ms < minMs || ms > maxMs) return null;
              const pct = ((ms - minMs) / spanMs) * 100;
              return (
                <span
                  key={tk.label}
                  className="absolute text-xs text-slate-300 -translate-x-1/2 whitespace-nowrap"
                  style={{ left: `${pct}%` }}
                >
                  {tk.label}
                </span>
              );
            })}
          </div>
        </div>
        <div className="sm:text-right sm:min-w-[110px]">
          <div className="text-xs text-slate-300">{t("asOf")}</div>
          <output htmlFor="as-of-date" className="font-mono font-semibold">{value}</output>
        </div>
      </div>
    </div>
  );
}