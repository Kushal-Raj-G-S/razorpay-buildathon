"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  listEscalations,
  reviewEscalation,
  getEscalationAdvice,
  MERCHANT_ID,
  type Escalation,
  type EscalationAdvice,
} from "@/lib/api";

const RECOMMENDATION_STYLE: Record<string, string> = {
  approve: "badge-allow",
  reject: "badge-block",
  needs_human_judgment: "badge-neutral",
};

const STATUS_BADGE: Record<string, string> = {
  approved: "badge-allow",
  rejected: "badge-block",
};

export default function EscalationsPage() {
  const [tab, setTab] = useState<"pending" | "reviewed">("pending");
  const [pending, setPending] = useState<Escalation[]>([]);
  const [reviewed, setReviewed] = useState<Escalation[]>([]);
  const [reviewedLoaded, setReviewedLoaded] = useState(false);
  const [loading, setLoading] = useState(true);
  const [note, setNote] = useState<Record<number, string>>({});
  const [message, setMessage] = useState<{ text: string; link?: string } | null>(null);
  const [advice, setAdvice] = useState<Record<number, EscalationAdvice>>({});
  const [advising, setAdvising] = useState<number | null>(null);

  async function askForAdvice(id: number) {
    setAdvising(id);
    try {
      const { advice: a } = await getEscalationAdvice(id);
      setAdvice((prev) => ({ ...prev, [id]: a }));
    } catch (e) {
      setMessage({ text: `Advisor failed: ${(e as Error).message}` });
    } finally {
      setAdvising(null);
    }
  }

  async function refresh() {
    setLoading(true);
    try {
      setPending(await listEscalations(MERCHANT_ID, "pending"));
    } finally {
      setLoading(false);
    }
  }

  // Approving or rejecting one used to make it disappear with no trace
  // anywhere in the app -- the receipt behind it still just says
  // "escalate" forever, since review_escalation only ever updates the
  // escalation row, not the original receipt. Backend already supported
  // fetching every status (status="" returns all); this just exposes it.
  async function loadReviewed() {
    setLoading(true);
    try {
      const all = await listEscalations(MERCHANT_ID, "");
      setReviewed(
        all
          .filter((e) => e.status !== "pending")
          .sort((a, b) => new Date(b.reviewed_at ?? 0).getTime() - new Date(a.reviewed_at ?? 0).getTime())
      );
      setReviewedLoaded(true);
    } finally {
      setLoading(false);
    }
  }

  function switchTab(next: "pending" | "reviewed") {
    setTab(next);
    setMessage(null);
    if (next === "pending") {
      refresh();
    } else if (!reviewedLoaded) {
      loadReviewed();
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function decide(id: number, approve: boolean) {
    setMessage(null);
    try {
      const result = await reviewEscalation(id, approve, note[id]);
      const shortUrl = result.payment?.short_url;
      setMessage(
        approve
          ? {
              text: "Approved — real Razorpay payment link created:",
              link: typeof shortUrl === "string" ? shortUrl : undefined,
            }
          : { text: "Rejected — no payment was created." }
      );
      // Remove it from the list immediately so it visibly leaves rather
      // than waiting for a full refetch -- the exit animation below is
      // what actually plays this.
      setPending((prev) => prev.filter((e) => e.id !== id));
      setReviewedLoaded(false); // stale now -- refetch next time that tab opens
    } catch (e) {
      setMessage({ text: `Failed: ${(e as Error).message}` });
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-6 py-16 sm:py-20">
      <p className="label-eyebrow mb-3">Human review</p>
      <h1 className="display text-3xl sm:text-4xl font-medium mb-3">Orders waiting for you</h1>
      <p className="text-ink-muted max-w-xl leading-relaxed mb-6">
        Every rule passed on these — they were just too big to auto-approve. Nothing happens with
        money until you decide. Approving creates a real Razorpay payment link right here.
      </p>

      <div className="flex items-center gap-2 mb-8">
        <button
          onClick={() => switchTab("pending")}
          className={`btn text-xs px-3.5 py-1.5 border ${
            tab === "pending" ? "btn-primary" : "btn-ghost border-border"
          }`}
        >
          Pending {pending.length > 0 && `(${pending.length})`}
        </button>
        <button
          onClick={() => switchTab("reviewed")}
          className={`btn text-xs px-3.5 py-1.5 border ${
            tab === "reviewed" ? "btn-primary" : "btn-ghost border-border"
          }`}
        >
          Reviewed — your own decisions
        </button>
      </div>

      {message && (
        <div className="card px-5 py-3.5 mb-6 text-sm bg-paper-2/60 break-words">
          {message.text}
          {message.link && (
            <>
              {" "}
              <a
                href={message.link}
                target="_blank"
                rel="noopener noreferrer"
                className="text-accent underline underline-offset-2"
              >
                {message.link}
              </a>
            </>
          )}
        </div>
      )}

      {loading && <p className="label-eyebrow">Loading…</p>}
      {!loading && tab === "pending" && pending.length === 0 && (
        <div className="card p-10 text-center">
          <p className="text-sm text-ink-muted">
            Nothing pending. Try an order between your escalate-above value and your max order
            value on{" "}
            <a href="/demo" className="text-accent underline underline-offset-2">
              the try-it page
            </a>
            .
          </p>
        </div>
      )}

      {tab === "pending" && (
      <div className="space-y-4">
        <AnimatePresence initial={false}>
          {pending.map((e) => (
            <motion.div
              key={e.id}
              layout
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, x: 40, scale: 0.97, transition: { duration: 0.25 } }}
              transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
              className="card overflow-hidden"
            >
              <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-warning-soft/40">
                <div className="flex items-center gap-3">
                  <span className="badge badge-escalate">Order #{e.id}</span>
                  <span className="text-sm text-ink-muted">agent: {e.agent_id}</span>
                </div>
                <span className="mono-num text-sm font-medium">₹{(e.cart_total / 100).toFixed(2)}</span>
              </div>

              <div className="px-6 py-4 space-y-1.5">
                {e.cart_items.map((item, i) => (
                  <div key={i} className="flex items-center justify-between text-sm">
                    <span>
                      {item.title} <span className="text-ink-faint">× {item.quantity}</span>
                    </span>
                    <span className="mono-num text-ink-muted">₹{(item.price / 100).toFixed(2)}</span>
                  </div>
                ))}
              </div>

              {advice[e.id] ? (
                <motion.div
                  initial={{ opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mx-6 mb-4 rounded-lg border border-border bg-paper-2/50 p-4"
                >
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className="label-eyebrow">AI advisor</span>
                    <span className={`badge ${RECOMMENDATION_STYLE[advice[e.id].recommendation]}`}>
                      {advice[e.id].recommendation.replace(/_/g, " ")}
                    </span>
                    <span className="text-xs text-ink-faint">
                      {advice[e.id].confidence} confidence
                    </span>
                  </div>
                  <p className="text-sm text-ink-muted">{advice[e.id].reasoning}</p>
                  <p className="text-xs text-ink-faint mt-2">
                    A suggestion only — you still decide below.
                  </p>
                </motion.div>
              ) : (
                <div className="px-6 pb-4">
                  <button
                    onClick={() => askForAdvice(e.id)}
                    disabled={advising === e.id}
                    className="btn btn-ghost text-xs border border-border"
                  >
                    {advising === e.id ? "Thinking…" : "Ask the AI advisor"}
                  </button>
                </div>
              )}

              <div className="px-6 pb-5 flex flex-wrap items-center gap-3">
                <input
                  type="text"
                  placeholder="optional note"
                  className="field-input flex-1 min-w-[160px]"
                  value={note[e.id] || ""}
                  onChange={(ev) => setNote({ ...note, [e.id]: ev.target.value })}
                />
                <button onClick={() => decide(e.id, true)} className="btn btn-primary">
                  Approve
                </button>
                <button onClick={() => decide(e.id, false)} className="btn btn-danger">
                  Reject
                </button>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
      )}

      {tab === "reviewed" && !loading && (
        <div className="space-y-3">
          {reviewed.length === 0 ? (
            <div className="card p-10 text-center">
              <p className="text-sm text-ink-muted">
                Nothing reviewed yet — approve or reject something in the Pending tab and it
                shows up here.
              </p>
            </div>
          ) : (
            reviewed.map((e) => (
              <div key={e.id} className="card overflow-hidden">
                <div className="flex items-center justify-between px-6 py-4 border-b border-border">
                  <div className="flex items-center gap-3">
                    <span className={`badge ${STATUS_BADGE[e.status] ?? "badge-neutral"}`}>
                      {e.status}
                    </span>
                    <span className="badge badge-neutral">Order #{e.id}</span>
                    <span className="text-sm text-ink-muted">agent: {e.agent_id}</span>
                  </div>
                  <span className="mono-num text-sm font-medium">₹{(e.cart_total / 100).toFixed(2)}</span>
                </div>
                <div className="px-6 py-4 space-y-1.5">
                  {e.cart_items.map((item, i) => (
                    <div key={i} className="flex items-center justify-between text-sm">
                      <span>
                        {item.title} <span className="text-ink-faint">× {item.quantity}</span>
                      </span>
                      <span className="mono-num text-ink-muted">₹{(item.price / 100).toFixed(2)}</span>
                    </div>
                  ))}
                </div>
                <div className="px-6 pb-4 flex items-center justify-between text-xs text-ink-faint">
                  <span>{e.reviewer_note ? `Note: ${e.reviewer_note}` : "No note left"}</span>
                  <span>{e.reviewed_at ? new Date(e.reviewed_at).toLocaleString() : ""}</span>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
