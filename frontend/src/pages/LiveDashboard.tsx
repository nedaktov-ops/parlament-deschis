import { lazy, Suspense, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api, committeeControl, switchWaves } from "../api/client";
import { useNavigate } from "@tanstack/react-router";
import { useScope } from "../hooks/useScope";
import HeroGraphic from "../components/HeroGraphic";
import DashboardCard from "../components/DashboardCard";
import PartyListTable from "../components/PartyListTable";
import CommitteeControl from "../components/CommitteeControl";
import DataQualityGauge from "../components/DataQualityGauge";
import DashboardHeader from "../components/ui/DashboardHeader";
import AgeDistributionSection from "../components/ui/AgeDistributionSection";
import Skeleton from "../components/ui/Skeleton";
import AsyncState, { resolveViewState } from "../components/ui/AsyncState";
import type { SwitchWaveData } from "../components/SwitchTimeline";
import { localISODate } from "../utils/date";
import LiveFeed from "../components/LiveFeed";

// Heavy visualisations load only when the dashboard is opened.
const PartyNetwork = lazy(() => import("../components/PartyNetwork"));
const SwitchTimeline = lazy(() => import("../components/SwitchTimeline"));
const CrossChamberFlow = lazy(() => import("../components/CrossChamberFlow"));

const TODAY = localISODate();

