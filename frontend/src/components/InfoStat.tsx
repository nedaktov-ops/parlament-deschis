import { memo } from "react";

export interface InfoStatProps {
  /** The stat label shown above the value. */
  label: string;
  /** The main value, rendered as a formatted number or raw string. */
  value: number | string;
  /** Maximum value used to compute the bar percentage. */
  max?: number;
  /** Value used for the bar (defaults to `value` when it is a number). */
  barValue?: number;
  /** Border-top accent colour (defaults to "sky"). */
  accent?: "sky" | "emerald" | "amber" | "rose";
  /** Show the data bar below the value (defaults to true). */
  showBar?: boolean;
  /** Show a small trend indicator (defaults to false). */
  showTrend?: boolean;
}

const ACCENT_BORDER: Record<"sky" | "emerald" | "amber" | "rose", string> = {
  sky: "border-t-sky-400",
  emerald: "border-t-emerald-400",
  amber: "border-t-amber-400",
  rose: "border-t-rose-400",
};

const ACCENT_BAR: Record<"sky" | "emerald" | "amber" | "rose", string> = {
  sky: "bg-sky-400/70",
  emerald: "bg-emerald-400/70",
  amber: "bg-amber-400/70",
  rose: "bg-rose-400/70",
};

function InfoStat({
  label,
  value,
  max,
  barValue,
  accent = "sky",
  showBar = true,
  showTrend = false,
}: InfoStatProps) {
  const numeric = typeof value === "number" ? value : barValue ?? 0;
  const limit = max ?? 0;
  const width = limit > 0 ? Math.min(100, Math.max(0, (numeric / limit) * 100)) : 0;
  const renderBar = showBar && limit > 0;

  return (
    <div
      className={[
        "bg-slate-800 rounded-xl border border-slate-700/50 p-4 shadow-sm",
        "print:bg-slate-100 print:border print:border-slate-300 print:shadow-none",
        `border-t-2 ${ACCENT_BORDER[accent]} print:border-t-2`,
        "card-hover hover:shadow-lg print:hover:translate-y-0",
      ].join(" ")}
    >
      <div className="flex items-end justify-between gap-2 mb-2">
        <span className="text-xs font-medium text-slate-400 tracking-wide uppercase print:text-slate-600">
          {label}
        </span>
        <span className="text-2xl font-bold text-slate-100 leading-none print:text-slate-900">
          {typeof value === "number" ? value.toLocaleString() : value}
        </span>
      </div>
      {renderBar && (
        <div
          className="h-1.5 w-full rounded-full bg-slate-700/40 overflow-hidden print:hidden"
          aria-hidden="true"
        >
          <div
            className={`h-full origin-left ${ACCENT_BAR[accent]}`}
            style={{ width: `${width}%` }}
          />
        </div>
      )}
      {showTrend && (
        <span className="text-slate-500 text-xs print:hidden" aria-hidden="true">
          ▪
        </span>
      )}
    </div>
  );
}

export { InfoStat };
export default memo(InfoStat);
