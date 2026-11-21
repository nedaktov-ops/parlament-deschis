import { useTranslation } from "react-i18next";

export interface ErrorStateProps {
  message?: string;
  description?: string;
  onRetry?: () => void;
}

export default function ErrorState({
  message,
  description,
  onRetry,
}: ErrorStateProps) {
  const { t } = useTranslation();

  return (
    <div
      role="alert"
      aria-live="assertive"
      className="flex flex-col items-center justify-center py-12 max-w-xs mx-auto text-center"
    >
      <svg
        aria-hidden="true"
        className="text-rose-400 mb-6"
        width="40" height="40" viewBox="0 0 24 24" fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          fill="currentColor" fillRule="evenodd" clipRule="evenodd"
          d="M18.486 15.286a3 3 0 0 1-3.972-.002L8.2 10.082a2 2 0 0 1 .055-2.898L12 4.774l3.745 2.412a2 2 0 0 1 .055 2.898l-6.317 5.204a3 3 0 0 1-3.972 0M12 7a1 1 0 1 0 0 2 1 1 0 0 0 0-2m0 10a1 1 0 1 0 0 2 1 1 0 0 0 0-2"
        />
      </svg>
      {message && <h2 className="text-sm font-semibold text-slate-200">{message}</h2>}
      {description && (
        <p className="text-xs text-slate-400 text-center max-w-xs">{description}</p>
      )}
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="btn btn-hover min-h-11 mt-4 bg-slate-700 hover:bg-slate-600"
          aria-label={t("retry", "Retry")}
        >
          {t("retry", "Retry")}
        </button>
      )}
    </div>
  );
}
