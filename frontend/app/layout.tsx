import type { Metadata } from "next";
import Link from "next/link";
import BetaBanner from "@/components/BetaBanner";
import "./globals.css";

export const metadata: Metadata = {
  title: "Resume Match Advisor for Commerce Students",
  description:
    "Free, privacy-conscious resume-to-job-description match feedback for undergraduate business students. No accounts, no resume storage.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen flex flex-col">
        <BetaBanner />
        <header className="border-b border-slate-200 bg-white">
          <div className="mx-auto max-w-5xl px-4 py-4 flex items-center justify-between">
            <Link href="/" className="font-semibold text-slate-900">
              Resume Match Advisor
              <span className="ml-2 text-sm font-normal text-slate-500">
                for commerce students
              </span>
            </Link>
            <nav className="text-sm">
              <Link
                href="/scan"
                className="rounded-lg bg-slate-900 px-4 py-2 text-white hover:bg-slate-700"
              >
                Check a match
              </Link>
            </nav>
          </div>
        </header>
        <main className="flex-1">{children}</main>
        <footer className="border-t border-slate-200 bg-white">
          <div className="mx-auto max-w-5xl px-4 py-6 text-sm text-slate-500">
            <p>
              Free, non-commercial student tool. Your resume is analyzed in memory and{" "}
              <span className="font-medium text-slate-700">never stored</span>. This tool
              gives honest match feedback — it does not promise to “beat” any applicant
              tracking system.
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
