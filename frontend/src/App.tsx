import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api } from "./api/client";
import About from "./components/About";
import ChamberView from "./components/ChamberView";
import DefectionSankey from "./components/DefectionSankey";
import DefectionsList from "./components/DefectionsList";
import CurrentLegislatureView from "./components/CurrentLegislatureView";
import LiveFeed from "./components/LiveFeed";
import PartyFlowDetail from "./components/PartyFlowDetail";
import PersonDrawer from "./components/PersonDrawer";
import Search from "./components/Search";
import TimelineChart from "./components/TimelineChart";
import TimeSlider from "./components/TimeSlider";

type Tab = "overview" | "current-legislature" | "defections" | "party-detail";

function getParam(key: string, fallback: string | null): string | null {
  return new URLSearchParams(window.location.search).get(key) ?? fallback;
}

function setParam(key: string, value: string | null) {
  const url = new URL(window.location.href);
  if (value === null) url.searchParams.delete(key);
  else url.searchParams.set(key, value);
  window.history.replaceState(null, "", url);
}

const TODAY = new Date().toISOString().slice(0, 10);
const FALLBACK_START = "1990-06-18";

function completenessClass(value: string): string {
  if (value === "full") return "bg-emerald-900/50 text-emerald-300";
  if (value === "partial") return "bg-amber-900/50 text-amber-300";
  return "bg-slate-800 text-slate-400";
}

export default function App() {
  const { t, i18n } = useTranslation();
  const [asOf, setAsOf] = useState<string>(() => getParam("date", TODAY) ?? TODAY);
  const [personId, setPersonId] = useState<string | null>(() => getParam("person", null));
  const [aboutOpen, setAboutOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>(() =>
    (getParam("tab", "overview") as Tab) ?? "overview"
  );
  const [selectedParty, setSelectedParty] = useState<string | null>(null);

  const meta = useQuery({ queryKey: ["meta"], queryFn: api.meta });
  const coverage = useQuery({ queryKey: ["coverage"], queryFn: api.coverage });

  const { min, ticks } = useMemo(() => {
    const legs = Object.values(meta.data?.legislatures ?? {})
      .filter((l) => l.start !== null)
      .sort((a, b) => (a.start ?? "").localeCompare(b.start ?? ""));
    const start = legs[0]?.start ?? null;
    const earliest = start !== null && start <= TODAY ? start : FALLBACK_START;
    return {
      min: earliest,
      ticks: legs.map((l) => ({ label: l.label, start: l.start ?? "" })),
    };
  }, [meta.data]);

  const clamped = asOf < min ? min : asOf > TODAY ? TODAY : asOf;

  const currentCoverage = useMemo(() => {
    const matched = (coverage.data ?? []).filter(
      (c) =>
        c.period_start !== null &&
        c.period_start <= clamped &&
        clamped < (c.period_end ?? TODAY),
    );
    if (matched.length === 0) return undefined;
    const rank = (value: string) =>
      value === "full" ? 2 : value === "partial" ? 1 : 0;
    // A term can have one coverage row per chamber; show the weakest so the
    // badge never overstates what is available.
    return matched.reduce((worst, row) =>
      rank(row.completeness) < rank(worst.completeness) ? row : worst,
    );
  }, [coverage.data, clamped]);

  const selectedLegislature = useMemo(() => {
    const legs = Object.values(meta.data?.legislatures ?? {})
      .filter((l) => l.start !== null)
      .sort((a, b) => (a.start ?? "").localeCompare(b.start ?? ""));
    return (
      legs.find(
        (l) => (l.start ?? "") <= clamped && clamped < (l.end ?? TODAY),
      )?.label ?? null
    );
  }, [meta.data, clamped]);

  const changeDate = (iso: string) => {
    setAsOf(iso);
    setParam("date", iso);
  };
  const setTab = (tab: Tab) => {
    setActiveTab(tab);
    setParam("tab", tab);
  };
  const openPerson = (id: string) => {
    setPersonId(id);
    setParam("person", id);
  };
  const openParty = (partyShortName: string) => {
    setSelectedParty(partyShortName);
    setTab("party-detail");
  };
  const closeParty = () => {
    setSelectedParty(null);
    setTab("defections");
  };
  const closePerson = () => {
    setPersonId(null);
    setSelectedParty(null);
    setParam("person", null);
  };

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-700/60 bg-panel/50">
        <div className="max-w-7xl mx-auto px-4 py-4 flex flex-col sm:flex-row sm:items-center gap-3">
          <div className="flex-1">
            <h1 className="text-xl font-bold tracking-tight">{t("title")}</h1>
            <p className="text-xs text-slate-400">{t("subtitle")}</p>
          </div>
          <div className="flex items-center gap-2">
            <Search onSelect={openPerson} />
            <button
              className="btn bg-slate-700 hover:bg-slate-600"
              onClick={() => setAboutOpen(true)}
            >
              {t("about")}
            </button>
            <button
              className="btn bg-slate-700 hover:bg-slate-600 uppercase"
              onClick={() => i18n.changeLanguage(i18n.language === "ro" ? "en" : "ro")}
              title="RO / EN"
            >
              {i18n.language === "ro" ? "EN" : "RO"}
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-5 space-y-4">
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="text-slate-500">{t("coverageNote")}:</span>
          <span className="bg-slate-800 rounded px-2 py-0.5 text-slate-300">
            {currentCoverage?.legislature ?? selectedLegislature ?? t("currentTerm")}
          </span>
          <span
            className={`rounded px-2 py-0.5 ${completenessClass(
              currentCoverage?.completeness ?? "none",
            )}`}
          >
            {t(currentCoverage?.completeness ?? "none")}
          </span>
        </div>

        <TimeSlider value={clamped} min={min} max={TODAY} onChange={changeDate} ticks={ticks} />

        <div className="flex gap-1 border-b border-slate-700 mb-4">
          <button
            onClick={() => setTab("overview")}
            className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
              activeTab === "overview"
                ? "bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            {t("overview")}
          </button>
          <button
            onClick={() => setTab("current-legislature")}
            className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
              activeTab === "current-legislature"
                ? "bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            {t("currentLegislature")}
          </button>
          <button
            onClick={() => setTab("defections")}
            className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
              activeTab === "defections"
                ? "bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            {t("defections")}
          </button>
        </div>

        {activeTab === "overview" && (
          <>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <ChamberView chamber="deputies" asOf={clamped} onSelect={openPerson} />
              <ChamberView chamber="senate" asOf={clamped} onSelect={openPerson} />
              <LiveFeed onSelect={openPerson} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <TimelineChart from={min} to={TODAY} groups={meta.data?.groups} />
              <DefectionSankey />
            </div>
          </>
        )}

        {activeTab === "defections" && (
          <DefectionsList onSelect={openPerson} onPartySelect={openParty} />
        )}

        {activeTab === "current-legislature" && (
          <CurrentLegislatureView
            asOf={clamped}
            onSelect={openPerson}
            currentLegislature={selectedLegislature}
          />
        )}

        {activeTab === "party-detail" && selectedParty && (
          <PartyFlowDetail
            partyShortName={selectedParty}
            onBack={closeParty}
            onPersonSelect={openPerson}
          />
        )}
      </main>

      <PersonDrawer personId={personId} onClose={closePerson} />
      <About open={aboutOpen} onClose={() => setAboutOpen(false)} />
    </div>
  );
}