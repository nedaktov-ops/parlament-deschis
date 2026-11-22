import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api, type EventItem, type HealthResponse } from "../api/client";
import RetryButton from "./RetryButton";

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
  // A scope change is a *different* feed, not a data release — reset the seen
  // set so old switches from the newly selected scope are not reported as new.
  const [switchAlerts, setSwitchAlerts] = useState<EventItem[]>([]);
  const [alertsMuted, setAlertsMuted] = useState(false);
  const seenIdsRef = useRef<Set<string> | null>(null);
  useEffect(() => {
    seenIdsRef.current = null;
    setSwitchAlerts([]);
    setAlertsMuted(false);
  }, [legislature, chamber]);
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

  // The API already scopes /events/recent by chamber and legislature. Repeating
  // that filter here could silently blank the feed if an event's field differs
  // in format from the prop, turning "wrongly empty" into a false "no data".
  const visibleEvents = events.data ?? [];

  // Show the applied scope next to the title so a reader knows what they are
  // looking at instead of mistaking a slice for the whole corpus.
  const chamberLabel = chamber
    ? chamber === "deputies"
      ? t("deputies")
      : chamber === "senate"
        ? t("senate")
        : chamber
    : null;
  const scopeLabel = [chamberLabel, legislature ? `${t("legislature")} ${legislature}` : null]
    .filter(Boolean)
    .join(" · ");

  return (
    <div className="card p-4 flex flex-col h-full min-h-96">
      <div className="mb-3 flex flex-wrap items-start justify-between gap-x-3 gap-y-2">
        <div className="min-w-0">
          <h2 className="text-base font-semibold text-slate-100">{t("liveFeed")}</h2>
          {scopeLabel ? <p className="mt-0.5 text-xs text-slate-400">{scopeLabel}</p> : null}
        </div>
        <div className="min-w-0 text-right text-xs text-slate-300">
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
          <div className="mb-1 flex items-center justify-between gap-2">
            <span className="text-xs font-semibold text-amber-300">
              {t("switchAlerts.title", "New party switches in this data release")}
            </span>
            <button
              type="button"
              onClick={() => setAlertsMuted(true)}
              aria-label={t("switchAlerts.dismiss", "dismiss")}
              className="btn-hover inline-flex min-h-11 items-center text-xs text-amber-400 underline hover:text-amber-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-amber-400"
            >
              {t("switchAlerts.dismiss", "dismiss")}
            </button>
          </div>
          <ul className="space-y-1">
            {switchAlerts.map((e) => (
              <li key={e.id} className="text-xs text-amber-200">
                <span className="font-mono text-amber-300">
                  {e.event_date}
                </span>{" "}
                {summary(e)}
                {e.person && (
                  <button
                    type="button"
                    onClick={() => onSelect(e.person!.id)}
                    aria-label={`${t("switchAlerts.view", "view")}: ${summary(e)}`}
                    className="btn-hover ml-1 inline-flex min-h-11 items-center text-sky-300 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-400"
                  >
                    {t("switchAlerts.view", "view")}
                  </button>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
      <div
        className="min-h-0 flex-1 space-y-2 overflow-y-auto pr-1"
        tabIndex={0}
        role="region"
        aria-label={scopeLabel ? `${t("liveFeed")}: ${scopeLabel}` : t("liveFeed")}
      >
        {events.isLoading && (
          <div className="flex items-center gap-2 text-sm text-slate-300" role="status" aria-live="polite">
            <span aria-hidden="true" className="inline-block h-2 w-2 rounded-full bg-sky-400 motion-safe:animate-pulse" />
            {t("loading")}
          </div>
        )}
        {events.isError && (
          <div className="rounded-md border border-rose-500/40 bg-slate-800/40 p-3" role="alert">
            <div className="text-sm text-rose-200">{t("activityLoadError")}</div>
            <div className="mt-2">
              <RetryButton
                onRetry={() => void events.refetch()}
                label={t("retry")}
                ariaLabel={t("retry")}
              />
            </div>
          </div>
        )}
        {events.isSuccess && visibleEvents.length === 0 && (
          <div className="text-sm text-slate-300" role="status" aria-live="polite">
            {t("noData")}
          </div>
        )}
        {visibleEvents.map((e) => (
          <button type="button" key={e.id}
            onClick={() => e.person && onSelect(e.person.id)}
            disabled={!e.person}
            className="btn-hover w-full rounded-md bg-slate-800/40 p-2 text-left transition-colors hover:bg-slate-800 disabled:cursor-default disabled:hover:bg-slate-800/40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-400"
          >
            <div className="flex items-center gap-2 text-xs">
              <span className={`font-semibold ${typeColor(e.type)}`}>{typeLabel(e.type)}</span>
              <span className="font-mono text-slate-400">{e.event_date}</span>
            </div>
            <div className="mt-0.5 text-sm">{summary(e)}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
