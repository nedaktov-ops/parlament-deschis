import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api, type VotePositionRow } from "../api/client";
import ErrorState from "./ErrorState";
import Skeleton from "./ui/Skeleton";

// backend/routers/api.py:1387 — vote_positions limit Query(100, ge=1, le=500).
const POSITION_LIMIT = 500;

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
    queryKey: ["votePositions", voteId, POSITION_LIMIT],
    queryFn: () => api.votePositions(voteId, { limit: POSITION_LIMIT }),
  });

  const data = query.data?.data ?? [];
  const total = query.data?.total ?? 0;
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
      <ErrorState
        message={t("view.voturi.loadError", "Failed to load votes.")}
        onRetry={() => void query.refetch()}
      />
    );
  }

  if (!dataExists || data.length === 0) {
    return (
      <div className="text-slate-400 text-sm py-6 text-center">
        {t("view.voturi.positionsEmpty", "No positions recorded for this vote.")}
      </div>
    );
  }

  return (
    <div
      className="overflow-x-auto"
      role="region"
      tabIndex={0}
      aria-label={t("aria.positionsScroll", "Scrollable table of vote positions")}
    >
      {total > data.length && (
        <p className="mb-2 text-xs text-slate-400" role="note">
          {t("vote.positionsTruncated", { n: data.length })}
        </p>
      )}
      <table
        className="min-w-full text-sm"
        aria-label={t("aria.rollcallTable", "Table of plenary votes and each MP's position")}
      >
        <caption className="sr-only">
          {t("aria.rollcallTable", "Table of plenary votes and each MP's position")}
        </caption>
        <thead>
          <tr className="text-left text-slate-400 border-b border-slate-700">
            <th className="py-2.5 pr-4 font-medium" scope="col">
              {t("report.col.mp", "MP")}
            </th>
            <th className="py-2.5 pr-4 font-medium" scope="col">
              {t("filter.party", "Party")}
            </th>
            <th className="py-2.5 pr-4 font-medium" scope="col">
              {t("view.voturi.col.choice", "Position")}
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
              className="border-b border-slate-700/40"
            >
              <td className="py-2.5 pr-4 text-slate-200">
                {p.name_raw || t("mpc.unknown", "unknown")}
              </td>
              <td className="py-2.5 pr-4">
                {p.group_raw ? (
                  <span className="text-slate-300 font-mono text-xs">{p.group_raw}</span>
                ) : (
                  "—"
                )}
              </td>
              <td className="py-2.5 pr-4 text-slate-300 tabular-nums">
                {/* Text label always accompanies colour: choice is never encoded by colour alone. */}
                <span
                  className="inline-flex items-center gap-1"
                  style={{ color: CHOICE_COLOR[p.choice] }}
                >
                  {choiceLabel(p.choice)}
                </span>
              </td>
              <td className="py-2.5 pr-4 text-right text-xs text-slate-400 tabular-nums">
                {p.source_url ? (
                  <a
                    href={p.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sky-400 hover:underline"
                  >
                    {p.source_url.split("/")[2] ?? t("mps.source", "Source")}
                  </a>
                ) : (
                  "—"
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
