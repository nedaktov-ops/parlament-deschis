import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

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
  const [playing, setPlaying] = useState(false);
  const timer = useRef<number | null>(null);
  const minMs = new Date(min).getTime();
  const maxMs = new Date(max).getTime();
  const valMs = new Date(value).getTime();
  const spanMs = Math.max(1, maxMs - minMs);

  useEffect(() => {
    if (!playing) return;
    timer.current = window.setInterval(() => {
      const cur = new Date(value).getTime();
      const next = cur + 7 * 86400_000;
      if (next >= maxMs) {
        onChange(toISO(new Date(maxMs)));
        setPlaying(false);
      } else {
        onChange(toISO(new Date(next)));
      }
    }, 120);
    return () => {
      if (timer.current) window.clearInterval(timer.current);
    };
  }, [playing, value, maxMs, onChange]);

  return (
    <div className="card p-4">
      <div className="flex items-center gap-3">
        <button
          className="btn bg-slate-700 hover:bg-slate-600"
          onClick={() => setPlaying((p) => !p)}
        >
          {playing ? t("pause") : t("play")}
        </button>
        <div className="flex-1">
          <input
            type="range"
            min={minMs}
            max={maxMs}
            step={86400_000}
            value={valMs}
            onChange={(e) => onChange(toISO(new Date(Number(e.target.value))))}
            className="w-full accent-sky-500"
          />
          <div className="relative h-4 mt-1">
            {ticks.map((tk) => {
              const ms = new Date(tk.start).getTime();
              if (!Number.isFinite(ms) || ms < minMs || ms > maxMs) return null;
              const pct = ((ms - minMs) / spanMs) * 100;
              return (
                <span
                  key={tk.label}
                  className="absolute text-[10px] text-slate-500 -translate-x-1/2"
                  style={{ left: `${pct}%` }}
                >
                  {tk.label}
                </span>
              );
            })}
          </div>
        </div>
        <div className="text-right min-w-[110px]">
          <div className="text-xs text-slate-400">{t("asOf")}</div>
          <div className="font-mono font-semibold">{value}</div>
        </div>
      </div>
    </div>
  );
}