import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api, type EventItem } from "../api/client";

interface PartyFlow {
  party: string;
  partyColor: string | null;
  totalIn: number;
  totalOut: number;
  netChange: number;
  membersIn: PartyMemberFlow[];
  membersOut: PartyMemberFlow[];
}

interface PartyMemberFlow {
  person_id: string;
  person_name: string;
  date: string;
  fromParty: string | null;
  fromPartyColor: string | null;
  toParty: string | null;
  toPartyColor: string | null;
  type: "switch_group" | "switch_party";
  chamber: string | null;
  role: string | null;
}

function aggregatePartyFlows(events: EventItem[]): Map<string, PartyFlow> {
  const partyMap = new Map<string, PartyFlow>();

  // First pass: collect all unique parties and their colors
  const partyColors = new Map<string, string | null>();
  for (const e of events) {
    if (e.from_org?.short_name && e.from_org.color) {
      partyColors.set(e.from_org.short_name, e.from_org.color);
    }
    if (e.to_org?.short_name && e.to_org.color) {
      partyColors.set(e.to_org.short_name, e.to_org.color);
    }
  }

  for (const e of events) {
    if (!e.person) continue;
    const fromParty = e.from_org?.short_name || e.from_org?.name || null;
    const toParty = e.to_org?.short_name || e.to_org?.name || null;
    const fromColor = fromParty ? partyColors.get(fromParty) ?? null : null;
    const toColor = toParty ? partyColors.get(toParty) ?? null : null;

    // Track outflow from fromParty
    if (fromParty) {
      const flow = partyMap.get(fromParty) ?? {
        party: fromParty,
        partyColor: fromColor,
        totalIn: 0,
        totalOut: 0,
        netChange: 0,
        membersIn: [],
        membersOut: [],
      };
      flow.totalOut += 1;
      flow.netChange -= 1;
      flow.membersOut.push({
        person_id: e.person.id,
        person_name: e.person.name,
        date: e.event_date ?? "",
        fromParty,
        fromPartyColor: fromColor,
        toParty,
        toPartyColor: toColor,
        type: e.type as "switch_group" | "switch_party",
        chamber: e.chamber,
        role: null, // We don't have role in EventItem
      });
      partyMap.set(fromParty, flow);
    }

    // Track inflow to toParty
    if (toParty) {
      const flow = partyMap.get(toParty) ?? {
        party: toParty,
        partyColor: toColor,
        totalIn: 0,
        totalOut: 0,
        netChange: 0,
        membersIn: [],
        membersOut: [],
      };
      flow.totalIn += 1;
      flow.netChange += 1;
      flow.membersIn.push({
        person_id: e.person.id,
        person_name: e.person.name,
        date: e.event_date ?? "",
        fromParty,
        fromPartyColor: fromColor,
        toParty,
        toPartyColor: toColor,
        type: e.type as "switch_group" | "switch_party",
        chamber: e.chamber,
        role: null,
      });
      partyMap.set(toParty, flow);
    }
  }

  // Sort members by date (newest first)
  for (const flow of partyMap.values()) {
    flow.membersIn.sort((a, b) => (b.date < a.date ? 1 : -1));
    flow.membersOut.sort((a, b) => (b.date < a.date ? 1 : -1));
  }

  return partyMap;
}

function typeColor(type: string): string {
  return type === "switch_party" ? "text-rose-400" : "text-amber-400";
}

function typeLabel(type: string, t: (k: string) => string): string {
  if (type === "switch_party") return t("switchParty");
  if (type === "switch_group") return t("switchGroup");
  return type;
}

interface PartyFlowDetailProps {
  partyShortName: string;
  onBack: () => void;
  onPersonSelect: (id: string) => void;
}

export default function PartyFlowDetail({
  partyShortName,
  onBack,
  onPersonSelect,
}: PartyFlowDetailProps) {
  const { t } = useTranslation();
  const events = useQuery({
    queryKey: ["party-flow", partyShortName],
    queryFn: () => api.movements(),
  });

  if (events.isLoading) {
    return (
      <div className="card p-4">
        <div className="text-slate-500 text-sm py-8">{t("loading")}</div>
      </div>
    );
  }

  const partyFlows = aggregatePartyFlows(events.data ?? []);
  const flow = partyFlows.get(partyShortName);

  if (!flow) {
    return (
      <div className="card p-4">
        <div className="text-rose-400 text-sm py-8">{t("noData")}</div>
      </div>
    );
  }

  return (
    <div className="card p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={onBack}
          className="btn bg-slate-700 hover:bg-slate-600 text-sm"
        >
          ← {t("backToDefections")}
        </button>
        <div className="flex items-center gap-3">
          <span
            className="w-6 h-6 rounded-full"
            style={{ background: flow.partyColor || "#64748b" }}
          />
          <h2 className="font-semibold text-lg">{flow.party}</h2>
        </div>
        <div className="w-20" />
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-3 mb-6">
        <div className="bg-emerald-900/30 border border-emerald-800 rounded-lg p-3">
          <div className="text-2xl font-bold text-emerald-300">+{flow.totalIn}</div>
          <div className="text-xs text-emerald-400">{t("joined")}</div>
        </div>
        <div className="bg-rose-900/30 border border-rose-800 rounded-lg p-3">
          <div className="text-2xl font-bold text-rose-300">−{flow.totalOut}</div>
          <div className="text-xs text-rose-400">{t("left")}</div>
        </div>
        <div className={`rounded-lg p-3 ${
          flow.netChange >= 0
            ? "bg-emerald-900/30 border border-emerald-800"
            : "bg-rose-900/30 border border-rose-800"
        }`}>
          <div className="text-2xl font-bold">
            {flow.netChange >= 0 ? "+" : ""}{flow.netChange}
          </div>
          <div className="text-xs text-slate-400">{t("netChange")}</div>
        </div>
      </div>

      {/* Tabs for In/Out */}
      <PartyFlowTabs flow={flow} onPersonSelect={onPersonSelect} />
    </div>
  );
}

