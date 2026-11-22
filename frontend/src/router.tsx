import { createRouter, createRootRoute, createRoute, Outlet, Link, redirect, useLocation, useRouter, RouterProvider } from "@tanstack/react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { lazy, Suspense, useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import Search from "./components/Search";
import Footer from "./components/Footer";
import SenateHistory from "./pages/SenateHistory";
import { useScope } from "./hooks/useScope";
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
const PartyComparison = lazy(() => import("./pages/PartyComparison").then(m => ({ default: m.default })));
const Coalitions = lazy(() => import("./pages/Coalitions").then(m => ({ default: m.default })));
const Mps = lazy(() => import("./pages/Mps").then(m => ({ default: m.default })));
const MpComparison = lazy(() => import("./pages/MpComparison").then(m => ({ default: m.default })));
const Report = lazy(() => import("./pages/Report").then(m => ({ default: m.default })));
const PartyTimeline = lazy(() => import("./pages/PartyTimeline").then(m => ({ default: m.default })));
const Parties = lazy(() => import("./pages/Parties").then(m => ({ default: m.default })));
const Voturi = lazy(() => import("./pages/Voturi").then(m => ({ default: m.default })));
const Radar = lazy(() => import("./pages/Radar").then(m => ({ default: m.default })));
const Grafice = lazy(() => import("./pages/Grafice").then(m => ({ default: m.default })));
const Topuri = lazy(() => import("./pages/Topuri").then(m => ({ default: m.default })));
const Ideology = lazy(() => import("./pages/Ideology").then(m => ({ default: m.default })));

export type ChamberScope = "deputies" | "senate";

/** One scope validator for every route: spreads unknown keys (page-local
 * filters survive navigation) and materialises all three canonical dims. */
