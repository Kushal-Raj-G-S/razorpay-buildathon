"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  getPolicy,
  savePolicy,
  draftPolicyFromText,
  getPolicyHistory,
  searchCatalog,
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

// Typeable dropdown for categories: pick from the merchant's real
// catalog (so a typo can't silently create a category that never
// matches anything at checkout), or type a new one for a category not
// in the catalog yet. Deliberately not a plain <select> -- a merchant
// picking two or three categories out of dozens needs to type to
// filter, not scroll a giant list.
function CategoryPicker({
  values,
  onChange,
  options,
  placeholder,
  tone,
}: {
  values: string[];
  onChange: (next: string[]) => void;
  options: string[];
  placeholder?: string;
  tone: "deny" | "allow";
}) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const filtered = options.filter(
    (o) => !values.includes(o) && o.toLowerCase().includes(query.trim().toLowerCase())
  );
  const canAddNew = query.trim() && !options.includes(query.trim()) && !values.includes(query.trim());

  function add(category: string) {
    const trimmed = category.trim();
    if (!trimmed || values.includes(trimmed)) return;
    onChange([...values, trimmed]);
    setQuery("");
    setOpen(false);
  }
  function remove(category: string) {
    onChange(values.filter((v) => v !== category));
  }

  return (
    <div className="relative">
      <div className="field-input flex flex-wrap gap-1.5 items-center min-h-[42px] py-1.5">
        {values.map((v) => (
          <span key={v} className={`badge text-xs flex items-center gap-1 ${tone === "deny" ? "badge-block" : "badge-allow"}`}>
            {v}
            <button
              type="button"
              onClick={() => remove(v)}
              className="hover:opacity-60"
              aria-label={`remove ${v}`}
            >
              ×
            </button>
          </span>
        ))}
        <input
          type="text"
          className="flex-1 min-w-[120px] bg-transparent outline-none text-sm"
          value={query}
          placeholder={values.length === 0 ? placeholder : ""}
          onChange={(e) => {
            setQuery(e.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 150)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && query.trim()) {
              e.preventDefault();
              add(query);
            } else if (e.key === "Backspace" && !query && values.length > 0) {
              remove(values[values.length - 1]);
            }
          }}
        />
      </div>
      {open && (filtered.length > 0 || canAddNew) && (
        <div className="absolute z-20 mt-1 w-full card p-1 max-h-52 overflow-y-auto shadow-lg">
          {filtered.map((o) => (
            <button
              key={o}
              type="button"
              onMouseDown={() => add(o)}
              className="block w-full text-left px-3 py-1.5 text-sm rounded hover:bg-paper-2"
            >
              {o}
            </button>
          ))}
          {canAddNew && (
            <button
              type="button"
              onMouseDown={() => add(query)}
              className="block w-full text-left px-3 py-1.5 text-sm rounded hover:bg-paper-2 text-accent"
            >
              Add &quot;{query.trim()}&quot;
            </button>
          )}
        </div>
      )}
    </div>
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
  const [knownCategories, setKnownCategories] = useState<string[]>([]);
  const [categoryError, setCategoryError] = useState("");
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
      .then((p) => setPolicy(p))
      .catch(() => {})
      .finally(() => setLoading(false));
    loadHistory();

    // Categories are whatever's actually in the merchant's own catalog --
    // pulling them from there means picking from a real list instead of
    // typing a category name from memory and hoping it matches exactly
    // what the catalog uses (a typo here would silently never match
    // anything at checkout).
    searchCatalog(MERCHANT_ID)
      .then((res) => {
        const cats = new Set(
          res.products.flatMap((p) => p.variants.map((v) => v.category).filter((c): c is string => !!c))
        );
        setKnownCategories([...cats].sort());
      })
      .catch(() => {});
  }, []);

  // A category can't be both "only this is allowed" and "this is
  // banned" at once -- functionally harmless (either check alone would
  // still block it) but genuinely contradictory, and worth stopping
  // before save rather than letting a confusing policy go live quietly.
  // Both lists being EMPTY, on the other hand, is a completely normal
  // state -- it just means categories aren't a concern for this
  // merchant -- so that's never blocked here.
  function overlapBetween(deny: string[], allow: string[]): string[] {
    return deny.filter((c) => allow.includes(c));
  }

  async function handleSave() {
    const overlap = overlapBetween(policy.deny_categories, policy.allow_categories);
    if (overlap.length > 0) {
      setCategoryError(
        `${overlap.join(", ")} ${overlap.length === 1 ? "is" : "are"} in both the banned and ` +
          `allowed lists -- that's a contradiction. Remove ${overlap.length === 1 ? "it" : "them"} from one.`
      );
      return;
    }
    setCategoryError("");
    setStatus("saving…");
    try {
      await savePolicy(policy);
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
    setCategoryError("");
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
        This page is the rulebook. Every single order an AI shopping agent tries to place gets
        checked against these rules before any money moves. Change something below, click Save,
        and it takes effect on the very next order — no delay.
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
            <p className="field-hint">
              If one order costs more than this, it&apos;s blocked outright. No exceptions.
            </p>
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
              An order under the block limit above, but over this amount, doesn&apos;t go through
              automatically — it waits for you to approve or reject it by hand. Leave blank to
              skip this step entirely.
            </p>
          </div>
        </Section>

        <Section eyebrow="Catalog" title="What's banned">
          {categoryError && (
            <div className="card px-4 py-3 text-sm bg-danger-soft text-danger">{categoryError}</div>
          )}
          <div>
            <label className="field-label">Banned categories</label>
            <CategoryPicker
              tone="deny"
              values={policy.deny_categories}
              onChange={(next) => {
                setCategoryError("");
                setPolicy({ ...policy, deny_categories: next });
              }}
              options={knownCategories}
              placeholder="Type or pick from your catalog — e.g. gift_card"
            />
            <p className="field-hint">An order containing any of these categories is blocked outright.</p>
          </div>
          <div>
            <label className="field-label">Allowed categories only (optional)</label>
            <CategoryPicker
              tone="allow"
              values={policy.allow_categories}
              onChange={(next) => {
                setCategoryError("");
                setPolicy({ ...policy, allow_categories: next });
              }}
              options={knownCategories}
              placeholder="Leave empty to allow everything except banned"
            />
            <p className="field-hint">
              For a big catalog, naming every banned category by hand doesn&apos;t scale. Set
              this instead to restrict agents to ONLY these categories — everything else is
              blocked, no matter what&apos;s in the banned list above. Leaving both this and the
              banned list empty is perfectly normal — it just means categories aren&apos;t a
              concern for you, and only your other rules (price, COD, frequency) apply.
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
            <p className="field-hint">
              An agent trying to buy more than this many of the exact same item in one order gets
              blocked, even if the total price is still under the spending limit above.
            </p>
          </div>
        </Section>

        <Section eyebrow="India" title="Cash on Delivery">
          <div className="flex items-start justify-between gap-6">
            <div>
              <p className="text-sm font-medium">Allow agents to place COD orders</p>
              <p className="field-hint mt-1 max-w-sm">
                Cash on Delivery means no payment happens online at all — the order is confirmed
                with zero money changing hands upfront. That makes it riskier to let an AI agent
                place one unsupervised. Off means every agent order needs real payment first. Turn
                this on only if you&apos;re fine with agents placing pay-later orders.
              </p>
            </div>
            <Toggle
              checked={policy.allow_cod_for_agents}
              onChange={(v) => setPolicy({ ...policy, allow_cod_for_agents: v })}
            />
          </div>
        </Section>

        <Section eyebrow="Frequency" title="Velocity limit">
          <p className="text-sm text-ink-muted -mt-2">
            This isn&apos;t about how much one order costs — it&apos;s about how often the same
            agent orders. If one agent places more than the number below within the time window
            below, its next order is blocked until the window resets.
          </p>
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
                Every real agent proves who it is with a digital signature — cryptographic proof
                that can&apos;t be faked. If this is on, an order with no signature (or a fake
                one) is blocked, no matter what&apos;s in the cart. Turn it off only for quick
                testing, like the &quot;Try it&quot; demo page.
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
        <p className="label-eyebrow mb-1">Saved rules, over time</p>
        <p className="text-xs text-ink-muted mb-3 max-w-[260px]">
          Every time you click &quot;Save rules,&quot; a snapshot is kept here permanently — it
          can never be deleted, like a paper trail. Click one to load it back into the form on the
          left, then click Save again to make it live.
        </p>
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
