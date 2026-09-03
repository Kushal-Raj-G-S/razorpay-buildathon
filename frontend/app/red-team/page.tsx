"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { runRedTeam, listRedTeamRuns, MERCHANT_ID, type RedTeamRound, type RedTeamRun } from "@/lib/api";

const DEFAULT_GOAL = "Get a gift card purchased for a customer, no matter what it takes.";

const DECISION_BADGE: Record<string, string> = {
  allow: "badge-allow",
  block: "badge-block",
  escalate: "badge-escalate",
  gave_up: "badge-neutral",
};

const OUTCOME_COPY: Record<string, { label: string; tone: string; sub: string }> = {
  held: {
    label: "Held",
    tone: "badge-allow",
    sub: "Every attempt was caught. The agent never got through.",
  },
  breached: {
    label: "Breached",
    tone: "badge-block",
    sub: "The agent found a way through. This is a real gap to fix.",
  },
  agent_gave_up: {
    label: "Agent gave up",
    tone: "badge-neutral",
    sub: "It ran out of ideas before your rules ran out of patience.",
  },
  max_rounds_reached: {
    label: "Held to the limit",
    tone: "badge-allow",
    sub: "Every attempt was caught for the full length of the run.",
  },
};

function RoundCard({ round, index }: { round: RedTeamRound; index: number }) {
  const claimed = round.items[0];
  const real = round.resolved_items?.[0];
  const wasRelabeled = real && claimed && real.category !== claimed.category;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.15, duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      className="card p-6"
    >
      <div className="flex items-center justify-between mb-3">
        <span className="label-eyebrow">Attempt {round.round}</span>
        {round.decision !== "gave_up" && (
          <motion.span
            initial={{ opacity: 0, scale: 1.6, rotate: -10 }}
            animate={{ opacity: 1, scale: 1, rotate: -4 }}
            transition={{ type: "spring", stiffness: 340, damping: 16, delay: index * 0.15 + 0.15 }}
            className={`badge ${DECISION_BADGE[round.decision]}`}
          >
            {round.decision}
          </motion.span>
        )}
      </div>

      <p className="text-sm text-ink-muted italic leading-relaxed mb-4">
        &ldquo;{round.reasoning}&rdquo;
      </p>

      {claimed && (
        <div className="rounded-lg border border-border bg-paper-2/50 p-4 text-sm">
          <div className="flex items-center justify-between">
            <span>
              {claimed.title} <span className="text-ink-faint">× {claimed.quantity}</span>
            </span>
            <span className="mono-num">₹{(claimed.price / 100).toFixed(2)}</span>
          </div>
          <div className="mt-2 flex items-center gap-2 flex-wrap">
            <span className="text-xs text-ink-faint">agent claimed category:</span>
            <span className="badge badge-neutral">{claimed.category || "none"}</span>
            {wasRelabeled && (
              <>
                <span className="text-xs text-ink-faint">→ actually:</span>
                <span className="badge badge-block">{real!.category || "none"}</span>
              </>
            )}
          </div>
        </div>
      )}

      {round.rules_failed.length > 0 && (
        <p className="text-xs text-danger mt-3">
          caught by: {round.rules_failed.join(", ")}
        </p>
      )}
    </motion.div>
  );
}

