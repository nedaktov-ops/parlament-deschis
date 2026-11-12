import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import * as echarts from "echarts";
import type { ECharts, EChartsOption } from "echarts";
import { api, type EventItem } from "../api/client";

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

interface FlowLink {
  source: string;
  target: string;
  value: number;
}

function orgLabel(org: EventItem["from_org"]): string | null {
  if (!org) return null;
  return org.short_name || org.name || null;
}

/**
 * ECharts' sankey layout throws on directed cycles, and group defections are
 * inherently cyclic (A→B and B→A both happen). Keep the heaviest set of links
 * that still forms a DAG and report how many reciprocal flows were omitted so
 * the diagram never crashes and the omission stays visible.
 */
function acyclicLinks(links: FlowLink[]): { links: FlowLink[]; omitted: number } {
  const adjacency = new Map<string, Set<string>>();
  const reachable = (from: string, to: string): boolean => {
    if (from === to) return true;
    const seen = new Set<string>([from]);
    const stack = [from];
    while (stack.length > 0) {
      const node = stack.pop()!;
      for (const next of adjacency.get(node) ?? []) {
        if (next === to) return true;
        if (!seen.has(next)) {
          seen.add(next);
          stack.push(next);
        }
      }
    }
    return false;
  };

  const keep: FlowLink[] = [];
  let omitted = 0;
  for (const link of [...links].sort((a, b) => b.value - a.value)) {
    if (reachable(link.target, link.source)) {
      omitted += 1;
      continue;
    }
    keep.push(link);
    const edges = adjacency.get(link.source) ?? new Set<string>();
    edges.add(link.target);
    adjacency.set(link.source, edges);
  }
  return { links: keep, omitted };
}

export default function DefectionSankey() {
  const { t } = useTranslation();
  const [chamber, setChamber] = useState<"deputies" | "senate">("deputies");
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<ECharts | null>(null);

  const movements = useQuery({
    queryKey: ["movements", chamber],
    queryFn: () => api.movements(chamber),
  });

  const { links, omitted, nodeColors, total } = useMemo(() => {
    const events = movements.data ?? [];
    const switches = events.filter(
      (e) => e.type === "switch_group" || e.type === "switch_party",
    );
    const counts = new Map<string, number>();
    const colors = new Map<string, string>();

    for (const e of switches) {
      const from = orgLabel(e.from_org);
      const to = orgLabel(e.to_org);
      if (from && e.from_org?.color && !colors.has(from)) {
        colors.set(from, e.from_org.color);
      }
      if (to && e.to_org?.color && !colors.has(to)) {
        colors.set(to, e.to_org.color);
      }
      if (!from || !to || from === to) continue;
      const key = `${from}\u0000${to}`;
      counts.set(key, (counts.get(key) ?? 0) + 1);
    }

    const aggregated: FlowLink[] = [...counts.entries()].map(([key, value]) => {
      const [source, target] = key.split("\u0000");
      return { source, target, value };
    });
    const acyclic = acyclicLinks(aggregated);
    return {
      links: acyclic.links,
      omitted: acyclic.omitted,
      nodeColors: colors,
      total: switches.length,
    };
  }, [movements.data]);

  const nodes = useMemo(() => {
    const names = new Set<string>();
    for (const link of links) {
      names.add(link.source);
      names.add(link.target);
    }
    return [...names].sort((a, b) => a.localeCompare(b)).map((name, i) => ({
      name,
      itemStyle: {
        color: nodeColors.get(name) ?? FALLBACK_COLORS[i % FALLBACK_COLORS.length],
      },
    }));
  }, [links, nodeColors]);

  const empty = !movements.isLoading && links.length === 0;

  const option = useMemo<EChartsOption>(() => {
    if (links.length === 0) return {};
    return {
      backgroundColor: "transparent",
      tooltip: {
        trigger: "item",
        backgroundColor: "#0f172a",
        borderColor: "#334155",
        textStyle: { color: "#e2e8f0", fontSize: 11 },
      },
      series: [
        {
          type: "sankey",
          data: nodes,
          links,
          left: 8,
          right: 16,
          top: 8,
          bottom: 8,
          nodeWidth: 12,
          nodeGap: 8,
          nodeAlign: "justify",
          layoutIterations: 32,
          lineStyle: { color: "gradient", opacity: 0.35, curveness: 0.5 },
          itemStyle: { borderWidth: 0 },
          label: { color: "#e2e8f0", fontSize: 11 },
          emphasis: { focus: "adjacency", lineStyle: { opacity: 0.6 } },
        },
      ],
    };
  }, [links, nodes]);

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

  useEffect(() => {
    const chart = chartRef.current;
    if (!chart) return;
    if (links.length === 0) {
      chart.clear();
      return;
    }
    chart.setOption(option, true);
  }, [option, links.length]);

  return (
    <div className="card p-4 flex flex-col">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
        <div className="flex items-baseline gap-2">
          <h2 className="font-semibold">{t("defections")}</h2>
          <span className="text-xs text-slate-400">
            {t("totalSwitches")}:{" "}
            <span className="text-slate-200 font-mono">{total}</span>
          </span>
        </div>
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
          aria-label={t("defections")}
        />
        {movements.isLoading && (
          <div className="absolute inset-0 flex items-center justify-center text-slate-500 text-sm pointer-events-none">
            {t("loading")}
          </div>
        )}
        {empty && (
          <div className="absolute inset-0 flex items-center justify-center text-slate-500 text-sm pointer-events-none px-4 text-center">
            {t("noSwitches")}
          </div>
        )}
      </div>

      {omitted > 0 && (
        <div className="text-[10px] text-slate-500 mt-1">
          {t("omittedFlows", { n: omitted })}
        </div>
      )}
    </div>
  );
}
