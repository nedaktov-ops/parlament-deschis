import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import * as echarts from "echarts";
import type { ECharts, EChartsOption, LineSeriesOption } from "echarts";
import { api, type OrgBrief } from "../api/client";

const AXIS_COLOR = "#94a3b8";
const SPLIT_COLOR = "rgba(148, 163, 184, 0.16)";
const FALLBACK_COLORS = [
  "#38bdf8",
  "#f59e0b",
  "#34d399",
  "#f472b6",
  "#a78bfa",
  "#fb7185",
  "#22d3ee",
  "#facc15",
  "#4ade80",
  "#c084fc",
];

export default function TimelineChart({
  from,
  to,
  groups,
}: {
  from: string;
  to: string;
  groups?: OrgBrief[];
}) {
  const { t, i18n } = useTranslation();
  const [chamber, setChamber] = useState<"deputies" | "senate">("deputies");
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<ECharts | null>(null);

  const timeline = useQuery({
    queryKey: ["timeline", chamber, from, to],
    queryFn: () => api.timeline(chamber, from, to, 30),
    enabled: from <= to,
  });

  const colorMap = useMemo(() => {
    const map: Record<string, string> = {};
    for (const g of groups ?? []) {
      const key = g.short_name || g.name;
      if (key && g.color && !map[key]) map[key] = g.color;
    }
    return map;
  }, [groups]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const chart = echarts.init(el);
    chartRef.current = chart;
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
  }, []);

  const data = timeline.data;

  const groupNames = useMemo(() => {
    if (!data) return [];
    return Object.keys(data.groups).sort((a, b) => {
      const maxA = Math.max(0, ...(data.groups[a] ?? []));
      const maxB = Math.max(0, ...(data.groups[b] ?? []));
      return maxB - maxA;
    });
  }, [data]);

  const empty = !data || data.dates.length === 0 || groupNames.length === 0;

  const option = useMemo<EChartsOption>(() => {
    if (!data) return {};
    const series: LineSeriesOption[] = [
      {
        name: t("totalSeatsLine"),
        type: "line",
        data: data.totals,
        showSymbol: false,
        symbol: "none",
        smooth: false,
        lineStyle: { color: "#64748b", width: 1, type: "dashed" },
        itemStyle: { color: "#64748b" },
        emphasis: { focus: "series" },
        z: 1,
      },
    ];
    groupNames.forEach((name, i) => {
      const color = colorMap[name] ?? FALLBACK_COLORS[i % FALLBACK_COLORS.length];
      series.push({
        name,
        type: "line",
        data: data.groups[name],
        showSymbol: false,
        symbol: "none",
        smooth: false,
        lineStyle: { color, width: 2 },
        itemStyle: { color },
        emphasis: { focus: "series" },
      });
    });
    return {
      backgroundColor: "transparent",
      color: FALLBACK_COLORS,
      grid: { left: 8, right: 16, top: 34, bottom: 8, containLabel: true },
      tooltip: {
        trigger: "axis",
        backgroundColor: "#0f172a",
        borderColor: "#334155",
        textStyle: { color: "#e2e8f0", fontSize: 11 },
        axisPointer: { type: "line", lineStyle: { color: "#475569" } },
      },
      legend: {
        type: "scroll",
        top: 0,
        textStyle: { color: "#cbd5e1", fontSize: 11 },
        pageTextStyle: { color: "#94a3b8" },
        pageIconColor: "#94a3b8",
        pageIconInactiveColor: "#475569",
      },
      xAxis: {
        type: "category",
        data: data.dates,
        boundaryGap: false,
        axisLine: { lineStyle: { color: "#334155" } },
        axisTick: { show: false },
        axisLabel: {
          color: AXIS_COLOR,
          fontSize: 10,
          hideOverlap: true,
          formatter: (value: string) => value.slice(0, 4),
        },
      },
      yAxis: {
        type: "value",
        axisLabel: { color: AXIS_COLOR, fontSize: 10 },
        splitLine: { lineStyle: { color: SPLIT_COLOR, type: "dashed" } },
      },
      series,
    };
  }, [data, groupNames, colorMap, t, i18n.language]);

  useEffect(() => {
    const chart = chartRef.current;
    if (!chart) return;
    if (empty) {
      chart.clear();
      return;
    }
    chart.setOption(option, true);
  }, [option, empty]);

  return (
    <div className="card p-4 flex flex-col">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
        <h2 className="font-semibold">{t("groupTimeline")}</h2>
        <div className="flex items-center gap-1" role="group" aria-label={t("chamber")}>
          {(["deputies", "senate"] as const).map((c) => (
            <button
              key={c}
              onClick={() => setChamber(c)}
              aria-pressed={chamber === c}
              className={`btn ${
                chamber === c
                  ? "bg-sky-600 text-white"
                  : "bg-slate-700 hover:bg-slate-600 text-slate-200"
              }`}
            >
              {t(c)}
            </button>
          ))}
        </div>
      </div>

      <div className="relative h-[320px]">
        <div
          ref={containerRef}
          className="absolute inset-0"
          role="img"
          aria-label={t("groupTimeline")}
        />
        {timeline.isLoading && (
          <div className="absolute inset-0 flex items-center justify-center text-slate-500 text-sm pointer-events-none">
            {t("loading")}
          </div>
        )}
        {!timeline.isLoading && empty && (
          <div className="absolute inset-0 flex items-center justify-center text-slate-500 text-sm pointer-events-none">
            {t("noData")}
          </div>
        )}
      </div>
    </div>
  );
}
