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
  legislature: string | null;
  from_org: OrgBrief | null;
  to_org: OrgBrief | null;
  event_date: string | null;
  precision: string | null;
  reason: string | null;
  confidence: string;
  summary_ro: string | null;
  summary_en: string | null;
  detected_at: string | null;
  source_url: string | null;
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
  committee_memberships?: Membership[];
  events: EventItem[];
  evidence: EvidenceItem[];
  as_of?: string | null;
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

export interface CoverageRow extends CoverageItem {
  persons: number;
  total_memberships: number;
  dated_pct: number | null;
  sourced_pct: number | null;
  total_switches: number;
  sourced_switches_pct: number | null;
  last_refresh: string | null;
}

/** R-08: honest per-scope coverage across three independent dimensions. */
export interface CoverageDimension {
  status: string;
  count: number;
  total?: number;
  note: string | null;
}
export interface CoverageDimensionRow {
  chamber: string;
  legislature: string | null;
  period_start: string | null;
  period_end: string | null;
  mandates: CoverageDimension;
  votes: CoverageDimension;
  biographies: CoverageDimension;
}

export interface DashboardStats {
  persons: number;
  memberships: number;
  switches: number; // deprecated alias of switches_all
  switches_all: number;
  switches_group: number;
  switches_party: number;
  committees: number;
  legislatures: number;
  parties: number;
  cross_chamber: number;
  coverage_score: number | null;
  coverage_full_rows: number;
  coverage_rows_total: number;
  definitions: Record<string, string>;
  computed_at: string;
}

/** R-04: canonical coverage aggregates; percentages are null when denominator is 0. */
export interface CoverageSummaryResponse {
  status: string;
  totals: {
    memberships: number;
    memberships_dated: number;
    memberships_sourced: number;
    switches_group: number;
    switches_party: number;
    switches_all: number;
    switches_sourced: number;
  };
  percentages: {
    dated: number | null;
    sourced: number | null;
    switches_sourced: number | null;
  };
  definitions: Record<string, string>;
}

export interface DashboardStatsResponse {
  status: string;
  data: DashboardStats;
}

export interface MetaResponse {
  legislatures: Record<string, { label: string; start: string | null; end: string | null }>;
  groups: OrgBrief[];
}

export interface HealthResponse {
  status: string;
  database: {
    status: string;
    persons: number;
    memberships: number;
  };
  dataset: {
    release_tag: string | null;
    published_at: string | null;
    asset_sha256: string | null;
  };
  sources: Record<
    string,
    string | {
      status?: string;
      finished_at?: string | null;
      rows?: number;
      error?: string | null;
    }
  >;
}

export interface MovementFilters {
  chamber?: string;
  legislature?: string;
  from?: string;
  to?: string;
  limit?: number;
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
  precision: string | null;
  reason: string | null;
  confidence: string;
  source_url: string | null;
}

export interface PartyTimelineResponse {
  dates: string[];
  groups: Record<string, number[]>;
  total: number[];
}

export interface CommitteeResponse {
  id: string;
  name: string;
  chamber: string | null;
  party: OrgBrief | null;
}

export interface CrossChamberPerson {
  person_id: string;
  name: string;
  chambers: Array<"deputies" | "senate">;
  deputies: string[];
  senate: string[];
}

export interface CrossChamberResponse {
  status: string;
  as_of: string;
  count: number;
  data: CrossChamberPerson[];
}

// --- Feature: Roll-call votes ----------------------------------------------

export interface VoteRow {
  id: string;
  native_vote_id: string;
  chamber: string;
  legislature: string | null;
  vote_time: string | null;
  title_raw: string | null;
  present: number | null;
  not_voting: number | null;
  yes: number | null;
  no: number | null;
  abstain: number | null;
  source_url: string;
  positions_incomplete: boolean;
}

/** A chamber/legislature pair that actually has votes in the corpus. */
export interface VoteScope {
  chamber: string;
  legislature: string | null;
  total: number;
}

export interface VotesResponse {
  status: string;
  data_exists: boolean;
  data: VoteRow[];
  total: number;
  offset: number;
  limit: number;
  /** Data-derived alternatives; summing their totals equals the corpus total. */
  scopes: VoteScope[];
}

