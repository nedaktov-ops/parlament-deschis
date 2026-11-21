import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { StateView, type ViewState } from "./ui/AsyncState";

export interface CoverageRow {
  chamber: string;
  legislature: string | null;
  period_start: string | null;
  period_end: string | null;
  completeness: string;
  note: string | null;
  persons: number;
  total_memberships: number;
  dated_pct: number | null;
  sourced_pct: number | null;
  total_switches: number;
  sourced_switches_pct: number | null;
  last_refresh: string | null;
}

export interface DataQualityGaugeProps {
  coverageData: CoverageRow[];
  // width and height are not currently used but kept for future extensibility
  width?: number;
  height?: number;
  view?: ViewState;
  onRetry?: () => void;
}

export default function DataQualityGauge({
  coverageData,
  view,
  onRetry,
  // width and height intentionally unused for now
}: DataQualityGaugeProps) {
  const { t } = useTranslation();
  const stats = useMemo(() => {
    if (!coverageData?.length) return null;
    
    const totalRows = coverageData.length;
    const fullCoverage = coverageData.filter(c => c.completeness === 'full').length;
    const partialCoverage = coverageData.filter(c => c.completeness === 'partial').length;
    
    const avgDated = coverageData
      .filter(c => c.dated_pct !== null)
      .reduce((sum, c) => sum + (c.dated_pct || 0), 0) / 
      (coverageData.filter(c => c.dated_pct !== null).length || 1);
      
    const avgSourced = coverageData
      .filter(c => c.sourced_pct !== null)
      .reduce((sum, c) => sum + (c.sourced_pct || 0), 0) / 
      (coverageData.filter(c => c.sourced_pct !== null).length || 1);
      
    return {
      totalRows,
      fullCoverage,
      partialCoverage,
      avgDated: Math.round(avgDated),
      avgSourced: Math.round(avgSourced),
      completenessScore: Math.round((fullCoverage / totalRows) * 100),
    };
  }, [coverageData]);

  if (view && view !== "ready") {
    return (
      <StateView
        view={view}
        variant="inline"
        onRetry={onRetry}
        errorLabel={t("dashboard.loadError")}
        emptyTitle={t("state.empty.dataQuality")}
      />
    );
  }

  if (!stats) {
    return (
      <StateView
        view="empty"
        variant="inline"
        emptyTitle={t("state.empty.dataQuality")}
      />
    );
  }

  const completenessColor = stats.completenessScore >= 90 
    ? 'text-emerald-400' 
    : stats.completenessScore >= 70 
    ? 'text-amber-400' 
    : 'text-rose-400';

  return (
    <div className="w-full bg-slate-800/30 rounded-xl p-4 overflow-hidden">
      <div className="text-xs text-slate-400 mb-2">Data Quality</div>
      
      <div className="flex items-center gap-3 mb-3">
        <div className="relative">
          <svg viewBox="0 0 100 100" className="w-20 h-20">
            {/* Background circle */}
            <circle
              cx="50"
              cy="50"
              r="45"
              fill="none"
              stroke="rgba(255,255,255,0.05)"
              strokeWidth="8"
            />
            {/* Progress circle */}
            <circle
              cx="50"
              cy="50"
              r="45"
              fill="none"
              stroke={completenessColor === 'text-emerald-400' ? '#34d399' : completenessColor === 'text-amber-400' ? '#fbbf24' : '#ef4444'}
              strokeWidth="8"
              strokeDasharray="282.74"
              strokeDashoffset={282.74 * (1 - stats.completenessScore / 100)}
              strokeLinecap="round"
            />
            {/* Center text */}
            <text
              x="50"
              y="55"
              textAnchor="middle"
              dominantBaseline="middle"
              fill="white"
              fontSize="12"
              fontWeight="600"
            >
              {stats.completenessScore}%
            </text>
          </svg>
        </div>
        
        <div className="flex-1 text-xs space-y-1">
          <div className="flex justify-between">
            <span className="text-slate-500">Dated:</span>
            <span className="text-slate-200">{stats.avgDated}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Sourced:</span>
            <span className="text-slate-200">{stats.avgSourced}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Complete:</span>
            <span className={completenessColor}>{stats.fullCoverage}/{stats.totalRows}</span>
          </div>
        </div>
      </div>
      
      <div className="text-xs text-slate-500">
        Last update: {coverageData[0]?.last_refresh ? new Date(coverageData[0].last_refresh).toLocaleDateString() : 'N/A'}
      </div>
    </div>
  );
}