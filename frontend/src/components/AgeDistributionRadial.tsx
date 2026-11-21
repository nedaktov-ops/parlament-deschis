import { useMemo } from "react";

export interface CohortData {
  label: string;
  // The radial chart only uses count/avgAge; the API has no age range.
  minAge?: number;
  maxAge?: number;
  count: number;
  avgAge: number;
}

export interface AgeDistributionRadialProps {
  cohorts: CohortData[];
  totalAge: number;
  onCohortClick?: (cohort: CohortData) => void;
  width?: number;
  height?: number;
}

export default function AgeDistributionRadial({
  cohorts,
  totalAge,
  onCohortClick,
  width = 200,
  height = 200,
}: AgeDistributionRadialProps) {
  const radius = Math.min(width, height) / 2 - 10;
  const centerX = width / 2;
  const centerY = height / 2;

  const arcs = useMemo(() => {
    if (!cohorts.length || totalAge === 0) return [];
    
    let cumulativeAngle = 0;
    const slices = cohorts.map(cohort => {
      const slice = {
        ...cohort,
        startAngle: cumulativeAngle,
        endAngle: cumulativeAngle + (2 * Math.PI * cohort.count / totalAge),
        arc: (cumulativeAngle: number, endAngle: number) => {
          const x1 = centerX + radius * Math.cos(cumulativeAngle);
          const y1 = centerY + radius * Math.sin(cumulativeAngle);
          const x2 = centerX + radius * Math.cos(endAngle);
          const y2 = centerY + radius * Math.sin(endAngle);
          
          const largeArc = endAngle - cumulativeAngle > Math.PI ? 1 : 0;
          
          return `M ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2} L ${centerX} ${centerY} Z`;
        }
      };
      cumulativeAngle = slice.endAngle;
      return slice;
    });
    return slices;
  }, [cohorts, totalAge, centerX, centerY, radius]);

  const avgAge = useMemo(() => {
    if (!cohorts.length) return 0;
    const weightedSum = cohorts.reduce((sum, c) => sum + (c.count * c.avgAge), 0);
    return weightedSum / totalAge;
  }, [cohorts, totalAge]);

  return (
    <div className="w-full bg-slate-800/30 rounded-xl p-4 overflow-hidden">
      <div className="text-xs text-slate-400 mb-2">Age Distribution</div>
      <div className="flex items-center justify-center">
        <svg viewBox="0 0 200 200" fill="none" className="w-32 h-32">
          {/* Background circle */}
          <circle
            cx={centerX}
            cy={centerY}
            r={radius}
            fill="rgba(30, 41, 59, 0.5)"
            stroke="rgba(255,255,255,0.05)"
            strokeWidth={1}
          />
          
          {/* Age cohorts as colored arcs */}
          {arcs.map((slice, i) => (
            <path
              key={slice.label}
              d={slice.arc(slice.startAngle, slice.endAngle)}
              fill={getCohortColor(i)}
              opacity={0.7}
              onClick={() => onCohortClick?.(slice)}
              className="cursor-pointer hover:opacity-100 transition-opacity"
            />
          ))}
          
          {/* Center circle with average age */}
          <circle
            cx={centerX}
            cy={centerY}
            r={avgAge / 100 * radius}
            fill="rgba(255, 255, 255, 0.1)"
            stroke="rgba(156, 163, 175, 0.3)"
            strokeWidth={1}
          />
          <circle
            cx={centerX}
            cy={centerY}
            r={radius * 0.1}
            fill="rgba(156, 163, 175, 0.5)"
          />
          
          {/* Average age text */}
          {avgAge > 0 && (
            <text
              x={centerX}
              y={centerY + 4}
              textAnchor="middle"
              dominantBaseline="middle"
              fill="white"
              fontSize={10}
              fontWeight="600"
            >
              {avgAge.toFixed(0)}
            </text>
          )}
        </svg>
      </div>
      
      {/* Legend */}
      <div className="mt-3 grid grid-cols-2 gap-1 text-xs">
        {cohorts.slice(0, 4).map((c, i) => (
          <div key={c.label} className="flex items-center gap-2">
            <div 
              className="w-3 h-3 rounded-full" 
              style={{ backgroundColor: getCohortColor(i) }}
            />
            <span className="text-slate-300 truncate">
              {c.label}: {c.count}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function getCohortColor(index: number): string {
  const colors = [
    "rgba(56, 189, 228, 0.6)",
    "rgba(34, 197, 94, 0.6)",
    "rgba(245, 158, 11, 0.6)",
    "rgba(219, 78, 40, 0.6)",
    "rgba(167, 139, 250, 0.6)",
    "rgba(236, 72, 153, 0.6)",
    "rgba(16, 185, 129, 0.6)",
    "rgba(245, 158, 11, 0.6)",
  ];
  return colors[index % colors.length];
}