function PartyFlowTabs({
  flow,
  onPersonSelect,
}: {
  flow: PartyFlow;
  onPersonSelect: (id: string) => void;
}) {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<"in" | "out">("in");

  return (
    <div>
      <div className="flex gap-1 border-b border-slate-700 mb-4">
        <button
          onClick={() => setActiveTab("in")}
          className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
            activeTab === "in"
              ? "bg-slate-800 text-emerald-300 border-b-2 border-emerald-500 -mb-px"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          {t("joined")} ({flow.membersIn.length})
        </button>
        <button
          onClick={() => setActiveTab("out")}
          className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
            activeTab === "out"
              ? "bg-slate-800 text-rose-300 border-b-2 border-rose-500 -mb-px"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          {t("left")} ({flow.membersOut.length})
        </button>
      </div>

      <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
        {(activeTab === "in" ? flow.membersIn : flow.membersOut).map((m) => (
          <button
            key={m.person_id}
            onClick={() => onPersonSelect(m.person_id)}
            className="w-full text-left bg-slate-800/40 hover:bg-slate-800 rounded-md p-3 transition-colors"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 text-sm">
                  <span className="font-medium truncate">{m.person_name}</span>
                  <span
                    className={`text-xs font-medium ${typeColor(m.type)}`}
                  >
                    {typeLabel(m.type, t)}
                  </span>
                  {m.chamber && (
                    <span className="text-[10px] text-slate-500 px-1.5 py-0.5 bg-slate-800 rounded">
                      {m.chamber}
                    </span>
                  )}
                </div>
                <div className="text-[11px] text-slate-500 mt-0.5 font-mono">
                  {m.date}
                </div>
              </div>
            </div>

            <div className="mt-2 flex items-center gap-1.5 text-xs flex-wrap">
              {activeTab === "in" ? (
                <>
                  <span className="text-slate-500">{t("from")}:</span>
                  {m.fromParty ? (
                    <span
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-800"
                      style={{ borderColor: m.fromPartyColor || "#64748b" }}
                    >
                      <span
                        className="w-2 h-2 rounded-full"
                        style={{ background: m.fromPartyColor || "#64748b" }}
                      />
                      <span className="text-sky-300">{m.fromParty}</span>
                    </span>
                  ) : (
                    <span className="text-slate-500">—</span>
                  )}
                  <span className="text-slate-500 mx-1">→</span>
                  <span
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-emerald-900/30 border border-emerald-800"
                    style={{ borderColor: flow.partyColor || "#64748b" }}
                  >
                    <span
                      className="w-2 h-2 rounded-full"
                      style={{ background: flow.partyColor || "#64748b" }}
                    />
                    <span className="text-emerald-300 font-medium">{flow.party}</span>
                  </span>
                </>
              ) : (
                <>
                  <span
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-rose-900/30 border border-rose-800"
                    style={{ borderColor: flow.partyColor || "#64748b" }}
                  >
                    <span
                      className="w-2 h-2 rounded-full"
                      style={{ background: flow.partyColor || "#64748b" }}
                    />
                    <span className="text-rose-300 font-medium">{flow.party}</span>
                  </span>
                  <span className="text-slate-500 mx-1">→</span>
                  <span className="text-slate-500">{t("to")}:</span>
                  {m.toParty ? (
                    <span
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-800"
                      style={{ borderColor: m.toPartyColor || "#64748b" }}
                    >
                      <span
                        className="w-2 h-2 rounded-full"
                        style={{ background: m.toPartyColor || "#64748b" }}
                      />
                      <span className="text-emerald-300">{m.toParty}</span>
                    </span>
                  ) : (
                    <span className="text-slate-500">—</span>
                  )}
                </>
              )}
            </div>
          </button>
        ))}
        {(activeTab === "in" ? flow.membersIn : flow.membersOut).length === 0 && (
          <div className="text-slate-500 text-sm py-8 text-center">
            {t(activeTab === "in" ? "noJoined" : "noLeft")}
          </div>
        )}
      </div>
    </div>
  );
}