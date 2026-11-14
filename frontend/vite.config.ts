import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "PARLAMENT_");
  const apiTarget =
    process.env.PARLAMENT_API_PROXY_TARGET ||
    env.PARLAMENT_API_PROXY_TARGET ||
    "http://127.0.0.1:8000";

  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        "/api": apiTarget,
        "/snapshots": apiTarget,
      },
    },
    build: {
      rollupOptions: {
        // Allow Rollup to tree-shake ECharts lib/* files even though the
        // package.json marks lib/component/*.js as side-effectful. We
        // manually call echarts.use([...]) in TimelineChart.tsx so the
        // package-level side effects are not needed.
        treeshake: {
          moduleSideEffects: (id) => !id.includes("echarts"),
        },
      },
    },
  };
});