export function LiveDashboard() {
  const { t } = useTranslation();
  const navigate = useNavigate({ from: "/" });
  const scope = useScope();
  const asOf = scope.date;

  const meta = useQuery({ queryKey: ["meta"], queryFn: api.meta });
  const dashboardStats = useQuery({ queryKey: ["dashboard-stats", asOf, ...scope.scopeKey], queryFn: () => api.dashboardStats(asOf) });
  const partiesData = useQuery({ queryKey: ["parties"], queryFn: api.parties });
  const switchWavesQuery = useQuery({ queryKey: ["switch-waves"], queryFn: () => switchWaves() });
  const committeeControlQuery = useQuery({ queryKey: ["committee-control", asOf, ...scope.scopeKey], queryFn: () => committeeControl(scope.legislature, asOf) });
  const crossChamberQuery = useQuery({ queryKey: ["cross-chamber", asOf, ...scope.scopeKey], queryFn: () => api.crossChamber(asOf) });
  const coverageDetailed = useQuery({ queryKey: ["coverage-detailed"], queryFn: api.coverage_detailed });

  const { min } = useMemo(() => {
    const legs = Object.values(meta.data?.legislatures ?? {})
      .filter((l) => l.start !== null)
      .sort((a, b) => (a.start ?? "").localeCompare(b.start ?? ""));
    const start = legs[0]?.start ?? null;
    const earliest = start !== null && start <= TODAY ? start : "1990-06-18";
    return {
      min: earliest,
    };
  }, [meta.data]);

  const clamped = asOf < min ? min : asOf > TODAY ? TODAY : asOf;

  const stats = dashboardStats.data?.data;
  const parties = partiesData.data?.data ?? [];
  const waves = switchWavesQuery.data ?? [];
  const committeeData = committeeControlQuery.data?.data;
  const crossChamberData = crossChamberQuery.data?.data ?? [];

  const statsView = resolveViewState({
    isLoading: dashboardStats.isLoading,
    isError: dashboardStats.isError,
    isEmpty: dashboardStats.isSuccess && !stats,
  });
  const partiesView = resolveViewState({
    isLoading: partiesData.isLoading,
    isError: partiesData.isError,
    isEmpty: partiesData.isSuccess && parties.length === 0,
  });
  const committeeView = resolveViewState({
    isLoading: committeeControlQuery.isLoading,
    isError: committeeControlQuery.isError,
    isEmpty: committeeControlQuery.isSuccess && !committeeData,
  });
  const coverageView = resolveViewState({
    isLoading: coverageDetailed.isLoading,
    isError: coverageDetailed.isError,
    isEmpty: coverageDetailed.isSuccess && (coverageDetailed.data ?? []).length === 0,
  });
  const crossView = resolveViewState({
    isLoading: crossChamberQuery.isLoading,
    isError: crossChamberQuery.isError,
    isEmpty: crossChamberQuery.isSuccess && crossChamberData.length === 0,
  });
  const wavesView = resolveViewState({
    isLoading: switchWavesQuery.isLoading,
    isError: switchWavesQuery.isError,
    isEmpty: switchWavesQuery.isSuccess && waves.length === 0,
  });

  const openParty = (shortName: string) => {
    navigate({
      to: "/party/$shortName",
      params: { shortName },
      search: scope.searchFor({ date: clamped }),
    });
  };

  const openPerson = (id: string) => {
    navigate({
      to: "/person/$id",
      params: { id },
      search: scope.searchFor({ date: clamped }),
    });
  };

  // Convert waves to the visualization component format
  const waveData: SwitchWaveData[] = waves.map(w => ({
    id: w.id,
    label: w.label,
    start_date: w.start_date,
    end_date: w.end_date,
    switch_count: w.switch_count,
    trigger_type: w.trigger_type,
    legislature: w.legislature,
    chamber: w.chamber,
  }));

  return (
    <div className="space-y-8">
      {/* Section 1: Hero Header - Concise, no wasted space */}
      <section className="py-8 sm:py-12 lg:py-14" data-enter>
        <div>
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-10 items-start">
            <div className="lg:col-span-7 space-y-5">
              <DashboardHeader />
              <p className="text-sm sm:text-base text-slate-300/90 max-w-2xl leading-relaxed">{t("dashboardIntro")}</p>
              
              {/* Key Metrics as DashboardCards - zero wasted space */}
              <AsyncState
                view={statsView}
                variant="inline"
                onRetry={() => void dashboardStats.refetch()}
                errorLabel={t("dashboard.loadError")}
              >
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4 pt-2">
                <DashboardCard
                  title={t("dashboardStatPersons", "Members of Parliament")}
                  icon={
                    <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
                      <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="2"/>
                    </svg>
                  }
                  value={stats?.persons ?? "--"}
                  linkTo="/mps"
                  color="sky"
                />
                <DashboardCard
                  title={t("dashboardStatMemberships", "Memberships")}
                  icon={
                    <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
                      <path d="M12 2L2 7l10 5 10-5-10-5ZM2 17l10 5 10-5M2 12l10 5 10-5"/>
                    </svg>
                  }
                  value={stats?.memberships ?? "--"}
                  linkTo="/mps"
                  color="emerald"
                />
                <DashboardCard
                  title={t("dashboardStatSwitches", "All observed affiliation changes")}
                  icon={
                    <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
                      <path d="M12 4v16M8 12h8"/>
                    </svg>
                  }
                  value={stats?.switches_all ?? "--"}
                  linkTo="/traseism"
                  color="amber"
                />
                <DashboardCard
                  title={t("dashboardStatCommittees", "Committees")}
                  icon={
                    <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
                      <rect x="3" y="4" width="18" height="16" rx="2"/>
                      <line x1="3" y1="9" x2="21" y2="9" stroke="currentColor" strokeWidth="2"/>
                    </svg>
                  }
                  value={stats?.committees ?? "--"}
                  linkTo="/committees"
                  color="rose"
                />
              </div>
              </AsyncState>
            </div>
            <div className="lg:col-span-5 lg:pt-1">
              <HeroGraphic variant="overview" className="mx-auto" />
            </div>
          </div>
          
          {/* Legislature info */}
          {meta.data && (
            <div className="mt-10 sm:mt-12 flex flex-wrap items-baseline gap-x-4 gap-y-2 border-t border-slate-800/80 pt-8" data-moment>
              <span className="moment-value">
                {Object.keys(meta.data.legislatures).length}
              </span>
              <span className="text-sm sm:text-base text-slate-400">
                {t("dashboardLegislatures", "legislatures in the corpus")}
              </span>
            </div>
          )}
        </div>
      </section>

      {/* Section 2: Party Ecosystem */}
      <section className="pb-8 sm:pb-10" data-enter>
        <div>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-100 mb-4 sm:mb-5">{t("partyEcosystem", "Party Ecosystem")}</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 lg:gap-6 lg:items-start">
            <AsyncState
              view={partiesView}
              variant="inline"
              onRetry={() => void partiesData.refetch()}
              errorLabel={t("dashboard.loadError")}
            >
              <PartyListTable
                parties={parties}
                onPartyClick={openParty}
                onViewAll={() => navigate({ to: "/parties", search: scope.searchFor({ date: clamped }) })}
              />
            </AsyncState>
            <div className="grid grid-cols-1 gap-4">
              <CommitteeControl
                data={committeeData}
                totalCommittees={stats?.committees ?? 0}
                onChairClick={(chair) => chair.chair_person_id && openPerson(chair.chair_person_id)}
                view={committeeView}
                onRetry={() => void committeeControlQuery.refetch()}
              />
              <DataQualityGauge
                coverageData={coverageDetailed.data ?? []}
                view={coverageView}
                onRetry={() => void coverageDetailed.refetch()}
              />
              <AgeDistributionSection />
            </div>
          </div>
        </div>
      </section>

      {/* Section 3: Deep Dive Visualizations */}
      <section className="pb-8 sm:pb-10" data-enter>
        <div>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-100 mb-4 sm:mb-5">{t("deepDiveViews", "Deep Dive Views")}</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-5">
            <AsyncState view={partiesView} variant="inline" onRetry={() => void partiesData.refetch()} errorLabel={t("dashboard.loadError")}>
            <Suspense fallback={<Skeleton className="h-64 w-full" />}>
              <PartyNetwork
                parties={parties.slice(0, 10)}
                edges={[]}
                onNodeClick={openParty}
                onViewAll={() => navigate({ to: "/mps", search: scope.searchFor({ date: clamped }) })}
              />
            </Suspense>
            </AsyncState>
            <AsyncState view={wavesView} variant="inline" onRetry={() => void switchWavesQuery.refetch()} errorLabel={t("dashboard.loadError")}>
            <Suspense fallback={<Skeleton className="h-64 w-full" />}>
              <SwitchTimeline
                waves={waveData}
                legislatures={meta.data?.legislatures ?? {}}
                onWaveClick={() => navigate({ to: "/traseism", search: scope.searchFor({ date: clamped, chamber: "deputies", legislature: undefined }) })}
              />
            </Suspense>
            </AsyncState>
            <AsyncState view={crossView} variant="inline" onRetry={() => void crossChamberQuery.refetch()} errorLabel={t("dashboard.loadError")}>
            <Suspense fallback={<Skeleton className="h-64 w-full" />}>
              <CrossChamberFlow
                data={crossChamberData}
                onPersonClick={openPerson}
              />
            </Suspense>
            </AsyncState>
            <AsyncState view={partiesView} variant="inline" onRetry={() => void partiesData.refetch()} errorLabel={t("dashboard.loadError")}>
            <LiveFeed
              legislature="2024"
              chamber="senate"
              onSelect={(id) => navigate({ to: "/person/$id", params: { id }, search: scope.searchFor({ date: clamped }) })}
            />
            </AsyncState>
          </div>
        </div>
      </section>
    </div>
  );
}