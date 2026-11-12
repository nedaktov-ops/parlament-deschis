import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api } from "../api/client";
import { useRouter, useSearch } from "@tanstack/react-router";
import ChamberView from "../components/ChamberView";
import LiveFeed from "../components/LiveFeed";
import TimelineChart from "../components/TimelineChart";
import DefectionSankey from "../components/DefectionSankey";
import Search from "../components/Search";
import TimeSlider from "../components/TimeSlider";
import PersonDrawer from "../components/PersonDrawer";

const TODAY = new Date().toISOString().slice(0, 10);

export function LiveDashboard() {
  const { t, i18n } = useTranslation();
  const router = useRouter();
  const search = useSearch({ from: "/", select: s => s.date });
  const [asOf, setAsOf] = useState<string>((search as string) ?? TODAY);
  const [personId, setPersonId] = useState<string | null>(null);

  const meta = useQuery({ queryKey: ["meta"], queryFn: api.meta });
  const coverage = useQuery({ queryKey: ["coverage"], queryFn: api.coverage });

  const { min, ticks } = useMemo(() => {
    const legs = Object.values(meta.data?.legislatures ?? {})
      .filter((l) => l.start !== null)
      .sort((a, b) => (a.start ?? "").localeCompare(b.start ?? ""));
    const start = legs[0]?.start ?? null;
    const earliest = start !== null && start <= TODAY ? start : "1990-06-18";
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
    router.navigate({ search: { date: iso } as any, replace: true });
  };

  const openPerson = (id: string) => {
    setPersonId(id);
    router.navigate({ to: "/person/$id", params: { id }, search: { date: clamped } as any, replace: false });
  };

  const closePerson = () => {
    setPersonId(null);
    router.navigate({ to: "/", search: { date: clamped } as any, replace: false });
  };

  function completenessClass(value: string): string {
    if (value === "full") return "bg-emerald-900/50 text-emerald-300";
    if (value === "partial") return "bg-amber-900/50 text-amber-300";
    return "bg-slate-800 text-slate-400";
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-700/60 bg-panel/50 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 py-4 flex flex-col sm:flex-row sm:items-center gap-3">
          <div className="flex-1">
            <h1 className="text-xl font-bold tracking-tight">{t("title")}</h1>
            <p className="text-xs text-slate-400">{t("subtitle")}</p>
          </div>
          <div className="flex items-center gap-2">
            <Search onSelect={openPerson} />
            <button
              className="btn bg-slate-700 hover:bg-slate-600"
              disabled
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

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <ChamberView chamber="deputies" asOf={clamped} onSelect={openPerson} />
          <ChamberView chamber="senate" asOf={clamped} onSelect={openPerson} />
          <LiveFeed onSelect={openPerson} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <TimelineChart from={min} to={TODAY} groups={meta.data?.groups} />
          <DefectionSankey />
        </div>
      </main>

      <PersonDrawer personId={personId} onClose={closePerson} />
    </div>
  );
}