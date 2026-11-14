import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api, type EventItem, type HealthResponse } from "../api/client";

type SourceHealth = Exclude<HealthResponse["sources"][string], string>;

function typeColor(type: string): string {
  switch (type) {
    case "switch_group":
    case "switch_party":
      return "text-amber-400";
    case "join":
    case "join_party":
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
  const sourceRuns = Object.values(health.data?.sources ?? {}).filter(
    (value): value is SourceHealth => typeof value === "object" && value !== null,
  );
  const refreshFailed = sourceRuns.some((source) => source.status === "FAILURE");
  const lastRefresh = sourceRuns
    .map((source) => source.finished_at)
    .filter((value): value is string => !!value)
    .sort();
  const mostRecentRefresh = lastRefresh[lastRefresh.length - 1];
  const refreshLabel = health.isError
    ? t("dataHealthLoadError")
    : refreshFailed
    ? t("dataRefreshFailed")
    : mostRecentRefresh
      ? t("lastDataRefresh", {
          date: Number.isNaN(Date.parse(mostRecentRefresh))
            ? mostRecentRefresh
            : new Date(mostRecentRefresh).toLocaleString(i18n.language),
        })
      : t("dataRefreshUnavailable");

  const summary = (e: EventItem) =>
    i18n.language === "en" ? e.summary_en || e.summary_ro : e.summary_ro || e.summary_en;
  const typeLabel = (type: string) => {
    const labels: Record<string, string> = {
      join: "joined",
      join_party: "joined",
      leave: "left",
      switch_group: "switchGroup",
      switch_party: "switchParty",
      group_founded: "groupFounded",
      group_renamed: "groupRenamed",
      committee_join: "committeeJoined",
      committee_leave: "committeeLeft",
      role_change: "roleChanged",
      mandate_start: "mandateStarted",
      mandate_end: "mandateEnded",
    };
    return t(labels[type] ?? "event");
  };

  return (
    <div className="card p-4 flex flex-col h-full">
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-semibold">{t("liveFeed")}</h2>
        <span className="flex items-center gap-1.5 text-xs text-slate-300" role="status">
          <span
            aria-hidden="true"
            className={`w-2 h-2 rounded-full ${
              refreshFailed ? "bg-rose-400" : mostRecentRefresh ? "bg-emerald-400" : "bg-slate-400"
            }`}
          />
          {refreshLabel}
        </span>
      </div>
      <div className="overflow-y-auto flex-1 space-y-2 max-h-[420px] pr-1">
        {events.isLoading && <div className="text-slate-500 text-sm">{t("loading")}</div>}
        {events.isError && (
          <div className="text-rose-200 text-sm" role="alert">
            {t("activityLoadError")}
          </div>
        )}
        {events.data?.map((e) => (
          <button
            key={e.id}
            onClick={() => e.person && onSelect(e.person.id)}
            disabled={!e.person}
            className="w-full text-left bg-slate-800/40 hover:bg-slate-800 disabled:cursor-default disabled:hover:bg-slate-800/40 rounded-md p-2 transition-colors"
          >
            <div className="flex items-center gap-2 text-xs">
              <span className={`font-semibold ${typeColor(e.type)}`}>{typeLabel(e.type)}</span>
              <span className="text-slate-500 font-mono">{e.event_date}</span>
            </div>
            <div className="text-sm mt-0.5">{summary(e)}</div>
          </button>
        ))}
        {events.data?.length === 0 && (
          <div className="text-slate-300 text-sm">{t("noData")}</div>
        )}
      </div>
    </div>
  );
}