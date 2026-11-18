export interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export default function ErrorState({
  message,
  onRetry,
}: ErrorStateProps) {
  return (
    <div
      role="alert"
      className="flex flex-col items-center justify-center py-12 max-w-xs mx-auto text-center"
    >
      <svg
        aria-hidden="true"
        role="alert"
        className="text-rose-400 mb-6"
        width="40"
        height="40"
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          fill="currentColor"
          fillRule="evenodd"
          d="M18.486 15.286a3 3 0 0 1-3.972-.002L8.2 10.082a2 2 0 0 1 .055-2.898L12 4.774l3.745 2.412a2 2 0 0 1 .055 2.898l-6.317 5.204a3 3 0 0 1-3.972 0M12 7a1 1 0 1 0 0 2 1 1 0 0 0 0-2m0 10a1 1 0 1 0 0 2 1 1 0 0 0 0-2"
          clipRule="evenodd"
        />
      </svg>
      {message && (
        <h3 className="text-sm font-semibold text-slate-200">{message}</h3>
      )}
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="btn mt-4 bg-slate-700 hover:bg-slate-600"
          aria-label="Retry"
        >
          Retry
        </button>
      )}
    </div>
  );
}
