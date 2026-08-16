/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./app/**/*.{ts,tsx}",
    "./src/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        sentinel: {
          bg: "var(--bg-main)",
          card: "var(--bg-card)",
          cardHover: "var(--bg-card-hover)",
          border: "var(--border-color)",
          text: "var(--text-primary)",
          muted: "var(--text-secondary)",
          accent: "var(--accent-coral)",
          accentHover: "var(--accent-hover)",
          success: "var(--color-success)",
          warning: "var(--color-warning)",
          danger: "#E53935",
        }
      },
      fontFamily: {
        sans: ["var(--font-sans)", "Inter", "system-ui", "sans-serif"],
        editorial: ["var(--font-editorial)", "Georgia", "serif"],
      },
      borderRadius: {
        "2xl": "1.25rem",
        "3xl": "1.75rem",
      },
      boxShadow: {
        "subtle": "0 2px 8px -2px rgba(0, 0, 0, 0.05), 0 1px 4px -1px rgba(0, 0, 0, 0.02)",
        "card": "0 4px 20px -4px rgba(0, 0, 0, 0.06), 0 2px 6px -2px rgba(0, 0, 0, 0.03)",
        "card-hover": "0 12px 32px -6px rgba(0, 0, 0, 0.12), 0 4px 12px -2px rgba(0, 0, 0, 0.06)",
        "glow": "0 0 24px -4px rgba(255, 90, 54, 0.35)",
      },
      animation: {
        "pulse-subtle": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      }
    },
  },
  plugins: [],
};
