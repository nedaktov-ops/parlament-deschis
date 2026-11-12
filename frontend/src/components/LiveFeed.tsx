import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api, type EventItem } from "../api/client";

function typeColor(type: string): string {
  switch (type) {
    case "switch_group":
    case "switch_party":
      return "text-amber-400";
    case "join":
      return "text-emerald-400";
    case "leave":
      return "text-rose-400";
    case "group_founded":
    case "group_renamed":
      return "text-sky-400";
    default:
      return "text-slate-400";
  }
}

export default function LiveFeed({ onSelect }: { onSelect: (id: string) => void }) {
  const { t, i18n } = useTranslation();
  const events = useQuery({ queryKey: ["recent"], queryFn: () => api.recentEvents(40) });
  const health = useQuery({
    queryKey: ["health"],
    queryFn: api.health,
    refetchInterval: 60_000,
  });

  const summary = (e: EventItem) =>
    i18n.language === "en" ? e.summary_en || e.summary_ro : e.summary_ro || e.summary_en;

  return (
    <div className="card p-4 flex flex-col h-full">
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-semibold">{t("liveFeed")}</h2>
        <span className="flex items-center gap-1.5 text-xs text-slate-400">
          <span
            className={`w-2 h-2 rounded-full ${
              health.data?.status === "ok" ? "bg-emerald-500 animate-pulse" : "bg-slate-500"
            }`}
          />
          live
        </span>
      </div>
      <div className="overflow-y-auto flex-1 space-y-2 max-h-[420px] pr-1">
        {events.isLoading && <div className="text-slate-500 text-sm">{t("loading")}</div>}
        {events.data?.map((e) => (
          <button
            key={e.id}
            onClick={() => e.person && onSelect(e.person.id)}
            className="w-full text-left bg-slate-800/40 hover:bg-slate-800 rounded-md p-2 transition-colors"
          >
            <div className="flex items-center gap-2 text-xs">
              <span className={`font-semibold ${typeColor(e.type)}`}>{e.type}</span>
              <span className="text-slate-500 font-mono">{e.event_date}</span>
            </div>
            <div className="text-sm mt-0.5">{summary(e)}</div>
          </button>
        ))}
        {events.data?.length === 0 && (
          <div className="text-slate-500 text-sm">{t("noData")}</div>
        )}
      </div>
    </div>
  );
}