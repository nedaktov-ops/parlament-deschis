import { useMemo } from "react";
import { useTranslation } from "react-i18next";

export interface CrossChamberPerson {
  person_id: string;
  name: string;
  chambers: Array<"deputies" | "senate">;
  deputies: string[];
  senate: string[];
}

export interface CrossChamberFlowProps {
  data: CrossChamberPerson[];
  onPersonClick?: (personId: string) => void;
  // width and height are not currently used but kept for future extensibility
  width?: number;
  height?: number;
}

export default function CrossChamberFlow({
  data,
  onPersonClick,
  // width and height intentionally unused for now
}: CrossChamberFlowProps) {
  const { t } = useTranslation();

  // The endpoint already returns people with a mandate in both chambers, so
  // the only honest headline figure is the size of that population. The list
  // below contains exactly these people (not a competing top-5 slice) and each
  // row navigates to its own person instead of a shared `data[0]`.
  const members = useMemo(
    () => [...data].sort((a, b) => a.name.localeCompare(b.name)),
    [data],
  );

  if (!data?.length) {
    return (
      <section className="card p-4 flex flex-col h-full min-h-72">
        <h2 className="text-base font-semibold text-slate-100">
          {t("crossChamberMPs")}
        </h2>
        <p className="mt-3 text-sm text-slate-300" role="status">
          {t("crossChamberNoData")}
        </p>
      </section>
    );
  }

  return (
    <section className="card p-4 flex flex-col h-full min-h-72">
      <h2 className="text-sm font-semibold text-slate-100">
        {t("crossChamberMPs")}
      </h2>

      {/* One labelled summary, followed by the caveat that explains what the
          count does and does not include. No overlapping percentage bars: the
          old pair was both left-anchored, both ~100% and both opened data[0]. */}
      <p className="mt-2 text-sm text-slate-200" aria-live="polite">
        {t("crossChamberCount", { count: data.length })}
      </p>
      <p className="mt-1 text-xs text-slate-400">
        {t("crossChamberDateLimit")}
      </p>

      <div
        className="mt-3 flex-1 min-h-0 overflow-y-auto pr-1"
        tabIndex={0}
        role="region"
        aria-label={t("crossChamberTableCaption")}
      >
        <ul className="space-y-1">
          {members.map((member) => {
            const chamberNames = [
              member.chambers.includes("deputies") ? t("deputies") : null,
              member.chambers.includes("senate") ? t("senate") : null,
            ]
              .filter(Boolean)
              .join(", ");
            const ariaLabel = chamberNames
              ? `${member.name}: ${chamberNames}`
              : member.name;
            return (
              <li key={member.person_id}>
                <button
                  type="button"
                  onClick={() => onPersonClick?.(member.person_id)}
                  disabled={!onPersonClick}
                  aria-label={ariaLabel}
                  className="btn-hover flex w-full min-h-11 items-center justify-between gap-2 rounded-md px-2 py-1.5 text-left hover:bg-slate-700/40 disabled:cursor-default disabled:hover:bg-transparent focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-400"
                >
                  <span className="truncate text-xs text-slate-200">
                    {member.name}
                  </span>
                  <span className="flex shrink-0 gap-1" aria-hidden="true">
                    {member.chambers.includes("deputies") && (
                      <span className="rounded bg-sky-400/20 px-1.5 py-0.5 text-xs font-semibold text-sky-300">
                        D
                      </span>
                    )}
                    {member.chambers.includes("senate") && (
                      <span className="rounded bg-rose-400/20 px-1.5 py-0.5 text-xs font-semibold text-rose-400">
                        S
                      </span>
                    )}
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      </div>
    </section>
  );
}
