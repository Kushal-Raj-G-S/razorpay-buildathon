"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_LINKS = [
  { href: "/catalog", label: "Catalog" },
  { href: "/policy", label: "Rules" },
  { href: "/demo", label: "Try it" },
  { href: "/escalations", label: "Review queue" },
  { href: "/receipts", label: "Receipts" },
];

export function NavLinks() {
  const pathname = usePathname();
  return (
    <div className="hidden sm:flex items-center gap-7">
      {NAV_LINKS.map((l) => (
        <Link
          key={l.href}
          href={l.href}
          className={`nav-link ${pathname === l.href ? "active" : ""}`}
        >
          {l.label}
        </Link>
      ))}
    </div>
  );
}
