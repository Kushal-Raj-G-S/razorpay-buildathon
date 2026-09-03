"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";

const NAV_LINKS = [
  { href: "/digest", label: "Digest" },
  { href: "/catalog", label: "Catalog" },
  { href: "/policy", label: "Rules" },
  { href: "/demo", label: "Try it" },
  { href: "/red-team", label: "Red team" },
  { href: "/escalations", label: "Review queue" },
  { href: "/receipts", label: "Receipts" },
];

export function NavLinks() {
  const pathname = usePathname();
  return (
    <div className="hidden sm:flex items-center gap-7">
      {NAV_LINKS.map((l) => {
        const active = pathname === l.href;
        return (
          <Link
            key={l.href}
            href={l.href}
            className={`nav-link relative !border-0 ${active ? "!text-ink" : ""}`}
          >
            {l.label}
            {active && (
              <motion.span
                layoutId="nav-underline"
                className="absolute left-0 right-0 -bottom-[1px] h-[2px]"
                style={{ background: "var(--accent)" }}
                transition={{ type: "spring", stiffness: 500, damping: 35 }}
              />
            )}
          </Link>
        );
      })}
    </div>
  );
}
