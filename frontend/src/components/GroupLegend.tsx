import { useTranslation } from "react-i18next";
import type { GroupComposition } from "../api/client";

export default function GroupLegend({ groups }: { groups: GroupComposition[] }) {
  const { t } = useTranslation();
  return (
    <div className="flex flex-wrap gap-2">
      {groups.map((g) => (
        <div
          key={g.short_name}
          className="flex items-center gap-1.5 bg-slate-800/60 rounded-md px-2 py-1 text-xs"
        >
          <span
            className="inline-block w-3 h-3 rounded-full"
            style={{ background: g.color || "#64748b" }}
          />
          <span className="font-medium">{g.short_name}</span>
          <span className="text-slate-400">
            {g.count} {t("members")}
          </span>
        </div>
      ))}
    </div>
  );
}