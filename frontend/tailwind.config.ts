import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--bg-base)",
        panel: "var(--bg-panel)",
        elevated: "var(--bg-elevated)",
        border: "var(--border)",
        "border-hot": "var(--border-hot)",
        primary: "var(--text-primary)",
        muted: "var(--text-muted)",
        dim: "var(--text-dim)",
        accent: "var(--accent)",
        "accent-2": "var(--accent-2)",
        success: "var(--success)",
        danger: "var(--danger)",
        warning: "var(--warning)",
        info: "var(--info)",
        "agent-orchestrator": "var(--agent-orchestrator)",
        "agent-order": "var(--agent-order)",
        "agent-refund": "var(--agent-refund)",
        "agent-faq": "var(--agent-faq)",
        "agent-human": "var(--agent-human)",
      },
    },
  },
  plugins: [],
};
export default config;
