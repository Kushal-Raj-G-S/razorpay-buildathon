"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  tryCheckout,
  revokeAgent,
  unrevokeAgent,
  MERCHANT_ID,
  type Receipt,
  type CartItemInput,
} from "@/lib/api";

const AGENT_ID = "shopping-agent-007";

const CLEAN_CART: CartItemInput[] = [
  { id: "shirt", title: "Blue Cotton Shirt L", price: 45000, category: "clothing", quantity: 1 },
];

const POISONED_CART: CartItemInput[] = [
  { id: "shirt", title: "Blue Cotton Shirt L", price: 45000, category: "clothing", quantity: 1 },
  { id: "giftcard", title: "Rs 2000 Gift Card", price: 200000, category: "gift_card", quantity: 1 },
];

const OVER_LIMIT_CART: CartItemInput[] = [
  { id: "jeans", title: "Denim Jeans 32", price: 1500000, category: "clothing", quantity: 1 },
];

const COD_CART: CartItemInput[] = [
  { id: "socks", title: "Pack of Socks", price: 40000, category: "clothing", quantity: 1 },
];

const SCENARIOS: {
  label: string;
  sub: string;
  cart: CartItemInput[];
  mode: "prepaid" | "cod";
}[] = [
  { label: "Clean cart", sub: "Everything about it is fine", cart: CLEAN_CART, mode: "prepaid" },
  {
    label: "Poisoned cart",
    sub: "A hidden gift card sneaked in",
    cart: POISONED_CART,
    mode: "prepaid",
  },
  { label: "Over the limit", sub: "One item, too expensive", cart: OVER_LIMIT_CART, mode: "prepaid" },
  {
    label: "Agentic COD",
    sub: "Zero payment authorization needed",
    cart: COD_CART,
    mode: "cod",
  },
];

const DECISION_BADGE: Record<Receipt["decision"], string> = {
  allow: "badge-allow",
  block: "badge-block",
  escalate: "badge-escalate",
};

function ReceiptCard({ receipt }: { receipt: Receipt }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10, transition: { duration: 0.15 } }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      className="card p-7 mt-8"
    >
      <div className="flex items-center justify-between mb-5">
        <motion.span
          key={receipt.decision + receipt.timestamp}
          initial={{ opacity: 0, scale: 1.7, rotate: -10 }}
          animate={{ opacity: 1, scale: 1, rotate: -4 }}
          transition={{ type: "spring", stiffness: 340, damping: 16, delay: 0.1 }}
          className={`badge ${DECISION_BADGE[receipt.decision]} text-[0.78rem] px-3 py-1.5`}
        >
          {receipt.decision}
        </motion.span>
        <span className="mono-num text-sm text-ink-muted">₹{(receipt.cart_total / 100).toFixed(2)}</span>
      </div>
      <div className="space-y-2.5 mb-5">
        {receipt.rules_checked.map((r, i) => (
          <motion.div
            key={r.rule_name}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.25 + i * 0.06, duration: 0.35 }}
            className="flex items-start gap-2.5 text-sm"
          >
            <span
              className={`mt-0.5 h-1.5 w-1.5 rounded-full shrink-0 ${r.passed ? "bg-accent" : "bg-danger"}`}
            />
            <span>
              <span className="font-medium">{r.rule_name}</span>
              <span className="text-ink-muted"> — {r.detail}</span>
            </span>
          </motion.div>
        ))}
      </div>
      <div className="pt-4 border-t border-border">
        <p className="label-eyebrow mb-1">Signature</p>
        <p className="mono-num text-xs text-ink-faint break-all">{receipt.signature}</p>
      </div>
    </motion.div>
  );
}

export default function DemoPage() {
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const [extra, setExtra] = useState("");
  const [error, setError] = useState("");
  const [revoked, setRevoked] = useState(false);
  const [loading, setLoading] = useState<string | null>(null);

  async function send(scenario: (typeof SCENARIOS)[number]) {
    setLoading(scenario.label);
    setError("");
    setExtra("");
    try {
      const result = await tryCheckout(MERCHANT_ID, AGENT_ID, scenario.cart, scenario.mode);
      setReceipt(result.receipt);
      if (result.payment) setExtra(`Real Razorpay link created: ${result.payment.short_url}`);
      if (result.order) setExtra("Order confirmed as Cash on Delivery — no payment link needed.");
      if (result.escalation_id) setExtra(`Sent to the review queue as order #${result.escalation_id}.`);
    } catch (e) {
      setError((e as Error).message);
      setReceipt(null);
    } finally {
      setLoading(null);
    }
  }

  async function toggleRevoke() {
    if (revoked) {
      await unrevokeAgent(AGENT_ID, MERCHANT_ID);
      setRevoked(false);
    } else {
      await revokeAgent(AGENT_ID, MERCHANT_ID);
      setRevoked(true);
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-6 py-16 sm:py-20">
      <p className="label-eyebrow mb-3">Live test</p>
      <h1 className="display text-3xl sm:text-4xl font-medium mb-3">Pretend you&apos;re an agent</h1>
      <p className="text-ink-muted max-w-xl leading-relaxed mb-10">
        Pick a scenario. It sends the cart to the real server exactly like a shopping agent
        would, and the bouncer decides in real time. Make sure you&apos;ve{" "}
        <a href="/policy" className="text-accent underline underline-offset-2">
          saved rules
        </a>{" "}
        first.
      </p>

      <div className="grid sm:grid-cols-2 gap-3">
        {SCENARIOS.map((s, i) => (
          <motion.button
            key={s.label}
            onClick={() => send(s)}
            disabled={loading !== null}
            whileTap={{ scale: 0.98 }}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05, duration: 0.35 }}
            className="card p-5 text-left hover:border-accent transition-colors disabled:opacity-50"
          >
            <p className="text-sm font-medium mb-0.5">
              {loading === s.label ? "Sending…" : s.label}
            </p>
            <p className="text-xs text-ink-muted">{s.sub}</p>
          </motion.button>
        ))}
      </div>

      <div className="mt-6 flex items-center justify-between card px-5 py-4">
        <div>
          <p className="text-sm font-medium">Agent access</p>
          <p className="text-xs text-ink-muted">
            {revoked ? "Revoked — every request from this agent will be refused" : "Currently allowed to transact"}
          </p>
        </div>
        <button onClick={toggleRevoke} className={`btn ${revoked ? "btn-secondary" : "btn-danger"}`}>
          {revoked ? "Un-revoke agent" : "Revoke this agent"}
        </button>
      </div>

      {error && <p className="text-sm text-danger mt-6">{error}</p>}
      {extra && <p className="text-sm text-ink-muted mt-6">{extra}</p>}
      <AnimatePresence mode="wait">
        {receipt && <ReceiptCard key={receipt.cart_id + receipt.timestamp} receipt={receipt} />}
      </AnimatePresence>
    </div>
  );
}
