import type { ReactNode } from "react";

/** Focus/hover-reachable text for an aria-describedby trigger. Place inside a
 *  `relative group` wrapper; the trigger carries `aria-describedby={id}`. */
export default function TooltipText({
  id,
  children,
}: {
  id: string;
  children: ReactNode;
}) {
  return (
    <span
      id={id}
      role="tooltip"
      className="pointer-events-none sr-only group-hover:not-sr-only group-focus-within:not-sr-only absolute left-1/2 top-full z-[70] mt-1 -translate-x-1/2 whitespace-nowrap rounded border border-slate-700 bg-slate-900 px-2 py-1 text-xs text-slate-100 shadow-lg"
    >
      {children}
    </span>
  );
}
