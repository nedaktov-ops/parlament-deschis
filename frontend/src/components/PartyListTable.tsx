import { useMemo } from "react";

interface PartyNode {
  id: string;
  short_name: string;
  name: string;
  color: string | null;
  total_members: number;
  switches_in: number;
}

export interface PartyListTableProps {
  parties: PartyNode[];
  onPartyClick?: (partyShortName: string) => void;
  maxRows?: number;
}

export default function PartyListTable({
  parties,
  onPartyClick,
  maxRows = 10,
}: PartyListTableProps) {
  const sortedParties = useMemo(() => {
    return [...parties]
      .sort((a, b) => b.total_members - a.total_members)
      .slice(0, maxRows);
  }, [parties, maxRows]);

  const totalMembers = useMemo(() => {
    return parties.reduce((sum, p) => sum + p.total_members, 0);
  }, [parties]);

  if (!parties?.length) {
    return (
      <div className="w-full bg-slate-800/30 rounded-xl p-4 overflow-hidden">
        <div className="text-xs text-slate-400 mb-2">Party Representation</div>
        <div className="flex items-center justify-center h-32 text-slate-500">
          Loading party data...
        </div>
      </div>
    );
  }

  return (
    <div className="w-full bg-slate-800/30 rounded-xl p-4 overflow-hidden">
      <div className="text-xs text-slate-400 mb-2 flex justify-between items-center">
        <span>Party Representation</span>
        <span className="text-slate-300">
          {parties.length} parties
        </span>
      </div>
      
      <div className="space-y-1 max-h-64 overflow-y-auto">
        {sortedParties.map((party, index) => {
          const percentage = totalMembers > 0 ? (party.total_members / totalMembers) * 100 : 0;
          const rankColor = index === 0 ? "text-amber-400" : index === 1 ? "text-slate-300" : index === 2 ? "text-rose-400" : "text-slate-400";
          
          return (
            <div
              key={party.id}
              onClick={() => onPartyClick?.(party.short_name || party.id)}
              className="group flex items-center gap-3 p-2 rounded-lg hover:bg-slate-700/30 cursor-pointer transition-all"
            >
              <div className="flex items-center gap-2 w-12">
                <span className={`text-xs font-bold ${rankColor}`}>
                  #{index + 1}
                </span>
              </div>
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span 
                    className="w-3 h-3 rounded-full" 
                    style={{ backgroundColor: party.color || "#64748b" }}
                  />
                  <span className="text-sm font-medium text-slate-200 truncate">
                    {party.short_name || party.name}
                  </span>
                </div>
              </div>
              
              <div className="text-right">
                <div className="text-sm font-bold text-slate-100">
                  {party.total_members.toLocaleString()}
                </div>
                <div className="text-xs text-slate-500">
                  {percentage.toFixed(1)}%
                </div>
              </div>
              
              {party.switches_in > 0 && (
                <div className="text-xs text-amber-400 font-medium">
                  ↗{party.switches_in}
                </div>
              )}
            </div>
          );
        })}
      </div>
      
      <div className="mt-3 pt-2 border-t border-slate-700/30 flex justify-between text-xs">
        <span className="text-slate-500">Total: {totalMembers.toLocaleString()}</span>
        <span 
          className="text-sky-400 cursor-pointer hover:underline"
          onClick={() => onPartyClick?.('all')}
        >
          View all →
        </span>
      </div>
    </div>
  );
}