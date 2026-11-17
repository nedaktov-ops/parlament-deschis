import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import type { Membership } from "../api/client";
import { localISODate } from "../utils/date";

const DAY = 86400_000;

function ms(iso: string | null): number | null {
  return iso ? new Date(iso).getTime() : null;
}

export default function MembershipGantt({ memberships }: { memberships: Membership[] }) {
  const { t } = useTranslation();
  const today = localISODate();

  const { rows, domainStart, domainEnd } = useMemo(() => {
    const sorted = [...memberships].sort(
      (a, b) => (a.start_date ?? "").localeCompare(b.start_date ?? ""),
    );
    const starts = sorted.map((m) => ms(m.start_date)).filter((x): x is number => x !== null);
    const ends = sorted.map((m) => ms(m.end_date)).filter((x): x is number => x !== null);
    const todayMs = ms(today)!;
    const lo = starts.length ? Math.min(...starts) : todayMs;
    const hi = Math.max(todayMs, ...ends);
    return { rows: sorted, domainStart: lo, domainEnd: hi === lo ? lo + DAY : hi };
  }, [memberships, today]);

  if (rows.length === 0) {
    return <div className="text-slate-500 text-sm">{t("noData")}</div>;
  }

  const span = domainEnd - domainStart;
  const fmt = (n: number) => new Date(n).toISOString().slice(0, 10);

  return (
    <div>
      <div className="flex justify-between text-xs text-slate-500 font-mono mb-1">
        <span>{fmt(domainStart)}</span>
        <span>{fmt(domainEnd)}</span>
      </div>
      <div className="space-y-1.5">
        {rows.map((m) => {
          const s = ms(m.start_date) ?? domainStart;
          const e = ms(m.end_date) ?? domainEnd;
          const left = Math.max(0, ((s - domainStart) / span) * 100);
          const width = Math.max(1.5, ((e - s) / span) * 100);
          const open = m.end_date === null;
          const color = m.org?.color || "#64748b";
          const label = m.org?.short_name || m.org?.name || "—";
          const partial = (m.start_precision?.length ?? 10) < 10;
          const tip = [
            `${label}${m.role ? " · " + m.role : ""}`,
            `${m.start_date ?? "?"} → ${m.end_date ?? t("present")}`,
            t(`confidence.${m.confidence}` as string),
          ].join("\n");
          return (
            <div key={m.id} className="flex items-center gap-2">
              <div className="w-32 shrink-0 text-right">
                <div className="text-xs font-medium truncate" title={m.org?.name ?? ""}>
                  {label}
                </div>
                {m.role && <div className="text-xs text-slate-500 truncate">{m.role}</div>}
              </div>
              <div className="relative flex-1 h-5 bg-slate-800/50 rounded">
                <div
                  className="absolute top-0.5 bottom-0.5 rounded transition-opacity hover:opacity-80"
                  style={{
                    left: `${left}%`,
                    width: `${Math.min(width, 100 - left)}%`,
                    background: color,
                    opacity: m.confidence === "official_ledger" ? 1 : 0.75,
                  }}
                  title={tip}
                />
                {open && (
                  <span
                    className="absolute top-1/2 -translate-y-1/2 text-[9px] text-slate-400"
                    style={{ left: `calc(${Math.min(left + width, 99)}% + 3px)` }}
                  >
                    →
                  </span>
                )}
                {partial && (
                  <span
                    className="absolute -top-1 text-[9px] text-amber-400"
                    style={{ left: `${left}%` }}
                    title={t("inferred")}
                  >
                    ~
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}