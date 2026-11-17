import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { Link } from "@tanstack/react-router";
import { get } from "../api/client";
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
  if (n === 0) return "bg-slate-700 text-slate-400";
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
    <div className="p-6">
      <h1 className="text-2xl font-bold text-slate-100 mb-2">
        {t("mps.title", "MP Biography Cards")}
      </h1>
      <p className="text-slate-400 mb-6">
        {t(
          "mps.intro",
          "Browse every person in the corpus with their party, age, observed switches and committee seats. Ages come from recorded birth dates — cards with no birth date show age as unknown, never a guess.",
        )}
      </p>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          setSubmitted(query.trim());
          setOffset(0);
        }}
        className="flex flex-wrap gap-4 mb-6 items-end"
      >
        <label className="flex flex-col gap-1 text-sm text-slate-400">
          {t("mps.search", "Search")}
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t("mps.search.placeholder", "name…")}
            className="bg-slate-800 border border-slate-700 rounded px-3 py-2 text-slate-200 w-56"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm text-slate-400">
          {t("mps.sort", "Sort by")}
          <select
            value={sort}
            onChange={(e) => {
              setSort(e.target.value);
              setOffset(0);
            }}
            className="bg-slate-800 border border-slate-700 rounded px-3 py-2 text-slate-200"
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
          className="bg-sky-600 hover:bg-sky-500 text-white px-4 py-2 rounded focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400"
        >
          {t("mps.go", "Go")}
        </button>
      </form>

      {cards.isLoading && (
        <div className="text-slate-500">{t("loading", "Loading…")}</div>
      )}
      {cards.isError && (
        <div className="text-red-400">
          {t("mps.loadError", "Failed to load MPs.")}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {rows.map((m) => (
          <div
            key={m.id}
            className="bg-slate-800 rounded-lg p-4 hover:bg-slate-750/60 transition-colors"
          >
            <Link
              to="/person/$id"
              params={{ id: m.id }}
              search={{ date: localISODate() }}
              className="text-slate-100 font-semibold hover:text-sky-300 hover:underline block"
            >
              {m.name}
            </Link>
            <div className="mt-2 flex flex-wrap gap-2 text-xs">
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
        <div className="text-slate-500">
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
          {t(
            "mps.coverage.desc",
            "3113 of 3381 persons (92%) have a birth date from cdep.ro committee ledgers. Switch counts are observed switch_group events; committee counts come from the 2024 legislature ingestion. Party is the most recent recorded affiliation.",
          )}
        </p>
      </div>
    </div>
  );
}
