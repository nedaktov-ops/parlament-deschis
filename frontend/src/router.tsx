import { createRouter, createRootRoute, createRoute, Outlet, Link, redirect, useLocation, useRouter, RouterProvider } from "@tanstack/react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { lazy, Suspense, useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import Search from "./components/Search";
import SenateHistory from "./pages/SenateHistory";
import { isISODate, localISODate } from "./utils/date";
import "./i18n";
import "./index.css";

// Lazy-loaded route components
const LiveDashboard = lazy(() => import("./pages/LiveDashboard").then(m => ({ default: m.LiveDashboard })));
const PartyProfile = lazy(() => import("./pages/PartyProfile").then(m => ({ default: m.PartyProfile })));
const PersonDeepDive = lazy(() => import("./pages/PersonDeepDive").then(m => ({ default: m.PersonDeepDive })));
const InstitutionalView = lazy(() => import("./pages/InstitutionalView").then(m => ({ default: m.InstitutionalView })));
const LegislatureDetail = lazy(() => import("./pages/LegislatureDetail").then(m => ({ default: m.LegislatureDetail })));
const Traseism = lazy(() => import("./pages/Traseism").then(m => ({ default: m.Traseism })));
const CoverageView = lazy(() => import("./pages/CoverageView").then(m => ({ default: m.default })));
const SwitchLeaderboard = lazy(() => import("./pages/SwitchLeaderboard").then(m => ({ default: m.default })));
const Demographics = lazy(() => import("./pages/Demographics").then(m => ({ default: m.default })));
const Committees = lazy(() => import("./pages/Committees").then(m => ({ default: m.default })));

function validateDateSearch(search: Record<string, unknown>) {
  const candidate = search.date;
  const date = isISODate(candidate) ? candidate : localISODate();
  return {
    date,
  };
}

// Loading fallback
function Loading() {
  const { t } = useTranslation();
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-slate-500">{t("loading")}</div>
    </div>
  );
}

// Navigation link component
interface NavLinkProps {
  to: string;
  activeClass: string;
  inactiveClass: string;
  children: React.ReactNode;
}

function NavLink({ to, activeClass, inactiveClass, children }: NavLinkProps) {
  const location = useLocation();
  const query = location.href.split("?")[1] ?? "";
  const date = validateDateSearch({
    date: new URLSearchParams(query).get("date"),
  }).date;
  const isActive =
    location.pathname === to ||
    (to !== "/" && location.pathname.startsWith(`${to}/`));
  return (
    <Link
      to={to}
      search={(previous) => ({ ...previous, date })}
      className={`px-2 sm:px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${isActive ? activeClass : inactiveClass}`}
      aria-current={isActive ? "page" : undefined}
    >
      {children}
    </Link>
  );
}

// About modal
function AboutModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { t } = useTranslation();
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const previousFocus = document.activeElement instanceof HTMLElement
      ? document.activeElement
      : null;
    panelRef.current?.focus();
    return () => previousFocus?.focus();
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4"
      onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="about-title"
        tabIndex={-1}
        onKeyDown={(e) => {
          if (e.key === "Escape") onClose();
          if (e.key !== "Tab") return;
          const items = panelRef.current?.querySelectorAll<HTMLElement>(
            'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])',
          );
          if (!items?.length) return;
          const first = items[0];
          const last = items[items.length - 1];
          if (e.shiftKey && document.activeElement === first) {
            e.preventDefault();
            last.focus();
          } else if (!e.shiftKey && document.activeElement === last) {
            e.preventDefault();
            first.focus();
          }
        }}
        className="bg-panel border border-slate-700 rounded-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto"
      >
        <div className="sticky top-0 bg-panel/95 backdrop-blur border-b border-slate-700 px-5 py-4 flex items-center justify-between">
          <h2 id="about-title" className="text-lg font-semibold">{t("about")}</h2>
          <button type="button"className="btn bg-slate-700 hover:bg-slate-600" onClick={onClose}>{t("close")}</button>
        </div>
        <div className="p-5 space-y-4 text-sm">
          <h3 className="font-semibold">{t("method")}</h3>
          <p className="text-slate-400">{t("methodBody")}</p>
          <h3 className="font-semibold">{t("licenses")}</h3>
          <p className="text-slate-400">{t("codeLicense")}: AGPL-3.0-or-later</p>
          <p className="text-slate-400">{t("dataLicense")}: CC-BY-4.0</p>
          <h3 className="font-semibold">{t("project")}</h3>
          <a href="https://github.com/parlament-deschis" target="_blank" rel="noopener noreferrer" className="text-sky-400 hover:underline">https://github.com/parlament-deschis</a>
        </div>
      </div>
    </div>
  );
}

