import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { useNavigate, useSearch } from "@tanstack/react-router";
import { api } from "../api/client";
import { localISODate } from "../utils/date";

const TODAY = localISODate();

export default function Parties() {
  const { t } = useTranslation();
  const navigate = useNavigate({ from: "/parties" });
  const search = useSearch({ from: "/parties", select: (s) => s.date });
  const asOf = search ?? TODAY;
  const [q, setQ] = useState("");

  const partiesQuery = useQuery({
    queryKey: ["parties"],
    queryFn: api.parties,
  });

  const parties = useMemo(
    () => partiesQuery.data?.data ?? [],
    [partiesQuery.data],
  );

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    if (!needle) return parties;
    return parties.filter(
      (p) =>
        p.short_name.toLowerCase().includes(needle) ||
        p.name.toLowerCase().includes(needle),
    );
  }, [parties, q]);

  const goToParty = (shortName: string) => {
    navigate({ to: "/party/$shortName", params: { shortName }, search: { date: asOf } });
  };

  return (
    <div className="space-y-6">
      <section className="py-2" data-enter>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-100">
          {t("nav.parties", "Parties")}
        </h1>
        <p className="mt-2 text-sm sm:text-base text-slate-400 max-w-3xl">
          {t(
            "parties.intro",
            "All parties in the corpus (from the public dataset). Click a party to open its profile for the selected date.",
          )}
        </p>
        <p className="mt-2 text-xs text-slate-500 max-w-3xl">
          {t(
            "parties.scopeNote",
            "This list is corpus-wide (not filtered by legislature/chamber in this view).",
          )}
        </p>
      </section>

      <section className="bg-slate-800/30 rounded-xl p-4 sm:p-5" data-enter>
        <div className="flex flex-col sm:flex-row sm:items-end gap-3 sm:gap-4 mb-4">
          <label className="flex-1 min-w-0">
            <span className="block text-xs text-slate-400 mb-1">
              {t("mps.search", "Search")}
            </span>
            <input
              type="text"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder={t("parties.search.placeholder", "name or acronym…")}
              className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-600 text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500/40 focus:border-sky-500"
            />
          </label>
          <div className="text-xs text-slate-400">
            {filtered.length} / {parties.length}
          </div>
        </div>

        {partiesQuery.isLoading && (
          <div className="text-slate-500 text-sm py-6">{t("loading", "Loading…")}</div>
        )}
        {partiesQuery.isError && (
          <div className="text-red-400 text-sm py-6">
            {t("parties.loadError", "Failed to load parties.")}
          </div>
        )}

        {!partiesQuery.isLoading && !partiesQuery.isError && filtered.length === 0 && (
          <div className="text-slate-500 text-sm py-6">
            {t("parties.empty", "No parties match this search.")}
          </div>
        )}

        {!partiesQuery.isLoading && !partiesQuery.isError && filtered.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-slate-400 border-b border-slate-700">
                  <th className="py-2 pr-4 font-medium">{t("party", "Party")}</th>
                  <th className="py-2 pr-4 font-medium">{t("parties.col.shortName", "Acronym")}</th>
                  <th className="py-2 pr-4 font-medium text-right">{t("parties.col.members", "Members")}</th>
                  <th className="py-2 pr-4 font-medium text-right">{t("parties.col.switchesIn", "Switches in")}</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((p) => (
                  <tr
                    key={p.id}
                    className="border-b border-slate-700/40 hover:bg-slate-800/40 cursor-pointer"
                    onClick={() => goToParty(p.short_name)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        goToParty(p.short_name);
                      }
                    }}
                  >
                    <td className="py-2.5 pr-4 text-slate-200">{p.name}</td>
                    <td className="py-2.5 pr-4">
                      <span className="inline-flex items-center gap-2">
                        {p.color ? (
                          <span
                            className="inline-block w-2.5 h-2.5 rounded-full"
                            style={{ backgroundColor: p.color }}
                            aria-hidden="true"
                          />
                        ) : null}
                        <span className="text-slate-300 font-mono text-xs">{p.short_name}</span>
                      </span>
                    </td>
                    <td className="py-2.5 pr-4 text-right text-slate-300 tabular-nums">{p.total_members}</td>
                    <td className="py-2.5 pr-4 text-right text-slate-300 tabular-nums">{p.switches_in}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
