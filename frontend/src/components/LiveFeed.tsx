import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api, type EventItem, type HealthResponse } from "../api/client";

type SourceHealth = Exclude<HealthResponse["sources"][string], string>;
const DATASET_STALE_AFTER_MS = 48 * 60 * 60 * 1000;

interface LiveFeedProps {
  onSelect: (id: string) => void;
  legislature?: string | null;
  chamber?: string | null;
}

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

// P0-A: a React component receives ONE props argument (the second argument is
// legacy context). The previous two-parameter signature silently discarded
// legislature/chamber, so the feed and its switch alerts mixed all scopes.
export default function LiveFeed({
  onSelect,
  legislature,
  chamber,
}: LiveFeedProps) {
  const { t, i18n } = useTranslation();
  const events = useQuery({
    queryKey: ["recent", legislature ?? undefined, chamber ?? undefined],
    queryFn: () => api.recentEvents(40, chamber ?? undefined, legislature ?? undefined),
    // Production data is immutable at runtime (the poller is disabled in
    // render.yaml). There is nothing new to poll for between releases, so the
    // feed refreshes on mount/window-focus only. Alerts therefore mean "new
    // since the previous data release", not "real-time".
  });

  // New-switch detection: everything present on first load is "seen"; any
  // switch_group/switch_party row arriving later raises a dismissible alert.
  const [switchAlerts, setSwitchAlerts] = useState<EventItem[]>([]);
  const [alertsMuted, setAlertsMuted] = useState(false);
  const seenIdsRef = useRef<Set<string> | null>(null);
  useEffect(() => {
    const list = events.data;
    if (!list) return;
    if (seenIdsRef.current === null) {
      seenIdsRef.current = new Set(list.map((e) => e.id));
      return;
    }
    const seen = seenIdsRef.current;
    const fresh = list.filter(
      (e) =>
        (e.type === "switch_group" || e.type === "switch_party") &&
        !seen.has(e.id),
    );
    for (const e of list) seen.add(e.id);
    if (fresh.length > 0) {
      setAlertsMuted(false);
      setSwitchAlerts((prev) => [...fresh, ...prev].slice(0, 5));
    }
  }, [events.data]);
  const health = useQuery({
    queryKey: ["health"],
    queryFn: api.health,
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
  const dataset = health.data?.dataset;
  const publishedAt = dataset?.published_at ? Date.parse(dataset.published_at) : Number.NaN;
  const datasetIsStale =
    Number.isFinite(publishedAt) && Date.now() - publishedAt > DATASET_STALE_AFTER_MS;
  const formattedPublishedAt = Number.isFinite(publishedAt)
    ? new Date(publishedAt).toLocaleString(i18n.language)
    : null;

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
        <div className="text-right text-xs text-slate-300">
          <span className="flex items-center justify-end gap-1.5" role="status">
            <span
              aria-hidden="true"
              className={`w-2 h-2 rounded-full ${
                refreshFailed ? "bg-rose-400" : mostRecentRefresh ? "bg-emerald-400" : "bg-slate-400"
              }`}
            />
            {refreshLabel}
          </span>
          {dataset?.release_tag ? (
            <div className="mt-1 text-slate-400">{t("datasetRelease", { tag: dataset.release_tag })}</div>
          ) : null}
          <div className={`mt-1 ${datasetIsStale ? "text-amber-200" : "text-slate-400"}`}>
            {formattedPublishedAt
              ? t("datasetPublished", { date: formattedPublishedAt })
              : t("datasetPublicationUnavailable")}
          </div>
          {datasetIsStale ? (
            <div className="mt-1 text-amber-200" role="status">{t("datasetStale")}</div>
          ) : null}
        </div>
      </div>
      {switchAlerts.length > 0 && !alertsMuted && (
        <div
          role="alert"
          className="mb-3 rounded-md border border-amber-500/50 bg-amber-950/40 p-2"
        >
          <div className="flex items-center justify-between gap-2 mb-1">
            <span className="text-amber-300 text-xs font-semibold">
              {t("switchAlerts.title", "New party switches in this data release")}
            </span>
              <button
                type="button"
                onClick={() => setAlertsMuted(true)}
                className="btn-hover text-amber-400/80 hover:text-amber-200 text-xs underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-amber-400"
              >
                {t("switchAlerts.dismiss", "dismiss")}
              </button>
          </div>
          <ul className="space-y-1">
            {switchAlerts.map((e) => (
              <li key={e.id} className="text-xs text-amber-100/90">
                <span className="font-mono text-amber-300/80">
                  {e.event_date}
                </span>{" "}
                {summary(e)}
                {e.person && (
                  <button
                    type="button"
                    onClick={() => onSelect(e.person!.id)}
                    className="ml-1 text-sky-300 hover:underline"
                  >
                    {t("switchAlerts.view", "view")}
                  </button>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
      <div className="overflow-y-auto flex-1 space-y-2 max-h-[420px] pr-1" tabIndex={0} role="region" aria-label={t("liveFeed", "Live feed")}>
        {events.isLoading && <div className="text-slate-500 text-sm">{t("loading")}</div>}
        {events.isError && (
          <div className="text-rose-200 text-sm" role="alert">
            {t("activityLoadError")}
          </div>
        )}
        {events.data?.filter((e) => {
          if (legislature && e.legislature !== legislature) return false;
          if (chamber && e.chamber !== chamber) return false;
          return true;
        })?.map((e) => (
          <button type="button" key={e.id}
            onClick={() => e.person && onSelect(e.person.id)}
            disabled={!e.person}
            className="btn-hover w-full text-left bg-slate-800/40 hover:bg-slate-800 disabled:cursor-default disabled:hover:bg-slate-800/40 rounded-md p-2 transition-colors"
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