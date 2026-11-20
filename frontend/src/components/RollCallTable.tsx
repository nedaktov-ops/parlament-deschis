import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api, type VotePositionRow } from "../api/client";
import Skeleton from "./ui/Skeleton";

const CHOICE_COLOR: Record<string, string> = {
  yes: "#10b981", // emerald-500
  no: "#ef4444", // rose-500
  abstain: "#f59e0b", // amber-500
  not_voting: "#94a3b8", // slate-400
};

interface RollCallTableProps {
  voteId: string;
}

export default function RollCallTable({ voteId }: RollCallTableProps) {
  const { t } = useTranslation();

  const query = useQuery({
    queryKey: ["votePositions", voteId],
    queryFn: () => api.votePositions(voteId),
  });

  const data = query.data?.data ?? [];
  const dataExists = query.data?.data_exists ?? false;

  const choiceLabel = (choice: string) => {
    switch (choice) {
      case "yes":
        return t("vote.yes", "Yes");
      case "no":
        return t("vote.no", "No");
      case "abstain":
        return t("vote.abstain", "Abstain");
      case "not_voting":
        return t("vote.not_voting", "Present, did not vote");
      default:
        return t("vote.not_voting", "Present, did not vote");
    }
  };

  if (query.isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Skeleton className="h-8 w-32" />
        <Skeleton className="mt-2 h-4 w-64" />
      </div>
    );
  }

  if (query.isError) {
    return (
      <div className="text-red-400 text-sm py-6 text-center">
        {t("view.voturi.loadError", "Failed to load votes.")}
      </div>
    );
  }

  if (!dataExists || data.length === 0) {
    return (
      <div className="text-slate-500 text-sm py-6 text-center">
        {t("empty.rollcall", "Roll-call vote data is not yet available for this legislature.")}
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table
        role="table"
        aria-label={t("aria.rollcallTable", "Table of plenary votes and each MP's position")}
        className="min-w-full text-sm"
      >
        <caption className="sr-only">
          {t("aria.rollcallTable", "Table of plenary votes and each MP's position")}
        </caption>
        <thead>
          <tr className="text-left text-slate-400 border-b border-slate-700">
            <th className="py-2.5 pr-4 font-medium" scope="col">
              {t("mps.search", "Search")}
            </th>
            <th className="py-2.5 pr-4 font-medium" scope="col">
              {t("filter.party", "Party")}
            </th>
            <th className="py-2.5 pr-4 font-medium" scope="col">
              {t("vote.yes", "Yes")} / {t("vote.no", "No")} / {t("vote.abstain", "Abstain")}
            </th>
            <th className="py-2.5 pr-4 font-medium text-right" scope="col">
              {t("mps.source", "Source")}
            </th>
          </tr>
        </thead>
        <tbody>
          {data.map((p: VotePositionRow) => (
            <tr
              key={p.person_id}
              className="border-b border-slate-700/40 hover:bg-slate-800/40"
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                }
              }}
            >
              <td className="py-2.5 pr-4 text-slate-200">
                {p.name_raw || t("mps.noParty", "no party recorded")}
              </td>
              <td className="py-2.5 pr-4">
                {p.group_raw ? (
                  <span className="text-slate-300 font-mono text-xs">{p.group_raw}</span>
                ) : null}
              </td>
              <td className="py-2.5 pr-4 text-slate-300 tabular-nums">
                <span
                  className="inline-flex items-center gap-1"
                  style={{ color: CHOICE_COLOR[p.choice] }}
                >
                  {choiceLabel(p.choice)}
                </span>
              </td>
              <td className="py-2.5 pr-4 text-right text-xs text-slate-500 tabular-nums">
                {p.source_url ? p.source_url.split("/")[2] : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