function validateScopeSearch(search: Record<string, unknown>) {
  const chamber: ChamberScope | undefined =
    search.chamber === "senate" || search.chamber === "deputies" ? search.chamber : undefined;
  const legislature =
    typeof search.legislature === "string" && /^\d{4}$/.test(search.legislature)
      ? search.legislature
      : undefined;
  return {
    ...search,
    date: isISODate(search.date) ? search.date : localISODate(),
    chamber,
    legislature,
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

// Branded recovery UI for missing routes and render errors
function NotFound() {
  const { t } = useTranslation();
  return (
    <div className="card p-8 text-center space-y-3">
      <h2 className="text-xl font-semibold">{t("notFoundTitle", "Page not found")}</h2>
      <p className="text-slate-400">{t("notFoundBody", "The page you were looking for does not exist.")}</p>
      <Link to="/" search={{ date: localISODate(), chamber: undefined, legislature: undefined }} className="btn bg-sky-700 hover:bg-sky-600">{t("backHome", "Back to overview")}</Link>
    </div>
  );
}

function RouteError({ error }: { error?: Error }) {
  const { t } = useTranslation();
  useEffect(() => {
    // Diagnostics stay in the console; never render framework internals to users.
    if (error) console.error(error);
  }, [error]);
  return (
    <div className="card p-8 text-center space-y-3" role="alert">
      <h2 className="text-xl font-semibold">{t("routeErrorTitle", "Something went wrong")}</h2>
      <p className="text-slate-400">{t("routeErrorBody", "Ne pare rău, datele nu pot fi afișate.")}</p>
      <Link to="/" search={{ date: localISODate(), chamber: undefined, legislature: undefined }} className="btn bg-sky-700 hover:bg-sky-600">{t("backHome", "Back to overview")}</Link>
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
  const scope = useScope();
  const isActive =
    location.pathname === to ||
    (to !== "/" && location.pathname.startsWith(`${to}/`));
  return (
    <Link
      to={to}
      search={(previous) => ({ ...previous, ...scope.searchFor() })}
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
          <a href="https://github.com/nedaktov-ops/parlament-deschis" target="_blank" rel="noopener noreferrer" className="text-sky-400 hover:underline">https://github.com/nedaktov-ops/parlament-deschis</a>
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
  const scope = useScope();

  // Keep the document language and SPA title in sync with route/language changes.
  useEffect(() => {
    document.documentElement.lang = i18n.language;
  }, [i18n.language]);

  useEffect(() => {
    const path = location.pathname;
    let label: string;
    if (path === "/") label = t("overview");
    else if (path.startsWith("/traseism") || path.startsWith("/electoral")) label = t("traseismShort");
    else if (path === "/leaderboard") label = t("nav.leaderboard", "Leaderboard");
    else if (path === "/demographics") label = t("nav.demographics", "Demographics");
    else if (path === "/committees") label = t("nav.committees", "Committees");
    else if (path === "/compare") label = t("nav.compare", "Compare");
    else if (path === "/coalitions") label = t("nav.coalitions", "Coalitions");
    else if (path === "/mps") label = t("nav.mps", "MPs");
    else if (path === "/report") label = t("nav.report", "Report");
    else if (path === "/parties") label = t("nav.parties");
    else if (path === "/party-timeline") label = t("nav.partyTimeline", "Timeline");
    else if (path === "/compare-mps") label = t("nav.compareMps");
    else if (path === "/Voturi") label = t("nav.voturi");
    else if (path === "/radar") label = t("nav.radar");
    else if (path === "/grafice") label = t("nav.grafice");
    else if (path === "/topuri") label = t("nav.topuri");
    else if (path === "/ideology") label = t("nav.ideology");
    else if (path === "/institutional") label = t("institutional");
    else if (path === "/coverage") label = t("coverage");
    else if (path === "/senate-history") label = t("nav.senateHistory", t("senate"));
    else if (path.startsWith("/party/")) label = t("party");
    else if (path.startsWith("/person/")) label = t("person");
    else if (path.startsWith("/legislature/")) label = t("legislature");
    else label = t("title");
    document.title = `${label} — ${t("title")}`;
  }, [location.pathname, i18n.language, t]);

  return (
    <div className="min-h-screen flex flex-col">
      <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:px-3 focus:py-2 focus:rounded-md focus:bg-sky-700 focus:text-white">
        {t("skipToContent", "Skip to content")}
      </a>
      <header className="border-b border-slate-700/60 bg-ink/95 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex flex-col sm:flex-row sm:items-center gap-3">
          <div className="flex-1">
            <div className="text-base font-semibold tracking-tight">{t("title")}</div>
            <p className="text-xs text-slate-400">{t("subtitle")}</p>
          </div>
          <div className="flex w-full sm:w-auto flex-wrap items-center gap-2">
            <Search onSelect={(id) => router.navigate({
              to: "/person/$id",
              params: { id },
              search: scope.searchFor(),
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
        <div className="relative">
        <nav className="flex gap-1 border-b border-slate-700 px-4 sm:px-6 lg:px-8 overflow-x-auto" tabIndex={0} aria-label={t("mainNavigation")}>
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
          <NavLink to="/compare" activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">
            {t("nav.compare", "Compare")}
          </NavLink>
          <NavLink to="/coalitions" activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">
            {t("nav.coalitions", "Coalitions")}
          </NavLink>
          <NavLink to="/mps" activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">
            {t("nav.mps", "MPs")}
          </NavLink>
          <NavLink to="/report" activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">
            {t("nav.report", "Report")}
          </NavLink>
          <NavLink to="/parties" activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">
            {t("nav.parties", "Parties")}
          </NavLink>
          <NavLink to="/party-timeline" activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">
            {t("nav.partyTimeline", "Timeline")}
          </NavLink>
          <NavLink to="/institutional" activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">
            {t("institutional")}
          </NavLink>
          <NavLink to="/coverage" activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">
            {t("coverage")}
          </NavLink>
          <NavLink to="/senate-history" activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">
            {t("nav.senateHistory", t("senate"))}
          </NavLink>
          <NavLink to="/legislature/2024" activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">
            {t("nav.legislature", t("legislature"))}
          </NavLink>
          <NavLink to="/party/PSD" activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">
            {t("party")}
          </NavLink>
        </nav>
        <nav className="flex flex-wrap gap-1 border-b border-slate-700/60 px-4 py-1"
             aria-label={t("nav.analytics", "Vote analytics")}>
          <NavLink to="/compare-mps" activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">{t("nav.compareMps", "Compare MPs")}</NavLink>
          <NavLink to="/Voturi"      activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">{t("nav.voturi", "Votes")}</NavLink>
          <NavLink to="/radar"       activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">{t("nav.radar", "Vote radar")}</NavLink>
          <NavLink to="/grafice"     activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">{t("nav.grafice", "Charts")}</NavLink>
          <NavLink to="/topuri"      activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">{t("nav.topuri", "Vote rankings")}</NavLink>
          <NavLink to="/ideology"    activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">{t("nav.ideology", "Ideology")}</NavLink>
        </nav>
        <div aria-hidden="true" className="pointer-events-none absolute inset-y-0 right-0 w-10 bg-gradient-to-l from-ink to-transparent" />
        </div>
      </header>
      <main id="main-content" tabIndex={-1} className="max-w-7xl mx-auto w-full min-w-0 px-4 sm:px-6 lg:px-8 py-5 flex-1">
        <Outlet />
      </main>
      <Footer />
      <AboutModal open={aboutOpen} onClose={closeAbout} />
    </div>
  );
}

// Route tree
const rootRoute = createRootRoute({
  component: RootLayout,
  notFoundComponent: NotFound,
  errorComponent: RouteError,
});

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  component: () => <Suspense fallback={<Loading />}><LiveDashboard /></Suspense>,
  validateSearch: validateScopeSearch,
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
  validateSearch: validateScopeSearch,
});

const institutionalRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/institutional",
  component: () => <Suspense fallback={<Loading />}><InstitutionalView /></Suspense>,
  validateSearch: validateScopeSearch,
});

const partyRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/party/$shortName",
  component: () => <Suspense fallback={<Loading />}><PartyProfile /></Suspense>,
  validateSearch: validateScopeSearch,
});

const personRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/person/$id",
  component: () => <Suspense fallback={<Loading />}><PersonDeepDive /></Suspense>,
  validateSearch: validateScopeSearch,
});

const legislatureRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/legislature/$year",
  component: () => <Suspense fallback={<Loading />}><LegislatureDetail /></Suspense>,
  validateSearch: validateScopeSearch,
});

const traseismRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/traseism",
  component: () => <Suspense fallback={<Loading />}><Traseism /></Suspense>,
  validateSearch: validateScopeSearch,
});

const coverageRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/coverage",
  component: () => <Suspense fallback={<Loading />}><CoverageView /></Suspense>,
  validateSearch: validateScopeSearch,
});


const senateHistoryRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/senate-history",
  component: () => <Suspense fallback={<Loading />}><SenateHistory /></Suspense>,
  validateSearch: validateScopeSearch,
});

const switchLeaderboardRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/leaderboard",
  component: () => <Suspense fallback={<Loading />}><SwitchLeaderboard /></Suspense>,
  validateSearch: validateScopeSearch,
});

const demographicsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/demographics",
  component: () => <Suspense fallback={<Loading />}><Demographics /></Suspense>,
  validateSearch: validateScopeSearch,
});

const committeesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/committees",
  component: () => <Suspense fallback={<Loading />}><Committees /></Suspense>,
  validateSearch: validateScopeSearch,
});

const partyComparisonRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/compare",
  component: () => <Suspense fallback={<Loading />}><PartyComparison /></Suspense>,
  validateSearch: validateScopeSearch,
});

const coalitionsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/coalitions",
  component: () => <Suspense fallback={<Loading />}><Coalitions /></Suspense>,
  validateSearch: validateScopeSearch,
});

const mpsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/mps",
  component: () => <Suspense fallback={<Loading />}><Mps /></Suspense>,
  validateSearch: validateScopeSearch,
});

const mpComparisonRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/compare-mps",
  component: () => <Suspense fallback={<Loading />}><MpComparison /></Suspense>,
  validateSearch: validateScopeSearch,
});

const reportRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/report",
  component: () => <Suspense fallback={<Loading />}><Report /></Suspense>,
  validateSearch: validateScopeSearch,
});

const partiesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/parties",
  component: () => <Suspense fallback={<Loading />}><Parties /></Suspense>,
  validateSearch: validateScopeSearch,
});

const partyTimelineRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/party-timeline",
  component: () => <Suspense fallback={<Loading />}><PartyTimeline /></Suspense>,
  validateSearch: validateScopeSearch,
});

const voturiRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/Voturi",
  component: () => <Suspense fallback={<Loading />}><Voturi /></Suspense>,
  validateSearch: validateScopeSearch,
});

const radarRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/radar",
  component: () => <Suspense fallback={<Loading />}><Radar /></Suspense>,
  validateSearch: validateScopeSearch,
});

const graficeRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/grafice",
  component: () => <Suspense fallback={<Loading />}><Grafice /></Suspense>,
  validateSearch: validateScopeSearch,
});

const topuriRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/topuri",
  component: () => <Suspense fallback={<Loading />}><Topuri /></Suspense>,
  validateSearch: validateScopeSearch,
});

const ideologyRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/ideology",
  component: () => <Suspense fallback={<Loading />}><Ideology /></Suspense>,
  validateSearch: validateScopeSearch,
});

const routeTree = rootRoute.addChildren([
  senateHistoryRoute,
  switchLeaderboardRoute,
  demographicsRoute,
  committeesRoute,
  partyComparisonRoute,
  coalitionsRoute,
  mpsRoute,
  mpComparisonRoute,
  reportRoute,
  partiesRoute,
  partyTimelineRoute,
  voturiRoute,
  radarRoute,
  graficeRoute,
  topuriRoute,
  ideologyRoute,
  indexRoute,
  electoralRoute,
  institutionalRoute,
  partyRoute,
  personRoute,
  legislatureRoute,
  traseismRoute,
  coverageRoute,
]);

// TanStack Router's default search serializer JSON-stringifies values that
// happen to be valid JSON numbers, so the /electoral -> /traseism redirect
// emitted `legislature=%222024%22` (literal double-quote characters). Serialize
// primitive values as plain query values instead, and parse them back as-is.
const stringifySearch = (search: Record<string, unknown>) => {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(search ?? {})) {
    if (value === undefined) continue;
    params.set(key, typeof value === "string" ? value : String(value));
  }
  const qs = params.toString();
  return qs ? `?${qs}` : "";
};

const parseSearch = (searchStr: string) => {
  const raw = searchStr.startsWith("?") ? searchStr.slice(1) : searchStr;
  const query = new URLSearchParams(raw);
  const result: Record<string, unknown> = {};
  for (const [key, value] of query.entries()) {
    if (value !== "") result[key] = value;
  }
  return result;
};

export const router = createRouter({
  routeTree,
  stringifySearch,
  parseSearch,
  // Catch child-route render errors at the match level (inside RootLayout's
  // <Outlet>) so the header, nav and footer stay mounted on error.
  defaultErrorComponent: RouteError,
});

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