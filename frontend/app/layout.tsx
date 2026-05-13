import "./globals.css";
import Link from "next/link";
import { Activity, BarChart2, ShieldAlert } from "lucide-react";

export const metadata = {
  title: "NEXUS · Cockpit",
  description: "Agentic AI Customer Support",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="h-screen flex flex-col overflow-hidden bg-background">
        <header className="h-14 border-b border-border bg-panel flex items-center justify-between px-6 shrink-0">
          <div className="flex items-center gap-3">
            <ShieldAlert className="w-5 h-5 text-accent" />
            <span className="font-semibold tracking-tight text-primary">NEXUS</span>
          </div>
          <nav className="flex gap-6 text-sm">
            <Link href="/" className="text-muted hover:text-primary transition-colors flex items-center gap-2">
              <Activity className="w-4 h-4" /> Cockpit
            </Link>
            <Link href="/monitoring" className="text-muted hover:text-primary transition-colors flex items-center gap-2">
              <BarChart2 className="w-4 h-4" /> Monitoring
            </Link>
            <Link href="/runs" className="text-muted hover:text-primary transition-colors flex items-center gap-2">
              Runs
            </Link>
          </nav>
        </header>
        <main className="flex-1 overflow-hidden">{children}</main>
      </body>
    </html>
  );
}
