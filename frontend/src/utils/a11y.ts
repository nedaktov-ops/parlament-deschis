import type { KeyboardEvent } from "react";

/** Activate a focusable SVG control with the keys a native button uses.
 *  Space is preventDefault-ed so the page does not scroll. */
export function activateOnKey<T extends SVGElement>(
  event: KeyboardEvent<T>,
  activate: () => void,
): void {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    activate();
  }
}
