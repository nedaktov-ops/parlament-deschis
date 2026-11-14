import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
// Tree-shakeable D3 imports: only scaleOrdinal + schemeCategory10 (~12 KB vs ~240 KB full d3)
import { scaleOrdinal } from "d3-scale";
import { schemeCategory10 } from "d3-scale-chromatic";
import { sankey } from "d3-sankey";
import { traseismSummary } from "../api/client";

interface FlowLink {
  source: string;
  target: string;
  value: number;
}

interface SankeyNode extends Record<string, unknown> {
  name: string;
  x0?: number;
  y0?: number;
  x1?: number;
  y1?: number;
  value?: number;
}

interface SankeyLink extends Record<string, unknown> {
  source: SankeyNode | string;
  target: SankeyNode | string;
  value: number;
}

interface SankeyLinkWithPath extends SankeyLink {
  source: SankeyNode;
  target: SankeyNode;
  width: number;
  y0: number;
  y1: number;
}

interface SankeyFlowProps {
  chamber: string;
  legislature: string;
}

function acyclicLinks(links: FlowLink[]): { links: FlowLink[]; omitted: number } {
  const adjacency = new Map<string, Set<string>>();
  const reaches = (from: string, to: string): boolean => {
    const pending = [from];
    const visited = new Set<string>();
    while (pending.length > 0) {
      const current = pending.pop()!;
      if (current === to) return true;
      if (visited.has(current)) continue;
      visited.add(current);
      pending.push(...(adjacency.get(current) ?? []));
    }
    return false;
  };

  const kept: FlowLink[] = [];
  let omitted = 0;
  for (const link of [...links].sort((a, b) => b.value - a.value)) {
    if (reaches(link.target, link.source)) {
      omitted += 1;
      continue;
    }
    kept.push(link);
    const targets = adjacency.get(link.source) ?? new Set<string>();
    targets.add(link.target);
    adjacency.set(link.source, targets);
  }
  return { links: kept, omitted };
}

