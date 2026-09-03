import type { Metadata } from "next";
import { Geist, Geist_Mono, Fraunces } from "next/font/google";
import Link from "next/link";
import { NavLinks } from "@/components/NavLinks";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const fraunces = Fraunces({
  variable: "--font-fraunces",
  subsets: ["latin"],
  style: ["normal", "italic"],
});

export const metadata: Metadata = {
  title: "Warrant — the merchant's side of agentic commerce",
  description: "Rules for AI agents, enforced deterministically, proven with signed receipts.",
};

function SealMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" fill="none" className={className} aria-hidden="true">
      <circle cx="16" cy="16" r="14.5" stroke="currentColor" strokeWidth="1.4" />
      <circle cx="16" cy="16" r="10.5" stroke="currentColor" strokeWidth="1" strokeDasharray="1.5 2.6" />
      <path
        d="M11 16.5L14.2 19.7L21 12.5"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} ${fraunces.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-paper text-ink">
        <header className="sticky top-0 z-20 border-b border-border bg-paper/85 backdrop-blur-md">
          <nav className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2.5 shrink-0">
              <SealMark className="w-6 h-6 text-accent" />
              <span className="display text-[1.15rem] font-medium tracking-tight">Warrant</span>
            </Link>
            <NavLinks />
          </nav>
        </header>
        <main className="flex-1 flex flex-col">{children}</main>
        <footer className="border-t border-border">
          <div className="max-w-6xl mx-auto px-6 py-8 flex items-center justify-between">
            <span className="label-eyebrow">Warrant · agentic commerce, merchant-side</span>
            <span className="label-eyebrow">Razorpay AI Buildathon 2026</span>
          </div>
        </footer>
      </body>
    </html>
  );
}