export interface VoteDetail {
  id: string;
  native_vote_id: string;
  chamber: string;
  legislature: string | null;
  vote_time: string | null;
  title_raw: string | null;
  present: number | null;
  not_voting: number | null;
  yes: number | null;
  no: number | null;
  abstain: number | null;
  official_vote_url: string | null;
  source_url: string;
  snapshot_hash: string | null;
  truth_contract_version: string | null;
  positions_incomplete: boolean;
  position_count: number;
}

/** Wire envelope returned by GET /votes/{vote_id} (api.py:1359-1381). */
export interface VoteDetailResponse {
  status: string;
  data_exists: boolean;
  data: VoteDetail | null;
}

export interface VotePositionRow {
  person_id: string;
  name_raw: string | null;
  group_raw: string | null;
  choice: string;
  resolution_scheme: string;
  source_url: string;
}

export interface VotePositionsResponse {
  status: string;
  data_exists: boolean;
  data: VotePositionRow[];
  total: number;
  offset: number;
  limit: number;
}

export interface CohesionParty {
  party: string;
  yes: number;
  no: number;
  abstain: number;
  not_voting: number;
  total_votes: number;
  yes_pct: number;
  no_pct: number;
  abstain_pct: number;
}

/** Provenance stamp carried by every /api/analytics response. */
export interface AnalyticsMeta {
  generated_at: string;
  count: number;
}

export interface VoteCohesionResponse {
  status: string;
  data_exists: boolean;
  data: CohesionParty[];
  denominator: string;
  meta: AnalyticsMeta;
}

export interface ActivityBucket {
  date: string;
  votes: number;
  yes: number;
  no: number;
  abstain: number;
  present: number;
}

export interface VoteActivityResponse {
  status: string;
  data_exists: boolean;
  data: ActivityBucket[];
  buckets: number;
  meta: AnalyticsMeta;
}

export interface VotesFilters {
  chamber?: string;
  legislature?: string;
  from?: string;
  to?: string;
  limit?: number;
  offset?: number;
}

export interface MpCard {
  id: string;
  name: string;
  birth_date: string | null;
  age: number | null;
  party: string | null;
  switches: number;
  committees: number;
}
export interface MpsResponse {
  status: string;
  data: MpCard[];
  offset: number;
  limit: number;
  /** R-04: corpus-wide denominator, independent of offset/limit (never the page length). */
  total: number;
  definition: string;
  scope: { as_of: string | null; chamber: string | null; legislature: string | null };
}
export interface MpsQuery {
  q?: string; sort?: string; offset?: number; limit?: number;
  chamber?: string; legislature?: string; asOf?: string;
}
export function mpsCards(query: MpsQuery = {}): Promise<MpsResponse> {
  const p = new URLSearchParams();
  if (query.q) p.set("q", query.q);
  if (query.sort) p.set("sort", query.sort);
  if (query.offset !== undefined) p.set("offset", String(query.offset));
  if (query.limit !== undefined) p.set("limit", String(query.limit));
  if (query.chamber) p.set("chamber", query.chamber);
  if (query.legislature) p.set("legislature", query.legislature);
  if (query.asOf) p.set("as_of", query.asOf);
  return get<MpsResponse>(`/mps${p.toString() ? `?${p.toString()}` : ""}`);
}

/** Map a route scope to /votes' supported parameters (date ⇒ upper bound). */
export function votesForScope(scope: { date: string; chamber?: string; legislature?: string },
                              extra: VotesFilters = {}): VotesFilters {
  return {
    chamber: scope.chamber,
    legislature: scope.legislature,
    to: scope.date,              // "votes up to <date>" — label it that way in the UI
    ...extra,                    // caller may override limit/offset/from/to
  };
}

const BASE = "/api";

