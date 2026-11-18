export interface EmptyStateProps {
  icon: React.ReactNode;      // SVG icon
  title: string;              // Heading text
  description: string;        // Supporting text
  ctaLabel?: string;          // Optional button label
  onCta?: () => void;         // Optional button handler
  className?: string;         // Optional CSS class
}

export default function EmptyState({
  icon,
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
      <svg aria-hidden="true" className="text-slate-400 mb-6">{icon}</svg>
      <h2 className="text-lg font-semibold text-slate-200">{title}</h2>
      <p className="text-sm text-slate-400 text-center max-w-xs">
        {description}
      </p>
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
