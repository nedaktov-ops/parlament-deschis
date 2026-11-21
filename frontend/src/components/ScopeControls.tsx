import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api } from "../api/client";
import { useScope } from "../hooks/useScope";
import { localISODate } from "../utils/date";

interface Props {
  showDate?: boolean;
  showChamber?: boolean;
  showLegislature?: boolean;
  /** Honest disclosure, e.g. "no point-in-time data for this view". */
  note?: string;
}
const FALLBACK_LEGISLATURES = ["1990","1992","1996","2000","2004","2008","2012","2016","2020","2024"];

export default function ScopeControls({ showDate, showChamber, showLegislature, note }: Props) {
  const { t } = useTranslation();
  const scope = useScope();
  const meta = useQuery({ queryKey: ["meta"], queryFn: api.meta });
  const legislatures = Object.keys(meta.data?.legislatures ?? {}).length
    ? Object.keys(meta.data!.legislatures)
    : FALLBACK_LEGISLATURES;
  const today = localISODate();
  if (!showDate && !showChamber && !showLegislature && !note) return null;
  const inputCls =
    "bg-slate-800 border border-slate-600 rounded-md px-3 py-2 text-sm min-h-11 focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400";
  return (
    <fieldset className="card p-3 flex flex-wrap items-end gap-4" aria-label={t("scope.title", "Scope")}>
      {showDate && (
        <label className="flex flex-col gap-1 text-xs text-slate-300">
          {t("asOf")}
          <input id="scope-date" type="date" className={inputCls}
            min="1990-01-01" max={today} value={scope.date}
            onChange={(e) => { if (e.target.value) scope.setScope({ date: e.target.value }); }} />
        </label>
      )}
      {showChamber && (
        <label className="flex flex-col gap-1 text-xs text-slate-300">
          {t("filter.chamber", "Chamber")}
          <select id="scope-chamber" className={inputCls} value={scope.chamber ?? ""}
            onChange={(e) => scope.setScope({ chamber: (e.target.value || undefined) as "deputies" | "senate" | undefined })}>
            <option value="">{t("scope.allChambers", "All chambers")}</option>
            <option value="deputies">{t("deputies", "Deputies")}</option>
            <option value="senate">{t("senate", "Senate")}</option>
          </select>
        </label>
      )}
      {showLegislature && (
        <label className="flex flex-col gap-1 text-xs text-slate-300">
          {t("filter.legislature", "Legislature")}
          <select id="scope-legislature" className={inputCls} value={scope.legislature ?? ""}
            onChange={(e) => scope.setScope({ legislature: e.target.value || undefined })}>
            <option value="">{t("scope.allLegislatures", "All legislatures")}</option>
            {legislatures.map((y) => <option key={y} value={y}>{y}</option>)}
          </select>
        </label>
      )}
      {note && <p className="text-xs text-slate-500 max-w-xl" role="note">{note}</p>}
    </fieldset>
  );
}
