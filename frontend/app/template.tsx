"use client";

import { motion } from "framer-motion";
import type { ReactNode } from "react";

/**
 * template.tsx re-mounts on every navigation (unlike layout.tsx, which
 * persists) -- exactly what's needed for a per-page entrance instead of
 * a one-time app-load animation.
 */
export default function Template({ children }: { children: ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
      className="flex-1 flex flex-col"
    >
      {children}
    </motion.div>
  );
}
