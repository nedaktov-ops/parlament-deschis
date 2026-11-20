import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { generationalShift } from "../../api/client";
import AgeDistributionRadial from "../AgeDistributionRadial";
import Skeleton from "./Skeleton";

/** Age-distribution radial chart, aggregated across every legislature. */
export default function AgeDistributionSection() {
  const { t } = useTranslation();
  const shift = useQuery({
    queryKey: ["generational-shift-dashboard"],
    queryFn: () => generationalShift(undefined),
  });

  if (shift.isLoading) {
    return <Skeleton className="h-64 w-full" />;
  }
  if (shift.isError) {
    return <div className="text-red-400 text-sm">{t("ageDistributionError")}</div>;
  }

  const cohorts = (shift.data?.data ?? []).map((row) => ({
    label: row.party,
    count: row.mps_with_birth_dates,
    avgAge: row.avg_age,
  }));
  const total = cohorts.reduce((sum, cohort) => sum + cohort.count, 0);

  return (
    <div className="bg-slate-800/30 rounded-xl p-4">
      <h3 className="text-sm font-semibold text-slate-300 mb-2">
        {t("ageDistribution")}
      </h3>
      <AgeDistributionRadial cohorts={cohorts} totalAge={total} width={250} height={250} />
    </div>
  );
}
