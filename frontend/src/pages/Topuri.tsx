import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api } from "../api/client";
import Skeleton from "../components/ui/Skeleton";

export default function Topuri() {
  const { t } = useTranslation();

  const votesQuery = useQuery({
    queryKey: ["topuri-votes"],
    queryFn: () => api.votes({ chamber: undefined, legislature: undefined, limit: 100 }),
  });

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
          {t("view.topuri.title", "MP behavioural scorecard")}
        </h1>
        <p className="mt-2 text-sm sm:text-base text-slate-400 max-w-3xl">
          {t(
            "view.topuri.intro",
            "Rank MPs by loyalty / rebellion / participation on roll-call votes.",
          )}
        </p>
      </section>

      <section className="bg-slate-800/30 rounded-xl p-4 sm:p-5" data-enter>
        {!dataExists ? (
          <div className="text-slate-500 text-sm py-12 text-center">
            {t("empty.rollcall", "Roll-call vote data is not yet available for this legislature.")}
          </div>
        ) : (
          <div className="text-slate-500 text-sm py-6 text-center">
            {t("topuri.empty", "No behavioural data available yet for the selected scope.")}
          </div>
        )}
      </section>
    </div>
  );
}
