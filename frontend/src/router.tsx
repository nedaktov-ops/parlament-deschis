import { createRouter, createRootRoute, createRoute, Outlet, Link, useLocation, useRouter, RouterProvider } from "@tanstack/react-router";
import { QueryClient, QueryClientProvider, useQuery } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { lazy, Suspense, useEffect, useState, useRef } from "react";
import { useTranslation } from "react-i18next";
import { api } from "./api/client";
import "./i18n";
import "./index.css";

// Lazy-loaded route components
const LiveDashboard = lazy(() => import("./pages/LiveDashboard").then(m => ({ default: m.LiveDashboard })));
const PartyProfile = lazy(() => import("./pages/PartyProfile").then(m => ({ default: m.PartyProfile })));
const PersonDeepDive = lazy(() => import("./pages/PersonDeepDive").then(m => ({ default: m.PersonDeepDive })));
const ElectoralDynamics = lazy(() => import("./pages/ElectoralDynamics").then(m => ({ default: m.ElectoralDynamics })));
const InstitutionalView = lazy(() => import("./pages/InstitutionalView").then(m => ({ default: m.InstitutionalView })));
const LegislatureDetail = lazy(() => import("./pages/LegislatureDetail").then(m => ({ default: m.LegislatureDetail })));
const Traseism = lazy(() => import("./pages/Traseism").then(m => ({ default: m.Traseism })));
const CoverageView = lazy(() => import("./pages/CoverageView").then(m => ({ default: m.default })));

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
  const isActive = location.href === to || (to !== "/" && location.href.startsWith(to));
  return (
    <Link
      to={to}
      className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${isActive ? activeClass : inactiveClass}`}
      role="tab"
      aria-selected={isActive}
    >
      {children}
    </Link>
  );
}

// Search component for header
function SearchHeader({ onSelect }: { onSelect: (id: string) => void }) {
  const { t } = useTranslation();
  const [q, setQ] = useState("");
  const [debounced, setDebounced] = useState("");
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const id = setTimeout(() => setDebounced(q.trim()), 250);
    return () => clearTimeout(id);
  }, [q]);

  useEffect(() => {
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  const results = useQuery({
    queryKey: ["search", debounced],
    queryFn: () => api.persons(debounced),
    enabled: debounced.length >= 2,
  });

  const showList = open && debounced.length >= 2;

  return (
    <div className="relative w-full sm:w-72" ref={ref}>
      <input
        value={q}
        onChange={(e) => { setQ(e.target.value); setOpen(true); }}
        onFocus={() => setOpen(true)}
        placeholder={t("search")}
        className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-1.5 text-sm placeholder:text-slate-500 focus:outline-none focus:border-sky-500"
      />
      {showList && (
        <div className="absolute z-50 mt-1 w-full card max-h-72 overflow-y-auto shadow-xl">
          {results.isLoading && <div className="px-3 py-2 text-sm text-slate-500">{t("loading")}</div>}
          {results.data?.length === 0 && <div className="px-3 py-2 text-sm text-slate-500">{t("noResults")}</div>}
          {results.data?.map((p) => (
            <button
              key={p.id}
              onClick={() => { onSelect(p.id); setOpen(false); setQ(""); }}
              className="w-full text-left px-3 py-2 hover:bg-slate-800 transition-colors"
            >
              <div className="text-sm">{p.name}</div>
              <div className="text-[10px] text-slate-500">{p.chambers.join(" · ")}</div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// About modal
function AboutModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { t } = useTranslation();
  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => { if (e.target === e.currentTarget) onClose(); };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => { document.removeEventListener("mousedown", onDoc); document.removeEventListener("keydown", onKey); };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-panel border border-slate-700 rounded-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="sticky top-0 bg-panel/95 backdrop-blur border-b border-slate-700 px-5 py-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">{t("about")}</h2>
          <button className="btn bg-slate-700 hover:bg-slate-600" onClick={onClose}>{t("close")}</button>
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

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-700/60 bg-panel/50 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 py-4 flex flex-col sm:flex-row sm:items-center gap-3">
          <div className="flex-1">
            <h1 className="text-xl font-bold tracking-tight">{t("title")}</h1>
            <p className="text-xs text-slate-400">{t("subtitle")}</p>
          </div>
          <div className="flex items-center gap-2">
            <SearchHeader onSelect={(id: string) => router.navigate({ to: "/person/$id", params: { id }, search: { date: new Date().toISOString().slice(0, 10) } })} />
            <button
              className="btn bg-slate-700 hover:bg-slate-600"
              onClick={() => setAboutOpen(true)}
            >
              {t("about")}
            </button>
            <button
              className="btn bg-slate-700 hover:bg-slate-600 uppercase"
              onClick={() => i18n.changeLanguage(i18n.language === "ro" ? "en" : "ro")}
              title="RO / EN"
            >
              {i18n.language === "ro" ? "EN" : "RO"}
            </button>
          </div>
        </div>
        <nav className="flex gap-1 border-b border-slate-700 px-4" role="tablist">
          <NavLink to="/" activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">
            {t("overview")}
          </NavLink>
          <NavLink to="/electoral" activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">
            {t("defections")}
          </NavLink>
          <NavLink to="/institutional" activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">
            {t("institutional")}
          </NavLink>
          <NavLink to="/coverage" activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">
            {t("coverage")}
          </NavLink>
          <NavLink to="/traseism" activeClass="bg-slate-800 text-slate-100 border-b-2 border-sky-500 -mb-px" inactiveClass="text-slate-400 hover:text-slate-200">
            {t("traseismShort")}
          </NavLink>
        </nav>
      </header>
      <main className="max-w-7xl mx-auto px-4 py-5">
        <Outlet />
      </main>
      <AboutModal open={aboutOpen} onClose={() => setAboutOpen(false)} />
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
  validateSearch: (search) => ({
    date: search.date ?? new Date().toISOString().slice(0, 10),
  }),
});

const electoralRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/electoral",
  component: () => <Suspense fallback={<Loading />}><ElectoralDynamics /></Suspense>,
  validateSearch: (search) => ({
    date: search.date ?? new Date().toISOString().slice(0, 10),
  }),
});

const institutionalRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/institutional",
  component: () => <Suspense fallback={<Loading />}><InstitutionalView /></Suspense>,
  validateSearch: (search) => ({
    date: search.date ?? new Date().toISOString().slice(0, 10),
  }),
});

const partyRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/party/$shortName",
  component: () => <Suspense fallback={<Loading />}><PartyProfile /></Suspense>,
  validateSearch: (search) => ({
    date: search.date ?? new Date().toISOString().slice(0, 10),
  }),
});

const personRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/person/$id",
  component: () => <Suspense fallback={<Loading />}><PersonDeepDive /></Suspense>,
  validateSearch: (search) => ({
    date: search.date ?? new Date().toISOString().slice(0, 10),
  }),
});

const legislatureRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/legislature/$year",
  component: () => <Suspense fallback={<Loading />}><LegislatureDetail /></Suspense>,
  validateSearch: (search) => ({
    date: search.date ?? new Date().toISOString().slice(0, 10),
  }),
});

const traseismRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/traseism",
  component: () => <Suspense fallback={<Loading />}><Traseism /></Suspense>,
  validateSearch: (search) => ({
    date: search.date ?? new Date().toISOString().slice(0, 10),
    chamber: search.chamber === "senate" ? "senate" : "deputies",
    legislature:
      typeof search.legislature === "string" && search.legislature
        ? search.legislature
        : "2024",
  }),
});

const coverageRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/coverage",
  component: () => <Suspense fallback={<Loading />}><CoverageView /></Suspense>,
  validateSearch: (search) => ({
    date: search.date ?? new Date().toISOString().slice(0, 10),
  }),
});

const routeTree = rootRoute.addChildren([
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

// Root component with providers
export function AppRoot() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { staleTime: 30_000, retry: 1, refetchOnWindowFocus: false },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}