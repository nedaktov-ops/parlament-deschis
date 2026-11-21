import { useState, useRef, useMemo, useCallback, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { Link } from "@tanstack/react-router";
import {
  committees,
  committeeMembers,
  committeeControl,
  type CommitteeListItem,
  type CommitteeMember,
} from "../api/client";
import { localISODate } from "../utils/date";
import HeroGraphic from "../components/HeroGraphic";
import InfoStat from "../components/InfoStat";
import LoadingState from "../components/LoadingState";
import EmptyState from "../components/EmptyState";

function fmtDate(value: string | null): string {
  if (!value) return "—";
  return value;
}

function MemberRow({ member }: { member: CommitteeMember }) {
  const { t } = useTranslation();
  return (
    <tr className="hover:bg-slate-700/40">
      <th scope="row" className="px-3 py-2 font-normal text-left">
        <Link
          to="/person/$id"
          params={{ id: member.person_id }}
          search={{ date: localISODate() }}
          className="text-sky-400 hover:text-sky-300 hover:underline"
        >
          {member.name}
        </Link>
      </th>
      <td className="px-3 py-2 text-slate-400 text-sm">{member.group ?? "—"}</td>
      <td className="px-3 py-2 text-slate-400 text-sm">{member.role ?? "—"}</td>
      <td className="px-3 py-2 text-slate-400 text-sm">
        {fmtDate(member.start_date)}
      </td>
      <td className="px-3 py-2 text-slate-400 text-sm">
        {fmtDate(member.end_date)}
      </td>
      <td className="px-3 py-2">
        {member.active ? (
          <span className="bg-emerald-900/50 text-emerald-300 px-2 py-0.5 rounded text-xs">
            {t("committees.active", "active")}
          </span>
        ) : (
          <span className="bg-slate-700 text-slate-400 px-2 py-0.5 rounded text-xs">
            {t("committees.former", "former")}
          </span>
        )}
      </td>
    </tr>
  );
}

function CommitteeCard({
  committee,
  onMembersLoaded,
}: {
  committee: CommitteeListItem;
  onMembersLoaded?: (committeeId: string, totalCount: number) => void;
}) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);

  const members = useQuery({
    queryKey: ["committee-members", committee.id],
    queryFn: () => committeeMembers(committee.id),
    enabled: open,
  });

  useEffect(() => {
    if (members.data) {
      onMembersLoaded?.(committee.id, members.data.total_count);
    }
  }, [members.data, committee.id, onMembersLoaded]);

  return (
    <div className="bg-slate-800 rounded-lg overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-slate-700/50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400"
      >
        <span className="text-slate-200 font-medium">{committee.name}</span>
        <span className="text-slate-500 text-sm flex items-center gap-2">
          {members.data
            ? t(
                "committees.memberCount",
                "{{active}} active / {{total}} total",
                {
                  active: members.data.active_count,
                  total: members.data.total_count,
                },
              )
            : open
              ? t("loading", "Loading…")
              : ""}
          <span aria-hidden="true">{open ? "▲" : "▼"}</span>
        </span>
      </button>

      {open && (
        <div className="border-t border-slate-700 overflow-x-auto max-w-full" tabIndex={0} role="region" aria-label={committee.name}>
          {members.isError && (
            <div className="px-4 py-3 text-red-400 text-sm">
              {t("committees.loadError", "Failed to load members.")}
            </div>
          )}
          {members.data && members.data.members.length > 0 && (
            <table className="min-w-full text-sm">
              <thead className="bg-slate-700/60">
                <tr>
                  <th scope="col" className="px-3 py-2 text-left text-slate-300 font-medium">
                    {t("committees.col.member", "Member")}
                  </th>
                  <th scope="col" className="px-3 py-2 text-left text-slate-300 font-medium">
                    {t("committees.col.group", "Group")}
                  </th>
                  <th scope="col" className="px-3 py-2 text-left text-slate-300 font-medium">
                    {t("committees.col.role", "Role")}
                  </th>
                  <th scope="col" className="px-3 py-2 text-left text-slate-300 font-medium">
                    {t("committees.col.joined", "Joined")}
                  </th>
                  <th scope="col" className="px-3 py-2 text-left text-slate-300 font-medium">
                    {t("committees.col.left", "Left")}
                  </th>
                  <th scope="col" className="px-3 py-2 text-left text-slate-300 font-medium">
                    {t("committees.col.status", "Status")}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/60">
                {members.data.members.map((m) => (
                  <MemberRow key={m.person_id + (m.start_date ?? "")} member={m} />
                ))}
              </tbody>
            </table>
          )}
          {members.data && members.data.members.length === 0 && (
            <div className="px-4 py-3 text-slate-500 text-sm">
              {t("committees.noMembers", "No member data for this committee.")}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function Committees() {
  const { t } = useTranslation();
  const [chamber, setChamber] = useState<string>("");
  const [totalMembers, setTotalMembers] = useState(0);
  const countedCommittees = useRef<Set<string>>(new Set());

  const list = useQuery({
    queryKey: ["committees"],
    queryFn: () => committees(),
  });

  const control = useQuery({
    queryKey: ["committee-control"],
    queryFn: () => committeeControl(),
  });

  const rows = (list.data ?? []).filter(
    (c) => !chamber || c.chamber === chamber,
  );

  const controlData = control.data?.status === "ok" ? control.data.data : null;
  // Derive the ingested-committee count from this page's own list.
  const committeeCount = list.data?.length;

  const chambersCovered = useMemo(() => {
    const chambers = new Set(
      (list.data ?? []).map((c) => c.chamber).filter(Boolean),
    );
    return chambers.size;
  }, [list.data]);

  const handleMembersLoaded = useCallback(
    (committeeId: string, totalCount: number) => {
      if (!countedCommittees.current.has(committeeId)) {
        countedCommittees.current.add(committeeId);
        setTotalMembers((prev) => prev + totalCount);
      }
    },
    [],
  );

  return (
    <div className="wrap py-6 print:p-0">
      <div
        className="min-h-screen flex flex-wrap items-start justify-between gap-3 mb-6 print:mb-3"
        data-enter
      >
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-100 print:text-slate-900">
            {t("committees.title", "Commitment Tracker")}
          </h1>
          <p className="text-slate-400 print:text-slate-600 text-sm mt-1">
            {t(
              "committees.intro",
              "Which committees does your MP serve on, and when did they join or leave? Data comes from the official cdep.ro committee ledgers.",
            )}
          </p>
          {list.data && (
            <p className="mt-4 text-slate-200" data-moment>
              <span className="text-5xl font-black block tracking-tight">
                {list.data.length.toLocaleString()}
              </span>
              <span className="text-sm text-slate-400 mt-1">
                {t("committees.totalCommittees", "total committees")}
              </span>
            </p>
          )}
        </div>
        <HeroGraphic variant="committee" className="print:hidden" />
      </div>

      {list.data && (
        <div className="bg-slate-800/30 rounded-xl p-4 mb-6 print:bg-transparent print:p-0">
          <section className="mb-4">
            <h2 className="font-semibold text-slate-200 print:text-slate-900 mb-2">
              {t("committees.overview", "Committees at a glance")}
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
              <InfoStat
                label={t("committees.totalCommittees", "Total committees")}
                value={committeeCount ?? 0}
                max={committeeCount ?? 0}
                accent="emerald"
              />
              <InfoStat
                label={t("committees.totalMembers", "Total members")}
                value={totalMembers}
                accent="sky"
              />
              <InfoStat
                label={t("committees.chambersCovered", "Chambers covered")}
                value={chambersCovered}
                max={2}
                accent="sky"
              />
            </div>
          </section>
        </div>
      )}

      {/* Feature 5: Committee Control Index */}
      {controlData && controlData.total_committees > 0 && (
        <section
          aria-label={t("control.title", "Committee control index")}
          className="mb-8 bg-slate-800/60 rounded-lg p-4"
        >
          <h2 className="text-lg font-semibold text-slate-100 mb-1">
            {t("control.title", "Committee Control Index")}
          </h2>
          <p className="text-slate-400 text-sm mb-4">
            {t(
              "control.intro",
              "Which party chairs which committees ({{count}} committees, as of {{date}}).",
              { count: controlData.total_committees, date: controlData.as_of },
            )}
          </p>
          <div className="overflow-x-auto max-w-full" tabIndex={0} role="region" aria-label={t("control.table", "Committee control table")}>
            <div className="space-y-2 mb-4">
              {controlData.parties.map((p) => (
                <div key={p.party} className="flex items-center gap-3">
                  <span className="w-24 text-sm text-slate-300 shrink-0">
                    {p.party}
                  </span>
                  <div className="bg-slate-700 rounded-full h-4 flex-1 min-w-[120px]">
                    <div
                      className="bg-sky-500 rounded-full h-4"
                      style={{ width: `${p.share_pct}%` }}
                      title={`${p.chairs} / ${controlData.total_committees}`}
                    />
                  </div>
                  <span className="w-20 text-sm text-slate-400 text-right shrink-0">
                    {p.chairs} ({p.share_pct}%)
                  </span>
                </div>
              ))}
            </div>
          </div>
          <details>
            <summary className="text-sm text-sky-400 cursor-pointer hover:text-sky-300">
              {t("control.showChairs", "Show all chairs →")}
            </summary>
            <table className="min-w-full text-sm mt-3">
              <thead className="bg-slate-700/60">
                <tr>
                  <th scope="col" className="px-3 py-2 text-left text-slate-300 font-medium">
                    {t("control.col.committee", "Committee")}
                  </th>
                  <th scope="col" className="px-3 py-2 text-left text-slate-300 font-medium">
                    {t("control.col.chair", "Chair")}
                  </th>
                  <th scope="col" className="px-3 py-2 text-left text-slate-300 font-medium">
                    {t("control.col.party", "Party")}
                  </th>
                  <th scope="col" className="px-3 py-2 text-left text-slate-300 font-medium">
                    {t("control.col.since", "Since")}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/60">
                {controlData.chairs.map((c) => (
                  <tr key={c.committee_id} className="hover:bg-slate-700/40">
                    <th scope="row" className="px-3 py-2 text-slate-300 font-normal text-left">{c.committee}</th>
                    <td className="px-3 py-2">
                      <Link
                        to="/person/$id"
                        params={{ id: c.chair_person_id }}
                        search={{ date: localISODate() }}
                        className="text-sky-400 hover:text-sky-300 hover:underline"
                      >
                        {c.chair}
                      </Link>
                    </td>
                    <td className="px-3 py-2 text-slate-400">{c.party}</td>
                    <td className="px-3 py-2 text-slate-400">
                      {c.chair_since ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </details>
        </section>
      )}

      {control.isError && (
        <div className="mb-6 text-amber-400 text-sm">
          {t("control.loadError", "Committee control data unavailable.")}
        </div>
      )}

      <div className="mb-6">
        <label className="flex flex-col gap-1 text-sm text-slate-400 max-w-xs">
          {t("committees.filter.chamber", "Chamber")}
          <select
            value={chamber}
            onChange={(e) => setChamber(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded px-3 py-2 text-slate-200"
          >
            <option value="">{t("committees.filter.all", "All")}</option>
            <option value="deputies">{t("deputies", "Deputies")}</option>
            <option value="senate">{t("senate", "Senate")}</option>
          </select>
        </label>
      </div>

      {list.isLoading && (
        <LoadingState label={t("loading", "Loading…")} />
      )}
      {list.isError && (
        <div className="text-red-400">
          {t("committees.loadError", "Failed to load committees.")}
        </div>
      )}

      <div className="space-y-2">
        {rows.map((c) => (
          <CommitteeCard
            key={c.id}
            committee={c}
            onMembersLoaded={handleMembersLoaded}
          />
        ))}
      </div>

      {rows.length === 0 && !list.isLoading && !list.isError && (
        <EmptyState
          title={t(
            "committees.empty",
            "No committee data ingested yet for this scope.",
          )}
        />
      )}

      <div className="mt-6 bg-slate-800/50 rounded p-4 text-sm text-slate-400">
        <h2 className="text-slate-200 font-semibold mb-1">
          {t("committees.coverage", "Data coverage")}
        </h2>
        <p>
          {committeeCount !== undefined &&
            t("committees.coverage.desc", { count: committeeCount })}
        </p>
      </div>
    </div>
  );
}
