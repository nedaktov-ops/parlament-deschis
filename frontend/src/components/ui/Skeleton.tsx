// src/components/ui/Skeleton.tsx
/**
 * Simple skeleton placeholder for loading states.
 * Usage: <Skeleton className="h-6 w-24" />
 */
export default function Skeleton({ className }: { className?: string }) {
  return (
    <div
      className={`animate-pulse rounded bg-slate-700/50 ${className ?? "h-4 w-full"}`}
    />
  );
}
