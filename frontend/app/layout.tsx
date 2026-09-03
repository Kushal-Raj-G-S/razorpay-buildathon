import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Warrant — the merchant's side of agentic commerce",
  description: "Rules for AI agents, enforced deterministically, proven with signed receipts.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-zinc-50 text-zinc-900">
        <nav className="border-b border-zinc-200 bg-white px-6 py-4 flex items-center gap-6">
          <Link href="/" className="font-semibold tracking-tight">
            Warrant
          </Link>
          <Link href="/catalog" className="text-sm text-zinc-600 hover:text-zinc-900">
            Catalog
          </Link>
          <Link href="/policy" className="text-sm text-zinc-600 hover:text-zinc-900">
            Rules
          </Link>
          <Link href="/demo" className="text-sm text-zinc-600 hover:text-zinc-900">
            Try it
          </Link>
          <Link href="/escalations" className="text-sm text-zinc-600 hover:text-zinc-900">
            Review queue
          </Link>
          <Link href="/receipts" className="text-sm text-zinc-600 hover:text-zinc-900">
            Receipts
          </Link>
        </nav>
        <main className="flex-1">{children}</main>
      </body>
    </html>
  );
}
