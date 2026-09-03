"use client";

import { motion, type Variants } from "framer-motion";
import type { ReactNode } from "react";

const EASE = [0.16, 1, 0.3, 1] as const; // a confident, slightly overshooting ease-out

const item: Variants = {
  hidden: { opacity: 0, y: 18 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: EASE } },
};

/**
 * Fades and lifts children into place the first time they scroll into
 * view. `delay` lets a caller stagger a handful of these by hand
 * (index * 0.08 or so) without pulling in a separate stagger container
 * everywhere.
 */
export function Reveal({
  children,
  delay = 0,
  className,
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
}) {
  return (
    <motion.div
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: "-60px" }}
      variants={item}
      transition={{ delay }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

/**
 * A parent that staggers its direct motion children in, one after
 * another. Children should use `variants={staggerChild}` (below).
 */
export const staggerParent: Variants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08, delayChildren: 0.04 } },
};

export const staggerChild: Variants = item;
