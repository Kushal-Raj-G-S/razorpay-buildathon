"use client";

import { useEffect, useState } from "react";
import { listReceipts, MERCHANT_ID, type Receipt } from "@/lib/api";

const DECISION_BADGE: Record<Receipt["decision"], string> = {
  allow: "badge-allow",
  block: "badge-block",
  escalate: "badge-escalate",
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
        Every time an agent tried to buy something, here&apos;s exactly what was checked and why
        it was allowed, blocked, or sent for review. Each row is signed — if anyone edits one
        afterward, the signature stops matching.
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

      <div className="space-y-3">
        {[...receipts].reverse().map((r) => (
          <details key={r.cart_id} className="card group overflow-hidden">
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
            <div className="px-6 pb-5 pt-1 border-t border-border space-y-2.5">
              {r.rules_checked.map((rule) => (
                <div key={rule.rule_name} className="flex items-start gap-2.5 text-sm pt-3">
                  <span
                    className={`mt-0.5 h-1.5 w-1.5 rounded-full shrink-0 ${rule.passed ? "bg-accent" : "bg-danger"}`}
                  />
                  <span>
                    <span className="font-medium">{rule.rule_name}</span>
                    <span className="text-ink-muted"> — {rule.detail}</span>
                  </span>
                </div>
              ))}
              <div className="pt-3">
                <p className="label-eyebrow mb-1">Signature</p>
                <p className="mono-num text-xs text-ink-faint break-all">{r.signature}</p>
              </div>
            </div>
          </details>
        ))}
      </div>
    </div>
  );
}
