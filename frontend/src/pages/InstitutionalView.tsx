import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api } from "../api/client";
import { useNavigate } from "@tanstack/react-router";
import { useScope } from "../hooks/useScope";
import { localISODate } from "../utils/date";

export function InstitutionalView() {
  const { t } = useTranslation();
  const navigate = useNavigate({ from: "/institutional" });
  const scope = useScope();
  const asOf = scope.date;
  const today = localISODate();

  const committees = useQuery({
    queryKey: ["committees", asOf, ...scope.scopeKey],
    queryFn: () => api.committees(asOf),
  });
  const crossChamber = useQuery({
    queryKey: ["cross-chamber", asOf, ...scope.scopeKey],
    queryFn: () => api.crossChamber(asOf),
  });

  return (
    <div className="space-y-4">
      <div className="card p-4">
        <h1 className="page-title mb-3">{t("institutionalView")}</h1>
        <p className="text-sm text-slate-400 mb-4">{t("institutionalViewDesc")}</p>
        <div className="mb-4">
          <label htmlFor="institutional-as-of" className="block text-xs text-slate-300 mb-1">
            {t("asOf")}
          </label>
          <input
            id="institutional-as-of"
            type="date"
            value={asOf}
            max={today}
            onChange={(event) => {
              if (event.target.value) {
                navigate({ search: scope.searchFor({ date: event.target.value }), replace: true });
              }
            }}
            className="bg-slate-800 border border-slate-600 rounded-md px-3 py-2 text-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="card p-4">
            <h2 className="font-semibold mb-3">{t("committeeControl")}</h2>
            {committees.isError ? (
              <div role="alert" className="text-rose-200 text-sm">
                {t("institutionalLoadError")}
                <button type="button"className="ml-3 underline" onClick={() => committees.refetch()}>
                  {t("traseismRetry")}
                </button>
              </div>
            ) : committees.isLoading ? (
              <div className="text-slate-500 text-sm">{t("loading")}</div>
            ) : committees.data?.length === 0 ? (
              <div className="text-slate-500 text-sm">{t("committeeDataUnavailable")}</div>
            ) : (
              <div className="space-y-2">
                {committees.data?.map(c => (
                  <div key={c.id} className="bg-slate-800/50 rounded p-2">
                    <span className="font-medium">{c.name}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="card p-4">
            <h2 className="font-semibold mb-3">{t("bureauComposition")}</h2>
            <div className="text-slate-500 text-sm">{t("bureauDataUnavailable")}</div>
          </div>
        </div>

        <div className="card p-4">
          <h2 className="font-semibold mb-3">{t("crossChamberMPs")}</h2>
          {crossChamber.isError ? (
            <div role="alert" className="text-rose-200 text-sm">
              {t("institutionalLoadError")}
              <button type="button"className="ml-3 underline" onClick={() => crossChamber.refetch()}>
                {t("traseismRetry")}
              </button>
            </div>
          ) : crossChamber.isLoading ? (
            <div className="text-slate-500 text-sm">{t("loading")}</div>
          ) : crossChamber.data?.data.length === 0 ? (
            <div className="text-slate-500 text-sm">{t("crossChamberNoData")}</div>
          ) : (
            <>
              <p className="text-sm text-slate-400 mb-3" aria-live="polite">
                {t("crossChamberCount", { count: crossChamber.data?.count ?? 0 })}
              </p>
              <p className="text-xs text-slate-500 mb-3">{t("crossChamberDateLimit")}</p>
              <div
                className="overflow-x-auto max-w-full"
                tabIndex={0}
                role="region"
                aria-label={t("crossChamberTableCaption")}
              >
                <table className="w-full text-sm text-left data-table">
                  <caption className="sr-only">{t("crossChamberTableCaption")}</caption>
                  <thead>
                    <tr className="border-b border-slate-700 text-slate-300">
                      <th scope="col" className="px-3 py-2">{t("person")}</th>
                      <th scope="col" className="px-3 py-2">{t("deputies")}</th>
                      <th scope="col" className="px-3 py-2">{t("senate")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {crossChamber.data?.data.map(person => (
                      <tr key={person.person_id} className="border-b border-slate-800">
                        <th scope="row" className="px-3 py-2 font-medium">{person.name}</th>
                        <td className="px-3 py-2">{person.deputies.join(", ") || "—"}</td>
                        <td className="px-3 py-2">{person.senate.join(", ") || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      </div>

    </div>
  );
}