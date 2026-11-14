import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import * as d3 from "d3";
import { sankey } from "d3-sankey";
import { api } from "../api/client";

interface FlowLink {
  source: string;
  target: string;
  value: number;
}

interface SankeyNode {
  name: string;
  x0?: number;
  y0?: number;
  x1?: number;
  y1?: number;
  value?: number;
}

interface SankeyLink {
  source: SankeyNode | string;
  target: SankeyNode | string;
  value: number;
}

// Link shape after sankeyGenerator adds layout properties.
interface SankeyLinkWithPath extends SankeyLink {
  source: SankeyNode;
  target: SankeyNode;
  path: string;
  width: number;
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

interface SankeyFlowProps {
  chamber: string;
  legislature: string;
}

export default function SankeyFlow({
  chamber,
  legislature,
}: SankeyFlowProps) {
  const { t } = useTranslation();
  const containerRef = useRef<HTMLDivElement | null>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [width, setWidth] = useState(0);

  const movements = useQuery({
    queryKey: ["sankey-flows", chamber, legislature],
    queryFn: () => api.movements(chamber),
  });

  // Build nodes and links from movements data.
  // Links represent switches between groups; value = number of switchers.
  // Both directions (A→B and B→A) are kept as separate links so cyclic
  // flows are visible, not silently dropped.
  const { nodes, links, total } = useMemo(() => {
    const events = movements.data ?? [];
    const switches = events.filter(
      (e) =>
        (e.type === "switch_group" || e.type === "switch_party") &&
        e.legislature === legislature,
    );

    const counts = new Map<string, number>();
    for (const e of switches) {
      const from = e.from_org?.short_name || e.from_org?.name;
      const to = e.to_org?.short_name || e.to_org?.name;
      if (!from || !to || from === to) continue;
      const key = `${from}\0${to}`;
      counts.set(key, (counts.get(key) ?? 0) + 1);
    }

    const aggregated: FlowLink[] = [...counts.entries()].map(
      ([key, value]) => {
        const [source, target] = key.split("\0");
        return { source, target, value };
      },
    );

    const nodeNames = new Set<string>();
    for (const link of aggregated) {
      nodeNames.add(link.source);
      nodeNames.add(link.target);
    }
    const sankeyNodes: SankeyNode[] = [...nodeNames].sort().map((name) => ({
      name,
    }));
    const sankeyLinks: SankeyLink[] = aggregated.map((l) => ({ ...l }));

    return {
      nodes: sankeyNodes,
      links: sankeyLinks,
      total: switches.length,
    };
  }, [movements.data]);

  // Run the d3-sankey layout. d3-sankey assumes a DAG; when the graph
  // contains cycles (A→B and B→A), the layout may not converge.
  // Strategy: try with all links; if any node is left unpositioned,
  // break cycles by removing the smallest link in each cycle and retry.
  const layoutHeight = width > 0 ? 320 : 0;

  const layout = useMemo(() => {
    if (nodes.length === 0 || links.length === 0) return null;

    const height = layoutHeight;

    let workingLinks = [...links];
    let workingNodes = nodes.map((n) => ({ ...n }));
    let attempts = 0;
    const maxAttempts = 5;

    while (attempts < maxAttempts) {
      attempts++;
      const sankeyGenerator = sankey<SankeyNode, SankeyLink>()
        .nodeId((d) => d.name)
        .nodeWidth(14)
        .nodePadding(12)
        .iterations(64)
        .extent([[1, 1], [width - 1, height - 6]]);

      const result = sankeyGenerator({
        nodes: workingNodes as unknown as any,
        links: workingLinks as unknown as any,
      }) as unknown as {
        nodes: SankeyNode[];
        links: SankeyLinkWithPath[];
      };

      // Check if all nodes were positioned.
      const unpositioned = result.nodes.some(
        (n) => n.x0 === undefined || n.x1 === undefined,
      );
      if (!unpositioned) {
        return result;
      }

      // Break cycles: find mutual pairs (A→B & B→A) and remove the smaller one.
      const linkMap = new Map<string, SankeyLink>();
      for (const l of workingLinks) {
        linkMap.set(`${l.source}\0${l.target}`, l);
      }

      let linkToRemove: SankeyLink | null = null;
      for (const l of workingLinks) {
        const reverse = linkMap.get(`${l.target}\0${l.source}`);
        if (reverse) {
          linkToRemove = l.value <= reverse.value ? l : reverse;
          break;
        }
      }

      if (!linkToRemove) {
        // No mutual pair found; remove the smallest link overall.
        linkToRemove = [...workingLinks].sort((a, b) => a.value - b.value)[0];
      }

      workingLinks = workingLinks.filter((l) => l !== linkToRemove);
    }

    // Last resort: return whatever we have, even if unpositioned.
    const sankeyGenerator = sankey<SankeyNode, SankeyLink>()
      .nodeId((d) => d.name)
      .nodeWidth(14)
      .nodePadding(12)
      .iterations(128)
      .extent([[1, 1], [width - 1, height - 6]]);

    return sankeyGenerator({
      nodes: workingNodes as unknown as any,
      links: workingLinks as unknown as any,
    }) as unknown as {
      nodes: SankeyNode[];
      links: SankeyLinkWithPath[];
    };
  }, [nodes, links, width, layoutHeight]);

  const empty = !movements.isLoading && links.length === 0;

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    setWidth(el.clientWidth);
    const observer = new ResizeObserver(() => setWidth(el.clientWidth));
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  if (empty) {
    return (
      <div className="card p-4 flex flex-col">
        <div className="flex items-center justify-between gap-2 mb-2">
          <h2 className="font-semibold">{t("defections")}</h2>
          <span className="text-xs text-slate-400">
            {t("totalSwitches")}:{" "}
            <span className="text-slate-200 font-mono">{total}</span>
          </span>
        </div>
        <div className="relative h-[320px]">
          <div className="absolute inset-0 flex items-center justify-center text-slate-500 text-sm">
            {t("noSwitches")}
          </div>
        </div>
      </div>
    );
  }

  if (!layout) {
    return (
      <div className="card p-4 flex flex-col">
        <div className="flex items-center justify-between gap-2 mb-2">
          <h2 className="font-semibold">{t("defections")}</h2>
          <span className="text-xs text-slate-400">
            {t("totalSwitches")}:{" "}
            <span className="text-slate-200 font-mono">{total}</span>
          </span>
        </div>
        <div className="relative h-[320px]">
          <div className="absolute inset-0 flex items-center justify-center text-slate-500 text-sm">
            {t("layoutUnavailable")}
          </div>
        </div>
      </div>
    );
  }

  const { nodes: sankeyNodes, links: sankeyLinks } = layout as {
    nodes: SankeyNode[];
    links: SankeyLinkWithPath[];
  };

  // Color scale for nodes.
  const color = d3.scaleOrdinal<string, string>(d3.schemeCategory10);

  return (
    <div className="card p-4 flex flex-col">
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-baseline gap-2">
          <h2 className="font-semibold">{t("defections")}</h2>
          <span className="text-xs text-slate-400">
            {t("totalSwitches")}:{" "}
            <span className="text-slate-200 font-mono">{total}</span>
          </span>
        </div>
      </div>

      <div className="relative w-full" style={{ height: layoutHeight }}>
        <svg
          ref={svgRef}
          className="w-full"
          height={layoutHeight}
          role="img"
          aria-label={t("defections")}
        >
          {/* Links */}
          {sankeyLinks.map((link) => {
            return (
              <path
                key={`${link.source.name}\0${link.target.name}`}
                d={link.path ?? `M${link.source.x1},${link.source.y0} L${link.target.x0},${link.target.y1}`}
                stroke={color(link.source.name)}
                strokeWidth={Math.max(1, link.width)}
                fill="none"
                strokeOpacity={0.4}
                className="cursor-pointer hover:stroke-opacity-0.8 transition-stroke"
              >
                <title>
                  {`${link.source.name} → ${link.target.name}: ${link.value} switch${
                    link.value === 1 ? "" : "s"
                  }`}
                </title>
              </path>
            );
          })}

          {/* Nodes */}
          {sankeyNodes.map((node) => (
            <g
              key={node.name}
              transform={`translate(${node.x0 ?? 0},${node.y0 ?? 0})`}
              className="cursor-pointer"
            >
              <rect
                width={Math.max(0, (node.x1 ?? 0) - (node.x0 ?? 0))}
                height={Math.max(0, (node.y1 ?? 0) - (node.y0 ?? 0))}
                fill={color(node.name)}
                fillOpacity={0.85}
                stroke="rgba(255,255,255,0.2)"
                strokeWidth={1}
                rx={3}
              />
              <foreignObject
                x={4}
                y={4}
                width={Math.max(0, (node.x1 ?? 0) - (node.x0 ?? 0) - 8)}
                height={Math.max(0, (node.y1 ?? 0) - (node.y0 ?? 0) - 8)}
              >
                <div
                  className="text-[10px] font-medium text-white leading-tight"
                  style={{
                    maxWidth: Math.max(
                      0,
                      (node.x1 ?? 0) - (node.x0 ?? 0) - 8,
                    ),
                  }}
                >
                  {node.name}
                </div>
              </foreignObject>
              <title>
                {`${node.name}\n${node.value} switch${
                  node.value === 1 ? "" : "s"
                } total`}
              </title>
            </g>
          ))}
        </svg>

        {sankeyLinks.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-400">
            {sankeyNodes.map((node) => (
              <span
                key={node.name}
                className="flex items-center gap-1 px-2 py-0.5 rounded bg-slate-800/50 border border-slate-700/50"
              >
                <span
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: color(node.name) }}
                />
                {node.name}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
