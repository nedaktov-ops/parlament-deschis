// src/components/ui/AgeDistributionSection.tsx
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { generationalShift, type GenerationalShiftEntry } from "../api/client";
import AgeDistributionRadial from "../AgeDistributionRadial";
import Skeleton from "./Skeleton";

/**
 * Shows an age‑distribution radial chart for all MPs.
 * Data is fetched from the `generationalShift` endpoint without a legislature filter
 * to aggregate across the whole corpus.
 */
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
    return (
      <div className="text-red-400 text-sm">
        {t("dashboard.ageDistributionError", "Failed to load age distribution")}
      </div>
    );
  }

  const rows = shift.data?.data ?? [];
  // Convert API rows into the CohortData shape expected by AgeDistributionRadial.
  const cohorts = rows.map((r: GenerationalShiftEntry) => ({
    label: r.party,
    minAge: r.min_age,
    maxAge: r.max_age,
    count: r.mps_with_birth_dates,
    avgAge: r.avg_age,
  }));
  const total = cohorts.reduce((sum, c) => sum + c.count, 0);

  return (
    <div className="bg-slate-800/30 rounded-xl p-4">
      <h2 className="text-sm font-semibold text-slate-300 mb-2">
        {t("dashboard.ageDistribution", "Age Distribution")}
      </h2>
      <AgeDistributionRadial cohorts={cohorts} totalAge={total} width={250} height={250} />
    </div>
  );
}
