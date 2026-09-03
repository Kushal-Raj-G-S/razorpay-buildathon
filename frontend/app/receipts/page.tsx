"use client";

import { useEffect, useState } from "react";
import { listReceipts, MERCHANT_ID, type Receipt } from "@/lib/api";

const DECISION_STYLE: Record<Receipt["decision"], string> = {
  allow: "bg-green-100 text-green-800",
  block: "bg-red-100 text-red-800",
  escalate: "bg-amber-100 text-amber-800",
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
    <div className="max-w-3xl mx-auto px-6 py-16">
      <div className="flex items-center justify-between mb-2">
        <h1 className="text-2xl font-semibold">Every decision, proven</h1>
        <button onClick={refresh} className="text-sm underline text-zinc-500">
          refresh
        </button>
      </div>
      <p className="text-sm text-zinc-500 mb-8">
        Every time an agent tried to buy something, here&apos;s exactly what was checked and why
        it was allowed, blocked, or sent for human review. Each row is cryptographically signed —
        if anyone edits one afterward, the signature stops matching.
      </p>

      {loading && <p className="text-sm text-zinc-400">Loading…</p>}
      {!loading && receipts.length === 0 && (
        <p className="text-sm text-zinc-400">
          No orders yet.{" "}
          <a href="/demo" className="underline">
            Go try one
          </a>
          .
        </p>
      )}

      <div className="space-y-3">
        {[...receipts].reverse().map((r) => (
          <details key={r.cart_id} className="rounded-lg border border-zinc-200 bg-white p-4">
            <summary className="cursor-pointer flex items-center justify-between">
              <span className="flex items-center gap-3">
                <span
                  className={`text-xs font-semibold uppercase px-2 py-1 rounded ${DECISION_STYLE[r.decision]}`}
                >
                  {r.decision}
                </span>
                <span className="text-sm text-zinc-600">
                  {r.agent_id} · Rs {(r.cart_total / 100).toFixed(2)}
                </span>
              </span>
              <span className="text-xs text-zinc-400">
                {new Date(r.timestamp).toLocaleString()}
              </span>
            </summary>
            <div className="mt-3 space-y-1 border-t border-zinc-100 pt-3">
              {r.rules_checked.map((rule) => (
                <div key={rule.rule_name} className="text-sm flex gap-2">
                  <span>{rule.passed ? "✅" : "❌"}</span>
                  <span className="font-medium">{rule.rule_name}:</span>
                  <span className="text-zinc-600">{rule.detail}</span>
                </div>
              ))}
              <div className="text-xs text-zinc-400 font-mono break-all pt-2">
                signature: {r.signature}
              </div>
            </div>
          </details>
        ))}
      </div>
    </div>
  );
}