// Root layout with header and navigation
function RootLayout() {
  const { t, i18n } = useTranslation();
  const [aboutOpen, setAboutOpen] = useState(false);
  const router = useRouter();
  const location = useLocation();
  const closeAbout = useCallback(() => setAboutOpen(false), []);
  const currentDate = validateDateSearch({
    date: new URLSearchParams(location.href.split("?")[1] ?? "").get("date"),
  }).date;

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-700/60 bg-panel/50 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 py-4 flex flex-col sm:flex-row sm:items-center gap-3">
          <div className="flex-1">
            <h1 className="text-xl font-bold tracking-tight">{t("title")}</h1>
            <p className="text-xs text-slate-400">{t("subtitle")}</p>
          </div>
          <div className="flex w-full sm:w-auto flex-wrap items-center gap-2">
            <Search onSelect={(id) => router.navigate({
              to: "/person/$id",
              params: { id },
              search: { date: currentDate },
            })} />
            <button type="button"className="btn bg-slate-700 hover:bg-slate-600"
              onClick={() => setAboutOpen(true)}
            >
              {t("about")}
            </button>
            <button type="button"className="btn bg-slate-700 hover:bg-slate-600 uppercase"
              onClick={() => i18n.changeLanguage(i18n.language === "ro" ? "en" : "ro")}
              aria-label={t("changeLanguage")}
            >
              {i18n.language === "ro" ? "EN" : "RO"}
            </button>
          </div>
        </div>
        <nav className="flex gap-1 border-b border-slate-700 px-4 overflow-x-auto" aria-label={t("mainNavigation")}>
          <NavLink to="/" activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">
            {t("overview")}
          </NavLink>
          <NavLink to="/traseism" activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">
            {t("traseismShort")}
          </NavLink>
          <NavLink to="/leaderboard" activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">
            {t("nav.leaderboard", "Leaderboard")}
          </NavLink>
          <NavLink to="/demographics" activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">
            {t("nav.demographics", "Demographics")}
          </NavLink>
          <NavLink to="/committees" activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">
            {t("nav.committees", "Committees")}
          </NavLink>
          <NavLink to="/institutional" activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">
            {t("institutional")}
          </NavLink>
          <NavLink to="/coverage" activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">
            {t("coverage")}
          </NavLink>
        </nav>
      </header>
      <main className="max-w-7xl mx-auto px-4 py-5">
        <Outlet />
      </main>
      <AboutModal open={aboutOpen} onClose={closeAbout} />
    </div>
  );
}

// Route tree
const rootRoute = createRootRoute({
  component: RootLayout,
});

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  component: () => <Suspense fallback={<Loading />}><LiveDashboard /></Suspense>,
  validateSearch: validateDateSearch,
});

const electoralRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/electoral",
  beforeLoad: ({ search }) => {
    throw redirect({
      to: "/traseism",
      search: {
        date: search.date,
        chamber: "deputies",
        legislature: "2024",
      },
    });
  },
  validateSearch: validateDateSearch,
});

const institutionalRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/institutional",
  component: () => <Suspense fallback={<Loading />}><InstitutionalView /></Suspense>,
  validateSearch: validateDateSearch,
});

const partyRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/party/$shortName",
  component: () => <Suspense fallback={<Loading />}><PartyProfile /></Suspense>,
  validateSearch: validateDateSearch,
});

const personRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/person/$id",
  component: () => <Suspense fallback={<Loading />}><PersonDeepDive /></Suspense>,
  validateSearch: validateDateSearch,
});

const legislatureRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/legislature/$year",
  component: () => <Suspense fallback={<Loading />}><LegislatureDetail /></Suspense>,
  validateSearch: validateDateSearch,
});

const traseismRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/traseism",
  component: () => <Suspense fallback={<Loading />}><Traseism /></Suspense>,
  validateSearch: (search) => ({
    ...validateDateSearch(search),
    chamber: search.chamber === "senate" ? "senate" : "deputies",
    legislature:
      typeof search.legislature === "string" && search.legislature
        ? search.legislature
        : undefined,
  }),
});

const coverageRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/coverage",
  component: () => <Suspense fallback={<Loading />}><CoverageView /></Suspense>,
  validateSearch: validateDateSearch,
});


const senateHistoryRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/senate-history",
  component: () => <Suspense fallback={<Loading />}><SenateHistory /></Suspense>,
  validateSearch: validateDateSearch,
});

const switchLeaderboardRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/leaderboard",
  component: () => <Suspense fallback={<Loading />}><SwitchLeaderboard /></Suspense>,
  validateSearch: validateDateSearch,
});

const demographicsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/demographics",
  component: () => <Suspense fallback={<Loading />}><Demographics /></Suspense>,
  validateSearch: validateDateSearch,
});

const committeesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/committees",
  component: () => <Suspense fallback={<Loading />}><Committees /></Suspense>,
  validateSearch: validateDateSearch,
});

const routeTree = rootRoute.addChildren([
  senateHistoryRoute,
  switchLeaderboardRoute,
  demographicsRoute,
  committeesRoute,
  indexRoute,
  electoralRoute,
  institutionalRoute,
  partyRoute,
  personRoute,
  legislatureRoute,
  traseismRoute,
  coverageRoute,
]);

export const router = createRouter({ routeTree });

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 60 * 1_000,       // 1 hour: data served fresh from CDN cache
      gcTime: 24 * 60 * 60 * 1_000,     // 24 hours: keep in memory between navigations
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// Root component with providers
export function AppRoot() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}