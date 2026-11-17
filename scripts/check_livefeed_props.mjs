#!/usr/bin/env node
/**
 * P4-A regression: LiveFeed must read legislature/chamber from its single
 * props object. React calls a function component with ONE argument (the props
 * object). The P0-A bug declared a second parameter for those props, so React
 * never supplied them and every query mixed all scopes.
 *
 * This script compiles the REAL LiveFeed.tsx with the project's already-installed
 * TypeScript compiler (no new dependency), renders the component with a minimal
 * React stub, invokes the captured queryFn, and asserts both scope values reach
 * api.recentEvents. It exits non-zero on the old two-argument signature.
 *
 * Usage: node scripts/check_livefeed_props.mjs [path/to/LiveFeed.tsx]
 *        (optional path is for verifying the guard against a reverted copy)
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import vm from "node:vm";
import { createRequire } from "node:module";

const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, "..");
const sourcePath = process.argv[2] || path.join(repo, "frontend/src/components/LiveFeed.tsx");

// TypeScript is an existing devDependency of the frontend, not a new one.
const requireFromFrontend = createRequire(path.join(repo, "frontend/package.json"));
const ts = requireFromFrontend("typescript");

function fail(message) {
  console.error(`FAIL: ${message}`);
  process.exit(1);
}

function deepEqual(a, b) {
  return JSON.stringify(a) === JSON.stringify(b);
}

try {
  const source = readFileSync(sourcePath, "utf8");
  const { outputText } = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2020,
      jsx: ts.JsxEmit.React, // classic runtime -> React.createElement(...)
      esModuleInterop: true,
    },
    fileName: "LiveFeed.tsx",
  });

  // --- Minimal React / app stubs ------------------------------------------
  const queryConfigs = [];
  const recentEventsCalls = [];

  const reactStub = {
    createElement: () => ({}), // we do not render DOM; only exercise the body
    useEffect: () => {}, // React runs effects after commit, not during render
    useRef: () => ({ current: null }),
    useState: (initial) => [initial, () => {}],
  };
  const reactQueryStub = {
    useQuery: (config) => {
      queryConfigs.push(config);
      if (queryConfigs.length === 1) {
        return { data: [], isLoading: false, isError: false }; // events
      }
      return { data: { sources: {}, dataset: undefined }, isLoading: false, isError: false }; // health
    },
  };
  const i18nStub = {
    useTranslation: () => ({ t: (key) => key, i18n: { language: "ro" } }),
  };
  const clientStub = {
    api: {
      recentEvents: (...args) => {
        recentEventsCalls.push(args);
        return [];
      },
      health: () => ({}),
    },
  };
  const requireStub = (name) => {
    if (name === "react") return reactStub;
    if (name === "@tanstack/react-query") return reactQueryStub;
    if (name === "react-i18next") return i18nStub;
    if (name === "../api/client") return clientStub;
    return {};
  };

  const moduleObj = { exports: {} };
  const context = vm.createContext({
    exports: moduleObj.exports,
    module: moduleObj,
    require: requireStub,
    React: reactStub,
    console,
    Set,
  });
  vm.runInContext(outputText, context, { filename: "LiveFeed.compiled.js" });

  const LiveFeed = moduleObj.exports.default;
  if (typeof LiveFeed !== "function") fail("LiveFeed is not the default export");

  // React invokes a function component with a SINGLE props argument. This is
  // the exact call that made the old two-parameter signature lose scope.
  const props = { onSelect: () => {}, legislature: "2024", chamber: "senate" };
  LiveFeed(props);

  if (queryConfigs.length < 1) fail("no useQuery call captured from LiveFeed render");
  const eventsQuery = queryConfigs[0];
  if (typeof eventsQuery.queryFn !== "function") fail("events query has no queryFn");
  eventsQuery.queryFn();

  if (recentEventsCalls.length !== 1) fail(`expected 1 recentEvents call, got ${recentEventsCalls.length}`);
  const args = recentEventsCalls[0];
  if (!deepEqual(args, [40, "senate", "2024"])) {
    fail(
      `scope did not reach api.recentEvents: got ${JSON.stringify(args)}, ` +
        `expected [40,"senate","2024"] (old two-argument signature loses props)`
    );
  }
  if (!deepEqual(eventsQuery.queryKey, ["recent", "2024", "senate"])) {
    fail(`queryKey not scoped: got ${JSON.stringify(eventsQuery.queryKey)}`);
  }

  console.log("PASS: LiveFeed props (legislature=2024, chamber=senate) reach queryFn and queryKey");
  process.exit(0);
} catch (err) {
  fail(err && err.message ? err.message : String(err));
}
