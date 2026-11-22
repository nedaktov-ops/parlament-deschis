import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import type { GroupComposition, MemberBrief } from "../api/client";

interface Seat {
  x: number;
  y: number;
  color: string;
  group: string;
  member: MemberBrief | null;
}

/**
 * Pure seat-count distribution for a hemicycle. Exported so termination and
 * exact totals can be asserted without React.
 *
 * Guarantees: returns exactly `n` seats for every `n >= 1, rows >= 1`; never
 * produces an empty row (rows are capped at `n`); and always terminates.
 *
 * The clamp `Math.max(1, ...)` can make the rounded counts sum to more than
 * `n` while every count is already 1 (e.g. n=1, rows=3 -> [1,1,1], diff=-2).
 * Capping rows at `n` removes that deadlock: when rows <= n, a negative diff
 * implies at least one count > 1, so the decrement branch always makes
 * progress. A bounded iteration guard is kept as defence in depth.
 */
export function computeHemicycleRows(n: number, rows: number): number[] {
  if (n <= 0 || rows <= 0) return [];
  const effectiveRows = Math.min(rows, n);
  const radii = Array.from({ length: effectiveRows }, (_, i) => i + 1);
  const sum = radii.reduce((a, b) => a + b, 0);
  const counts = radii.map((r) => Math.max(1, Math.round((n * r) / sum)));
  let diff = n - counts.reduce((a, b) => a + b, 0);
  let i = effectiveRows - 1;
  // Defensive bound: each full pass over `effectiveRows` indices makes at
  // least one unit of progress, so this is always >= the work required.
  const maxIterations = (Math.abs(diff) + 1) * (effectiveRows + 1);
  let iterations = 0;
  while (diff !== 0 && iterations < maxIterations) {
    const idx = ((i % effectiveRows) + effectiveRows) % effectiveRows;
    if (diff > 0) {
      counts[idx] += 1;
      diff -= 1;
    } else if (counts[idx] > 1) {
      counts[idx] -= 1;
      diff += 1;
    }
    i -= 1;
    iterations += 1;
  }
  return counts;
}

function layout(n: number, rows: number): { x: number; y: number }[] {
  const counts = computeHemicycleRows(n, rows);
  const maxR = counts.length;
  if (maxR === 0) return [];
  const pts: { x: number; y: number }[] = [];
  for (let r = 0; r < maxR; r++) {
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
  const { t } = useTranslation();
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
      <svg viewBox="0 0 100 56" className="w-full" aria-hidden="true" focusable="false">
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
      <details className="mt-2 text-sm">
        <summary className="cursor-pointer text-sky-300 hover:text-sky-200">
          {t("hemicycleMemberList", { count: total })}
        </summary>
        <div className="mt-2 max-h-64 overflow-y-auto space-y-3" tabIndex={0} aria-label="List of all MPs in this hemicycle group">
          {groups.map((group, groupIndex) => (
            <section key={`${group.short_name}-${groupIndex}`}>
              <h3 className="font-semibold text-slate-200">
                {group.short_name} <span className="font-normal text-slate-300">({group.count})</span>
              </h3>
              <ul className="mt-1 grid grid-cols-1 sm:grid-cols-2 gap-1">
                {group.members.map((member, memberIndex) => (
                  <li key={`${member.person_id}-${memberIndex}`}>
                    <button type="button"onClick={() => onSelect(member.person_id)}
                      className="w-full text-left px-2 py-1 rounded text-slate-200 hover:bg-slate-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400"
                    >
                      {member.name}
                      {member.role ? <span className="text-slate-300"> · {member.role}</span> : null}
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>
      </details>
    </div>
  );
}