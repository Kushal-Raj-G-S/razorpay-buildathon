"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { listReceipts, MERCHANT_ID, type Receipt } from "@/lib/api";
import { staggerParent, staggerChild } from "@/components/Reveal";

const DECISION_BADGE: Record<Receipt["decision"], string> = {
  allow: "badge-allow",
  block: "badge-block",
  escalate: "badge-escalate",
};

const DECISION_EXPLAIN: Record<Receipt["decision"], string> = {
  allow: "Approved — every rule passed.",
  block: "Rejected — broke at least one rule.",
  escalate: "Paused — sent to a human to decide.",
};

// Same plain-English mapping as the Demo page -- so a viewer reading this
// list doesn't need to know what "cod_allowed" or "deny_categories" mean.
const RULE_LABELS: Record<string, string> = {
  items_are_listed: "Does the shop actually sell this?",
  max_order_value: "Is the order under the spending limit?",
  deny_categories: "Is anything in a banned category?",
  allow_categories: "Is everything in an allowed category?",
  max_units_per_sku: "Is the quantity reasonable?",
  cod_allowed: "Is pay-on-delivery switched on for agents?",
  identity_verified: "Do we know which agent this really is?",
  velocity: "Has this agent ordered too many times recently?",
};

export default function ReceiptsPage() {
  const [receipts, setReceipts] = useState<Receipt[]>([]);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    setLoading(true);
    try {
      setReceipts(await listReceipts(MERCHANT_ID));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  return (
    <div className="max-w-3xl mx-auto px-6 py-16 sm:py-20">
      <div className="flex items-center justify-between mb-3">
        <p className="label-eyebrow">Audit trail</p>
        <button onClick={refresh} className="btn btn-ghost text-xs">
          refresh
        </button>
      </div>
      <h1 className="display text-3xl sm:text-4xl font-medium mb-3">Every decision, proven</h1>
      <p className="text-ink-muted max-w-xl leading-relaxed mb-10">
        This is the permanent record. Every single time an AI agent tried to place an order,
        one row got added here forever — whether it was let through, rejected, or paused for a
        human. Click any row to see exactly which checks it passed or failed. The signature at
        the bottom of each one is proof this exact decision was made — if anyone tried to alter
        it afterward, the signature would no longer match.
      </p>

      {loading && <p className="label-eyebrow">Loading…</p>}
      {!loading && receipts.length === 0 && (
        <div className="card p-10 text-center">
          <p className="text-sm text-ink-muted">
            No orders yet.{" "}
            <a href="/demo" className="text-accent underline underline-offset-2">
              Go try one
            </a>
            .
          </p>
        </div>
      )}

      <motion.div initial="hidden" animate="visible" variants={staggerParent} className="space-y-3">
        {[...receipts].reverse().map((r) => (
          <motion.details key={r.cart_id} variants={staggerChild} className="card group overflow-hidden">
            <summary className="cursor-pointer list-none px-6 py-4 flex items-center justify-between gap-4 hover:bg-paper-2/50 transition-colors">
              <div className="flex items-center gap-3 min-w-0">
                <span className={`badge ${DECISION_BADGE[r.decision]}`}>{r.decision}</span>
                <span className="text-sm truncate">
                  {r.agent_id} <span className="text-ink-faint">·</span>{" "}
                  <span className="mono-num">₹{(r.cart_total / 100).toFixed(2)}</span>
                </span>
              </div>
              <span className="text-xs text-ink-faint shrink-0">
                {new Date(r.timestamp).toLocaleString()}
              </span>
            </summary>
            <div className="px-6 pb-5 pt-3 border-t border-border space-y-2.5">
              <p className="text-sm font-medium">{DECISION_EXPLAIN[r.decision]}</p>
              {r.rules_checked.map((rule) => (
                <div key={rule.rule_name} className="flex items-start gap-2.5 text-sm pt-1">
                  <span
                    className={`mt-0.5 h-4 w-4 rounded-full shrink-0 flex items-center justify-center text-[0.6rem] font-bold ${rule.passed ? "bg-accent/20 text-accent" : "bg-danger/20 text-danger"}`}
                  >
                    {rule.passed ? "✓" : "✕"}
                  </span>
                  <span>
                    <span className="font-medium">{RULE_LABELS[rule.rule_name] ?? rule.rule_name}</span>
                    <span className="text-ink-muted"> — {rule.detail}</span>
                  </span>
                </div>
              ))}
              <div className="pt-3">
                <p className="label-eyebrow mb-1">Signature — proof this can&apos;t be faked or changed later</p>
                <p className="mono-num text-xs text-ink-faint break-all">{r.signature}</p>
              </div>
            </div>
          </motion.details>
        ))}
      </motion.div>
    </div>
  );
}
