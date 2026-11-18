import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api } from "../api/client";
import GroupLegend from "./GroupLegend";
import Hemicycle from "./Hemicycle";

export default function ChamberView({
  chamber,
  asOf,
  onSelect,
}: {
  chamber: "deputies" | "senate";
  asOf: string;
  onSelect: (id: string) => void;
}) {
  const { t } = useTranslation();
  const data = useQuery({
    queryKey: ["chamber", chamber, asOf],
    queryFn: () => api.chamber(chamber, asOf),
  });

  return (
    <div className="card card-hover p-4 flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <h2 className="font-semibold">{t(chamber)}</h2>
        {data.data && (
          <span className="text-xs text-slate-300">
            {data.data.total} {t("totalSeats")}
          </span>
        )}
      </div>
      {data.isLoading && <div role="status" className="text-slate-300 text-sm py-8">{t("loading")}</div>}
      {data.isError && (
        <div role="alert" className="text-rose-200 text-sm py-4">
          {t("chamberLoadError")}
          <button type="button"className="ml-3 underline" onClick={() => data.refetch()}>
            {t("traseismRetry")}
          </button>
        </div>
      )}
      {data.data && data.data.total === 0 && (
        <div className="text-slate-300 text-sm py-8">{t("noData")}</div>
      )}
      {data.data && data.data.total > 0 && (
        <>
          <Hemicycle groups={data.data.groups} onSelect={onSelect} />
          <div className="mt-3">
            <GroupLegend groups={data.data.groups} />
          </div>
        </>
      )}
    </div>
  );
}