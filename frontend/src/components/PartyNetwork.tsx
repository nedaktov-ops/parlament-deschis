import { useId, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { activateOnKey } from "../utils/a11y";
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

export default function PartyNetwork({
  parties,
  edges,
  onNodeClick,
  onViewAll,
}: PartyNetworkProps) {
  const { t } = useTranslation();
  const uid = useId().replace(/:/g, "");
  const nodes = useMemo(() => {
    return parties.map((p, i) => ({
      ...p,
      x: 100 + (i % 5) * 80,
      y: 60 + Math.floor(i / 5) * 50,
      radius: Math.sqrt(p.total_members) * 0.8,
    }));
  }, [parties]);

  const maxRadius = Math.max(...nodes.map(n => n.radius), 10);
  const nodeRadius = (r: number) => Math.max(10, Math.min(30, (r / maxRadius) * 25));

  return (
    <div className="w-full bg-slate-800/30 rounded-xl p-4 overflow-hidden">
      <div className="text-xs text-slate-400 mb-2">Party Network</div>
      <div 
        className="relative h-40"
        style={{ minHeight: "160px" }}
      >
        {nodes.length > 0 ? (
          <>
          <svg
            viewBox="0 0 500 160"
            fill="none"
            className="w-full h-full"
          >
            {nodes.map((node) => (
              <g
                key={node.id}
                role="button"
                tabIndex={0}
                aria-label={t("a11y.partyNode", "Party {{party}}: {{members}} members", { party: node.short_name, members: node.total_members })}
                aria-describedby={`${uid}-node-${node.id}`}
                className="cursor-pointer focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-400"
                onClick={() => onNodeClick?.(node.short_name || node.id)}
                onKeyDown={(e) => activateOnKey(e, () => onNodeClick?.(node.short_name || node.id))}
              >
                <title>{`${node.short_name}: ${node.total_members} members`}</title>
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={nodeRadius(node.radius)}
                  fill={node.color || "#64748b"}
                  opacity={0.7}
                  stroke="rgba(255,255,255,0.1)"
                  strokeWidth={1}
                />
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={nodeRadius(node.radius) + 2}
                  fill="none"
                  stroke="rgba(255,255,255,0.1)"
                  strokeWidth={1}
                />
                <text
                  x={node.x}
                  y={node.y + 4}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fill="white"
                  fontSize={8}
                  fontWeight="600"
                >
                  {node.short_name}
                </text>
                <text
                  x={node.x}
                  y={node.y + 16}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  fill="#94a3b8"
                  fontSize={6}
                >
                  {node.total_members}
                </text>
              </g>
            ))}
            {edges.slice(0, 15).map((edge, idx) => {
              const fromNode = nodes.find(n => n.short_name === edge.from);
              const toNode = nodes.find(n => n.short_name === edge.to);
              if (!fromNode || !toNode) return null;
              
              return (
                <line
                  key={`${edge.from}-${edge.to}-${idx}`}
                  x1={fromNode.x + nodeRadius(fromNode.radius)}
                  y1={fromNode.y}
                  x2={toNode.x - nodeRadius(toNode.radius)}
                  y2={toNode.y}
                  stroke="rgba(156, 163, 175, 0.3)"
                  strokeWidth={Math.max(0.5, edge.count / 10)}
                  strokeLinecap="round"
                />
              );
            })}
          </svg>
          {nodes.map((node) => (
            <TooltipText key={node.id} id={`${uid}-node-${node.id}`}>
              {`${node.short_name}: ${node.total_members} members`}
            </TooltipText>
          ))}
          </>
        ) : (
          <div className="flex items-center justify-center h-full text-slate-500 text-sm">
            Loading network data...
          </div>
        )}
      </div>
      <div className="mt-2 flex flex-wrap gap-2 text-xs">
        <span className="text-slate-500">Nodes: {nodes.length}</span>
        <span className="text-slate-500">Edges: {edges.length}</span>
        {onViewAll && (
          <button
            type="button"
            className="btn-hover min-h-11 ml-auto text-sky-400 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-400"
            onClick={onViewAll}
          >
            View all →
          </button>
        )}
      </div>
    </div>
  );
}