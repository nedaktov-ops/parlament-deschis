import { useEffect, useMemo, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
// Modular ECharts: register only what this chart needs.
import * as echarts from "echarts/core";
import { BarChart, LineChart } from "echarts/charts";
import {
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  TooltipComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import type { ECharts } from "echarts/core";
import type { EChartsOption } from "echarts";
import { api, type ActivityBucket } from "../api/client";

echarts.use([
  BarChart,
  LineChart,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  DataZoomComponent,
  CanvasRenderer,
]);

const AXIS_COLOR = "#94a3b8";
const SPLIT_COLOR = "rgba(148, 163, 184, 0.16)";

interface VoteActivityChartProps {
  chamber?: string;
  legislature?: string;
}

/**
 * Roll-call vote activity over time: daily vote counts (bars) with yes/no/abstain
 * breakdown (lines). Powered by the /api/analytics/vote-activity endpoint.
 */
export default function VoteActivityChart({
  chamber,
  legislature,
}: VoteActivityChartProps) {
  const { t } = useTranslation();
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<ECharts | null>(null);

  const activityQuery = useQuery({
    queryKey: ["vote-activity-chart", chamber, legislature],
    queryFn: () => api.voteActivity(chamber, legislature),
  });

  const buckets: ActivityBucket[] = useMemo(
    () => activityQuery.data?.data ?? [],
    [activityQuery.data],
  );

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const chart = echarts.init(el);
    chartRef.current = chart;

    const dates = buckets.map((b) => b.date);
    const totalVotes = buckets.map((b) => b.votes ?? 0);
    const yesVotes = buckets.map((b) => b.yes ?? 0);
    const noVotes = buckets.map((b) => b.no ?? 0);
    const abstainVotes = buckets.map((b) => b.abstain ?? 0);

    const option: EChartsOption = {
      backgroundColor: "transparent",
      tooltip: {
        trigger: "axis",
        backgroundColor: "#0f172a",
        borderColor: "#334155",
        textStyle: { color: "#e2e8f0", fontSize: 11 },
        axisPointer: { type: "cross", lineStyle: { color: "#475569" } },
      },
      legend: {
        top: 0,
        textStyle: { color: "#cbd5e1", fontSize: 11 },
        pageTextStyle: { color: "#94a3b8" },
        pageIconColor: "#94a3b8",
        pageIconInactiveColor: "#475569",
      },
      grid: { left: 60, right: 16, top: 44, bottom: 44, containLabel: true },
      xAxis: {
        type: "category",
        data: dates,
        axisLine: { lineStyle: { color: AXIS_COLOR } },
        axisLabel: { color: AXIS_COLOR, fontSize: 10 },
        splitLine: { show: false },
      },
      yAxis: {
        type: "value",
        axisLine: { lineStyle: { color: AXIS_COLOR } },
        axisLabel: { color: AXIS_COLOR, fontSize: 10 },
        splitLine: { lineStyle: { color: SPLIT_COLOR } },
      },
      dataZoom: [
        { type: "inside", start: 0, end: 100 },
        { type: "slider", bottom: 8, height: 18, start: 0, end: 100 },
      ],
      series: [
        {
          name: t("vote.activityTotal", "Total votes"),
          type: "bar",
          data: totalVotes,
          itemStyle: { color: "#64748b" },
          barWidth: "55%",
          emphasis: { focus: "series" },
        },
        {
          name: t("vote.yes", "Yes"),
          type: "line",
          data: yesVotes,
          showSymbol: false,
          smooth: false,
          lineStyle: { color: "#10b981", width: 2 },
          itemStyle: { color: "#10b981" },
          emphasis: { focus: "series" },
        },
        {
          name: t("vote.no", "No"),
          type: "line",
          data: noVotes,
          showSymbol: false,
          smooth: false,
          lineStyle: { color: "#ef4444", width: 2 },
          itemStyle: { color: "#ef4444" },
          emphasis: { focus: "series" },
        },
        {
          name: t("vote.abstain", "Abstain"),
          type: "line",
          data: abstainVotes,
          showSymbol: false,
          smooth: false,
          lineStyle: { color: "#f59e0b", width: 2 },
          itemStyle: { color: "#f59e0b" },
          emphasis: { focus: "series" },
        },
      ],
    };

    chart.setOption(option);

    const onResize = () => chart.resize();
    const observer =
      typeof ResizeObserver !== "undefined" ? new ResizeObserver(onResize) : null;
    observer?.observe(el);
    window.addEventListener("resize", onResize);
    return () => {
      observer?.disconnect();
      window.removeEventListener("resize", onResize);
      chart.dispose();
      chartRef.current = null;
    };
  }, [buckets, t]);

  const empty = buckets.length === 0;

  return (
    <div className="card p-4 flex flex-col">
      <div className="flex items-center justify-between gap-2 mb-3">
        <h2 className="font-semibold text-slate-100">
          {t("view.grafice.activityTitle", "Roll-call vote activity over time")}
        </h2>
      </div>
      <div className="relative h-[300px]">
        <div
          ref={containerRef}
          className="absolute inset-0"
          role="img"
          aria-label={
            t("view.grafice.activityTitle", "Roll-call vote activity over time")
          }
        />
        {activityQuery.isLoading && (
          <div className="absolute inset-0 flex items-center justify-center text-slate-300 text-sm pointer-events-none">
            {t("loading")}
          </div>
        )}
        {!activityQuery.isLoading && empty && (
          <div className="absolute inset-0 flex items-center justify-center text-slate-300 text-sm pointer-events-none">
            {t("view.grafice.activityEmpty", "No vote activity recorded yet.")}
          </div>
        )}
      </div>
      {!empty && (
        <div className="mt-3 text-xs text-slate-400">
          {t(
            "view.grafice.activityNote",
            "Daily roll-call vote counts with yes/no/abstain breakdown. Data from the official cdep.ro feed.",
          )}
        </div>
      )}
    </div>
  );
}