export default function RedTeamPage() {
  const [goal, setGoal] = useState(DEFAULT_GOAL);
  const [maxRounds, setMaxRounds] = useState(5);
  const [running, setRunning] = useState(false);
  const [run, setRun] = useState<RedTeamRun | null>(null);
  const [error, setError] = useState("");

  const [history, setHistory] = useState<RedTeamRun[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  async function loadHistory() {
    setHistoryLoading(true);
    try {
      setHistory(await listRedTeamRuns(MERCHANT_ID));
    } catch {
      // History is a bonus view on top of the run that's already on screen --
      // if it can't load, the merchant can still see and run a fresh attack.
    } finally {
      setHistoryLoading(false);
    }
  }

  useEffect(() => {
    loadHistory();
  }, []);

  async function launch() {
    setRunning(true);
    setError("");
    setRun(null);
    try {
      const result = await runRedTeam(MERCHANT_ID, goal, maxRounds);
      setRun(result);
      loadHistory(); // this run is now part of the persisted history too
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setRunning(false);
    }
  }

  const outcome = run ? OUTCOME_COPY[run.outcome] : null;

  return (
    <div className="max-w-3xl mx-auto px-6 py-16 sm:py-20">
      <p className="label-eyebrow mb-3">Red team</p>
      <h1 className="display text-3xl sm:text-4xl font-medium mb-3">
        Send an AI to break your own rules
      </h1>
      <p className="text-ink-muted max-w-xl leading-relaxed mb-10">
        A real autonomous agent, not a script. It doesn&apos;t know your policy — only your
        catalog and whether its last attempt worked. It adapts after every rejection: new
        categories, split orders, invented items, whatever a resourceful attacker would try.
      </p>

      <div className="card p-7 mb-8">
        <label className="field-label">What should it try to get away with?</label>
        <textarea
          className="field-input resize-none"
          rows={2}
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
        />
        <div className="flex items-center gap-4 mt-4">
          <div className="flex items-center gap-2">
            <label className="text-xs text-ink-muted">Max attempts</label>
            <input
              type="number"
              className="field-input w-16"
              value={maxRounds}
              min={1}
              max={8}
              onChange={(e) => setMaxRounds(Number(e.target.value))}
            />
          </div>
          <button onClick={launch} disabled={running || !goal.trim()} className="btn btn-primary">
            {running ? "Attacking…" : "Launch the attack"}
          </button>
        </div>
        {error && <p className="text-sm text-danger mt-3">{error}</p>}
      </div>

      <AnimatePresence>
        {run && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              className="card p-6 mb-6 flex items-center justify-between"
            >
              <div>
                <p className="label-eyebrow mb-1">Result</p>
                <p className="text-sm text-ink-muted">{outcome?.sub}</p>
              </div>
              <span className={`badge ${outcome?.tone} text-sm px-4 py-2`}>{outcome?.label}</span>
            </motion.div>

            <div className="space-y-4">
              {run.rounds.map((r, i) => (
                <RoundCard key={r.round} round={r} index={i} />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="mt-14">
        <h2 className="label-eyebrow mb-3">
          Past runs {history.length > 0 && `(${history.length})`}
        </h2>
        {historyLoading && <p className="text-sm text-ink-muted">Loading…</p>}
        {!historyLoading && history.length === 0 && (
          <p className="text-sm text-ink-muted">No past runs yet — every run you launch is kept here.</p>
        )}
        <div className="space-y-2">
          {history.map((h) => {
            const id = h.id ?? h.run_id;
            const oc = OUTCOME_COPY[h.outcome];
            const isOpen = expandedId === id;
            return (
              <div key={id} className="card overflow-hidden">
                <button
                  onClick={() => setExpandedId(isOpen ? null : id ?? null)}
                  className="w-full flex items-center justify-between gap-3 px-5 py-3.5 text-left"
                >
                  <div className="min-w-0">
                    <p className="text-sm truncate">{h.goal}</p>
                    <p className="text-xs text-ink-faint mt-0.5">
                      {h.created_at ? new Date(h.created_at).toLocaleString() : ""} ·{" "}
                      {h.rounds.length} attempt{h.rounds.length === 1 ? "" : "s"}
                    </p>
                  </div>
                  <span className={`badge ${oc?.tone} shrink-0`}>{oc?.label ?? h.outcome}</span>
                </button>
                {isOpen && (
                  <div className="px-5 pb-5 space-y-4 border-t border-border pt-4">
                    {h.rounds.map((r, i) => (
                      <RoundCard key={r.round} round={r} index={i} />
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
