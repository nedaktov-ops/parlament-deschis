import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api } from "../api/client";
import { useSearch } from "@tanstack/react-router";
import TimelineChart from "../components/TimelineChart";
import DefectionSankey from "../components/DefectionSankey";

export function InstitutionalView() {
  const { t } = useTranslation();
  const search = useSearch({ from: "/institutional", select: s => s.date });
  const asOf: string = (search as string) ?? new Date().toISOString().slice(0, 10);

  const committees = useQuery({
    queryKey: ["committees", asOf],
    queryFn: () => api.committees(asOf),
  });

  if (committees.isLoading) {
    return (
      <div className="card p-4">
        <div className="text-slate-500 text-sm py-8">{t("loading")}</div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="card p-4">
        <h2 className="font-semibold mb-3">{t("institutionalView")}</h2>
        <p className="text-sm text-slate-400 mb-4">{t("institutionalViewDesc")}</p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="card p-4">
            <h3 className="font-semibold mb-3">{t("committeeControl")}</h3>
            {committees.isLoading ? (
              <div className="text-slate-500 text-sm">{t("loading")}</div>
            ) : committees.data?.length === 0 ? (
              <div className="text-slate-500 text-sm">{t("noData")}</div>
            ) : (
              <div className="space-y-2">
                {committees.data?.map((c: { id: string; name: string; party: { short_name: string | null } | null }) => (
                  <div key={c.id} className="flex items-center justify-between bg-slate-800/50 rounded p-2">
                    <span className="font-medium truncate">{c.name}</span>
                    <span className="text-slate-400 text-sm">{c.party?.short_name || "—"}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="card p-4">
            <h3 className="font-semibold mb-3">{t("bureauComposition")}</h3>
            <div className="text-slate-500 text-sm">{t("notImplementedYet")}</div>
          </div>
        </div>

        <div className="card p-4">
          <h3 className="font-semibold mb-3">{t("crossChamberMPs")}</h3>
          <div className="text-slate-500 text-sm">{t("notImplementedYet")}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <TimelineChart from={asOf} to={asOf} />
        <DefectionSankey />
      </div>
    </div>
  );
}