export interface EmptyStateProps {
  icon?: React.ReactNode;      // Decorative SVG icon (defaults to a magnifier)
  title: string;              // Heading text
  description?: string;       // Optional supporting text
  ctaLabel?: string;          // Optional button label
  onCta?: () => void;         // Optional button handler
  className?: string;         // Optional CSS class
}

export default function EmptyState({
  icon = (
    <svg
      width="40"
      height="40"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
    >
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.5-3.5" strokeLinecap="round" />
    </svg>
  ),
  title,
  description,
  ctaLabel,
  onCta,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center py-12 max-w-xs mx-auto text-center ${className ?? ""}`}
    >
      <div aria-hidden="true" className="text-slate-400 mb-6">{icon}</div>
      <h2 className="text-lg font-semibold text-slate-200">{title}</h2>
      {description && (
        <p className="text-sm text-slate-400 text-center max-w-xs">
          {description}
        </p>
      )}
      {onCta && ctaLabel && (
        <button
          type="button"
          onClick={onCta}
          className="btn mt-4 bg-slate-700 hover:bg-slate-600"
          aria-label={ctaLabel}
        >
          {ctaLabel}
        </button>
      )}
    </div>
  );
}