export default function SankeyFlow({
  chamber,
  legislature,
}: SankeyFlowProps) {
  const { t } = useTranslation();
  const containerRef = useRef<HTMLDivElement | null>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);
  const [width, setWidth] = useState(0);

  const summary = useQuery({
    queryKey: ["traseism-summary", legislature, chamber],
    queryFn: () => traseismSummary(legislature, chamber),
  });

  const { nodes, links, omitted, total } = useMemo(() => {
    const matrix = summary.data?.matrix ?? [];
    const aggregated = matrix
      .filter((cell) => cell.count > 0 && cell.from !== cell.to)
      .map((cell) => ({ source: cell.from, target: cell.to, value: cell.count }));
    const acyclic = acyclicLinks(aggregated);

    const nodeNames = new Set<string>();
    for (const link of acyclic.links) {
      nodeNames.add(link.source);
      nodeNames.add(link.target);
    }
    const sankeyNodes: SankeyNode[] = [...nodeNames].sort().map((name) => ({
      name,
    }));
    const sankeyLinks: SankeyLink[] = acyclic.links.map((link) => ({ ...link }));

    return {
      nodes: sankeyNodes,
      links: sankeyLinks,
      omitted: acyclic.omitted,
      total: summary.data?.switches ?? 0,
    };
  }, [summary.data]);

  const layoutHeight = 320;

  const layout = useMemo(() => {
    if (nodes.length === 0 || links.length === 0 || width <= 2) return null;
    const sankeyGenerator = sankey<SankeyNode, SankeyLink>()
      .nodeId((d) => d.name)
      .nodeWidth(14)
      .nodePadding(12)
      .iterations(64)
      .extent([[1, 1], [width - 1, layoutHeight - 6]]);

    const result = sankeyGenerator({
      nodes: nodes.map((node) => ({ ...node })),
      links: links.map((link) => ({ ...link })),
    });
    const laidOutLinks = result.links.map((link): SankeyLinkWithPath => {
      if (
        typeof link.source !== "object" ||
        link.source === null ||
        typeof link.target !== "object" ||
        link.target === null ||
        link.width === undefined ||
        link.y0 === undefined ||
        link.y1 === undefined
      ) {
        throw new Error("Sankey layout returned an incomplete link");
      }
      return {
        source: link.source,
        target: link.target,
        value: link.value,
        width: link.width,
        y0: link.y0,
        y1: link.y1,
      };
    });
    return { nodes: result.nodes, links: laidOutLinks };
  }, [nodes, links, width, layoutHeight]);

  const empty = !summary.isLoading && links.length === 0;

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    setWidth(el.clientWidth);
    const observer = new ResizeObserver(() => setWidth(el.clientWidth));
    observer.observe(el);
    return () => observer.disconnect();
  }, [summary.isLoading, summary.isError, empty]);

  if (summary.isLoading) {
    return (
      <div className="card p-4 flex flex-col" role="status">
        <h2 className="font-semibold">{t("defections")}</h2>
        <div className="h-[320px] flex items-center justify-center text-slate-300 text-sm">
          {t("loading")}
        </div>
      </div>
    );
  }

  if (summary.isError) {
    return (
      <div className="card p-4 flex flex-col" role="alert">
        <h2 className="font-semibold">{t("defections")}</h2>
        <div className="h-[320px] flex flex-col items-center justify-center gap-2 text-center">
          <p className="text-rose-200 text-sm">{t("traseismLoadError")}</p>
          <button type="button" className="btn bg-slate-700 hover:bg-slate-600" onClick={() => summary.refetch()}>
            {t("traseismRetry")}
          </button>
        </div>
      </div>
    );
  }

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
            {total > 0 ? t("traseismNoFlowPairs") : t("noSwitches")}
          </div>
        </div>
      </div>
    );
  }

  const sankeyNodes = layout?.nodes ?? [];
  const sankeyLinks = layout?.links ?? [];

  // Color scale for nodes.
  const color = scaleOrdinal<string, string>(schemeCategory10);

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

      <div ref={containerRef} className="relative w-full" style={{ height: layoutHeight }}>
        {layout ? (
          <svg
            ref={svgRef}
            className="w-full"
            height={layoutHeight}
            role="img"
            aria-label={t("traseismFlowDesc")}
          >
          {/* Links */}
          {sankeyLinks.map((link) => {
            const startX = link.source.x1 ?? 0;
            const endX = link.target.x0 ?? 0;
            const middleX = (startX + endX) / 2;
            return (
              <path
                key={`${link.source.name}\0${link.target.name}`}
                d={`M${startX},${link.y0} C${middleX},${link.y0} ${middleX},${link.y1} ${endX},${link.y1}`}
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
              <title>
                {`${node.name}\n${node.value} switch${
                  node.value === 1 ? "" : "s"
                } total`}
              </title>
            </g>
          ))}
          </svg>
        ) : (
          <div role="status" className="absolute inset-0 flex items-center justify-center text-slate-300 text-sm">
            {width <= 2 ? t("loading") : t("layoutUnavailable")}
          </div>
        )}
      </div>
      {layout && sankeyLinks.length > 0 && (
        <div
          className="mt-2 flex flex-wrap gap-2 text-xs text-slate-400"
          role="list"
          aria-label={t("traseismLegend")}
        >
          {sankeyNodes.map((node) => (
            <span
              key={node.name}
              className="flex items-center gap-1 px-2 py-0.5 rounded bg-slate-800/50 border border-slate-700/50"
              role="listitem"
            >
              <span
                className="w-2 h-2 shrink-0 rounded-full"
                style={{ backgroundColor: color(node.name) }}
                aria-hidden="true"
              />
              <span className="break-words">{node.name}</span>
            </span>
          ))}
        </div>
      )}
      {omitted > 0 && (
        <p className="text-xs text-amber-200 mt-2" role="note">
          {t("traseismSankeyOmitted", { count: omitted })}
        </p>
      )}
    </div>
  );
}
