"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  getPolicy,
  savePolicy,
  draftPolicyFromText,
  getPolicyHistory,
  MERCHANT_ID,
  type Policy,
  type PolicyHistoryEntry,
} from "@/lib/api";

// Minimal shape of the browser's built-in Web Speech API -- not part of
// TypeScript's standard DOM lib, and we only need a few fields of it.
type SpeechRecognitionEventLike = {
  results: ArrayLike<ArrayLike<{ transcript: string }>>;
  resultIndex: number;
};
type SpeechRecognitionLike = {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start: () => void;
  stop: () => void;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
};
type SpeechRecognitionCtor = new () => SpeechRecognitionLike;

const DEFAULT_POLICY: Policy = {
  merchant_id: MERCHANT_ID,
  max_order_value: 1000000, // Rs 10,000 in paise
  deny_categories: ["gift_card"],
  allow_categories: [],
  max_units_per_sku: 5,
  escalate_above: null,
  require_signed_identity: true,
  allow_cod_for_agents: false,
  max_orders_per_agent_per_window: null,
  velocity_window_minutes: 60,
};

function Toggle({
  checked,
  onChange,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className="relative inline-flex h-6 w-10 shrink-0 items-center rounded-full transition-colors duration-150"
      style={{ background: checked ? "var(--accent)" : "var(--border-strong)" }}
    >
      <span
        className="inline-block h-[18px] w-[18px] transform rounded-full bg-white shadow transition-transform duration-150"
        style={{ transform: checked ? "translateX(19px)" : "translateX(3px)" }}
      />
    </button>
  );
}

function Section({
  eyebrow,
  title,
  children,
}: {
  eyebrow: string;
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="grid sm:grid-cols-[180px_1fr] gap-4 sm:gap-8 py-8 first:pt-0 border-b border-border last:border-0 last:pb-0">
      <div>
        <p className="label-eyebrow mb-1.5">{eyebrow}</p>
        <h3 className="display text-base font-medium">{title}</h3>
      </div>
      <div className="space-y-6">{children}</div>
    </div>
  );
}

