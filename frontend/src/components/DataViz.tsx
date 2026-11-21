export interface SparklineProps {
  data: number[];
  height?: number;
  color?: string;
}

/** Build the SVG polyline `points` string. Exported for the no-NaN unit test. */
export function sparklinePoints(data: number[]): string {
  if (data.length === 0) return "";

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  // A single sample makes `data.length - 1 === 0`; clamping the denominator
  // to >= 1 prevents 0/0 -> NaN (which produced `<polyline points="NaN,100">`).
  const denominator = Math.max(1, data.length - 1);

  return data
    .map((v, i) => {
      const x = (i / denominator) * 100;
      const y = 100 - ((v - min) / range) * 100;
      return `${x},${y}`;
    })
    .join(" ");
}

export function Sparkline({
  data,
  height = 40,
  color = "stroke-sky-400",
}: SparklineProps) {
  if (data.length === 0) return null;

  const points = sparklinePoints(data);

  return (
    <svg
      width="100%"
      height={height}
      viewBox="0 0 100 100"
      preserveAspectRatio="none"
      role="img"
      aria-hidden="true"
      className={color}
    >
      <polyline points={points} fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export type DataBarTone = "accent" | "success" | "warning" | "danger" | "info";

export interface DataBarProps {
  value: number;
  max: number;
  label?: string;
  tone?: DataBarTone;
}

const DATA_BAR_TONE: Record<DataBarTone, string> = {
  accent: "data-bar-fill--accent",
  success: "data-bar-fill--success",
  warning: "data-bar-fill--warning",
  danger: "data-bar-fill--danger",
  info: "data-bar-fill--info",
};

export function DataBar({
  value,
  max,
  label,
  tone = "accent",
}: DataBarProps) {
  const width = max > 0 ? Math.min(100, Math.max(0, (value / max) * 100)) : 0;

  return (
    <div className="flex flex-col gap-1">
      {label && (
        <div className="flex justify-between text-xs text-slate-300">
          <span>{label}</span>
          <span className="font-mono text-slate-100">{value}</span>
        </div>
      )}
      <div className="data-bar">
        <div
          className={`data-bar-fill ${DATA_BAR_TONE[tone]}`}
          style={{ width: `${width}%` }}
        />
      </div>
    </div>
  );
}

export interface ProgressRingProps {
  value: number;
  max?: number;
  color?: string;
  size?: number;
}

export function ProgressRing({
  value,
  max = 100,
  color = "stroke-emerald-400",
  size = 60,
}: ProgressRingProps) {
  const pct = max > 0 ? Math.min(100, Math.max(0, (value / max) * 100)) : 0;
  // r=22 + strokeWidth/2=2 lands exactly on the 48-unit viewBox edge;
  // the old r=24 clipped half the stroke.
  const radius = 22;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (pct / 100) * circumference;

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      role="img"
      aria-label={`${pct}% complete`}
      className={`rotate-[-90deg] ${color}`}
    >
      <circle
        cx="24" cy="24" r={radius}
        fill="none"
        stroke="rgb(var(--slate-700) / 0.4)"
        strokeWidth="4"
      />
      <circle
        cx="24" cy="24" r={radius}
        fill="none"
        stroke="currentColor"
        strokeWidth="4"
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        strokeLinecap="round"
        className="transition-all duration-500 ease-out"
      />
      <text
        x="24" y="28"
        textAnchor="middle"
        fontSize="10"
        fontFamily="ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace"
        fill="rgb(var(--slate-200))"
      >
        {Math.round(pct)}%
      </text>
    </svg>
  );
}

export interface StatBadgeProps {
  number: number;
  label: string;
  color?: string;
}

export function StatBadge({
  number,
  label,
  color = "text-slate-400",
}: StatBadgeProps) {
  return (
    <span className="badge">
      <span className={`w-2 h-2 shrink-0 rounded-full ${color.replace("text-", "bg-")}`} />
      <span className={`text-xs ${color}`}>{number}</span>
      <span className="text-xs text-slate-500">{label}</span>
    </span>
  );
}
