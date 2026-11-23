import { useMemo } from "react";

export interface CohortData {
  label: string;
  minAge?: number;
  maxAge?: number;
  count: number;
  avgAge: number;
}

export interface AgeDistributionRadialProps {
  cohorts: CohortData[];
  totalAge: number;
  width?: number;
  height?: number;
}

/* On-palette cycle: no violet, purple, cyan or pink. Values are CSS colours so
   the same source works in SVG `fill` and in an inline `style` for the legend. */
const COHORT_FILLS = [
  "rgb(var(--accent-rgb))",
  "rgb(var(--success-rgb))",
  "rgb(var(--warning-rgb))",
  "rgb(var(--danger-rgb))",
  "rgb(var(--info-rgb))",
];

function getCohortColor(index: number): string {
  return COHORT_FILLS[index % COHORT_FILLS.length];
}

export default function AgeDistributionRadial({
  cohorts,
  totalAge,
  width = 200,
  height = 200,
}: AgeDistributionRadialProps) {
  const radius = Math.min(width, height) / 2 - 10;
  const centerX = width / 2;
  const centerY = height / 2;

  const arcs = useMemo(() => {
    if (!cohorts.length || totalAge <= 0) return [];
    let cumulativeAngle = 0;
    return cohorts.map((cohort) => {
      const startAngle = cumulativeAngle;
      const endAngle = cumulativeAngle + (2 * Math.PI * cohort.count / totalAge);
      cumulativeAngle = endAngle;
      return { ...cohort, startAngle, endAngle };
    });
  }, [cohorts, totalAge]);

  const avgAge = useMemo(
    () => totalAge > 0
      ? cohorts.reduce((sum, c) => sum + c.count * c.avgAge, 0) / totalAge
      : 0,
    [cohorts, totalAge],
  );

  const arcPath = (startAngle: number, endAngle: number) => {
    const x1 = centerX + radius * Math.cos(startAngle);
    const y1 = centerY + radius * Math.sin(startAngle);
    const x2 = centerX + radius * Math.cos(endAngle);
    const y2 = centerY + radius * Math.sin(endAngle);
    const largeArc = endAngle - startAngle > Math.PI ? 1 : 0;
    return `M ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} L ${centerX} ${centerY} Z`;
  };

  return (
    <div className="surface p-4 overflow-hidden">
      <div className="text-xs text-slate-400 mb-2">Age Distribution</div>
      <div className="flex items-center justify-center">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          fill="none"
          className="w-32 h-32"
          role="img"
          aria-label={`Age distribution across ${cohorts.length} cohorts, average age ${avgAge.toFixed(0)}`}
        >
          <circle
            cx={centerX} cy={centerY} r={radius}
            fill="rgb(var(--slate-800) / 0.5)"
            stroke="rgb(var(--slate-600) / 0.4)"
            strokeWidth={1}
          />
          {arcs.map((slice, i) => (
            <path
              key={slice.label}
              d={arcPath(slice.startAngle, slice.endAngle)}
              fill={getCohortColor(i)}
              opacity={0.85}
            >
              <title>{`${slice.label}: ${slice.count} (avg ${slice.avgAge.toFixed(1)})`}</title>
            </path>
          ))}
          <circle
            cx={centerX} cy={centerY} r={(avgAge / 100) * radius}
            fill="rgb(var(--slate-400) / 0.18)"
            stroke="rgb(var(--slate-400) / 0.6)"
            strokeWidth={1}
          />
          <circle cx={centerX} cy={centerY} r={radius * 0.1} fill="rgb(var(--slate-400) / 0.6)" />
          {avgAge > 0 && (
            <text
              x={centerX} y={centerY + 4}
              textAnchor="middle"
              dominantBaseline="middle"
              fill="rgb(var(--slate-100))"
              fontSize={10}
              fontWeight="600"
            >
              {avgAge.toFixed(0)}
            </text>
          )}
        </svg>
      </div>

      <ul className="mt-3 grid grid-cols-2 gap-1 text-xs">
        {cohorts.map((c, i) => (
          <li key={c.label} className="flex items-center gap-2">
            <span
              aria-hidden="true"
              className="w-3 h-3 shrink-0 rounded-full"
              style={{ backgroundColor: getCohortColor(i) }}
            />
            <span className="text-slate-300 truncate">{c.label}: {c.count}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