export async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) {
    let message = `API ${res.status}: ${path}`;
    if (res.headers.get("content-type")?.includes("json")) {
      const body: unknown = await res.json();
      if (typeof body === "object" && body !== null && !Array.isArray(body)) {
        const detail =
          "detail" in body && typeof body.detail === "string"
            ? body.detail
            : "title" in body && typeof body.title === "string"
              ? body.title
              : null;
        if (detail) message = `API ${res.status}: ${detail}`;
      }
    }
    throw new Error(message);
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
  person: (id: string, asOf?: string) =>
    get<PersonDetail>(`/persons/${encodeURIComponent(id)}${asOf ? `?as_of=${encodeURIComponent(asOf)}` : ""}`),
  personHistory: (id: string) =>
    get<PersonHistoryResponse>(`/persons/${encodeURIComponent(id)}/history`),
  partyProfile: (shortName: string, asOf: string) =>
    get<PartyProfileResponse>(`/party/${encodeURIComponent(shortName)}?as_of=${asOf}`),
  partyMovements: (shortName: string, asOf: string, limit = 50) =>
    get<PartyMovementResponse[]>(`/party/${encodeURIComponent(shortName)}/movements?as_of=${asOf}&limit=${limit}`),
  partyTimeline: (shortName: string, from: string, to: string) =>
    get<PartyTimelineResponse>(`/party/${encodeURIComponent(shortName)}/timeline?from=${from}&to=${to}`),
  committees: (asOf: string) => get<CommitteeResponse[]>(`/committees?as_of=${asOf}`),
  parties: () => get<{ status: string; data: PartyListEntry[] }>("/parties"),
  crossChamber: (asOf: string) =>
    get<CrossChamberResponse>(`/analytics/cross-chamber?as_of=${asOf}`),
  movements: (filters: MovementFilters | string = {}) => {
    const options = typeof filters === "string" ? { chamber: filters } : filters;
    const params = new URLSearchParams();
    if (options.chamber) params.set("chamber", options.chamber);
    if (options.legislature) params.set("legislature", options.legislature);
    if (options.from) params.set("from", options.from);
    if (options.to) params.set("to", options.to);
    if (options.limit !== undefined) params.set("limit", String(options.limit));
    const query = params.toString();
    return get<EventItem[]>(`/movements${query ? `?${query}` : ""}`);
  },
  recentEvents: (limit = 50, chamber?: string, legislature?: string) =>
  get<EventItem[]>(
    `/events/recent?limit=${limit}${chamber ? `&chamber=${chamber}` : ""}${legislature ? `&legislature=${legislature}` : ""}`
  ),
  coverage: () => get<CoverageItem[]>("/coverage"),
  coverage_detailed: () => get<CoverageRow[]>("/coverage/detailed"),
  coverageDimensions: () => get<CoverageDimensionRow[]>("/coverage/dimensions"),
  coverageSummary: () => get<CoverageSummaryResponse>("/coverage/summary"),
  about: () => get<AboutResponse>("/about"),
  health: () => get<HealthResponse>("/health"),
  dashboardStats: (asOf?: string) =>
    get<DashboardStatsResponse>(asOf ? `/dashboard/stats?as_of=${asOf}` : "/dashboard/stats"),

  votes: (query: VotesFilters = {}) =>
    get<VotesResponse>("/votes" + (() => {
      const params = new URLSearchParams();
      if (query.chamber) params.set("chamber", query.chamber);
      if (query.legislature) params.set("legislature", query.legislature);
      if (query.from) params.set("from", query.from);
      if (query.to) params.set("to", query.to);
      if (query.limit !== undefined) params.set("limit", String(query.limit));
      if (query.offset !== undefined) params.set("offset", String(query.offset));
      const qs = params.toString();
      return qs ? `?${qs}` : "";
    })()),
  voteDetail: (voteId: string) =>
    get<VoteDetailResponse>(`/votes/${encodeURIComponent(voteId)}`),
  votePositions: (voteId: string, query: { limit?: number; offset?: number; choice?: string } = {}) => {
    const params = new URLSearchParams();
    if (query.limit !== undefined) params.set("limit", String(query.limit));
    if (query.offset !== undefined) params.set("offset", String(query.offset));
    if (query.choice) params.set("choice", query.choice);
    const qs = params.toString();
    return get<VotePositionsResponse>(
      `/votes/${encodeURIComponent(voteId)}/positions${qs ? `?${qs}` : ""}`,
    );
  },
  voteCohesion: (chamber?: string, legislature?: string) => {
    const params = new URLSearchParams();
    if (chamber) params.set("chamber", chamber);
    if (legislature) params.set("legislature", legislature);
    const qs = params.toString();
    return get<VoteCohesionResponse>(
      `/analytics/vote-cohesion${qs ? `?${qs}` : ""}`,
    );
  },
  voteActivity: (
    chamber?: string,
    legislature?: string,
    from?: string,
    to?: string,
  ) => {
    const params = new URLSearchParams();
    if (chamber) params.set("chamber", chamber);
    if (legislature) params.set("legislature", legislature);
    if (from) params.set("from", from);
    if (to) params.set("to", to);
    const qs = params.toString();
    return get<VoteActivityResponse>(
      `/analytics/vote-activity${qs ? `?${qs}` : ""}`,
    );
  },

  scorecard: (
    legislature?: string,
    chamber?: string,
    limit = 50,
    offset = 0,
    min_votes = 1,
  ) => {
    const params = new URLSearchParams();
    if (legislature) params.set("legislature", legislature);
    if (chamber) params.set("chamber", chamber);
    params.set("limit", String(limit));
    params.set("offset", String(offset));
    params.set("min_votes", String(min_votes));
    return get<ScorecardResponse>(`/votes/scorecard?${params.toString()}`);
  },
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

// ---------------------------------------------------------------------------
// Traseism (party / parliamentary group switching) statistics
// ---------------------------------------------------------------------------

export interface TraseismPeriod {
  start: string | null;
  end: string | null;
}

export interface TraseismPartyMovement {
  party: string;
  gains: number;
  losses: number;
  net: number;
  seats_start: number;
  seats_end: number;
}

export interface TraseismMatrixCell {
  from: string;
  to: string;
  count: number;
}

export interface TraseismRepeatSwitchers {
  people: number;
  max_switches: number;
}

export interface TraseismTiming {
  median_months: number | null;
  by_month: Array<{ month: number; count: number }>;
}

export interface TraseismCoverage {
  completeness: string;
  note: string | null;
}

/**
 * The party-level view: a change of the party behind the group. The
 * unaffiliated bucket is not a party, so a member who leaves a party, sits
 * unaffiliated and then joins another party counts as ONE party switch.
 */
export interface TraseismPartyView {
  switches: number;
  switchers: number;
  switch_rate: number;
  switches_per_100_members: number;
  entries: number;
  exits: number;
  matrix: TraseismMatrixCell[];
}

/** The full statistical block for one (chamber, legislature) scope. */
export interface TraseismScope {
  legislature: string;
  chamber: string;
  period: TraseismPeriod;
  members: number;
  switches: number;
  switchers: number;
  switch_rate: number;
  switches_per_100_members: number;
  party: TraseismPartyView;
  by_party: TraseismPartyMovement[];
  matrix: TraseismMatrixCell[];
  repeat_switchers: TraseismRepeatSwitchers;
  timing: TraseismTiming;
  coverage: TraseismCoverage;
  definitions: Record<string, string>;
}

export interface TraseismSwitchRow {
  person_id: string;
  name: string;
  from_group: string | null;
  to_group: string | null;
  date: string | null;
  legislature: string | null;
  chamber: string | null;
  source_url: string | null;
  precision: string | null;
}

export interface TraseismSwitchesResponse {
  rows: TraseismSwitchRow[];
  total: number;
}

export interface TraseismSwitchesQuery {
  legislature?: string;
  chamber?: string;
  group?: string;
  person?: string;
  limit?: number;
  offset?: number;
}

/** One row per (chamber, legislature) scope, with the full statistical block. */
export function traseismOverview(): Promise<TraseismScope[]> {
  return get<TraseismScope[]>("/traseism/overview");
}

/** The same statistical block for a single chamber + legislature scope. */
export function traseismSummary(
  legislature: string,
  chamber: string,
): Promise<TraseismScope> {
  return get<TraseismScope>(
    `/traseism/summary?legislature=${encodeURIComponent(legislature)}&chamber=${encodeURIComponent(chamber)}`,
  );
}

/** The individual switch ledger, paginated. */
export function traseismSwitches(
  query: TraseismSwitchesQuery = {},
): Promise<TraseismSwitchesResponse> {
  const params = new URLSearchParams();
  if (query.legislature) params.set("legislature", query.legislature);
  if (query.chamber) params.set("chamber", query.chamber);
  if (query.group) params.set("group", query.group);
  if (query.person) params.set("person", query.person);
  if (query.limit !== undefined) params.set("limit", String(query.limit));
  if (query.offset !== undefined) params.set("offset", String(query.offset));
  const qs = params.toString();
  return get<TraseismSwitchesResponse>(
    `/traseism/switches${qs ? `?${qs}` : ""}`,
  );
}

// --- Feature 1: Switch leaderboard ---------------------------------------

export interface SwitchLeaderboardEntry {
  person_id: string;
  name: string;
  switch_count: number;
  first_switch: string | null;
  last_switch: string | null;
  parties: string[];
  total_events: number;
  tenure_years: number;
  loyalty_score: number | null;
  loyalty_status: string;
  loyalty_inputs: {
    switch_count: number;
    total_events_in_scope: number;
    tenure_years: number;
    tenure_weight: number | null;
  };
}

export interface SwitchLeaderboardResponse {
  status: string;
  score_scope: string;
  definitions: Record<string, string>;
  data: SwitchLeaderboardEntry[];
}

/** Top party switchers, ranked by observed switch_group count. */
export function switchLeaderboard(
  limit = 20,
  legislature?: string,
  chamber?: string,
): Promise<SwitchLeaderboardResponse> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (legislature) params.set("legislature", legislature);
  if (chamber) params.set("chamber", chamber);
  return get<SwitchLeaderboardResponse>(
    `/analytics/switch-leaderboard?${params.toString()}`,
  );
}

