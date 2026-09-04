"use client";

import { useEffect, useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  getDigest,
  narrateDigest,
  revokeAgent,
  unrevokeAgent,
  listReceipts,
  MERCHANT_ID,
  type DigestStats,
  type DigestNarrative,
  type Receipt,
} from "@/lib/api";

const SEVERITY_STYLE: Record<string, string> = {
  high: "badge-block",
  medium: "badge-escalate",
  low: "badge-neutral",
};

const FLAG_LABEL: Record<string, string> = {
  catalog_mismatch: "Tried to sell something not in your catalog",
  velocity_cap_hit: "Hit your order-frequency limit",
  repeated_blocks: "Blocked repeatedly, kept trying",
};

const WINDOWS = [
  { hours: 24, label: "24 hours" },
  { hours: 168, label: "7 days" },
  { hours: 720, label: "30 days" },
];

const DECISION_BADGE: Record<string, string> = {
  allow: "badge-allow",
  block: "badge-block",
  escalate: "badge-escalate",
};

const AGENTS_PER_PAGE = 10;

export default function DigestPage() {
  const [windowHours, setWindowHours] = useState(168);
  const [stats, setStats] = useState<DigestStats | null>(null);
  const [narrative, setNarrative] = useState<DigestNarrative | null>(null);
  const [narrating, setNarrating] = useState(false);
  const [narrateError, setNarrateError] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [revokeBusy, setRevokeBusy] = useState<string | null>(null);
  const [revokeError, setRevokeError] = useState("");

  // Clicking a totals tile drills into the real receipts behind that
  // number -- "0 Allowed" used to be just a number with nothing to back
  // it up. Reuses the existing /receipts endpoint rather than adding a
  // new one; filtering by decision and by this page's own time window
  // happens client-side.
  const [selectedDecision, setSelectedDecision] = useState<"allow" | "block" | "escalate" | null>(null);
  const [allReceipts, setAllReceipts] = useState<Receipt[] | null>(null);
  const [receiptsLoading, setReceiptsLoading] = useState(false);
  const [receiptsError, setReceiptsError] = useState("");

  const [agentPage, setAgentPage] = useState(0);
  const [expandedReceipt, setExpandedReceipt] = useState<string | null>(null);

  function loadReceiptsIfNeeded() {
    if (allReceipts || receiptsLoading) return;
    setReceiptsLoading(true);
    setReceiptsError("");
    listReceipts(MERCHANT_ID)
      .then(setAllReceipts)
      .catch((e) => setReceiptsError((e as Error).message))
      .finally(() => setReceiptsLoading(false));
  }

  function selectDecision(decision: "allow" | "block" | "escalate") {
    setSelectedDecision((prev) => (prev === decision ? null : decision));
    setExpandedReceipt(null);
    loadReceiptsIfNeeded();
  }

  const windowCutoffMs = Date.now() - windowHours * 60 * 60 * 1000;
  const filteredReceipts = useMemo(() => {
    if (!selectedDecision || !allReceipts) return [];
    return allReceipts
      .filter((r) => r.decision === selectedDecision && new Date(r.timestamp).getTime() >= windowCutoffMs)
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  }, [allReceipts, selectedDecision, windowCutoffMs]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    setStats(null);
    setNarrative(null);
    setNarrateError("");
    setSelectedDecision(null);
    setAgentPage(0);

    // Stats come back fast -- pure deterministic code, no AI, no network
    // call to a model. Render them the moment they arrive; don't make
    // the merchant wait on the (much slower) narration below just to see
    // real numbers.
    getDigest(MERCHANT_ID, windowHours)
      .then((res) => {
        if (cancelled) return;
        setStats(res.stats);
        setLoading(false);
        if (res.stats.totals.attempts === 0) return;

        setNarrating(true);
        narrateDigest(MERCHANT_ID, res.stats)
          .then((n) => !cancelled && setNarrative(n.narrative))
          .catch((e) => !cancelled && setNarrateError((e as Error).message))
          .finally(() => !cancelled && setNarrating(false));
      })
      .catch((e) => {
        if (cancelled) return;
        setError((e as Error).message);
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [windowHours]);

  const explanationFor = (agentId: string) =>
    narrative?.flag_explanations.find((f) => f.agent_id === agentId)?.plain_english;

  // The whole point of surfacing a flag is that the merchant can act on
  // it right here -- not read a warning, then go hunt for how to revoke
  // an agent elsewhere. Updates the agent's `revoked` flag locally on
  // success instead of a full refetch, so the button state flips
  // immediately.
  async function toggleRevoke(agentId: string, currentlyRevoked: boolean) {
    setRevokeBusy(agentId);
    setRevokeError("");
    try {
      if (currentlyRevoked) {
        await unrevokeAgent(agentId, MERCHANT_ID);
      } else {
        await revokeAgent(agentId, MERCHANT_ID);
      }
      setStats((prev) =>
        prev
          ? {
              ...prev,
              agents: prev.agents.map((a) =>
                a.agent_id === agentId ? { ...a, revoked: !currentlyRevoked } : a
              ),
            }
          : prev
      );
    } catch (e) {
      setRevokeError(`Couldn't update ${agentId}: ${(e as Error).message}`);
    } finally {
      setRevokeBusy(null);
    }
  }

  const agentPageCount = stats ? Math.ceil(stats.agents.length / AGENTS_PER_PAGE) : 0;
  const pagedAgents = stats
    ? stats.agents.slice(agentPage * AGENTS_PER_PAGE, agentPage * AGENTS_PER_PAGE + AGENTS_PER_PAGE)
    : [];

  return (
    <div className="max-w-6xl mx-auto px-6 py-16 sm:py-20">
      <p className="label-eyebrow mb-3">What's actually been happening</p>
      <h1 className="display text-3xl sm:text-4xl font-medium mb-3">Digest</h1>
      <p className="text-ink-muted max-w-xl leading-relaxed mb-8">
        Not a log to read line by line — a summary. Every flag below is decided by the same
        fixed code that runs at checkout, before any AI ever sees it. If AI is configured, it
        only translates those already-decided facts into plain language.
      </p>

      <div className="flex items-center gap-2 mb-8">
        {WINDOWS.map((w) => (
          <button
            key={w.hours}
            onClick={() => setWindowHours(w.hours)}
            className={`btn text-xs px-3.5 py-1.5 border ${
              windowHours === w.hours ? "btn-primary" : "btn-ghost border-border"
            }`}
          >
            {w.label}
          </button>
        ))}
      </div>

      {loading && <p className="label-eyebrow">Loading…</p>}
      {error && <div className="card px-5 py-3.5 mb-6 text-sm bg-danger-soft text-danger">{error}</div>}

      {!loading && !error && stats && (
        <div className="grid lg:grid-cols-[1fr_340px] gap-10 items-start">
          <div className="min-w-0 space-y-8">
            {narrative && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="card p-6 bg-accent-soft/40"
              >
                <p className="text-lg font-medium mb-2">{narrative.headline}</p>
                <p className="text-sm text-ink-muted leading-relaxed">{narrative.summary}</p>
              </motion.div>
            )}
            {stats.totals.attempts === 0 && (
              <div className="card p-6 bg-accent-soft/40">
                <p className="text-lg font-medium mb-1">Quiet window — nothing happened yet</p>
                <p className="text-sm text-ink-muted">
                  No agent has tried to check out with your store in this window.
                </p>
              </div>
            )}
            {!narrative && narrating && (
              <div className="card px-5 py-3.5 text-sm text-ink-muted flex items-center gap-2">
                <span className="inline-block h-1.5 w-1.5 rounded-full bg-accent animate-pulse" />
                Writing a plain-language summary…
              </div>
            )}
            {!narrative && !narrating && narrateError && (
              <div className="card px-5 py-3.5 text-sm text-ink-muted">
                Couldn't generate a plain-language summary ({narrateError}) — the numbers below are
                still accurate.
              </div>
            )}

            <div className="grid grid-cols-4 gap-3">
              {(
                [
                  ["Attempts", stats.totals.attempts, null],
                  ["Allowed", stats.totals.allowed, "allow"],
                  ["Blocked", stats.totals.blocked, "block"],
                  ["Escalated", stats.totals.escalated, "escalate"],
                ] as const
              ).map(([label, value, decision]) => (
                <button
                  key={label}
                  onClick={() => decision && selectDecision(decision)}
                  disabled={!decision}
                  className={`card p-4 text-center transition-colors ${
                    decision ? "hover:border-accent cursor-pointer" : "cursor-default"
                  } ${selectedDecision === decision ? "border-accent bg-accent-soft/30" : ""}`}
                >
                  <p className="mono-num text-2xl font-medium">{value}</p>
                  <p className="text-xs text-ink-faint mt-1">
                    {label}
                    {decision && <span className="block text-[10px] mt-0.5">click to see</span>}
                  </p>
                </button>
              ))}
            </div>

            {revokeError && (
              <div className="card px-5 py-3.5 text-sm bg-danger-soft text-danger">{revokeError}</div>
            )}

            {!selectedDecision && (
              <p className="text-sm text-ink-faint">
                Click a number above — Allowed shows what agents actually bought, Blocked shows
                what they tried and why it was caught, Escalated shows what's waiting on you.
              </p>
            )}

            <AnimatePresence>
              {selectedDecision && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="overflow-hidden"
                >
                  <div className="card overflow-hidden">
                    <div className="px-5 py-3 border-b border-border flex items-center justify-between">
                      <p className="text-sm font-medium capitalize">
                        {selectedDecision === "allow" ? "Allowed" : selectedDecision === "block" ? "Blocked" : "Escalated"}{" "}
                        orders in this window
                      </p>
                      <button
                        onClick={() => setSelectedDecision(null)}
                        className="text-xs text-ink-faint hover:text-ink"
                      >
                        close
                      </button>
                    </div>

                    {/* Flags live here, not as a separate always-visible section --
                        they're all about blocked-pattern agents, so they belong inside
                        the "why was this blocked" drilldown, not duplicated next to it. */}
                    {selectedDecision === "block" && stats.flags.length > 0 && (
                      <div className="px-5 py-4 border-b border-border bg-paper-2/30 space-y-3">
                        <p className="label-eyebrow">Patterns worth noticing ({stats.flags.length})</p>
                        {stats.flags.map((f) => {
                          const agent = stats.agents.find((a) => a.agent_id === f.agent_id);
                          const isRevoked = agent?.revoked ?? false;
                          return (
                            <div key={`${f.agent_id}-${f.flag_type}`} className="card p-4">
                              <div className="flex items-center gap-3 mb-1.5">
                                <span className={`badge ${SEVERITY_STYLE[f.severity]}`}>{f.severity}</span>
                                <span className="text-sm font-medium">
                                  {FLAG_LABEL[f.flag_type] ?? f.flag_type}
                                </span>
                                <span className="text-xs text-ink-faint ml-auto">agent: {f.agent_id}</span>
                              </div>
                              <p className="text-sm text-ink-muted mb-2.5">
                                {explanationFor(f.agent_id) ?? f.detail}
                              </p>
                              {isRevoked ? (
                                <span className="badge badge-neutral text-xs">Access revoked</span>
                              ) : (
                                <button
                                  onClick={() => toggleRevoke(f.agent_id, false)}
                                  disabled={revokeBusy === f.agent_id}
                                  className="btn btn-danger text-xs px-3.5 py-1.5"
                                >
                                  {revokeBusy === f.agent_id ? "Revoking…" : `Revoke ${f.agent_id}`}
                                </button>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}

                    {receiptsLoading && <p className="text-sm text-ink-muted p-5">Loading…</p>}
                    {receiptsError && (
                      <p className="text-sm text-danger p-5">Couldn't load receipts: {receiptsError}</p>
                    )}
                    {!receiptsLoading && !receiptsError && filteredReceipts.length === 0 && (
                      <p className="text-sm text-ink-muted p-5">None in this window.</p>
                    )}
                    {!receiptsLoading && filteredReceipts.length > 0 && (
                      <div className="divide-y divide-border">
                        {filteredReceipts.map((r) => {
                          const isOpen = expandedReceipt === r.cart_id;
                          const hasItems = (r.cart_items?.length ?? 0) > 0;
                          const failedRules = r.rules_checked.filter((rc) => !rc.passed);
                          const canExpand = hasItems || failedRules.length > 0;
                          return (
                            <div key={r.cart_id}>
                              <button
                                onClick={() => canExpand && setExpandedReceipt(isOpen ? null : r.cart_id)}
                                className={`w-full px-5 py-3 flex items-center justify-between text-sm text-left ${
                                  canExpand ? "hover:bg-paper-2/40" : ""
                                }`}
                              >
                                <div className="flex items-center gap-3">
                                  <span className={`badge ${DECISION_BADGE[r.decision]} text-xs`}>
                                    {r.decision}
                                  </span>
                                  <span>{r.agent_id}</span>
                                </div>
                                <div className="flex items-center gap-3">
                                  <span className="mono-num text-ink-muted">
                                    ₹{(r.cart_total / 100).toFixed(2)}
                                  </span>
                                  <span className="text-xs text-ink-faint">
                                    {new Date(r.timestamp).toLocaleString()}
                                  </span>
                                  {canExpand && (
                                    <span
                                      className={`text-ink-faint transition-transform ${isOpen ? "rotate-180" : ""}`}
                                    >
                                      ▾
                                    </span>
                                  )}
                                </div>
                              </button>
                              <AnimatePresence>
                                {isOpen && canExpand && (
                                  <motion.div
                                    initial={{ opacity: 0, height: 0 }}
                                    animate={{ opacity: 1, height: "auto" }}
                                    exit={{ opacity: 0, height: 0 }}
                                    className="overflow-hidden bg-paper-2/30"
                                  >
                                    <div className="px-5 pb-3 pt-1 space-y-2.5">
                                      {hasItems && (
                                        <div className="space-y-1.5">
                                          <p className="text-[10px] uppercase tracking-wide text-ink-faint">
                                            What was requested
                                          </p>
                                          {r.cart_items!.map((item, i) => (
                                            <div
                                              key={`${item.id}-${i}`}
                                              className="flex items-center justify-between text-xs text-ink-muted"
                                            >
                                              <span>
                                                {item.title}
                                                {item.category && (
                                                  <span className="badge badge-neutral text-[10px] ml-2 px-1.5 py-0">
                                                    {item.category}
                                                  </span>
                                                )}
                                                <span className="text-ink-faint"> × {item.quantity}</span>
                                              </span>
                                              <span className="mono-num">₹{(item.price / 100).toFixed(2)}</span>
                                            </div>
                                          ))}
                                        </div>
                                      )}
                                      {failedRules.length > 0 && (
                                        <div className="space-y-1">
                                          <p className="text-[10px] uppercase tracking-wide text-ink-faint">
                                            Why it was {r.decision === "block" ? "blocked" : "flagged"}
                                          </p>
                                          {failedRules.map((rc) => (
                                            <p key={rc.rule_name} className="text-xs text-danger">
                                              <span className="font-medium">{rc.rule_name}:</span> {rc.detail}
                                            </p>
                                          ))}
                                        </div>
                                      )}
                                    </div>
                                  </motion.div>
                                )}
                              </AnimatePresence>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <div className="lg:sticky lg:top-8">
            <h2 className="label-eyebrow mb-3">
              Every agent seen in this window {stats.agents.length > 0 && `(${stats.agents.length})`}
            </h2>
            {stats.agents.length === 0 ? (
              <p className="text-sm text-ink-muted">No agents yet.</p>
            ) : (
              <>
                <div className="card overflow-hidden">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border text-left text-ink-faint">
                        <th className="px-4 py-2.5 font-normal text-xs">Agent</th>
                        <th className="px-4 py-2.5 font-normal text-xs">A</th>
                        <th className="px-4 py-2.5 font-normal text-xs">Bl</th>
                        <th className="px-4 py-2.5 font-normal text-xs">Access</th>
                      </tr>
                    </thead>
                    <tbody>
                      {pagedAgents.map((a) => (
                        <tr key={a.agent_id} className="border-b border-border last:border-0">
                          <td className="px-4 py-2.5 font-medium truncate max-w-[120px]" title={a.agent_id}>
                            {a.agent_id}
                          </td>
                          <td className="px-4 py-2.5 mono-num">{a.allowed}</td>
                          <td className="px-4 py-2.5 mono-num">{a.blocked}</td>
                          <td className="px-4 py-2.5">
                            <button
                              onClick={() => toggleRevoke(a.agent_id, a.revoked)}
                              disabled={revokeBusy === a.agent_id}
                              className={`btn text-xs px-2.5 py-1 ${
                                a.revoked ? "btn-ghost border border-border" : "btn-danger"
                              }`}
                            >
                              {revokeBusy === a.agent_id ? "…" : a.revoked ? "Unrevoke" : "Revoke"}
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {agentPageCount > 1 && (
                  <div className="flex items-center justify-between mt-3">
                    <button
                      onClick={() => setAgentPage((p) => Math.max(0, p - 1))}
                      disabled={agentPage === 0}
                      className="btn btn-ghost text-xs border border-border px-3 py-1.5 disabled:opacity-40"
                    >
                      ← Prev
                    </button>
                    <p className="text-xs text-ink-faint">
                      {agentPage + 1} / {agentPageCount}
                    </p>
                    <button
                      onClick={() => setAgentPage((p) => Math.min(agentPageCount - 1, p + 1))}
                      disabled={agentPage >= agentPageCount - 1}
                      className="btn btn-ghost text-xs border border-border px-3 py-1.5 disabled:opacity-40"
                    >
                      Next →
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
