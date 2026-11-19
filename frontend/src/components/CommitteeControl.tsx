import { useMemo } from "react";

export interface CommitteeControlData {
  as_of: string;
  total_committees: number;
  parties: Array<{
    party: string;
    chairs: number;
    share_pct: number;
  }>;
  chairs: Array<{
    committee_id: string;
    committee: string;
    chamber: string | null;
    chair_person_id: string;
    chair: string;
    party: string;
    chair_since: string | null;
  }>;
}

export interface CommitteeControlProps {
  data: CommitteeControlData;
  totalCommittees: number;
  onChairClick?: (chair: CommitteeControlData['chairs'][0]) => void;
  width?: number;
}

export default function CommitteeControl({
  data,
  totalCommittees,
  onChairClick,
  // width parameter kept for API consistency
}: CommitteeControlProps) {
  const { parties, chairs } = data;
  
  const topParties = useMemo(() => {
    return [...parties]
      .sort((a, b) => b.chairs - a.chairs)
      .slice(0, 5);
  }, [parties]);

  if (!parties?.length) {
    return (
      <div className="w-full bg-slate-800/30 rounded-xl p-4 overflow-hidden">
        <div className="text-xs text-slate-400 mb-2">Committee Control</div>
        <div className="flex items-center justify-center h-32 text-slate-500">
          Loading committee data...
        </div>
      </div>
    );
  }

  const maxVal = Math.max(...parties.map(p => p.chairs), 1);

  return (
    <div className="w-full bg-slate-800/30 rounded-xl p-4 overflow-hidden">
      <div className="text-xs text-slate-400 mb-2 flex justify-between items-center">
        <span>Committee Control</span>
        <span className="text-slate-300">
          {totalCommittees} committees
        </span>
      </div>
      
      <div className="space-y-1">
        {topParties.map((party, index) => {
          const widthPct = (party.chairs / maxVal) * 100;
          const percentage = party.share_pct;
          const chairForParty = chairs.find(c => c.party === party.party);
          
          return (
            <div key={party.party} className="group">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs w-8 text-slate-400">
                  {party.party}
                </span>
                <div 
                  className="relative flex-1 h-3 rounded-full bg-slate-700/30 overflow-hidden cursor-pointer"
                  onClick={() => chairForParty && onChairClick?.(chairForParty)}
                >
                  <div
                    className="absolute left-0 top-0 h-full rounded-full transition-all"
                    style={{
                      width: `${widthPct}%`,
                      backgroundColor: getPartyColor(party.party, index),
                      opacity: 0.7,
                    }}
                  />
                  <div
                    className="absolute right-0 top-0 h-full w-2 rounded-r-full"
                    style={{ backgroundColor: getPartyColor(party.party, index) }}
                  />
                </div>
                <span className="text-xs w-10 text-right text-slate-300">
                  {party.chairs}
                </span>
              </div>
              <div className="text-xs text-slate-500 text-right">
                {percentage.toFixed(1)}%
              </div>
            </div>
          );
        })}
      </div>
      
      <div className="mt-3 pt-2 border-t border-slate-700/30">
        <div className="text-xs text-slate-500 mb-2">Total chairs filled: {parties.reduce((sum, p) => sum + p.chairs, 0)}</div>
        <div className="grid grid-cols-3 gap-2 text-xs">
          <div className="text-center">
            <div className="text-2xl font-bold text-slate-100">
              {parties.length}
            </div>
            <div className="text-slate-500">Parties</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-slate-100">
              {parties.reduce((sum, p) => sum + p.chairs, 0)}
            </div>
            <div className="text-slate-500">Chairs</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-emerald-400">
              {parties.every(p => p.chairs > 0) ? '100%' : 'N/A'}
            </div>
            <div className="text-slate-500">Coverage</div>
          </div>
        </div>
      </div>
      
      {chairs.length > 0 && (
        <div className="mt-2">
          <details className="text-xs">
            <summary className="cursor-pointer text-sky-400 hover:underline">
              View all chairs ({chairs.length})
            </summary>
            <ul className="mt-2 space-y-1 max-h-32 overflow-y-auto">
              {chairs.slice(0, 10).map(chair => (
                <li key={chair.committee_id} className="flex justify-between">
                  <span className="text-slate-300">{chair.committee}</span>
                  <span className="text-slate-400">{chair.chair}</span>
                </li>
              ))}
            </ul>
          </details>
        </div>
      )}
    </div>
  );
}

function getPartyColor(party: string, index: number): string {
  const colors: Record<string, string> = {
    'PSD': 'rgba(56, 189, 228, 0.8)',
    'PNL': 'rgba(34, 197, 94, 0.8)',
    'USR': 'rgba(245, 158, 11, 0.8)',
    'PPE': 'rgba(219, 78, 40, 0.8)',
    'PLUS': 'rgba(167, 139, 250, 0.8)',
  };
  return colors[party] || `hsl(${index * 60}, 50%, 50%)`;
}