import { useMemo } from "react";

export interface TimelineStripProps {
  legislatures: Record<string, { 
    label: string; 
    start: string | null; 
    end: string | null 
  }>;
  switchWaves?: Array<{
    start_date: string;
    switch_count: number;
  }>;
  asOf?: string;
  minDate?: string;
  maxDate?: string;
}

export default function TimelineStrip({
  legislatures,
  switchWaves = [],
  asOf,
  minDate,
  maxDate,
}: TimelineStripProps) {
  const timelineData = useMemo(() => {
    const legs = Object.values(legislatures)
      .filter(l => l.start)
      .sort((a, b) => (a.start ?? "").localeCompare(b.start ?? ""));
    
    const startDate = minDate || legs[0]?.start || "1990-06-18";
    const endDate = maxDate || asOf || new Date().toISOString().split('T')[0];
    
    const startObj = new Date(startDate);
    const endObj = new Date(endDate);
    const durationMs = endObj.getTime() - startObj.getTime();
    
    return {
      legs,
      startDate,
      endDate,
      durationMs,
      wavesByDate: switchWaves
        .filter(w => w.start_date)
        .map(w => ({
          ...w,
          daysFromStart: Math.round(
            (new Date(w.start_date!).getTime() - startObj.getTime()) / 
            (durationMs / 100)
          ),
          intensity: Math.min(1, w.switch_count / 100),
        })),
    };
  }, [legislatures, switchWaves, minDate, maxDate, asOf]);

  if (!timelineData.legs.length) {
    return (
      <div className="w-full bg-slate-800/30 rounded-xl p-4 overflow-hidden">
        <div className="text-xs text-slate-400 mb-2">Legislative Timeline</div>
        <div className="h-8 flex items-center justify-center">
          <span className="text-slate-500">Loading timeline data...</span>
        </div>
      </div>
    );
  }

  const xScale = (days: number) => (days / 100) * 400;

  return (
    <div className="w-full bg-slate-800/30 rounded-xl p-4 overflow-hidden">
      <div className="text-xs text-slate-400 mb-2 flex justify-between items-center">
        <span>Timeline</span>
        <span className="text-slate-300">
          {timelineData.legs.length} periods
        </span>
      </div>
      
      <div className="relative h-8">
        {/* Background timeline */}
        <div className="absolute inset-y-0 left-0 right-0 flex items-center">
          <div className="h-1 bg-slate-700/30 rounded-full flex-1 mx-2" />
        </div>
        
        {/* Legislature markers */}
        {timelineData.legs.map(leg => {
          const legDate = leg.start ? new Date(leg.start).getTime() : null;
          if (!legDate) return null;
          
          const x = xScale(Math.round(
            (legDate - new Date(timelineData.startDate).getTime()) / 
            (timelineData.durationMs / 100)
          ));
          
          return (
            <g key={leg.label} style={{ position: 'absolute', left: `${x}%` }}>
              <line
                x1="50%"
                y1="0"
                x2="50%"
                y2="100%"
                stroke="rgba(156, 163, 175, 0.5)"
                strokeWidth={1}
              />
              <text
                x="50%"
                y="110%"
                textAnchor="middle"
                fontSize={7}
                fill="#94a3b8"
                dominantBaseline="middle"
              >
                {leg.label}
              </text>
            </g>
          );
        })}
        
        {/* Switch wave indicators */}
        {timelineData.wavesByDate.map((wave, idx) => (
          <g key={wave.start_date || idx} style={{ position: 'absolute', left: `${xScale(wave.daysFromStart)}%` }}>
            <circle
              cx="50%"
              cy="50%"
              r={2 + wave.intensity * 3}
              fill="rgba(236, 72, 153, 0.8)"
              className="cursor-pointer"
              onClick={() => {
                // TODO: Add click handler to navigate to traseism detail
              }}
            />
            <text
              x="50%"
              y="60%"
              textAnchor="middle"
              fontSize={5}
              fill="#cbd5e1"
              dominantBaseline="middle"
            >
              {wave.switch_count}
            </text>
          </g>
        ))}
      </div>
      
      {/* Timeline legend */}
      <div className="mt-2 flex justify-between text-xs">
        <span className="text-slate-500">Events: {switchWaves.length}</span>
        <span className="text-slate-500">
          {timelineData.startDate} — {timelineData.endDate}
        </span>
      </div>
    </div>
  );
}