import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import LoadingState from "../LoadingState";
import EmptyState from "../EmptyState";
import ErrorState from "../ErrorState";

export type ViewState = "loading" | "error" | "empty" | "ready";
export type PendingViewState = Exclude<ViewState, "ready">;

export interface ResolveViewStateArgs {
  isLoading: boolean;
  isError: boolean;
  isEmpty: boolean; // MUST be derived from loaded data only (rows.length === 0)
}

/**
 * The single precedence rule for every data region: loading → error → empty → ready.
 * A pending fetch can never yield "empty" (isLoading wins).
 * A failed fetch can never yield "empty" (isError wins).
 */
export function resolveViewState({
  isLoading,
  isError,
  isEmpty,
}: ResolveViewStateArgs): ViewState {
  if (isLoading) return "loading";
  if (isError) return "error";
  if (isEmpty) return "empty";
  return "ready";
}

export interface StateViewProps {
  view: PendingViewState;
  /** sr-only h1 for full-page states; omit when the page's visible h1 stays rendered. */
  pageTitle?: string;
  variant?: "page" | "inline";
  loadingLabel?: string;
  loadingDescription?: string;
  errorLabel?: string;
  errorDescription?: string;
  onRetry?: () => void;
  emptyTitle?: string;
  emptyDescription?: string;
  emptyCtaLabel?: string;
  onEmptyCta?: () => void;
  className?: string;
}

/** Renders exactly one non-ready state. `data-state` makes probes deterministic. */
export function StateView({
  view,
  pageTitle,
  variant = "page",
  loadingLabel,
  loadingDescription,
  errorLabel,
  errorDescription,
  onRetry,
  emptyTitle,
  emptyDescription,
  emptyCtaLabel,
  onEmptyCta,
  className,
}: StateViewProps) {
  const { t } = useTranslation();
  return (
    <div
      data-state={view}
      className={variant === "inline" ? "py-6" : "py-12"}
    >
      {pageTitle ? <h1 className="sr-only">{pageTitle}</h1> : null}
      {view === "loading" && (
        <LoadingState
          label={loadingLabel ?? t("loading")}
          description={loadingDescription}
        />
      )}
      {view === "error" && (
        <ErrorState
          message={errorLabel ?? t("state.error.title")}
          description={errorDescription ?? t("state.error.description")}
          onRetry={onRetry}
        />
      )}
      {view === "empty" && (
        <EmptyState
          title={emptyTitle ?? t("state.empty.title")}
          description={emptyDescription ?? t("state.empty.description")}
          ctaLabel={emptyCtaLabel}
          onCta={onEmptyCta}
          className={className}
        />
      )}
    </div>
  );
}

export interface AsyncStateProps extends Omit<StateViewProps, "view"> {
  view: ViewState;
  children?: ReactNode; // optional: full-page early returns render a state with no children
}

/** Gate one data region. `children` render only when view === "ready". */
export default function AsyncState({
  view,
  children,
  ...state
}: AsyncStateProps) {
  if (view === "ready") return <>{children}</>;
  return <StateView {...state} view={view} />;
}