// --- Feature 4: Demographics (age per party) ------------------------------

export interface GenerationalShiftEntry {
  party: string;
  mps_with_birth_dates: number;
  avg_age: number;
  median_age: number;
}

export interface GenerationalShiftResponse {
  status: string;
  as_of: string;
  totals: {
    mps_in_scope: number;
    mps_with_birth_date: number;
    mps_unknown_birth_date: number;
    population_avg_age: number | null;
    population_median_age: number | null;
    coverage_pct: number | null;
    definition: string;
  };
  data: GenerationalShiftEntry[];
}

/** Age summaries per party from dated group memberships. */
export function generationalShift(
  legislature?: string,
  asOf?: string,
): Promise<GenerationalShiftResponse> {
  const params = new URLSearchParams();
  if (legislature) params.set("legislature", legislature);
  if (asOf) params.set("as_of", asOf);
  const qs = params.toString();
  return get<GenerationalShiftResponse>(
    `/analytics/generational-shift${qs ? `?${qs}` : ""}`,
  );
}

// --- Feature 2: Commitment Tracker (committee membership) -----------------

export interface PartyListEntry {
  id: string;
  short_name: string;
  name: string;
  color: string | null;
  total_members: number;
  switches_in: number;
}

export interface CommitteeListItem {
  id: string;
  name: string;
  chamber: string | null;
  party: string | null;
}

