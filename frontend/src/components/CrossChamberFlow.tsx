import { useMemo } from "react";

export interface CrossChamberPerson {
  person_id: string;
  name: string;
  chambers: Array<"deputies" | "senate">;
  deputies: string[];
  senate: string[];
}

export interface CrossChamberFlowProps {
  data: CrossChamberPerson[];
  onPersonClick?: (personId: string) => void;
  // width and height are not currently used but kept for future extensibility
  width?: number;
  height?: number;
}

export default function CrossChamberFlow({
  data,
  onPersonClick,
  // width and height intentionally unused for now
}: CrossChamberFlowProps) {
  const stats = useMemo(() => {
    const deputies = data.filter(d => d.chambers.includes('deputies')).length;
    const senate = data.filter(d => d.chambers.includes('senate')).length;
    const both = data.length;
    
    return {
      deputies,
      senate,
      both,
      total: data.length,
    };
  }, [data]);

  if (!data?.length) {
    return (
      <div className="w-full bg-slate-800/30 rounded-xl p-4 overflow-hidden">
        <div className="text-xs text-slate-400 mb-2">Cross-Chamber Movement</div>
        <div className="flex items-center justify-center h-32 text-slate-500">
          Loading cross-chamber data...
        </div>
      </div>
    );
  }

  const topMembers = useMemo(() => {
    return [...data]
      .sort((a, b) => a.name.localeCompare(b.name))
      .slice(0, 5);
  }, [data]);

  // Flow percentages
  const deputiesPct = stats.total > 0 ? (stats.deputies / stats.total) * 100 : 0;
  const senatePct = stats.total > 0 ? (stats.senate / stats.total) * 100 : 0;

  return (
    <div className="w-full bg-slate-800/30 rounded-xl p-4 overflow-hidden">
      <div className="text-xs text-slate-400 mb-2 flex justify-between items-center">
        <span>Cross-Chamber</span>
        <span className="text-slate-300">
          {stats.total} MPs
        </span>
      </div>
      
      {/* Flow visualization */}
      <div className="relative h-8 mb-3">
        {/* Deputies bar */}
        <div 
          className="absolute left-0 top-0 h-full bg-sky-400/40 rounded-l-lg cursor-pointer"
          style={{ width: `${deputiesPct}%` }}
          onClick={() => onPersonClick?.(data[0]?.person_id || '')}
        />
        
        {/* Senate bar */}
        <div 
          className="absolute left-0 top-0 h-full bg-rose-400/40 rounded-r-lg cursor-pointer"
          style={{ width: `${senatePct}%` }}
          onClick={() => onPersonClick?.(data[0]?.person_id || '')}
        />
        
        {/* Both indicator */}
        {stats.total > 0 && (
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-xs font-bold text-slate-200">
              {stats.both} in both
            </span>
          </div>
        )}
      </div>
      
      {/* Stats */}
      <div className="grid grid-cols-3 gap-2 text-xs text-center">
        <div>
          <div className="text-lg font-bold text-sky-400">{stats.deputies}</div>
          <div className="text-slate-500">Deputies</div>
        </div>
        <div>
          <div className="text-lg font-bold text-slate-300">{stats.both}</div>
          <div className="text-slate-500">Both</div>
        </div>
        <div>
          <div className="text-lg font-bold text-rose-400">{stats.senate}</div>
          <div className="text-slate-500">Senate</div>
        </div>
      </div>
      
      {/* Top members list */}
      {topMembers.length > 0 && (
        <div className="mt-3 pt-2 border-t border-slate-700/30">
          <div className="text-xs text-slate-400 mb-2">Cross-chamber MPs</div>
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {topMembers.map((member) => (
              <div
                key={member.person_id}
                onClick={() => onPersonClick?.(member.person_id)}
                className="flex items-center justify-between p-1 rounded hover:bg-slate-700/30 cursor-pointer"
              >
                <span className="text-xs text-slate-300 truncate">
                  {member.name}
                </span>
                <div className="flex gap-1">
                  {member.chambers.includes('deputies') && (
                    <span className="text-xs bg-sky-400/20 px-1 rounded">D</span>
                  )}
                  {member.chambers.includes('senate') && (
                    <span className="text-xs bg-rose-400/20 px-1 rounded">S</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}