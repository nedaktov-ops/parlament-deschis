import { useId, useMemo } from "react";
import { useTranslation } from "react-i18next";
import TooltipText from "./ui/TooltipText";

interface PartyNode {
  id: string;
  short_name: string;
  name: string;
  color: string | null;
  total_members: number;
  switches_in: number;
}

interface SwitchEdge {
  from: string;
  to: string;
  count: number;
}

export interface PartyNetworkProps {
  parties: PartyNode[];
  edges: SwitchEdge[];
  onNodeClick?: (partyShortName: string) => void;
  onViewAll?: () => void;
}

/** Nodes live on a 0–100 grid. The canvas is square, so the edge SVG (viewBox
 *  0 0 100 100) scales uniformly and its coordinates line up exactly with the
 *  percentage-positioned HTML buttons. Labels are HTML text, not SVG text, so
 *  they keep their authored 12px/11px size at every card width (an SVG label in
 *  a stretched viewBox shrank to ~3–4px in the 4-column dashboard grid). */
const COLUMNS = 4;
const GRID_X = (i: number) => 14 + (i % COLUMNS) * 24;
const GRID_Y = (i: number) => 22 + Math.floor(i / COLUMNS) * 28;

export default function PartyNetwork({
  parties,
  edges,
  onNodeClick,
  onViewAll,
}: PartyNetworkProps) {
  const { t } = useTranslation();
  const uid = useId().replace(/:/g, "");
  const nodes = useMemo(
    () =>
      parties.map((p, i) => ({
        ...p,
        x: GRID_X(i),
        y: GRID_Y(i),
        dot: Math.round(Math.max(14, Math.min(30, Math.sqrt(p.total_members) * 1.5))),
      })),
    [parties],
  );

  return (
    <div className="w-full bg-slate-800/30 rounded-xl p-4 overflow-hidden">
      <div className="text-xs text-slate-400 mb-2">Party Network</div>
      {nodes.length > 0 ? (
        <div className="relative mx-auto w-full max-w-[260px] aspect-square">
          {/* Edges only — no text, so no distorted/stretched glyphs. Default
              preserveAspectRatio is safe here: square viewBox, square canvas. */}
          {edges.length > 0 && (
            <svg
              className="absolute inset-0 h-full w-full"
              viewBox="0 0 100 100"
              fill="none"
              aria-hidden="true"
              focusable="false"
            >
              {edges.slice(0, 15).map((edge, idx) => {
                const fromNode = nodes.find((n) => n.short_name === edge.from);
                const toNode = nodes.find((n) => n.short_name === edge.to);
                if (!fromNode || !toNode) return null;
                return (
                  <line
                    key={`${edge.from}-${edge.to}-${idx}`}
                    x1={fromNode.x}
                    y1={fromNode.y}
                    x2={toNode.x}
                    y2={toNode.y}
                    strokeWidth={0.5}
                    strokeLinecap="round"
                    className="stroke-slate-500 opacity-40"
                  />
                );
              })}
            </svg>
          )}

          {nodes.map((node) => (
            <button
              key={node.id}
              type="button"
              className="group absolute flex min-w-11 flex-col items-center justify-center rounded-lg p-1 text-center transition-opacity duration-150 motion-reduce:transition-none hover:opacity-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-400"
              style={{
                left: `${node.x}%`,
                top: `${node.y}%`,
                transform: "translate(-50%, -50%)",
              }}
              aria-label={t("a11y.partyNode", "Party {{party}}: {{members}} members", {
                party: node.short_name,
                members: node.total_members,
              })}
              aria-describedby={`${uid}-node-${node.id}`}
              onClick={() => onNodeClick?.(node.short_name || node.id)}
            >
              <span
                aria-hidden="true"
                className="mb-1 block shrink-0 rounded-full border border-slate-600/60"
                style={{
                  width: node.dot,
                  height: node.dot,
                  backgroundColor: node.color ?? "rgb(var(--slate-500))",
                }}
              />
              <span className="max-w-[72px] truncate text-xs font-semibold leading-tight text-slate-100">
                {node.short_name}
              </span>
              <span className="text-[11px] leading-tight text-slate-400 tabular-nums">
                {node.total_members}
              </span>
              <TooltipText id={`${uid}-node-${node.id}`}>
                {`${node.short_name}: ${node.total_members} members`}
              </TooltipText>
            </button>
          ))}
        </div>
      ) : (
        <div
          role="status"
          className="flex aspect-square max-w-[260px] mx-auto flex-col items-center justify-center gap-1 text-center"
        >
          <span className="text-sm font-medium text-slate-300">No party data</span>
          <span className="text-xs text-slate-400">
            Party connections will appear here once data is available.
          </span>
        </div>
      )}

      <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
        <span className="text-slate-500">{nodes.length} parties</span>
        {edges.length > 0 && (
          <span className="text-slate-500">{edges.length} links</span>
        )}
        {onViewAll && (
          <button
            type="button"
            className="btn btn-hover min-h-11 ml-auto text-sky-400 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-400"
            onClick={onViewAll}
          >
            View all →
          </button>
        )}
      </div>
    </div>
  );
}