export interface CommitteeMember {
  person_id: string;
  name: string;
  role: string | null;
  group: string | null;
  start_date: string | null;
  end_date: string | null;
  start_precision: string | null;
  end_precision: string | null;
  active: boolean;
  source_url: string | null;
}

export interface CommitteeMembersResponse {
  committee: {
    id: string;
    name: string;
    chamber: string | null;
    legislature: string | null;
  };
  as_of: string;
  members: CommitteeMember[];
  active_count: number;
  total_count: number;
}

/** Committees with at least one active dated member. */
export function committees(asOf?: string): Promise<CommitteeListItem[]> {
  const qs = asOf ? `?as_of=${encodeURIComponent(asOf)}` : "";
  return get<CommitteeListItem[]>(`/committees${qs}`);
}

/** Dated member ledger of one committee. */
export function committeeMembers(
  committeeId: string,
  asOf?: string,
): Promise<CommitteeMembersResponse> {
  const qs = asOf ? `?as_of=${encodeURIComponent(asOf)}` : "";
  return get<CommitteeMembersResponse>(
    `/committees/${encodeURIComponent(committeeId)}/members${qs}`,
  );
}

// --- Feature 5: Committee Control Index -----------------------------------

export interface CommitteeControlParty {
  party: string;
  chairs: number;
  share_pct: number;
}

