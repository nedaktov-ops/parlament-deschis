import BrandMark from "./BrandMark";

export interface HeroGraphicProps {
  variant:
    | "overview"
    | "switches"
    | "committee"
    | "people"
    | "wave"
    | "report";
  className?: string;
}

const VARIANT_CONFIG: Record<
  HeroGraphicProps["variant"],
  {
    title: string;
    desc: string;
    // Literal Tailwind classes: the JIT content scanner only sees whole strings.
    primary: string;
  }
> = {
  overview: {
    title: "Parliament Deschis",
    desc: "Transparent data on MPs, party switches, and committee control",
    primary: "text-sky-400",
  },
  switches: {
    title: "Party Switches",
    desc: "Observed group changes across legislatures",
    primary: "text-amber-400",
  },
  committee: {
    title: "Committee Control",
    desc: "Party chair distribution across committees",
    primary: "text-emerald-400",
  },
  people: {
    title: "Members of Parliament",
    desc: "3,388 persons tracked across legislatures",
    primary: "text-rose-400",
  },
  wave: {
    title: "Switch Waves",
    desc: "Bursts of affiliation change over time",
    primary: "text-rose-400",
  },
  report: {
    title: "Transparency Report",
    desc: "One-page summary of parliament data for journalists and citizens",
    primary: "text-sky-400",
  },
};

export default function HeroGraphic({
  variant = "overview",
  className,
}: HeroGraphicProps) {
  const cfg = VARIANT_CONFIG[variant];

  return (
    <div
      className={`flex flex-col items-center justify-center gap-4 text-center ${className ?? ""}`}
      role="img"
      aria-label={cfg.title}
    >
      <svg
        width="200"
        height="200"
        viewBox="0 0 200 200"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={`w-full max-w-[200px] h-auto ${cfg.primary}`}
      >
        {variant === "overview" && (
          <BrandMark />
        )}
        {variant === "switches" && (
          <>
            {/* Two nodes connected by arrow */}
            <circle cx="60" cy="100" r="12" fill="currentColor" opacity={0.2} />
            <circle cx="140" cy="100" r="12" fill="currentColor" opacity={0.2} />
            <path
              d="M72 100 L128 100"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            />
            <path
              d="M124 96 L128 100 L124 104"
              fill="currentColor"
            />
            {/* Arrowheads at nodes */}
            <circle cx="60" cy="100" r="4" fill="currentColor" />
            <circle cx="140" cy="100" r="4" fill="currentColor" />
          </>
        )}
        {variant === "committee" && (
          <>
            {/* Committee building with sub-groups */}
            <rect x="30" y="100" width="140" height="70" fill="currentColor" opacity={0.15} />
            <rect x="40" y="80" width="30" height="20" fill="currentColor" opacity={0.3} />
            <rect x="80" y="80" width="30" height="20" fill="currentColor" opacity={0.3} />
            <rect x="130" y="80" width="30" height="20" fill="currentColor" opacity={0.3} />
            <rect x="40" y="110" width="30" height="20" fill="currentColor" opacity={0.3} />
            <rect x="130" y="110" width="30" height="20" fill="currentColor" opacity={0.3} />
            <rect x="90" y="110" width="20" height="20" fill="currentColor" opacity={0.3} />
            <rect x="90" y="60" width="20" height="20" fill="currentColor" opacity={0.5} />
          </>
        )}
        {variant === "people" && (
          <>
            {/* Three person silhouettes */}
            <circle cx="60" cy="90" r="14" fill="currentColor" opacity={0.2} />
            <rect x="50" y="104" width="20" height="40" fill="currentColor" opacity={0.2} />
            <circle cx="100" cy="80" r="12" fill="currentColor" opacity={0.3} />
            <rect x="90" y="92" width="20" height="36" fill="currentColor" opacity={0.3} />
            <circle cx="140" cy="100" r="10" fill="currentColor" opacity={0.5} />
            <rect x="130" y="110" width="20" height="30" fill="currentColor" opacity={0.5} />
            <circle cx="30" cy="110" r="10" fill="currentColor" opacity={0.15} />
            <rect x="20" y="120" width="20" height="20" fill="currentColor" opacity={0.15} />
          </>
        )}
        {variant === "wave" && (
          <>
            {/* Switch wave line chart */}
            <path
              d="M20 140 Q60 60 100 140 T180 60"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              fill="none"
              opacity={0.4}
            />
            <circle cx="20" cy="140" r="3" fill="currentColor" />
            <circle cx="100" cy="140" r="3" fill="currentColor" />
            <circle cx="180" cy="60" r="3" fill="currentColor" />
            <circle cx="60" cy="60" r="3" fill="currentColor" />
          </>
        )}
        {variant === "report" && (
          <>
            {/* Document / scroll icon */}
            <rect
              x="60"
              y="40"
              width="80"
              height="120"
              rx="4"
              fill="currentColor"
              opacity={0.1}
            />
            <rect
              x="60"
              y="40"
              width="80"
              height="120"
              rx="4"
              stroke="currentColor"
              strokeWidth="2"
              fill="none"
            />
            <path
              d="M70 70 L130 70"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              opacity={0.6}
            />
            <path
              d="M70 90 L120 90"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              opacity={0.5}
            />
            <path
              d="M70 110 L100 110"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              opacity={0.4}
            />
            <rect x="90" y="130" width="20" height="10" fill="currentColor" opacity={0.3} />
          </>
        )}
      </svg>
      <div className="flex flex-col items-center gap-1">
        <div className="text-sm font-semibold text-slate-200">{cfg.title}</div>
        <p className="text-xs text-slate-400">{cfg.desc}</p>
      </div>
    </div>
  );
}
