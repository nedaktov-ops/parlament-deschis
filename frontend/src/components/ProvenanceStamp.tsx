import { useTranslation } from "react-i18next";

export interface ProvenanceStampProps {
  sourceUrl?: string | null;
  confidence?: string | null;
  precision?: string | null;
  snapshotHash?: string | null;
  snapshotUrl?: string | null;
  note?: string | null;
  className?: string;
}

const CONFIDENCE_KEYS: Record<string, string> = {
  official_ledger: "confidence.official_ledger",
  official_profile: "confidence.official_profile",
  derived: "confidence.derived",
  community: "confidence.community",
};

/** Renders provenance only for fields the API actually supplied. */
export default function ProvenanceStamp({
  sourceUrl,
  confidence,
  precision,
  snapshotHash,
  snapshotUrl,
  note,
  className = "",
}: ProvenanceStampProps) {
  const { t } = useTranslation();
  if (!sourceUrl && !confidence && !precision && !snapshotHash && !snapshotUrl && !note) {
    return null;
  }
  const confidenceLabel = confidence
    ? CONFIDENCE_KEYS[confidence]
      ? t(CONFIDENCE_KEYS[confidence])
      : confidence
    : null;

  return (
    <dl className={`flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-slate-500 ${className}`}>
      {sourceUrl && (
        <div className="flex gap-1">
          <dt className="sr-only">{t("source")}</dt>
          <dd>
            <a href={sourceUrl} target="_blank" rel="noopener noreferrer"
               className="text-sky-400 hover:underline">{t("viewOriginal")} ↗</a>
          </dd>
        </div>
      )}
      {confidenceLabel && (
        <div className="flex gap-1">
          <dt>{t("prov.confidence")}:</dt><dd className="text-slate-400">{confidenceLabel}</dd>
        </div>
      )}
      {precision && (
        <div className="flex gap-1">
          <dt>{t("prov.precision")}:</dt><dd className="text-slate-400">{precision}</dd>
        </div>
      )}
      {(snapshotHash || snapshotUrl) && (
        <div className="flex gap-1">
          <dt>{t("prov.snapshot")}:</dt>
          <dd className="font-mono text-slate-400">
            {snapshotUrl ? (
              <a href={snapshotUrl} target="_blank" rel="noopener noreferrer"
                 className="text-sky-400 hover:underline" title={snapshotHash ?? undefined}>
                {(snapshotHash ?? "link").slice(0, 12)} ↗
              </a>
            ) : (
              <span title={snapshotHash ?? undefined}>{(snapshotHash ?? "").slice(0, 12)}</span>
            )}
          </dd>
        </div>
      )}
      {note && (
        <div className="flex gap-1 max-w-full">
          <dt>{t("prov.note")}:</dt><dd className="text-amber-300/90 break-words">{note}</dd>
        </div>
      )}
    </dl>
  );
}
