import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api } from "../api/client";
import { useNavigate, useSearch } from "@tanstack/react-router";
import HeroGraphic from "../components/HeroGraphic";
import DashboardCard from "../components/DashboardCard";
import PartyListTable from "../components/PartyListTable";
import PartyNetwork from "../components/PartyNetwork";
import AgeDistributionRadial from "../components/AgeDistributionRadial";
import SwitchTimeline, { SwitchWaveData } from "../components/SwitchTimeline";
import CommitteeControl from "../components/CommitteeControl";
import CrossChamberFlow from "../components/CrossChamberFlow";
import DataQualityGauge from "../components/DataQualityGauge";
import { committeeControl, generationalShift, switchWaves } from "../api/client";
import { localISODate } from "../utils/date";

const TODAY = localISODate();

export function LiveDashboard() {
  const { t } = useTranslation();
  const navigate = useNavigate({ from: "/" });
  const search = useSearch({ from: "/", select: s => s.date });
  const asOf = search ?? TODAY;

  const meta = useQuery({ queryKey: ["meta"], queryFn: api.meta });
  const dashboardStats = useQuery({ queryKey: ["dashboard-stats", asOf], queryFn: () => api.dashboardStats(asOf) });
  const partiesData = useQuery({ queryKey: ["parties"], queryFn: api.parties });
  const switchWavesQuery = useQuery({ queryKey: ["switch-waves"], queryFn: () => switchWaves() });
  const committeeControlQuery = useQuery({ queryKey: ["committee-control", asOf], queryFn: () => committeeControl(undefined, asOf) });
  const crossChamberQuery = useQuery({ queryKey: ["cross-chamber", asOf], queryFn: () => api.crossChamber(asOf) });
  const generationalShiftQuery = useQuery({ queryKey: ["generational-shift", asOf], queryFn: () => generationalShift(undefined, asOf) });
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
  const ageCohorts = generationalShiftQuery.data?.data ?? [];

  const openParty = (shortName: string) => {
    navigate({
      to: "/party/$shortName",
      params: { shortName },
      search: { date: clamped },
    });
  };

  const openPerson = (id: string) => {
    navigate({
      to: "/person/$id",
      params: { id },
      search: { date: clamped },
    });
  };

  // Convert age cohorts to visualization format
  const ageVisualizationData = useMemo(() => {
    if (!ageCohorts.length) return [];
    
    return ageCohorts.map(c => ({
      label: `${c.avg_age}-${c.avg_age + 10}`,
      minAge: c.avg_age,
      maxAge: c.avg_age + 10,
      count: c.mps_with_birth_dates,
      avgAge: c.average_age ?? c.avg_age ?? 0,
    }));
  }, [ageCohorts]);

  const totalAge = useMemo(() => {
    return ageCohorts.reduce((sum: number, c: { avg_age: number; mps_with_birth_dates: number }) => sum + (c.avg_age * c.mps_with_birth_dates), 0);
  }, [ageCohorts]);

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
    <div className="wrap space-y-8">
      {/* Section 1: Hero Header - Concise, no wasted space */}
      <section className="py-8 sm:py-12" data-enter>
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            <div className="lg:col-span-7 space-y-4">
              <h1 className="text-3xl font-bold tracking-tight text-slate-100">{t("overview")}</h1>
              <p className="text-sm text-slate-400">{t("dashboardIntro")}</p>
              
              {/* Key Metrics as DashboardCards - zero wasted space */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
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
                  title={t("dashboardStatSwitches", "Switches")}
                  icon={
                    <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
                      <path d="M12 4v16M8 12h8"/>
                    </svg>
                  }
                  value={stats?.switches ?? "--"}
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
            </div>
            <div className="lg:col-span-5">
              <HeroGraphic variant="overview" className="mx-auto" />
            </div>
          </div>
          
          {/* Legislature info */}
          {meta.data && (
            <div className="mt-8 flex items-center gap-4" data-moment>
              <span className="text-5xl font-black block tracking-tight text-slate-100">
                {Object.keys(meta.data.legislatures).length}
              </span>
              <span className="text-sm text-slate-400">
                {t("dashboardLegislatures", "legislatures in the corpus")}
              </span>
            </div>
          )}
        </div>
      </section>

      {/* Section 2: Party Ecosystem */}
      <section className="px-4 pb-8" data-enter>
        <div className="max-w-7xl mx-auto">
          <h2 className="text-2xl font-bold text-slate-100 mb-6">{t("partyEcosystem", "Party Ecosystem")}</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <PartyListTable
              parties={parties}
              onPartyClick={openParty}
            />
            <div className="grid grid-cols-1 gap-4">
              <CommitteeControl
                data={committeeData ?? { as_of: clamped, total_committees: 0, parties: [], chairs: [] }}
                totalCommittees={stats?.committees ?? 0}
                onChairClick={(chair) => chair.chair_person_id && openPerson(chair.chair_person_id)}
              />
              <DataQualityGauge
                coverageData={coverageDetailed.data ?? []}
              />
            </div>
          </div>
        </div>
      </section>

      {/* Section 3: Deep Dive Visualizations */}
      <section className="px-4 pb-8" data-enter>
        <div className="max-w-7xl mx-auto">
          <h2 className="text-2xl font-bold text-slate-100 mb-6">{t("deepDiveViews", "Deep Dive Views")}</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <PartyNetwork
              parties={parties.slice(0, 10)}
              edges={[]}
              onNodeClick={openParty}
            />
            <AgeDistributionRadial
              cohorts={ageVisualizationData}
              totalAge={totalAge}
            />
            <SwitchTimeline
              waves={waveData}
              legislatures={meta.data?.legislatures ?? {}}
              onWaveClick={(wave: SwitchWaveData) => wave.switch_count > 0 && wave.label && openParty(wave.label)}
            />
            <CrossChamberFlow
              data={crossChamberData}
              onPersonClick={openPerson}
            />
          </div>
        </div>
      </section>
    </div>
  );
}