import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api, type VoteRow } from "../api/client";
import Skeleton from "../components/ui/Skeleton";

export default function Radar() {
  const { t } = useTranslation();

  const votesQuery = useQuery({
    queryKey: ["radar-votes"],
    queryFn: () => api.votes({ chamber: undefined, legislature: undefined, limit: 100 }),
  });

  const votes = useMemo(() => votesQuery.data?.data ?? [], [votesQuery.data]);
  const dataExists = votesQuery.data?.data_exists ?? false;

  if (votesQuery.isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Skeleton className="h-8 w-32" />
        <Skeleton className="mt-2 h-4 w-64" />
        <p className="mt-2 text-sm text-slate-500">{t("loading", "Loading…")}</p>
      </div>
    );
  }

  if (votesQuery.isError) {
    return (
      <div className="text-red-400 text-sm py-6 text-center">
        {t("view.voturi.loadError", "Failed to load votes.")}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <section className="py-2" data-enter>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-100">
          {t("view.radar.title", "Roll-call alignment matrix")}
        </h1>
        <p className="mt-2 text-sm sm:text-base text-slate-400 max-w-3xl">
          {t(
            "view.radar.intro",
            "How parliamentary groups align on roll-call votes: yes / no / abstain / did-not-vote heatmap by party.",
          )}
        </p>
      </section>

      <section className="bg-slate-800/30 rounded-xl p-4 sm:p-5" data-enter>
        {!dataExists || votes.length === 0 ? (
          <div className="text-slate-500 text-sm py-12 text-center">
            {t("empty.rollcall", "Roll-call vote data is not yet available for this legislature.")}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table
              role="table"
              aria-label={t("aria.rollcallTable", "Table of plenary votes and each MP's position")}
              className="min-w-full text-sm"
            >
              <thead>
                <tr className="text-left text-slate-400 border-b border-slate-700">
                  <th className="py-2.5 pr-4 font-medium" scope="col">
                    {t("filter.date", "Date")}
                  </th>
                  <th className="py-2.5 pr-4 font-medium" scope="col">
                    {t("mps.search", "Title")}
                  </th>
                  <th className="py-2.5 pr-4 font-medium" scope="col">
                    {t("filter.chamber", "Chamber")}
                  </th>
                </tr>
              </thead>
              <tbody>
                {votes.map((v: VoteRow) => (
                  <tr key={v.native_vote_id} className="border-b border-slate-700/40">
                    <td className="py-2.5 pr-4 text-slate-200">{v.vote_time ?? "—"}</td>
                    <td className="py-2.5 pr-4 text-slate-200">{v.title_raw ?? "—"}</td>
                    <td className="py-2.5 pr-4 text-slate-300">{v.chamber}</td>
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
