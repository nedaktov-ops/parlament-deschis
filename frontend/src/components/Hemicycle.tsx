import { useMemo, useState } from "react";
import type { GroupComposition, MemberBrief } from "../api/client";

interface Seat {
  x: number;
  y: number;
  color: string;
  group: string;
  member: MemberBrief | null;
}

function layout(n: number, rows: number): { x: number; y: number }[] {
  if (n <= 0) return [];
  const radii = Array.from({ length: rows }, (_, i) => i + 1);
  const sum = radii.reduce((a, b) => a + b, 0);
  const counts = radii.map((r) => Math.max(1, Math.round((n * r) / sum)));
  let diff = n - counts.reduce((a, b) => a + b, 0);
  let i = rows - 1;
  while (diff !== 0) {
    const idx = ((i % rows) + rows) % rows;
    if (diff > 0) {
      counts[idx] += 1;
      diff -= 1;
    } else if (counts[idx] > 1) {
      counts[idx] -= 1;
      diff += 1;
    }
    i -= 1;
  }
  const pts: { x: number; y: number }[] = [];
  const maxR = rows;
  for (let r = 0; r < rows; r++) {
    const radius = ((r + 1) / maxR) * 48;
    const c = counts[r];
    for (let s = 0; s < c; s++) {
      const theta = Math.PI - (Math.PI * (s + 0.5)) / c;
      pts.push({ x: 50 + radius * Math.cos(theta), y: 52 - radius * Math.sin(theta) });
    }
  }
  return pts;
}

export default function Hemicycle({
  groups,
  onSelect,
}: {
  groups: GroupComposition[];
  onSelect: (personId: string) => void;
}) {
  const [hover, setHover] = useState<Seat | null>(null);
  const total = groups.reduce((a, g) => a + g.count, 0);
  const rows = Math.max(3, Math.ceil(Math.sqrt(total / 3)));

  const seats = useMemo<Seat[]>(() => {
    const pts = layout(total, rows);
    const out: Seat[] = [];
    let idx = 0;
    for (const g of groups) {
      for (let k = 0; k < g.count; k++) {
        const p = pts[idx++];
        if (!p) break;
        out.push({
          x: p.x,
          y: p.y,
          color: g.color || "#64748b",
          group: g.short_name,
          member: g.members[k] ?? null,
        });
      }
    }
    return out;
  }, [groups, total, rows]);

  if (total === 0) {
    return <div className="text-slate-500 text-sm p-6">—</div>;
  }

  return (
    <div className="relative">
      <svg viewBox="0 0 100 56" className="w-full">
        {seats.map((s, i) => (
          <circle
            key={i}
            cx={s.x}
            cy={s.y}
            r={1.15}
            fill={s.color}
            className="cursor-pointer transition-opacity hover:opacity-70"
            onMouseEnter={() => setHover(s)}
            onMouseLeave={() => setHover(null)}
            onClick={() => s.member && onSelect(s.member.person_id)}
          />
        ))}
      </svg>
      {hover && (
        <div className="absolute top-1 left-1 bg-slate-900/95 border border-slate-600 rounded px-2 py-1 text-xs pointer-events-none">
          <span className="font-semibold">{hover.member?.name ?? "—"}</span>
          <span className="text-slate-400"> · {hover.group}</span>
          {hover.member?.role && <span className="text-slate-400"> · {hover.member.role}</span>}
        </div>
      )}
    </div>
  );
}