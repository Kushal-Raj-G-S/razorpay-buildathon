"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { getDigest, narrateDigest, MERCHANT_ID, type DigestStats, type DigestNarrative } from "@/lib/api";

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

export default function DigestPage() {
  const [windowHours, setWindowHours] = useState(168);
  const [stats, setStats] = useState<DigestStats | null>(null);
  const [narrative, setNarrative] = useState<DigestNarrative | null>(null);
  const [narrating, setNarrating] = useState(false);
  const [narrateError, setNarrateError] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    setStats(null);
    setNarrative(null);
    setNarrateError("");

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

  return (
    <div className="max-w-3xl mx-auto px-6 py-16 sm:py-20">
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
        <div className="space-y-8">
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
            {[
              ["Attempts", stats.totals.attempts],
              ["Allowed", stats.totals.allowed],
              ["Blocked", stats.totals.blocked],
              ["Escalated", stats.totals.escalated],
            ].map(([label, value]) => (
              <div key={label as string} className="card p-4 text-center">
                <p className="mono-num text-2xl font-medium">{value}</p>
                <p className="text-xs text-ink-faint mt-1">{label}</p>
              </div>
            ))}
          </div>

          <div>
            <h2 className="label-eyebrow mb-3">
              Flags {stats.flags.length > 0 && `(${stats.flags.length})`}
            </h2>
            {stats.flags.length === 0 ? (
              <p className="text-sm text-ink-muted">Nothing flagged in this window.</p>
            ) : (
              <div className="space-y-3">
                {stats.flags.map((f, i) => (
                  <motion.div
                    key={`${f.agent_id}-${f.flag_type}`}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="card p-5"
                  >
                    <div className="flex items-center gap-3 mb-2">
                      <span className={`badge ${SEVERITY_STYLE[f.severity]}`}>{f.severity}</span>
                      <span className="text-sm font-medium">{FLAG_LABEL[f.flag_type] ?? f.flag_type}</span>
                      <span className="text-xs text-ink-faint ml-auto">agent: {f.agent_id}</span>
                    </div>
                    <p className="text-sm text-ink-muted">
                      {explanationFor(f.agent_id) ?? f.detail}
                    </p>
                  </motion.div>
                ))}
              </div>
            )}
          </div>

          <div>
            <h2 className="label-eyebrow mb-3">Every agent seen in this window</h2>
            {stats.agents.length === 0 ? (
              <p className="text-sm text-ink-muted">No agents yet.</p>
            ) : (
              <div className="card overflow-hidden">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-ink-faint">
                      <th className="px-5 py-3 font-normal">Agent</th>
                      <th className="px-5 py-3 font-normal">Attempts</th>
                      <th className="px-5 py-3 font-normal">Allowed</th>
                      <th className="px-5 py-3 font-normal">Blocked</th>
                      <th className="px-5 py-3 font-normal">Last seen</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.agents.map((a) => (
                      <tr key={a.agent_id} className="border-b border-border last:border-0">
                        <td className="px-5 py-3 font-medium">{a.agent_id}</td>
                        <td className="px-5 py-3 mono-num">{a.attempts}</td>
                        <td className="px-5 py-3 mono-num">{a.allowed}</td>
                        <td className="px-5 py-3 mono-num">{a.blocked}</td>
                        <td className="px-5 py-3 text-ink-faint">
                          {new Date(a.last_seen).toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
