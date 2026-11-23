import { useCallback } from "react";
import { useLocation, useNavigate, useSearch } from "@tanstack/react-router";
import { isISODate, localISODate } from "../utils/date";
import type { ChamberScope } from "../router";

export interface Scope {
  date: string;                    // always a validated ISO date
  chamber?: ChamberScope;          // undefined = no chamber filter requested
  legislature?: string;            // undefined = no legislature filter requested
}

/** The exact shape TanStack derives from `validateScopeSearch`: all three
 * keys are present (undefined values are dropped by `stringifySearch`). */
export interface ScopeSearch extends Record<string, unknown> {
  date: string;
  chamber: ChamberScope | undefined;
  legislature: string | undefined;
}

/** Stable, cache-safe representation of the active scope (order matters). */
export function scopeKeyOf(s: Scope): readonly [string, string, string] {
  return [s.date, s.chamber ?? "*", s.legislature ?? "*"];
}

/**
 * Single source of truth for route-driven scope. Pure: no fetching, no clamping.
 * Pages that need legislature bounds (LegislatureDetail) apply their own clamp
 * to `date` after `api.meta` resolves — the classic pattern at LegislatureDetail.tsx:20-29.
 */
export function useScope(): Scope & {
  scopeKey: readonly [string, string, string];
  setScope: (patch: Partial<Scope>) => void;
  searchFor: (extra?: Record<string, unknown>) => ScopeSearch;
} {
  const raw = useSearch({ strict: false }) as Record<string, unknown>;
  // All routes share the validateScopeSearch shape; anchoring `from` gives
  // TanStack a concrete search type for the reducer; setScope passes an explicit `to`.
  const navigate = useNavigate({ from: "/" });
  const location = useLocation();

  const date = isISODate(raw.date) ? raw.date : localISODate();
  const chamber: ChamberScope | undefined =
    raw.chamber === "senate" || raw.chamber === "deputies" ? raw.chamber : undefined;
  const legislature =
    typeof raw.legislature === "string" && /^\d{4}$/.test(raw.legislature)
      ? raw.legislature
      : undefined;
  const scope: Scope = { date, chamber, legislature };

  const setScope = useCallback(
    (patch: Partial<Scope>) => {
      navigate({
        to: location.pathname,
        // functional updater: never drop page-local params (q, sort, offset, year, …)
        // and always emit the three canonical keys so TanStack's derived search
        // type is satisfied (undefined values are omitted from the URL).
        search: (prev) => {
          const merged = { ...(prev as Record<string, unknown>), ...patch };
          return {
            ...merged,
            date: merged.date as string,
            chamber: merged.chamber as ChamberScope | undefined,
            legislature: merged.legislature as string | undefined,
          };
        },
        replace: false, // back/forward must step through filter changes (FN-7)
      });
    },
    [navigate, location.pathname],
  );
  const searchFor = useCallback(
    (extra: Record<string, unknown> = {}) => ({ ...scope, ...extra }) as ScopeSearch,
    [date, chamber, legislature], // eslint-disable-line react-hooks/exhaustive-deps
  );

  return { ...scope, scopeKey: scopeKeyOf(scope), setScope, searchFor };
}
