import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api, type EventItem } from "../api/client";

interface SwitcherSummary {
  person_id: string;
  name: string;
  switch_count: number;
  last_switch: string;
  switches: Array<{
    date: string;
    from: string | null;
    to: string | null;
    type: string;
    chamber: string | null;
  }>;
}

function aggregateSwitchers(events: EventItem[]): SwitcherSummary[] {
  const byPerson: Map<string, SwitcherSummary> = new Map();

  for (const e of events) {
    if (!e.person) continue;
    const pid = e.person.id;
    const existing = byPerson.get(pid);
    const fromLabel = e.from_org?.short_name || e.from_org?.name || null;
    const toLabel = e.to_org?.short_name || e.to_org?.name || null;

    if (existing) {
      existing.switch_count += 1;
      if (e.event_date && e.event_date > existing.last_switch) {
        existing.last_switch = e.event_date;
      }
      existing.switches.push({
        date: e.event_date ?? "",
        from: fromLabel,
        to: toLabel,
        type: e.type,
        chamber: e.chamber,
      });
    } else {
      byPerson.set(pid, {
        person_id: pid,
        name: e.person.name,
        switch_count: 1,
        last_switch: e.event_date ?? "",
        switches: [{
          date: e.event_date ?? "",
          from: fromLabel,
          to: toLabel,
          type: e.type,
          chamber: e.chamber,
        }],
      });
    }
  }

  return Array.from(byPerson.values())
    .sort((a, b) => b.switch_count - a.switch_count || (b.last_switch < a.last_switch ? 1 : -1));
}

function typeColor(type: string): string {
  switch (type) {
    case "switch_group":
    case "switch_party":
      return "text-amber-400";
    default:
      return "text-slate-400";
  }
}

function typeLabel(type: string, t: (k: string) => string): string {
  if (type === "switch_group") return t("switchGroup");
  if (type === "switch_party") return t("switchParty");
  return type;
}

export default function DefectionsList({
  onSelect,
  onPartySelect,
}: {
  onSelect: (id: string) => void;
  onPartySelect?: (partyShortName: string) => void;
}) {
  const { t } = useTranslation();
  const events = useQuery({
    queryKey: ["defections-list"],
    queryFn: () => api.movements(),
  });

  if (events.isLoading) {
    return (
      <div className="card p-4">
        <div className="text-slate-500 text-sm py-8">{t("loading")}</div>
      </div>
    );
  }

  if (events.isError) {
    return (
      <div className="card p-4">
        <div className="text-rose-400 text-sm py-8">API error</div>
      </div>
    );
  }

  const switchers = aggregateSwitchers(events.data ?? []);

  if (switchers.length === 0) {
    return (
      <div className="card p-4">
        <div className="text-slate-500 text-sm py-8">{t("noSwitches")}</div>
      </div>
    );
  }

  return (
    <div className="card p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-semibold">{t("defections")}</h2>
        <span className="text-xs text-slate-400">
          {switchers.length} {t("switchers")}
        </span>
      </div>

      <div className="space-y-3 max-h-[600px] overflow-y-auto pr-1">
        {switchers.map((s) => (
          <button
            key={s.person_id}
            onClick={() => onSelect(s.person_id)}
            className="w-full text-left bg-slate-800/40 hover:bg-slate-800 rounded-md p-3 transition-colors"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 text-sm">
                  <span className="font-medium truncate">{s.name}</span>
                  <span className="text-slate-500 text-xs whitespace-nowrap">
                    {s.switch_count}× {t("switchesShort")}
                  </span>
                </div>
                <div className="text-[11px] text-slate-500 mt-0.5 font-mono">
                  {s.last_switch ? t("lastSwitch") + " " + s.last_switch : "—"}
                </div>
              </div>
              <span className="text-xs text-slate-400 shrink-0">{t("viewDetails")}</span>
            </div>

            <div className="mt-2 space-y-1 border-t border-slate-700/50 pt-2">
              {s.switches
                .slice()
                .sort((a, b) => (b.date < a.date ? 1 : -1))
                .slice(0, 3)
                .map((sw, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-xs">
                    <span className={`font-medium ${typeColor(sw.type)}`}>
                      {typeLabel(sw.type, t)}
                    </span>
                    <span className="text-slate-500 font-mono">{sw.date}</span>
                    <span className="text-slate-500">:</span>
                    {onPartySelect && sw.from ? (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onPartySelect(sw.from!);
                        }}
                        className="text-sky-300 hover:underline text-sky-400"
                      >
                        {sw.from}
                      </button>
                    ) : (
                      <span className="text-sky-300">{sw.from ?? "—"}</span>
                    )}
                    <span className="text-slate-500">→</span>
                    {onPartySelect && sw.to ? (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onPartySelect(sw.to!);
                        }}
                        className="text-emerald-300 hover:underline text-emerald-400"
                      >
                        {sw.to}
                      </button>
                    ) : (
                      <span className="text-emerald-300">{sw.to ?? "—"}</span>
                    )}
                    {sw.chamber && (
                      <span className="text-[10px] text-slate-500 px-1.5 py-0.5 bg-slate-800 rounded">
                        {sw.chamber}
                      </span>
                    )}
                  </div>
                ))}
              {s.switches.length > 3 && (
                <div className="text-[11px] text-slate-500">
                  +{s.switches.length - 3} {t("more")}
                </div>
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}