export default function PolicyPage() {
  const [policy, setPolicy] = useState<Policy>(DEFAULT_POLICY);
  const [categoriesText, setCategoriesText] = useState(DEFAULT_POLICY.deny_categories.join(", "));
  const [allowCategoriesText, setAllowCategoriesText] = useState(DEFAULT_POLICY.allow_categories.join(", "));
  const [status, setStatus] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [plainEnglish, setPlainEnglish] = useState("");
  const [drafting, setDrafting] = useState(false);
  const [draftError, setDraftError] = useState("");

  // Not every owner wants to type out their rules -- this feeds the
  // exact same textarea the AI drafter already reads, using the
  // browser's own built-in speech recognition. No backend change: by
  // the time text lands here, it's indistinguishable from typing.
  const [listening, setListening] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(true);
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);

  useEffect(() => {
    const SpeechRecognition =
      (window as unknown as { SpeechRecognition?: SpeechRecognitionCtor }).SpeechRecognition ||
      (window as unknown as { webkitSpeechRecognition?: SpeechRecognitionCtor }).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSpeechSupported(false);
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.lang = "en-IN";
    recognition.onresult = (event: SpeechRecognitionEventLike) => {
      // Real bug, found live: in continuous mode, event.results is
      // cumulative across the whole listening session -- every prior
      // utterance is still in there. Joining the whole array on every
      // firing and prepending it onto text that already has those same
      // earlier words duplicated everything said before the last pause.
      // event.resultIndex marks where the NEW results start; only those
      // are new speech since the previous firing.
      let newText = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        newText += event.results[i][0].transcript;
      }
      if (!newText.trim()) return;
      setPlainEnglish((prev) => (prev ? `${prev} ${newText}` : newText));
    };
    recognition.onerror = () => setListening(false);
    recognition.onend = () => setListening(false);
    recognitionRef.current = recognition;
  }, []);

  function toggleListening() {
    if (!recognitionRef.current) return;
    if (listening) {
      recognitionRef.current.stop();
      setListening(false);
    } else {
      recognitionRef.current.start();
      setListening(true);
    }
  }

  const [history, setHistory] = useState<PolicyHistoryEntry[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);

  function loadHistory() {
    setHistoryLoading(true);
    getPolicyHistory(MERCHANT_ID)
      .then(setHistory)
      .catch(() => {})
      .finally(() => setHistoryLoading(false));
  }

  useEffect(() => {
    getPolicy(MERCHANT_ID)
      .then((p) => {
        setPolicy(p);
        setCategoriesText(p.deny_categories.join(", "));
        setAllowCategoriesText(p.allow_categories.join(", "));
      })
      .catch(() => {})
      .finally(() => setLoading(false));
    loadHistory();
  }, []);

  async function handleSave() {
    setStatus("saving…");
    try {
      const toSave: Policy = {
        ...policy,
        deny_categories: categoriesText.split(",").map((c) => c.trim()).filter(Boolean),
        allow_categories: allowCategoriesText.split(",").map((c) => c.trim()).filter(Boolean),
      };
      await savePolicy(toSave);
      setStatus("Saved — these rules are live.");
      loadHistory(); // this save is now part of the record too
    } catch (e) {
      setStatus(`Failed to save: ${(e as Error).message}`);
    }
  }

  // Loads a past version into the form -- does NOT save it. Same rule as
  // the plain-English drafter: nothing from history becomes live rules
  // until the merchant reviews it and clicks Save themselves.
  function loadFromHistory(entry: PolicyHistoryEntry) {
    setPolicy(entry.policy);
    setCategoriesText(entry.policy.deny_categories.join(", "));
    setAllowCategoriesText(entry.policy.allow_categories.join(", "));
    setStatus(
      `Loaded rules from ${new Date(entry.saved_at).toLocaleString()} — review, then Save to make this active again.`
    );
  }

  async function handleDraft() {
    setDrafting(true);
    setDraftError("");
    try {
      const { draft } = await draftPolicyFromText(MERCHANT_ID, plainEnglish);
      setPolicy({ ...policy, ...draft });
      setCategoriesText(draft.deny_categories.join(", "));
      setAllowCategoriesText(draft.allow_categories.join(", "));
      setStatus("Draft filled in below — review it, then Save to apply.");
    } catch (e) {
      setDraftError((e as Error).message);
    } finally {
      setDrafting(false);
    }
  }

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-6 py-24">
        <p className="label-eyebrow">Loading…</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-16 sm:py-20">
      <p className="label-eyebrow mb-3">Merchant policy</p>
      <h1 className="display text-3xl sm:text-4xl font-medium mb-3">Your rules for AI agents</h1>
      <p className="text-ink-muted max-w-xl leading-relaxed mb-10">
        Every order an agent tries to place is checked against this rulebook before anything
        happens with money. Change anything, save, and it applies immediately.
      </p>

      <div className="grid lg:grid-cols-[1fr_300px] gap-10 items-start">
      <div className="min-w-0 max-w-3xl">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
        className="card p-7 mb-6 bg-paper-2/60"
      >
        <div className="flex items-center justify-between mb-1 gap-3">
          <p className="field-label mb-0">Describe your rules in plain English instead</p>
          {speechSupported && (
            <button
              type="button"
              onClick={toggleListening}
              className={`btn text-xs px-3 py-1.5 border shrink-0 ${
                listening ? "btn-danger" : "btn-ghost border-border"
              }`}
            >
              {listening ? "● Stop" : "🎙 Speak instead"}
            </button>
          )}
        </div>
        <p className="field-hint mb-3 mt-0">
          AI turns this into the fields below — it only fills the form, it never saves by itself.
          {speechSupported && " Don't want to type? Tap the mic and just talk."}
        </p>
        <textarea
          className="field-input resize-none"
          rows={3}
          placeholder="e.g. don't let agents buy gift cards, cap orders at 5000 rupees, anything over 2000 needs my approval first"
          value={plainEnglish}
          onChange={(e) => setPlainEnglish(e.target.value)}
        />
        <div className="flex items-center gap-3 mt-3">
          <button
            onClick={handleDraft}
            disabled={drafting || !plainEnglish.trim()}
            className="btn btn-secondary"
          >
            {drafting ? "Drafting…" : "Draft rules from this"}
          </button>
          {listening && (
            <p className="text-sm text-accent flex items-center gap-1.5">
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-accent animate-pulse" />
              Listening…
            </p>
          )}
          {draftError && <p className="text-sm text-danger">{draftError}</p>}
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.08, ease: [0.16, 1, 0.3, 1] }}
        className="card p-7 sm:p-9"
      >
        <Section eyebrow="Money" title="Spending limits">
          <div>
            <label className="field-label">Maximum order value (₹)</label>
            <input
              type="number"
              className="field-input max-w-xs"
              value={policy.max_order_value / 100}
              onChange={(e) =>
                setPolicy({ ...policy, max_order_value: Math.round(Number(e.target.value) * 100) })
              }
            />
            <p className="field-hint">Any single order above this is blocked, or escalated below.</p>
          </div>
          <div>
            <label className="field-label">Escalate to human review above (₹, optional)</label>
            <input
              type="number"
              className="field-input max-w-xs"
              placeholder="leave blank to disable"
              value={policy.escalate_above ? policy.escalate_above / 100 : ""}
              onChange={(e) =>
                setPolicy({
                  ...policy,
                  escalate_above: e.target.value ? Math.round(Number(e.target.value) * 100) : null,
                })
              }
            />
            <p className="field-hint">
              Orders above this value that pass every rule get flagged for a human instead of
              going straight through.
            </p>
          </div>
        </Section>

        <Section eyebrow="Catalog" title="What's banned">
          <div>
            <label className="field-label">Banned categories (comma separated)</label>
            <input
              type="text"
              className="field-input"
              value={categoriesText}
              onChange={(e) => setCategoriesText(e.target.value)}
              placeholder="gift_card, clearance"
            />
            <p className="field-hint">An order containing any of these categories is blocked outright.</p>
          </div>
          <div>
            <label className="field-label">Allowed categories only (comma separated, optional)</label>
            <input
              type="text"
              className="field-input"
              value={allowCategoriesText}
              onChange={(e) => setAllowCategoriesText(e.target.value)}
              placeholder="e.g. electronics, daily_essentials — leave blank to allow everything except banned"
            />
            <p className="field-hint">
              For a big catalog, naming every banned category by hand doesn&apos;t scale. Set
              this instead to restrict agents to ONLY these categories — everything else is
              blocked, no matter what&apos;s in the banned list above. Leave blank if you&apos;d
              rather just ban a few specific ones.
            </p>
          </div>
          <div>
            <label className="field-label">Max units of one item per order</label>
            <input
              type="number"
              className="field-input max-w-xs"
              value={policy.max_units_per_sku}
              onChange={(e) => setPolicy({ ...policy, max_units_per_sku: Number(e.target.value) })}
            />
          </div>
        </Section>

        <Section eyebrow="India" title="Cash on Delivery">
          <div className="flex items-start justify-between gap-6">
            <div>
              <p className="text-sm font-medium">Allow agents to place COD orders</p>
              <p className="field-hint mt-1 max-w-sm">
                No agentic-commerce protocol governs COD — it needs zero payment authorization to
                place. Off by default; an agent order is prepaid unless you opt in here.
              </p>
            </div>
            <Toggle
              checked={policy.allow_cod_for_agents}
              onChange={(v) => setPolicy({ ...policy, allow_cod_for_agents: v })}
            />
          </div>
        </Section>

        <Section eyebrow="Frequency" title="Velocity limit">
          <div className="flex flex-wrap gap-6">
            <div>
              <label className="field-label">Max orders per agent</label>
              <input
                type="number"
                className="field-input w-32"
                placeholder="no limit"
                value={policy.max_orders_per_agent_per_window ?? ""}
                onChange={(e) =>
                  setPolicy({
                    ...policy,
                    max_orders_per_agent_per_window: e.target.value ? Number(e.target.value) : null,
                  })
                }
              />
            </div>
            <div>
              <label className="field-label">Per window (minutes)</label>
              <input
                type="number"
                className="field-input w-32"
                value={policy.velocity_window_minutes}
                onChange={(e) => setPolicy({ ...policy, velocity_window_minutes: Number(e.target.value) })}
              />
            </div>
          </div>
          <p className="field-hint -mt-2">
            UPI Reserve Pay itself caps retries at 3 in 24h — the regulator already treats
            frequency, not just size, as the primary risk.
          </p>
        </Section>

        <Section eyebrow="Trust" title="Identity">
          <div className="flex items-start justify-between gap-6">
            <div>
              <p className="text-sm font-medium">Require every agent to sign its cart</p>
              <p className="field-hint mt-1 max-w-sm">
                Without a valid signature, no cart can be trusted as coming from the agent it
                claims to be.
              </p>
            </div>
            <Toggle
              checked={policy.require_signed_identity}
              onChange={(v) => setPolicy({ ...policy, require_signed_identity: v })}
            />
          </div>
        </Section>

        <div className="pt-8 flex items-center gap-4">
          <motion.button whileTap={{ scale: 0.97 }} onClick={handleSave} className="btn btn-primary">
            Save rules
          </motion.button>
          <AnimatePresence mode="wait">
            {status && (
              <motion.p
                key={status}
                initial={{ opacity: 0, x: -6 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0 }}
                className="text-sm text-ink-muted"
              >
                {status}
              </motion.p>
            )}
          </AnimatePresence>
        </div>
      </motion.div>
      </div>

      <div className="lg:sticky lg:top-8">
        <p className="label-eyebrow mb-3">Saved rules, over time</p>
        {historyLoading && <p className="text-sm text-ink-muted">Loading…</p>}
        {!historyLoading && history.length === 0 && (
          <p className="text-sm text-ink-muted">
            Nothing saved yet — your first save will show up here.
          </p>
        )}
        <div className="space-y-2 max-h-[70vh] overflow-y-auto pr-1">
          {history.map((entry, i) => (
            <button
              key={entry.id}
              onClick={() => loadFromHistory(entry)}
              className="card w-full text-left p-4 hover:border-accent-soft-border transition-colors"
            >
              <p className="text-xs text-ink-faint mb-1.5">
                {new Date(entry.saved_at).toLocaleString()}
                {i === 0 && <span className="badge badge-allow ml-2 text-[10px] px-1.5 py-0.5">current</span>}
              </p>
              <p className="text-sm font-medium mono-num">
                ₹{(entry.policy.max_order_value / 100).toLocaleString()} limit
              </p>
              <p className="text-xs text-ink-muted mt-0.5">
                {entry.policy.allow_categories.length > 0
                  ? `only ${entry.policy.allow_categories.length} categor${entry.policy.allow_categories.length === 1 ? "y" : "ies"} allowed`
                  : entry.policy.deny_categories.length > 0
                  ? `${entry.policy.deny_categories.length} banned categor${entry.policy.deny_categories.length === 1 ? "y" : "ies"}`
                  : "no banned categories"}
                {" · "}
                COD {entry.policy.allow_cod_for_agents ? "on" : "off"}
              </p>
            </button>
          ))}
        </div>
      </div>
      </div>
    </div>
  );
}
