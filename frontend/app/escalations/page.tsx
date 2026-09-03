"use client";

import { useEffect, useState } from "react";
import { listEscalations, reviewEscalation, MERCHANT_ID, type Escalation } from "@/lib/api";

export default function EscalationsPage() {
  const [pending, setPending] = useState<Escalation[]>([]);
  const [loading, setLoading] = useState(true);
  const [note, setNote] = useState<Record<number, string>>({});
  const [message, setMessage] = useState("");

  async function refresh() {
    setLoading(true);
    try {
      setPending(await listEscalations(MERCHANT_ID, "pending"));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function decide(id: number, approve: boolean) {
    setMessage("");
    try {
      const result = await reviewEscalation(id, approve, note[id]);
      setMessage(
        approve
          ? `Approved. Real Razorpay payment link created: ${result.payment?.short_url ?? "n/a"}`
          : "Rejected. No payment was created."
      );
      refresh();
    } catch (e) {
      setMessage(`Failed: ${(e as Error).message}`);
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-16">
      <h1 className="text-2xl font-semibold mb-2">Orders waiting for you</h1>
      <p className="text-sm text-zinc-500 mb-8">
        Every rule passed on these, but they were too big to auto-approve. Nothing happens with
        money until you decide. Approve creates a real Razorpay payment link right here.
      </p>

      {loading && <p className="text-sm text-zinc-400">Loading…</p>}
      {!loading && pending.length === 0 && (
        <p className="text-sm text-zinc-400">
          Nothing pending. Try an order between your escalate-above value and your max order
          value on the{" "}
          <a href="/demo" className="underline">
            try it
          </a>{" "}
          page.
        </p>
      )}

      {message && (
        <div className="mb-4 text-sm rounded border border-zinc-200 bg-zinc-50 p-3 break-all">
          {message}
        </div>
      )}

      <div className="space-y-4">
        {pending.map((e) => (
          <div key={e.id} className="rounded-lg border border-amber-300 bg-amber-50 p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="font-medium">Order #{e.id}</span>
              <span className="text-sm text-zinc-600">Rs {(e.cart_total / 100).toFixed(2)}</span>
            </div>
            <div className="text-sm text-zinc-600 mb-3">agent: {e.agent_id}</div>
            <ul className="text-sm mb-3 list-disc list-inside">
              {e.cart_items.map((item, i) => (
                <li key={i}>
                  {item.title} × {item.quantity} — Rs {(item.price / 100).toFixed(2)}
                </li>
              ))}
            </ul>
            <input
              type="text"
              placeholder="optional note"
              className="w-full rounded border border-zinc-300 px-3 py-1.5 text-sm mb-3"
              value={note[e.id] || ""}
              onChange={(ev) => setNote({ ...note, [e.id]: ev.target.value })}
            />
            <div className="flex gap-2">
              <button
                onClick={() => decide(e.id, true)}
                className="rounded bg-green-600 text-white px-4 py-1.5 text-sm font-medium"
              >
                Approve
              </button>
              <button
                onClick={() => decide(e.id, false)}
                className="rounded bg-red-600 text-white px-4 py-1.5 text-sm font-medium"
              >
                Reject
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
