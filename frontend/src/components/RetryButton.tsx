import { useTranslation } from "react-i18next";

/** The single retry control: one 44 px press target with press feedback and
 *  the inherited global focus ring. */
export default function RetryButton({
  onRetry,
  label,
  ariaLabel,
  className = "",
}: {
  onRetry: () => void;
  label?: string;
  ariaLabel?: string;
  className?: string;
}) {
  const { t } = useTranslation();
  return (
    <button
      type="button"
      onClick={onRetry}
      aria-label={ariaLabel}
      className={`btn btn-hover min-h-11 bg-slate-700 hover:bg-slate-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-400 ${className}`}
    >
      {label ?? t("traseismRetry")}
    </button>
  );
}
