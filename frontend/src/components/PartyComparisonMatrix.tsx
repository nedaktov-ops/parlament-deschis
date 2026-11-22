import { useTranslation } from "react-i18next";

export interface SwitchMatrixCell {
  from: string;
  to: string;
  count: number;
}

export interface PartyComparisonMatrixProps {
  matrix: SwitchMatrixCell[];
  onCellClick?: (from: string, to: string) => void;
  maxRows?: number;
}

export default function PartyComparisonMatrix({
  matrix,
  onCellClick,
  maxRows,
}: PartyComparisonMatrixProps) {
  const { t } = useTranslation();
  const topMatrix = matrix
    .sort((a, b) => b.count - a.count)
    .slice(0, maxRows || 8);

  if (!matrix?.length) {
    return (
      <div className="w-full bg-slate-800/30 rounded-xl p-4 overflow-hidden">
        <div className="text-xs text-slate-400 mb-2">Party Comparison</div>
        <div className="flex items-center justify-center h-32 text-slate-500">
          Loading matrix data...
        </div>
      </div>
    );
  }

  return (
    <div className="w-full bg-slate-800/30 rounded-xl p-4 overflow-hidden">
      <div className="text-xs text-slate-400 mb-2 flex justify-between items-center">
        <span>Switch Matrix</span>
        <span className="text-slate-300">
          {matrix.length} transitions
        </span>
      </div>
      
      <div className="space-y-2 max-h-64 overflow-y-auto" tabIndex={0} role="region" aria-label={t("a11y.switchMatrixScroll", "Scrollable party switch matrix")}>
        {topMatrix.map((cell, idx) => {
          const intensity = Math.min(1, cell.count / 20);
          
          return (
            <button
              type="button"
              key={`${cell.from}-${cell.to}-${idx}`}
              onClick={() => onCellClick?.(cell.from, cell.to)}
              className="flex w-full items-center gap-3 p-2 rounded-lg hover:bg-slate-700/30 cursor-pointer transition-all btn-hover min-h-11"
            >
              <span className="text-xs text-slate-500 w-12">{cell.from} →</span>
              <div 
                className="flex-1 h-2 rounded-full bg-slate-700/30 overflow-hidden"
              >
                <div
                  className="h-full rounded-full transition-all"
                  style={{
                    width: `${Math.min(100, intensity * 100)}%`,
                    backgroundColor: `rgba(236, 72, 153, ${0.4 + intensity * 0.5})`,
                  }}
                />
              </div>
              <span className="text-xs font-mono text-slate-200 w-8 text-right">
                {cell.count}
              </span>
              <span className="text-xs text-slate-400">→ {cell.to}</span>
            </button>
          );
        })}
      </div>
      
      <div className="mt-3 pt-2 border-t border-slate-700/30">
        <div className="text-xs text-slate-500 mb-2">
          Top transitions show major party switching activity
        </div>
        <button
          type="button"
          onClick={() => onCellClick?.('all', 'all')}
          className="text-sky-400 hover:underline text-xs"
        >
          View all transitions →
        </button>
      </div>
    </div>
  );
}