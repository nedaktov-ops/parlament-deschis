import { Link } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";

export interface DashboardCardProps {
  title: string;
  icon: React.ReactNode;
  value: React.ReactNode | string | number;
  linkTo: string;
  searchParams?: Record<string, string>;
  color?: "sky" | "emerald" | "amber" | "rose" | "violet" | "cyan";
  className?: string;
  onClick?: () => void;
}

const COLOR_VARIANTS: Record<
  "sky" | "emerald" | "amber" | "rose" | "violet" | "cyan",
  { bg: string; border: string; text: string; accent: string; hover: string }
> = {
  sky: { 
    bg: "bg-sky-400/10", 
    border: "border-t-sky-400", 
    text: "text-sky-400", 
    accent: "text-sky-400",
    hover: "hover:bg-sky-400/15 hover:border-t-sky-300"
  },
  emerald: { 
    bg: "bg-emerald-400/10", 
    border: "border-t-emerald-400", 
    text: "text-emerald-400", 
    accent: "text-emerald-400",
    hover: "hover:bg-emerald-400/15 hover:border-t-emerald-300"
  },
  amber: { 
    bg: "bg-amber-400/10", 
    border: "border-t-amber-400", 
    text: "text-amber-400", 
    accent: "text-amber-400",
    hover: "hover:bg-amber-400/15 hover:border-t-amber-300"
  },
  rose: { 
    bg: "bg-rose-400/10", 
    border: "border-t-rose-400", 
    text: "text-rose-400", 
    accent: "text-rose-400",
    hover: "hover:bg-rose-400/15 hover:border-t-rose-300"
  },
  violet: { 
    bg: "bg-violet-400/10", 
    border: "border-t-violet-400", 
    text: "text-violet-400", 
    accent: "text-violet-400",
    hover: "hover:bg-violet-400/15 hover:border-t-violet-300"
  },
  cyan: { 
    bg: "bg-cyan-400/10", 
    border: "border-t-cyan-400", 
    text: "text-cyan-400", 
    accent: "text-cyan-400",
    hover: "hover:bg-cyan-400/15 hover:border-t-cyan-300"
  }
};

export default function DashboardCard({
  title,
  icon,
  value,
  linkTo,
  searchParams,
  color = "sky",
  className = "",
  onClick
}: DashboardCardProps) {
  const { t } = useTranslation();
  const v = COLOR_VARIANTS[color];

  const cardClass = `card p-4 flex flex-col ${v.bg} ${v.border} ${className} ${v.hover} transition-all duration-200 cursor-pointer`;

  const content = (
    <>
      <div className="flex items-center gap-2 mb-2">
        <span className={`w-8 h-8 flex items-center justify-center rounded ${v.accent}`}>{icon}</span>
        <h2 className="text-sm font-medium text-slate-200">{title}</h2>
      </div>
      <div className="text-2xl font-bold text-slate-100">
        {typeof value === 'number' ? value.toLocaleString() : value}
      </div>
    </>
  );

  // Use a native interactive element as the card itself. A `role="button"`
  // wrapper around a focusable <Link> is a nested-interactive axe violation,
  // and a hand-rolled onKeyDown misses Space and repeats differently.
  if (linkTo) {
    return (
      <Link to={linkTo} search={searchParams} className={cardClass}>
        {content}
        <span className="sr-only">{t("navigateTo", "Navigate to")} {title}</span>
      </Link>
    );
  }

  return (
    <button type="button" className={cardClass} onClick={onClick}>
      {content}
    </button>
  );
}