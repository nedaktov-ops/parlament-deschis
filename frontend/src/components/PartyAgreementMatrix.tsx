import { useEffect, useMemo, useRef } from "react";
import { useTranslation } from "react-i18next";
// Modular ECharts: register only what this chart needs.
import * as echarts from "echarts/core";
import { HeatmapChart } from "echarts/charts";
import {
  GridComponent,
  LegendComponent,
  TooltipComponent,
  ToolboxComponent,
  VisualMapComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import type { ECharts } from "echarts/core";
import type { EChartsOption } from "echarts";
import { type VotePositionRow, type VoteRow } from "../api/client";
import { useReducedMotion } from "../hooks/useReducedMotion";

echarts.use([
  HeatmapChart,
  GridComponent,
  LegendComponent,
  TooltipComponent,
  ToolboxComponent,
  VisualMapComponent,
  CanvasRenderer,
]);

const AXIS_COLOR = "#94a3b8";

interface PartyAgreementCell {
  partyA: string;
  partyB: string;
  agree: number;
  total: number;
  rate: number; // 0..100
}

interface PartyAgreementMatrixProps {
  votes: VoteRow[];
  positionsByVote: Map<string, VotePositionRow[]>;
}

/**
 * Party-to-party vote agreement heatmap. For each pair of parties, shows the
 * share of roll-call votes where both parties had the same dominant choice.
 * Computed from vote positions data already fetched by the Radar page.
 */
export default function PartyAgreementMatrix({
  votes,
  positionsByVote,
}: PartyAgreementMatrixProps) {
  const { t } = useTranslation();
  const reducedMotion = useReducedMotion();
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<ECharts | null>(null);

  // Build party x party agreement matrix from per-vote dominant choices.
  const agreementData = useMemo<PartyAgreementCell[]>(() => {
    const parties = new Set<string>();
    const pairStats = new Map<string, { agree: number; total: number }>();

    votes.forEach((vote) => {
      const positions = positionsByVote.get(vote.native_vote_id) ?? [];
      const byParty = new Map<string, Record<string, number>>();
      positions.forEach((p) => {
        if (!p.group_raw) return;
        parties.add(p.group_raw);
        const counts = byParty.get(p.group_raw) ?? {};
        counts[p.choice] = (counts[p.choice] || 0) + 1;
        byParty.set(p.group_raw, counts);
      });
      const dominantByParty = new Map<string, string>();
      byParty.forEach((counts, party) => {
        const dominant = Object.entries(counts).sort(
          (a, b) => b[1] - a[1],
        )[0];
        if (dominant) dominantByParty.set(party, dominant[0]);
      });
      const partyList = Array.from(dominantByParty.keys());
      for (let i = 0; i < partyList.length; i++) {
        for (let j = i + 1; j < partyList.length; j++) {
          const a = partyList[i];
          const b = partyList[j];
          const key = a < b ? `${a}|${b}` : `${b}|${a}`;
          const entry = pairStats.get(key) ?? { agree: 0, total: 0 };
          entry.total += 1;
          if (dominantByParty.get(a) === dominantByParty.get(b)) {
            entry.agree += 1;
          }
          pairStats.set(key, entry);
        }
      }
    });

    const result: PartyAgreementCell[] = [];
    pairStats.forEach((stats, key) => {
      const [partyA, partyB] = key.split("|");
      result.push({
        partyA,
        partyB,
        agree: stats.agree,
        total: stats.total,
        rate: stats.total > 0 ? Math.round((stats.agree / stats.total) * 100) : 0,
      });
    });
    return result.sort((a, b) => b.rate - a.rate);
  }, [votes, positionsByVote]);

  const parties = useMemo(() => {
    const set = new Set<string>();
    agreementData.forEach((c) => {
      set.add(c.partyA);
      set.add(c.partyB);
    });
    return Array.from(set).sort();
  }, [agreementData]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const chart = echarts.init(el);
    chartRef.current = chart;

    if (parties.length < 2 || agreementData.length === 0) {
      chart.clear();
      return;
    }

    // Build heatmap data: [xIndex, yIndex, value]
    const partyIndex: Record<string, number> = {};
    parties.forEach((p, i) => {
      partyIndex[p] = i;
    });

    const heatmapData: number[][] = [];
    agreementData.forEach((c) => {
      const x = partyIndex[c.partyA];
      const y = partyIndex[c.partyB];
      heatmapData.push([x, y, c.rate]);
      heatmapData.push([y, x, c.rate]); // symmetric
    });

    const option: EChartsOption = {
      backgroundColor: "transparent",
      animation: !reducedMotion,
      tooltip: {
        trigger: "item",
        backgroundColor: "#0f172a",
        borderColor: "#334155",
        textStyle: { color: "#e2e8f0", fontSize: 11 },
        formatter: (params: any) => {
          const [xIdx, yIdx, value] = params.data as number[];
          const a = parties[xIdx];
          const b = parties[yIdx];
          const cell = agreementData.find(
            (d) => (d.partyA === a && d.partyB === b) || (d.partyA === b && d.partyB === a),
          );
          return [
            `<div style="padding: 8px">`,
            `<div style="font-weight: bold">${a} ↔ ${b}</div>`,
            `<div>Agreement: ${value.toFixed(0)}%</div>`,
            `<div>Matching votes: ${cell ? cell.agree : 0} / ${cell ? cell.total : 0}</div>`,
            `</div>`,
          ].join("");
        },
      },
      grid: { left: 120, right: 40, top: 60, bottom: 80, containLabel: true },
      xAxis: {
        type: "category",
        data: parties,
        axisLine: { lineStyle: { color: AXIS_COLOR } },
        axisLabel: { color: AXIS_COLOR, fontSize: 11, rotate: 45 },
        axisTick: { show: false },
        splitLine: { show: false },
      },
      yAxis: {
        type: "category",
        data: parties,
        axisLine: { lineStyle: { color: AXIS_COLOR } },
        axisLabel: { color: AXIS_COLOR, fontSize: 11 },
        axisTick: { show: false },
        splitLine: { show: false },
        inverse: true,
      },
      visualMap: {
        min: 0,
        max: 100,
        calculable: true,
        orient: "horizontal",
        left: "center",
        bottom: 30,
        textStyle: { color: AXIS_COLOR, fontSize: 10 },
        inRange: {
          color: ["#94a3b8", "#60a5fa", "#22c55e"],
        },
      },
      series: [
        {
          name: t("view.radar.agreementRate", "Agreement rate"),
          type: "heatmap",
          data: heatmapData,
          label: {
            show: true,
            formatter: "{c}%",
            color: "#e2e8f0",
            fontSize: 10,
          },
          emphasis: {
            focus: "series",
          },
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
  }, [agreementData, parties, t, reducedMotion]);

  const empty = parties.length < 2 || agreementData.length === 0;

  return (
    <div className="card p-4 flex flex-col">
      <div className="flex items-center justify-between gap-2 mb-3">
        <h2 className="font-semibold text-slate-100">
          {t("view.radar.agreementTitle", "Party agreement matrix")}
        </h2>
      </div>
      <div className="relative h-[420px]">
        <div
          ref={containerRef}
          className="absolute inset-0"
          role="img"
          aria-label={
            t("view.radar.agreementTitle", "Party agreement matrix")
          }
        />
        {empty && (
          <div className="absolute inset-0 flex items-center justify-center text-slate-300 text-sm pointer-events-none">
            {t("view.radar.agreementEmpty", "Insufficient data for agreement matrix.")}
          </div>
        )}
      </div>
      {!empty && (
        <div className="mt-3 text-xs text-slate-400">
          {t(
            "view.radar.agreementNote",
            "Agreement rate = share of roll-call votes where two parties had the same dominant choice. Based on observed roll-call positions only.",
          )}
        </div>
      )}
    </div>
  );
}
