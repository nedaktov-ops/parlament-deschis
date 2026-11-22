/** Pure legislature → start-year helpers for the overview slider.
 *
 * Kept free of React/i18n imports so the ordering and clamping rules can be
 * reasoned about (and tested) on their own. Dates are ISO `YYYY-MM-DD`, so
 * lexicographic comparison is chronological.
 */

export interface LegislatureStop {
  /** Meta key, e.g. "2024". Also the value written to the `legislature` scope. */
  id: string;
  /** Four-digit start year, e.g. 2024. */
  year: number;
  /** Human label from meta, or the year when label is empty. */
  label: string;
  /** First day of the legislature — the date the hemicycles are sampled at. */
  start: string;
  /** Last day of the legislature, when known. */
  end: string | null;
}

export type LegislatureMap = Record<
  string,
  { label: string; start: string | null; end: string | null }
>;

/** Ordered, validated slider stops. Entries without a parseable start date
 * are skipped rather than plotted at a guessed position. */
export function legislatureStops(map: LegislatureMap): LegislatureStop[] {
  return Object.entries(map)
    .filter(([, v]) => typeof v.start === "string" && /^\d{4}-\d{2}-\d{2}$/.test(v.start))
    .map(([id, v]) => ({
      id,
      year: Number(v.start!.slice(0, 4)),
      label: v.label || v.start!.slice(0, 4),
      start: v.start!,
      end: v.end ?? null,
    }))
    .sort((a, b) => a.start.localeCompare(b.start));
}

/** Index of the legislature whose start is the latest one not after `date`.
 * Returns -1 when there is no stop (caller renders a loading/empty state) and
 * 0 before the first start date. */
export function stopIndexForDate(stops: LegislatureStop[], date: string): number {
  if (stops.length === 0) return -1;
  let index = 0;
  for (let i = 0; i < stops.length; i += 1) {
    if (stops[i].start > date) break;
    index = i;
  }
  return index;
}
