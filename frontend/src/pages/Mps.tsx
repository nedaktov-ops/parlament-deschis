import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { Link } from "@tanstack/react-router";
import { get } from "../api/client";
import HeroGraphic from "../components/HeroGraphic";
import InfoStat from "../components/InfoStat";
import { localISODate } from "../utils/date";

interface MpCard {
  id: string;
  name: string;
  birth_date: string | null;
  age: number | null;
  party: string | null;
  switches: number;
  committees: number;
}

interface MpsResponse {
  status: string;
  data: MpCard[];
  offset: number;
  limit: number;
}

const PAGE_SIZE = 60;

function fetchMps(
  q: string,
  sort: string,
  offset: number,
): Promise<MpsResponse> {
  const params = new URLSearchParams({
    limit: String(PAGE_SIZE),
    offset: String(offset),
    sort,
  });
  if (q) params.set("q", q);
  return get<MpsResponse>(`/mps?${params.toString()}`);
}

function switchBadge(n: number): string {
  if (n === 0) return "bg-slate-700 text-slate-300";
  if (n <= 2) return "bg-amber-900/40 text-amber-300";
  return "bg-red-900/40 text-red-300";
}

export default function Mps() {
  const { t } = useTranslation();
  const [query, setQuery] = useState<string>("");
  const [submitted, setSubmitted] = useState<string>("");
  const [sort, setSort] = useState<string>("name");
  const [offset, setOffset] = useState<number>(0);

  const cards = useQuery({
    queryKey: ["mps", submitted, sort, offset],
    queryFn: () => fetchMps(submitted, sort, offset),
    placeholderData: (prev) => prev,
  });

  const rows = cards.data?.data ?? [];
  const canPrev = offset > 0;
  const canNext = rows.length === PAGE_SIZE;

  return (
    <div className="wrap space-y-6">
      <section className="min-h-screen flex flex-col justify-center py-8" data-enter>
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row md:items-center gap-8">
            <div className="flex-1 space-y-4">
              <h1 className="text-3xl font-bold tracking-tight">{t("mps.title", "MP Biography Cards")}</h1>
              <p className="text-sm text-slate-300 mt-2">
                {t("mps.intro")}
              </p>
            </div>
            <div className="w-full md:w-auto max-w-[260px]">
              <HeroGraphic variant="people" className="mx-auto" />
            </div>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
            <InfoStat
              label={t("mpsTotalMps", "Total MPs")}
              value={rows.length}
              accent="sky"
            />
            <InfoStat
              label={t("mpsWithParty", "With party")}
              value={rows.filter((m) => m.party).length}
              accent="emerald"
            />
            <InfoStat
              label={t("mpsWithCommittees", "With committees")}
              value={rows.filter((m) => m.committees > 0).length}
              accent="amber"
            />
            <InfoStat
              label={t("mpsTotalSwitches", "Total switches")}
              value={rows.reduce((sum, m) => sum + m.switches, 0)}
              accent="rose"
            />
          </div>
          <div className="mt-8 flex items-center gap-4" data-moment>
            <span className="text-5xl font-black block tracking-tight">
              {rows.length}
            </span>
            <span className="text-sm text-slate-400">
              {t("mpsTotalMpsLabel", "members of parliament in corpus")}
            </span>
          </div>
        </div>
      </section>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          setSubmitted(query.trim());
          setOffset(0);
        }}
        className="flex flex-wrap gap-4 mb-6 items-end bg-slate-800/40 border border-slate-700/60 rounded-lg p-4"
      >
        <label className="flex flex-col gap-1 text-sm text-slate-300">
          {t("mps.search", "Search")}
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t("mps.search.placeholder", "name…")}
            className="bg-slate-800 border border-slate-700 rounded px-3 py-2 text-slate-200 w-56 focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm text-slate-300">
          {t("mps.sort", "Sort by")}
          <select
            value={sort}
            onChange={(e) => {
              setSort(e.target.value);
              setOffset(0);
            }}
            className="bg-slate-800 border border-slate-700 rounded px-3 py-2 text-slate-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400"
          >
            <option value="name">{t("mps.sort.name", "Name")}</option>
            <option value="switches">{t("mps.sort.switches", "Switches")}</option>
            <option value="committees">
              {t("mps.sort.committees", "Committees")}
            </option>
            <option value="age">{t("mps.sort.age", "Age (oldest)")}</option>
          </select>
        </label>
        <button
          type="submit"
          className="bg-sky-700 hover:bg-sky-800 text-white px-4 py-2 rounded btn-hover focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400"
        >
          {t("mps.go", "Go")}
        </button>
      </form>

      {cards.isLoading && (
        <div className="text-slate-400 bg-slate-800/40 border border-slate-700/60 rounded-lg p-4">
          {t("loading", "Loading…")}
        </div>
      )}
      {cards.isError && (
        <div className="text-red-300 bg-red-900/20 border border-red-800/60 rounded-lg p-4">
          {t("mps.loadError", "Failed to load MPs.")}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {rows.map((m) => (
          <div
            key={m.id}
            className="card-hover bg-slate-800 rounded-lg p-4 border border-slate-700/50 hover:bg-slate-750/60 transition-colors"
          >
            <Link
              to="/person/$id"
              params={{ id: m.id }}
              search={{ date: localISODate() }}
              className="link-hover text-slate-100 font-semibold text-lg leading-snug hover:text-sky-300 block focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400 rounded-sm"
            >
              {m.name}
            </Link>
            <div className="mt-3 flex flex-wrap gap-2 text-xs">
              <span className="bg-slate-700 text-slate-300 px-2 py-0.5 rounded">
                {m.party ?? t("mps.noParty", "no party recorded")}
              </span>
              <span className="bg-slate-700 text-slate-300 px-2 py-0.5 rounded">
                {m.age !== null
                  ? t("mps.age", "{{age}} yrs", { age: m.age })
                  : t("mps.ageUnknown", "age unknown")}
              </span>
              <span className={`px-2 py-0.5 rounded ${switchBadge(m.switches)}`}>
                {t("mps.switches", "{{n}} switches", { n: m.switches })}
              </span>
              {m.committees > 0 && (
                <span className="bg-sky-900/40 text-sky-300 px-2 py-0.5 rounded">
                  {t("mps.committees", "{{n}} committees", { n: m.committees })}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {rows.length === 0 && !cards.isLoading && !cards.isError && (
        <div className="text-slate-400 bg-slate-800/30 border border-slate-700/50 rounded-lg p-4">
          {t("mps.empty", "No persons match this search.")}
        </div>
      )}

      <div className="mt-6 flex items-center gap-4">
        <button
          type="button"
          disabled={!canPrev}
          onClick={() => setOffset((o) => Math.max(0, o - PAGE_SIZE))}
          className="bg-slate-700 hover:bg-slate-600 disabled:opacity-40 text-slate-200 px-4 py-2 rounded focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400"
        >
          {t("mps.prev", "Previous")}
        </button>
        <span className="text-slate-500 text-sm">
          {t("mps.offset", "{{offset}}+", { offset })}
        </span>
        <button
          type="button"
          disabled={!canNext}
          onClick={() => setOffset((o) => o + PAGE_SIZE)}
          className="bg-slate-700 hover:bg-slate-600 disabled:opacity-40 text-slate-200 px-4 py-2 rounded focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400"
        >
          {t("mps.next", "Next")}
        </button>
      </div>

      <div className="mt-6 bg-slate-800/50 rounded p-4 text-sm text-slate-400">
        <h2 className="text-slate-200 font-semibold mb-1">
          {t("mps.coverage", "Data coverage")}
        </h2>
        <p>
          {t("mps.coverage.desc")}
        </p>
      </div>
    </div>
  );
}
