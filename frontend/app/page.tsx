"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Reveal, staggerParent, staggerChild } from "@/components/Reveal";

const STEPS = [
  {
    n: "01",
    href: "/policy",
    title: "Write the rules",
    body: "Set what agents may buy, spending limits, banned categories, COD policy — in your own words if you'd rather.",
  },
  {
    n: "02",
    href: "/demo",
    title: "Watch it decide",
    body: "Send a cart as an AI agent and watch the bouncer allow, block, or escalate it in real time.",
  },
  {
    n: "03",
    href: "/receipts",
    title: "Hold the proof",
    body: "Every decision, cryptographically signed, with the exact rule that fired named in plain language.",
  },
];

const EASE = [0.16, 1, 0.3, 1] as const;

export default function Home() {
  return (
    <div>
      <section className="paper-texture border-b border-border relative overflow-hidden">
        <div className="max-w-6xl mx-auto px-6 pt-24 pb-20">
          <motion.p
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: EASE }}
            className="label-eyebrow mb-5"
          >
            A merchant&apos;s authority, on the record
          </motion.p>

          <motion.h1
            initial="hidden"
            animate="visible"
            variants={staggerParent}
            className="display text-[2.75rem] sm:text-[3.75rem] leading-[1.05] font-medium max-w-3xl"
          >
            <motion.span variants={staggerChild} className="block">
              AI agents are starting to shop your store.
            </motion.span>
            <motion.span variants={staggerChild} className="block italic text-accent">
              Say what they&apos;re allowed to do.
            </motion.span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.35, ease: EASE }}
            className="mt-7 text-lg text-ink-muted max-w-xl leading-relaxed"
          >
            Every agentic-commerce protocol lets the <em>buyer</em> put a leash on the agent.
            None of them let the <em>merchant</em> say what it will accept — or prove, afterward,
            what it decided. Warrant is that missing half.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5, ease: EASE }}
            className="mt-9 flex flex-wrap items-center gap-4"
          >
            <Link href="/policy" className="btn btn-primary">
              Write your rules
            </Link>
            <Link href="/demo" className="btn btn-secondary">
              Try it as an agent
            </Link>
          </motion.div>
        </div>

        {/* scroll cue */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1, duration: 0.6 }}
          className="flex justify-center pb-6"
        >
          <motion.div
            animate={{ y: [0, 6, 0] }}
            transition={{ duration: 1.6, repeat: Infinity, ease: "easeInOut" }}
            className="text-ink-faint"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M3 6L8 11L13 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </motion.div>
        </motion.div>
      </section>

      <section className="max-w-6xl mx-auto px-6 py-20">
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-80px" }}
          variants={staggerParent}
          className="grid gap-6 sm:grid-cols-3"
        >
          {STEPS.map((s) => (
            <motion.div key={s.href} variants={staggerChild}>
              <Link
                href={s.href}
                className="card p-7 flex flex-col hover:shadow-lg hover:-translate-y-1 transition-all duration-200 group h-full"
              >
                <span className="label-eyebrow text-accent mb-5">{s.n}</span>
                <h3 className="display text-xl font-medium mb-2.5 group-hover:text-accent transition-colors">
                  {s.title}
                </h3>
                <p className="text-sm text-ink-muted leading-relaxed">{s.body}</p>
              </Link>
            </motion.div>
          ))}
        </motion.div>
      </section>

      <section className="border-t border-border bg-paper-2">
        <div className="max-w-6xl mx-auto px-6 py-16 grid gap-10 sm:grid-cols-2">
          <Reveal>
            <h2 className="display text-2xl font-medium mb-3">No LLM in the decision path.</h2>
            <p className="text-sm text-ink-muted leading-relaxed">
              NIST measured agent-hijacking success rising from 11% to 81% once an attack is
              tailored to the target agent. A bound enforced by a prompt is not a bound. AI drafts
              a merchant&apos;s rules from plain English — deterministic code is what actually
              enforces them.
            </p>
          </Reveal>
          <Reveal delay={0.12}>
            <h2 className="display text-2xl font-medium mb-3">Built for how India actually buys.</h2>
            <p className="text-sm text-ink-muted leading-relaxed">
              AP2, ACP, UCP, even UPI Reserve Pay — none of them govern Cash on Delivery, because
              COD barely exists outside India. It&apos;s 50–70% of real D2C orders here, and needs
              zero payment authorization to place. Warrant gates it by default.
            </p>
          </Reveal>
        </div>
      </section>

      <p className="text-xs text-ink-faint text-center py-10">
        Backend must be running on http://127.0.0.1:8000
      </p>
    </div>
  );
}
