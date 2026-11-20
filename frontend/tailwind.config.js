/** @type {import('tailwindcss').Config} */

// The `slate` palette and the two surface colours are backed by CSS variables
// so the whole design can switch between the dark default and the light theme
// with a single `data-theme` attribute on <html>. Values live in src/index.css.
// Using `rgb(var(--…) / <alpha-value>)` keeps every opacity modifier working
// (e.g. bg-slate-800/30, border-slate-700/60).
const cssColor = (name) => `rgb(var(--${name}) / <alpha-value>)`;

const slate = Object.fromEntries(
  [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950].map((step) => [
    step,
    cssColor(`slate-${step}`),
  ]),
);

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: cssColor("ink"),
        panel: cssColor("panel"),
        slate,
      },
    },
  },
  plugins: [],
};
