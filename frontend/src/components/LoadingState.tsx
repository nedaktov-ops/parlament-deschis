export interface LoadingStateProps {
  label?: string;
  description?: string;
}

export default function LoadingState({
  label,
  description
}: LoadingStateProps) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="flex flex-col items-center justify-center py-12 max-w-xs mx-auto text-center"
    >
      <svg
        aria-hidden="true"
        className="animate-spin text-sky-400 mb-6"
        width="40"
        height="40"
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <circle
          className="opacity-25"
          cx="12" cy="12" r="10"
          stroke="currentColor" strokeWidth="4" strokeLinecap="round"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
      {label && <h2 className="text-sm font-semibold text-slate-200">{label}</h2>}
      {description && (
        <p className="text-xs text-slate-400 text-center max-w-xs">{description}</p>
      )}
    </div>
  );
}
