export interface OrgBrief {
  id: string;
  name: string;
  short_name: string | null;
  classification: string;
  color: string | null;
  localised_labels?: Record<string, Record<string, string>> | null;
}

export interface MemberBrief {
  person_id: string;
  name: string;
  role: string | null;
}

export interface GroupComposition {
  short_name: string;
  org: OrgBrief | null;
  count: number;
  members: MemberBrief[];
  color: string | null;
}

export interface ChamberResponse {
  chamber: string;
  as_of: string;
  total: number;
  groups: GroupComposition[];
}

export interface Membership {
  id: string;
  org: OrgBrief | null;
  party: OrgBrief | null;
  chamber: string;
  legislature: string | null;
  role: string | null;
  start_date: string | null;
  end_date: string | null;
  start_precision: string | null;
  end_precision: string | null;
  confidence: string;
  source_url: string | null;
}

export interface EventItem {
  id: string;
  type: string;
  person: { id: string; name: string } | null;
  chamber: string | null;
  from_org: OrgBrief | null;
  to_org: OrgBrief | null;
  event_date: string | null;
  precision: string | null;
  reason: string | null;
  confidence: string;
  summary_ro: string | null;
  summary_en: string | null;
  detected_at: string | null;
}

export interface EvidenceItem {
  id: string;
  membership_id: string;
  type: string;
  source_url: string | null;
  snapshot_hash: string | null;
  snapshot_url: string | null;
  note: string | null;
  observed_at: string | null;
}

export interface PersonDetail {
  id: string;
  name: string;
  birth_date: string | null;
  wikidata_qid: string | null;
  match_status: string;
  identifiers: { scheme: string; identifier: string; legislature: string | null }[];
  memberships: Membership[];
  events: EventItem[];
  evidence: EvidenceItem[];
}

export interface PersonSummary {
  id: string;
  name: string;
  birth_date: string | null;
  wikidata_qid: string | null;
  chambers: string[];
  match_status: string;
}

export interface TimelineResponse {
  chamber: string;
  dates: string[];
  totals: number[];
  groups: Record<string, number[]>;
  switches: EventItem[];
}

export interface CoverageItem {
  chamber: string;
  legislature: string | null;
  period_start: string | null;
  period_end: string | null;
  completeness: string;
  note: string | null;
}

export interface MetaResponse {
  legislatures: Record<string, { label: string; start: string | null; end: string | null }>;
  groups: OrgBrief[];
}

export interface HealthResponse {
  status: string;
  sources: Record<string, unknown>;
}

export interface PersonHistoryEntry {
  field: string;
  from: string | null;
  to: string | null;
  date: string | null;
  org?: string | null;
  event_type?: string | null;
  source_url?: string | null;
}

export interface PersonHistoryResponse {
  person_id: string;
  history: PersonHistoryEntry[];
}

export interface AboutSource {
  name: string;
  url: string;
  note: string | null;
}

export interface AboutLicenses {
  code: string;
  data: string;
  code_url: string | null;
  data_url: string | null;
}

export interface AboutResponse {
  name: string;
  description: string;
  sources: AboutSource[];
  licenses: AboutLicenses;
  coverage: CoverageItem[];
  freshness: Record<string, unknown>;
  generated_at: string;
}

export interface PartyProfileResponse {
  id: string;
  name: string;
  short_name: string | null;
  color: string | null;
  wikidata_qid: string | null;
  current_members: number | null;
  switches_in: number | null;
  switches_out: number | null;
  net_change: number | null;
}

export interface PartyMovementResponse {
  id: string;
  type: string;
  event_date: string;
  chamber: string | null;
  person: { id: string; name: string } | null;
  from_org: OrgBrief | null;
  to_org: OrgBrief | null;
  summary_ro: string | null;
  summary_en: string | null;
}

export interface PartyTimelineResponse {
  dates: string[];
  groups: Record<string, number[]>;
  total: number[];
}

export interface CommitteeResponse {
  id: string;
  name: string;
  chamber: string;
  party: OrgBrief | null;
}

const BASE = "/api";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${path}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  meta: () => get<MetaResponse>("/meta"),
  chamber: (chamber: string, asOf: string) =>
    get<ChamberResponse>(`/chamber?chamber=${chamber}&as_of=${asOf}`),
  timeline: (chamber: string, from: string, to: string, stepDays = 30) =>
    get<TimelineResponse>(
      `/timeline?chamber=${chamber}&from=${from}&to=${to}&step_days=${stepDays}`,
    ),
  persons: (q: string, chamber?: string) =>
    get<PersonSummary[]>(
      `/persons?q=${encodeURIComponent(q)}${chamber ? `&chamber=${chamber}` : ""}`,
    ),
  person: (id: string) => get<PersonDetail>(`/persons/${id}`),
  personHistory: (id: string) =>
    get<PersonHistoryResponse>(`/persons/${encodeURIComponent(id)}/history`),
  partyProfile: (shortName: string, asOf: string) =>
    get<PartyProfileResponse>(`/party/${encodeURIComponent(shortName)}?as_of=${asOf}`),
  partyMovements: (shortName: string, asOf: string, limit = 50) =>
    get<PartyMovementResponse[]>(`/party/${encodeURIComponent(shortName)}/movements?as_of=${asOf}&limit=${limit}`),
  partyTimeline: (shortName: string, from: string, to: string) =>
    get<PartyTimelineResponse>(`/party/${encodeURIComponent(shortName)}/timeline?from=${from}&to=${to}`),
  committees: (asOf: string) => get<CommitteeResponse[]>(`/committees?as_of=${asOf}`),
  movements: (chamber?: string) =>
    get<EventItem[]>(`/movements${chamber ? `?chamber=${chamber}` : ""}`),
  recentEvents: (limit = 50) => get<EventItem[]>(`/events/recent?limit=${limit}`),
  coverage: () => get<CoverageItem[]>("/coverage"),
  about: () => get<AboutResponse>("/about"),
  health: () => get<HealthResponse>("/health"),
};

function withScope(path: string, chamber?: string, legislature?: string): string {
  const params = new URLSearchParams();
  if (chamber) params.set("chamber", chamber);
  if (legislature) params.set("legislature", legislature);
  const qs = params.toString();
  return qs ? `${path}?${qs}` : path;
}

/** Popolo JSON export URL (no fetch — link/download it directly). */
export function exportPopoloUrl(chamber?: string, legislature?: string): string {
  return withScope("/api/export/popolo", chamber, legislature);
}

/** Flat CSV export URL for one dataset (persons, organizations, posts, memberships, events). */
export function exportCsvUrl(
  dataset: string,
  chamber?: string,
  legislature?: string,
): string {
  return withScope(`/api/export/${encodeURIComponent(dataset)}.csv`, chamber, legislature);
}