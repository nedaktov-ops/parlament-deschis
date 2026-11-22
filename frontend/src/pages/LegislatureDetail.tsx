import { Suspense, lazy } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api } from "../api/client";
import { useNavigate, useParams } from "@tanstack/react-router";
import { useScope } from "../hooks/useScope";
import HeroGraphic from "../components/HeroGraphic";
import InfoStat from "../components/InfoStat";
import { localISODate } from "../utils/date";
import Skeleton from "../components/ui/Skeleton";
import AsyncState, { resolveViewState } from "../components/ui/AsyncState";

const TimelineChart = lazy(() => import("../components/TimelineChart"));

export function LegislatureDetail() {
  const { t } = useTranslation();
  const navigate = useNavigate({ from: "/legislature/$year" });
  const params = useParams({ from: "/legislature/$year" });
  const scope = useScope();
  const year = params.year;
  const asOf = scope.date;

  const meta = useQuery({ queryKey: ["meta"], queryFn: api.meta });
  const leg = meta.data?.legislatures?.[year];
  // R-08: guard an unknown year before any data query runs. Without this,
  // `start` fell back to 1990 and the page showed an unrelated corpus window.
  const knownYears = Object.keys(meta.data?.legislatures ?? {});
  const yearUnknown = meta.isSuccess && !leg;
  const scoped = !!leg && !yearUnknown;
  const today = localISODate();
  const start = leg?.start ?? "1990-01-01";
  const end = leg?.end ?? today;
  // When no date search param is present, default to the legislature start date
  // so past legislatures show their own data instead of today's.
  const selectedDate = asOf
    ? asOf < start ? start : asOf > end ? end : asOf
    : start;
  const chamberFilter = scope.chamber ?? "deputies";
  const chamber = useQuery({
    queryKey: ["chamber", chamberFilter, selectedDate, ...scope.scopeKey],
    queryFn: () => api.chamber(chamberFilter, selectedDate),
    enabled: scoped,
  });
  const movements = useQuery({
    queryKey: ["leg-movements", year, chamberFilter, start, selectedDate, ...scope.scopeKey],
    queryFn: () => api.movements({
      from: start,
      to: selectedDate,
      limit: 1000,
      chamber: chamberFilter,
      legislature: year,
    }),
    enabled: scoped,
  });

  const metaView = resolveViewState({
    isLoading: meta.isLoading,
    isError: meta.isError,
    isEmpty: meta.isSuccess && !leg,
  });
  if (metaView !== "ready") {
    return (
      <AsyncState
        view={metaView}
        pageTitle={`${t("legislature")} ${year}`}
        onRetry={() => void meta.refetch()}
        errorLabel={t("chamberLoadError")}
      />
    );
  }

  if (yearUnknown) {
    return (
      <div className="wrap p-6" role="alert">
        <h1 className="text-xl font-semibold">{t("legislatureUnknown", { year })}</h1>
        <p className="text-sm text-slate-400">
          {t("legislatureKnownYears", { years: knownYears.join(", ") || "—" })}
        </p>
      </div>
    );
  }

  const chamberView = resolveViewState({
    isLoading: chamber.isLoading,
    isError: chamber.isError,
    isEmpty: chamber.isSuccess && (chamber.data?.total ?? 0) === 0,
  });
  const movementsView = resolveViewState({
    isLoading: movements.isLoading,
    isError: movements.isError,
    isEmpty: movements.isSuccess && (movements.data?.length ?? 0) === 0,
  });

  return (
    <div className="space-y-6">
      <section className="hero-section" data-enter>
        <div>
          <div className="flex flex-col md:flex-row md:items-center gap-8">
            <div className="flex-1 space-y-4">
              <h1 className="page-title">
                {t("legislature")} {year}
              </h1>
              <p className="text-sm text-slate-300 mt-2">
                {t("period")}: {start} → {leg?.end ?? t("present")}
              </p>
            </div>
            <div className="w-full md:w-auto max-w-[260px]">
              <HeroGraphic variant="wave" className="mx-auto" />
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
            <InfoStat
              label={t("legislatureStatMembers", "Members")}
              value={chamber.data?.total ?? "--"}
              accent="sky"
            />
            <InfoStat
              label={t("legislatureStatGroups", "Groups")}
              value={chamber.data?.groups?.length ?? "--"}
              accent="emerald"
            />
            <InfoStat
              label={t("legislatureStatSwitches", "Group switches in this legislature (first 1000)")}
              value={
                movements.isLoading || movements.isError
                  ? "--"
                  : (movements.data?.filter((e) => e.type === "switch_group").length ?? "--")
              }
              accent="amber"
            />
            <InfoStat
              label={t("legislatureStatYears", "Years")}
              value={
                leg?.start && leg?.end
                  ? `${new Date(leg.end).getFullYear() - new Date(leg.start).getFullYear() + 1}`
                  : "--"
              }
              accent="rose"
            />
          </div>
          <div className="mt-8 flex items-center gap-4" data-moment>
            <span className="moment-value block">
              {chamber.data?.total ?? "--"}
            </span>
            <span className="text-sm text-slate-400">
              {t("legislatureStatMembersLabel", "members in legislature")}
            </span>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="card p-4">
          <h2 className="font-semibold mb-3">{t("deputies")}</h2>
          <AsyncState
            view={chamberView}
            variant="inline"
            onRetry={() => void chamber.refetch()}
            errorLabel={t("chamberLoadError")}
            emptyTitle={t("noData")}
          >
            <div className="space-y-2">
              {chamber.data?.groups?.map((g) => (
                <div key={g.short_name} className="flex items-center justify-between bg-slate-800/50 rounded p-2">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full" style={{ background: g.color || "#64748b" }} />
                    <span className="font-medium">{g.short_name}</span>
                  </div>
                  <span className="text-slate-400">{g.count} {t("members")}</span>
                </div>
              ))}
            </div>
          </AsyncState>
        </div>

        <div className="card p-4">
          <h2 className="font-semibold mb-3">{t("recentMovements")}</h2>
          <AsyncState
            view={movementsView}
            variant="inline"
            onRetry={() => void movements.refetch()}
            errorLabel={t("electoralLoadError")}
            emptyTitle={t("noData")}
          >
            <>
              {movements.data?.length === 1000 && (
                <p role="note" className="text-amber-200 text-sm mb-2">{t("displayedMaxMovements")}</p>
              )}
              <div className="space-y-2 max-h-[400px] overflow-y-auto pr-1">
                {movements.data?.slice(0, 20).map((m) => (
                  <button type="button"key={m.id}disabled={!m.person}
                    onClick={() => {
                      if (m.person) {
                        navigate({
                          to: "/person/$id",
                          params: { id: m.person.id },
                          search: scope.searchFor({ date: selectedDate }),
                        });
                      }
                    }}
                    className="w-full text-left bg-slate-800/40 hover:bg-slate-800 rounded-md p-2 transition-colors"
                  >
                    <div className="flex items-center gap-2 text-xs">
                      <span className={`font-semibold ${m.type === "switch_group" || m.type === "switch_party" ? "text-amber-400" : m.type === "join" ? "text-emerald-400" : "text-rose-400"}`}>
                        {m.type}
                      </span>
                      <span className="text-slate-500 font-mono">{m.event_date}</span>
                    </div>
                    <div className="text-sm mt-0.5">
                      {m.person?.name ?? "—"}:
                      {m.from_org?.short_name ?? "—"} → {m.to_org?.short_name ?? "—"}
                    </div>
                  </button>
                ))}
              </div>
            </>
          </AsyncState>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4">
        <Suspense fallback={<Skeleton className="h-64 w-full" />}>
          <TimelineChart from={start} to={selectedDate} />
        </Suspense>
      </div>
    </div>
  );
}