export interface CommitteeControlChair {
  committee_id: string;
  committee: string;
  chamber: string | null;
  chair_person_id: string;
  chair: string;
  party: string;
  chair_since: string | null;
}

export interface CommitteeControlData {
  as_of: string;
  total_committees: number;
  parties: CommitteeControlParty[];
  chairs: CommitteeControlChair[];
}

export interface CommitteeControlResponse {
  status: string;
  reason?: string;
  data: CommitteeControlData;
}

/** Which party chairs which committees (dated, source-backed). */
export function committeeControl(
  legislature?: string,
  asOf?: string,
): Promise<CommitteeControlResponse> {
  const params = new URLSearchParams();
  if (legislature) params.set("legislature", legislature);
  if (asOf) params.set("as_of", asOf);
  const qs = params.toString();
  return get<CommitteeControlResponse>(
    `/analytics/committee-control${qs ? `?${qs}` : ""}`,
  );
}

// --- Feature 11: Switch waves --------------------------------------------

export interface SwitchWave {
  id: string;
  label: string | null;
  start_date: string | null;
  end_date: string | null;
  switch_count: number;
  trigger_type: string | null;
  trigger_event: string | null;
  /** Editor-curated trigger disclosure; null when the wave has no label. */
  trigger_provenance: string | null;
  legislature: string | null;
  chamber: string | null;
  created_at: string | null;
}

export interface GenerationalShiftEntry {
  party: string;
  mps_with_birth_dates: number;
  avg_age: number;
  median_age: number;
  average_age?: number;
}

/** Detected switch waves (bursts of affiliation change), newest first. */
export function switchWaves(
  chamber?: string,
  legislature?: string,
): Promise<SwitchWave[]> {
  const params = new URLSearchParams();
  if (chamber) params.set("chamber", chamber);
  if (legislature) params.set("legislature", legislature);
  const qs = params.toString();
  return get<SwitchWave[]>(`/analytics/switch-waves${qs ? `?${qs}` : ""}`);
}

export function ideology(
  year?: string,
): Promise<IdeologyResponse> {
  const params = new URLSearchParams();
  if (year) params.set("year", year);
  return get<IdeologyResponse>(`/analytics/ideology${params.toString() ? `?${params.toString()}` : ""}`);
}

// --- Feature: Roll-call vote scorecard -------------------------------------

export interface ScorecardEntry {
  person_id: string;
  name_raw: string | null;
  canonical_name: string | null;
  group_raw: string | null;
  party: string | null;
  total_votes: number;
  yes_votes: number;
  no_votes: number;
  abstain_votes: number;
  not_voting_votes: number;
  loyalty_pct: number | null;
  rebellion_pct: number | null;
  participation_pct: number | null;
  denominators: {
    alignment: number;
    participation: number;
    definition: string;
  };
}

export interface ScorecardResponse {
  status: string;
  data_exists: boolean;
  data: ScorecardEntry[];
  total: number;
  offset: number;
  limit: number;
}

// --- Feature: Roll-call vote ideology (CHES) ---------------------------------

export interface IdeologyEntry {
  party_name: string;
  partyfacts_id: string | null;
  survey_year: number;
  lrgen: number | null;
  lrecon: number | null;
  galtan: number | null;
  eu_position: number | null;
  antielite_salience: number | null;
  people_vs_elite: number | null;
}

export interface IdeologyResponse {
  status: string;
  data_exists: boolean;
  data: IdeologyEntry[];
  meta: AnalyticsMeta;
}