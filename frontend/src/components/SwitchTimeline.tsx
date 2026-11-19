import { useMemo } from "react";

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

const WIDTH = 500;

export default function SwitchTimeline({
  waves,
  legislatures,
  onWaveClick,
  height = 120,
}: SwitchTimelineProps) {
  const timelineData = useMemo(() => {
    const sortedLegs = Object.values(legislatures)
      .filter(l => l.start)
      .sort((a, b) => (a.start ?? "").localeCompare(b.start ?? ""));
    
    const startDate = sortedLegs[0]?.start || "1990-06-18";
    const startDateObj = new Date(startDate);
    const endDate = new Date();
    const durationMs = endDate.getTime() - startDateObj.getTime();
    
    return {
      legs: sortedLegs,
      startDate,
      totalSwiches: waves.reduce((sum, w) => sum + w.switch_count, 0),
      wavesByDate: waves.map(wave => ({
        ...wave,
        daysFromStart: wave.start_date 
          ? Math.round((new Date(wave.start_date).getTime() - startDateObj.getTime()) / (durationMs / 100)) 
          : 0,
      })),
      durationMs,
    };
  }, [legislatures, waves]);

  const xScale = (days: number) => (days / 100) * WIDTH;
  const barHeight = 20;
  const barSpacing = 8;

  if (!waves?.length) {
    return (
      <div className="w-full bg-slate-800/30 rounded-xl p-4 overflow-hidden">
        <div className="text-xs text-slate-400 mb-2">Switch Timeline</div>
        <div className="flex items-center justify-center h-32 text-slate-500">
          No activity data
        </div>
      </div>
    );
  }

  const activeWaves = timelineData.wavesByDate
    .filter(w => w.daysFromStart >= 0 && w.daysFromStart <= 100)
    .sort((a, b) => b.switch_count - a.switch_count)
    .slice(0, 8);

  return (
    <div className="w-full bg-slate-800/30 rounded-xl p-4 overflow-hidden">
      <div className="text-xs text-slate-400 mb-2">Switch Waves</div>
      <div className="relative h-8">
        {/* Timeline bar */}
        <div 
          className="absolute top-1/2 -translate-y-1/2 bg-slate-700/30 rounded-full h-2"
          style={{ left: 0, right: 0 }}
        />
        
        {/* Legislature markers */}
        {timelineData.legs.map(leg => {
          const legDate = leg.start ? new Date(leg.start).getTime() : null;
          if (!legDate) return null;
          
          const x = xScale(Math.round((legDate - new Date(timelineData.startDate).getTime()) / (timelineData.durationMs / 100)));
          
          return (
            <g key={leg.label}>
              <line
                x1={x}
                y1="0"
                x2={x}
                y2={height}
                stroke="rgba(156, 163, 175, 0.5)"
                strokeWidth={1}
              />
              <text
                x={x}
                y={height + 16}
                textAnchor="middle"
                fontSize={7}
                fill="#94a3b8"
              >
                {leg.label}
              </text>
            </g>
          );
        })}
        
        {/* Switch wave bars */}
        {activeWaves.map((wave, idx) => {
          const x = Math.max(0, Math.min(WIDTH - 20, xScale(wave.daysFromStart)));
          const barWidth = Math.min(20, WIDTH * 0.03);
          const intensity = Math.min(1, wave.switch_count / 100);
          
          return (
            <g key={wave.id}>
              <rect
                x={x}
                y={idx * (barHeight + barSpacing)}
                width={barWidth}
                height={barHeight}
                fill="rgba(236, 72, 153, 0.6)"
                opacity={intensity}
                onClick={() => onWaveClick?.(wave)}
                className="cursor-pointer hover:opacity-100 transition-opacity"
              />
              <text
                x={x + barWidth + 4}
                y={idx * (barHeight + barSpacing) + barHeight / 2 + 3}
                fontSize={7}
                fill="#94a3b8"
              >
                {wave.switch_count}
              </text>
            </g>
          );
        })}
      </div>
      
      <div className="mt-2 flex justify-between text-xs">
        <span className="text-slate-500">
          {waves.length} events
        </span>
        <span 
          className="text-sky-400 cursor-pointer" 
          onClick={() => onWaveClick?.({id: 'all', label: null, start_date: null, end_date: null, switch_count: timelineData.totalSwiches, trigger_type: null, legislature: null, chamber: null} as SwitchWaveData)}
        >
          View all →
        </span>
      </div>
    </div>
  );
}