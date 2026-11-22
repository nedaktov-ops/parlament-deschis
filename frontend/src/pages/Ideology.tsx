import { useEffect, useMemo, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
// Modular ECharts: register only what this chart needs.
// Measured chunk: ~487 KB minified / 164 KB gzip (vs 1,040 KB / 345 KB monolith).
import * as echarts from "echarts/core";
import { ScatterChart } from "echarts/charts";
import {
  GridComponent,
  LegendComponent,
  TooltipComponent,
  ToolboxComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import type { ECharts } from "echarts/core";
import type { EChartsOption } from "echarts";
import { useNavigate, useSearch } from "@tanstack/react-router";
import { ideology, type IdeologyEntry } from "../api/client";
import { useScope } from "../hooks/useScope";
import ScopeControls from "../components/ScopeControls";
import AsyncState, { resolveViewState } from "../components/ui/AsyncState";

echarts.use([ScatterChart, GridComponent, LegendComponent, TooltipComponent, ToolboxComponent, CanvasRenderer]);

const AXIS_COLOR = "#94a3b8";
const SPLIT_COLOR = "rgba(148, 163, 184, 0.16)";

// Distinct colors for parties (fallback cycle)
const PARTY_COLORS = [
  "#ef4444",
  "#10b981",
  "#3b82f6",
  "#f59e0b",
  "#8b5cf6",
  "#ec4899",
  "#06b6d4",
  "#84cc16",
  "#f97316",
  "#eab308",
  "#6366f1",
  "#14b8a6",
  "#a855f7",
  "#fb923c",
  "#c026d3",
];

export default function Ideology() {
  const { t } = useTranslation();
  const scope = useScope();
  const navigate = useNavigate({ from: "/ideology" });
  // CHES survey year is a distinct URL param, never a mapped as_of date.
  const yearSearch = useSearch({
    from: "/ideology",
    select: (s) => (s as Record<string, unknown>).chesYear,
  });
  const chesYear = typeof yearSearch === "string" ? yearSearch : undefined;
  const setYear = (value: string | undefined) =>
    navigate({ search: scope.searchFor({ chesYear: value }) });

  const ideologyQuery = useQuery({
    queryKey: ["ideology", chesYear, ...scope.scopeKey],
    queryFn: () => ideology(chesYear),
  });

  const data = useMemo(() => ideologyQuery.data?.data ?? [], [ideologyQuery.data]);
  const dataExists = ideologyQuery.data?.data_exists ?? false;

  // Group data by year for the year selector
  const years = useMemo(() => {
    const yset = new Set<number>();
    for (const d of data) {
      if (d.survey_year) yset.add(d.survey_year);
    }
    return Array.from(yset).sort((a, b) => b - a);
  }, [data]);

  // Filter data by selected year (show latest year by default)
  const selectedYear = chesYear || (years.length > 0 ? String(years[0]) : undefined);
  const filteredData = useMemo(
    () =>
      selectedYear
        ? data.filter((d: IdeologyEntry) => d.survey_year === parseInt(selectedYear, 10))
        : data,
    [data, selectedYear],
  );

  // Build scatter plot data.
  // R-04: parties without a published score are omitted, not plotted at zero;
  // R-08: only finite, complete CHES triples enter the plot.
  const AXIS_KEYS = ["lrgen", "galtan", "eu_position"] as const;
  const hasAxes = (
    d: IdeologyEntry,
  ): d is IdeologyEntry & { lrgen: number; galtan: number; eu_position: number } =>
    AXIS_KEYS.every((k) => typeof d[k] === "number" && Number.isFinite(d[k]));
  const plottedData = filteredData.filter(hasAxes);
  const omittedCount = filteredData.length - plottedData.length;

  const scatterData = plottedData.map((d) => ({
      value: [d.lrgen, d.galtan, d.eu_position],
      name: d.party_name,
      partyfacts_id: d.partyfacts_id,
      survey_year: d.survey_year,
      eu_position: d.eu_position,
      antielite_salience: d.antielite_salience,
      people_vs_elite: d.people_vs_elite,
    }));

  const colorMap = useMemo(() => {
    const map: Record<string, string> = {};
    let idx = 0;
    for (const d of filteredData) {
      if (!map[d.party_name]) {
        map[d.party_name] = PARTY_COLORS[idx % PARTY_COLORS.length];
        idx++;
      }
    }
    return map;
  }, [filteredData]);

  const chartRef = useRef<ECharts | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const chart = echarts.init(el);
    chartRef.current = chart;

    const option: EChartsOption = {
      backgroundColor: "transparent",
      tooltip: {
        trigger: "item",
        formatter: (params: any) => {
          const d = params.data as any;
          return [
            `<div style="padding: 8px">`,
            `<div style="font-weight: bold">${d.name}</div>`,
            `<div>Year: ${d.survey_year}</div>`,
            `<div>Left-Right: ${d.value[0].toFixed(2)}</div>`,
            `<div>GAL-TAN: ${d.value[1].toFixed(2)}</div>`,
            `<div>EU Position: ${d.value[2].toFixed(2)}</div>`,
            `<div>Anti-Elite: ${d.antielite_salience == null ? "—" : d.antielite_salience.toFixed(2)}</div>`,
            `<div>People vs Elite: ${d.people_vs_elite == null ? "—" : d.people_vs_elite.toFixed(2)}</div>`,
            `</div>`,
          ].join("");
        },
      },
      xAxis: {
        name: t("view.ideology.axis_left_right", "Economic Left ← → Right"),
        nameLocation: "middle",
        nameGap: 30,
        min: 0,
        max: 10,
        splitNumber: 10,
        axisLine: { lineStyle: { color: AXIS_COLOR } },
        axisLabel: { color: AXIS_COLOR },
        splitLine: { lineStyle: { color: SPLIT_COLOR } },
      },
      yAxis: {
        name: t("view.ideology.axis_gal_tan", "Authoritarian ← → Libertarian"),
        nameLocation: "middle",
        nameGap: 40,
        nameRotate: 90,
        min: 0,
        max: 10,
        splitNumber: 10,
        axisLine: { lineStyle: { color: AXIS_COLOR } },
        axisLabel: { color: AXIS_COLOR },
        splitLine: { lineStyle: { color: SPLIT_COLOR } },
      },
      series: [
        {
          name: "Parties",
          type: "scatter",
          data: scatterData.map((d) => ({
            ...d,
            itemStyle: {
              color: colorMap[d.name] ?? "#94a3b8",
            },
            label: {
              show: false,
            },
            emphasis: {
              label: {
                show: true,
                formatter: d.name,
              },
            },
          })),
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
    };
  }, [filteredData, scatterData, colorMap, t]);

  const view = resolveViewState({
    isLoading: ideologyQuery.isLoading,
    isError: ideologyQuery.isError,
    isEmpty: ideologyQuery.isSuccess && (!dataExists || filteredData.length === 0),
  });
  if (view !== "ready") {
    return (
      <AsyncState
        view={view}
        pageTitle={t("view.ideology.title", "Ideological spatial map")}
        onRetry={() => void ideologyQuery.refetch()}
        errorLabel={t("view.ideology.loadError", "The ideological map could not be loaded.")}
        emptyTitle={dataExists
          ? t("view.ideology.noYear", "No CHES wave is available for the selected year.")
          : t("empty.ideology", "Ideological data not yet available.")}
      />
    );
  }

  return (
    <div className="space-y-6">
      <ScopeControls note={t("scope.note.ideology")} />
      <section className="py-2" data-enter>
        <h1 className="page-title">
          {t("view.ideology.title", "Ideological spatial map")}
        </h1>
        <p className="mt-2 text-sm sm:text-base text-slate-400 max-w-3xl">
          {t("view.ideology.intro", "Party positions from CHES expert-survey scores (0–10 axes: left-right, GAL-TAN, EU). PopuList is NOT ingested in this corpus and is not used here.")}
        </p>
      </section>

      <section className="bg-slate-800/30 rounded-xl p-4 sm:p-5" data-enter>
        <div className="flex flex-col sm:flex-row sm:items-end gap-3 sm:gap-4 mb-4">
          <label className="flex-1 min-w-0">
            <span className="block text-xs text-slate-400 mb-1">
              {t("filter.year", "Year")}
            </span>
            <select
              value={selectedYear ?? ""}
              onChange={(e) => setYear(e.target.value || undefined)}
              className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-600 text-slate-100 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500/40 focus:border-sky-500"
            >
              <option value="">
                {t("filter.year_all", "All years")}
              </option>
              {years.map((y) => (
                <option key={y} value={String(y)}>
                  {y}
                </option>
              ))}
            </select>
          </label>
          <div className="text-xs text-slate-400">
            {filteredData.length} parties in {years.length} wave(s)
          </div>
        </div>

        <div className="h-[500px] w-full">
          <div ref={containerRef} id="ideology-chart" className="h-full w-full" />
        </div>
        <p role="note" className="mt-2 text-xs text-slate-400">
          {t("view.ideology.scoresNote", "Parties without a published CHES score are omitted, not plotted at zero.")}
        </p>
      </section>

      <section className="bg-slate-800/30 rounded-xl p-4 sm:p-5" data-enter>
        <h2 className="text-lg font-semibold text-slate-100 mb-3">
          {t("view.ideology.legend_title", "Party positions")}
        </h2>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm data-table">
            <thead>
              <tr className="text-left text-slate-400 border-b border-slate-700">
                <th className="py-2.5 pr-4 font-medium" scope="col">
                  Party
                </th>
                <th className="py-2.5 pr-4 font-medium text-right" scope="col">
                  Year
                </th>
                <th className="py-2.5 pr-4 font-medium text-right" scope="col">
                  Left-Right
                </th>
                <th className="py-2.5 pr-4 font-medium text-right" scope="col">
                  GAL-TAN
                </th>
                <th className="py-2.5 pr-4 font-medium text-right" scope="col">
                  EU Position
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredData.map((d: IdeologyEntry) => (
                <tr
                  key={`${d.party_name}-${d.survey_year}`}
                  className="border-b border-slate-700/40 hover:bg-slate-800/40"
                >
                  <td className="py-2.5 pr-4 text-slate-200 font-medium">
                    {d.party_name}
                  </td>
                  <td className="py-2.5 pr-4 text-right text-slate-300 tabular-nums">
                    {d.survey_year}
                  </td>
                  <td className="py-2.5 pr-4 text-right text-slate-300 tabular-nums">
                    {d.lrgen == null || !Number.isFinite(d.lrgen) ? "—" : d.lrgen.toFixed(2)}
                  </td>
                  <td className="py-2.5 pr-4 text-right text-slate-300 tabular-nums">
                    {d.galtan == null || !Number.isFinite(d.galtan) ? "—" : d.galtan.toFixed(2)}
                  </td>
                  <td className="py-2.5 pr-4 text-right text-slate-300 tabular-nums">
                    {d.eu_position == null || !Number.isFinite(d.eu_position) ? "—" : d.eu_position.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="text-xs text-slate-500 mt-2 max-w-3xl">
        <p role="note">
          {t(
            "view.ideology.provenance",
            "Source: CHES, EUI archive (hdl.handle.net/1814/69975), CC BY 4.0. Parties are matched by Party Facts ID; PopuList is excluded (licence UNVERIFIED).",
          )}
        </p>
        {omittedCount > 0 && (
          <p role="note" className="mt-1">
            {t("view.ideology.omitted", "{{n}} party-wave(s) omitted from the plot: at least one CHES axis is missing. Missing values are shown as — in the table, never as 0.", { n: omittedCount })}
          </p>
        )}
        <p className="mt-1">
          {t("view.ideology.licence", "CHES: CC BY 4.0.")}
        </p>
      </section>
    </div>
  );
}
