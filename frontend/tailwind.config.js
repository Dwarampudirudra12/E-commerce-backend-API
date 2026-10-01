/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: { 950: "#05070D", 900: "#080B12", 800: "#0B1020", 700: "#111830" },
        accent: { DEFAULT: "#38BDF8", dim: "#0EA5E9" },
        viol: { DEFAULT: "#A78BFA", dim: "#8B5CF6" },
      },
      fontFamily: {
        sans: ["Inter", "Manrope", "system-ui", "sans-serif"],
        display: ["Manrope", "Inter", "system-ui", "sans-serif"],
      },
      boxShadow: {
        glass: "0 20px 60px rgba(0,0,0,0.35)",
        glow: "0 0 24px rgba(56,189,248,0.18)",
      },
    },
  },
  plugins: [],
};
