"use client";

import { useEffect, useState, type ReactNode } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { getPolicy, savePolicy, draftPolicyFromText, MERCHANT_ID, type Policy } from "@/lib/api";

const DEFAULT_POLICY: Policy = {
  merchant_id: MERCHANT_ID,
  max_order_value: 1000000, // Rs 10,000 in paise
  deny_categories: ["gift_card"],
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
  const [status, setStatus] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [plainEnglish, setPlainEnglish] = useState("");
  const [drafting, setDrafting] = useState(false);
  const [draftError, setDraftError] = useState("");

  useEffect(() => {
    getPolicy(MERCHANT_ID)
      .then((p) => {
        setPolicy(p);
        setCategoriesText(p.deny_categories.join(", "));
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  async function handleSave() {
    setStatus("saving…");
    try {
      const toSave: Policy = {
        ...policy,
        deny_categories: categoriesText.split(",").map((c) => c.trim()).filter(Boolean),
      };
      await savePolicy(toSave);
      setStatus("Saved — these rules are live.");
    } catch (e) {
      setStatus(`Failed to save: ${(e as Error).message}`);
    }
  }

  async function handleDraft() {
    setDrafting(true);
    setDraftError("");
    try {
      const { draft } = await draftPolicyFromText(MERCHANT_ID, plainEnglish);
      setPolicy({ ...policy, ...draft });
      setCategoriesText(draft.deny_categories.join(", "));
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
    <div className="max-w-3xl mx-auto px-6 py-16 sm:py-20">
      <p className="label-eyebrow mb-3">Merchant policy</p>
      <h1 className="display text-3xl sm:text-4xl font-medium mb-3">Your rules for AI agents</h1>
      <p className="text-ink-muted max-w-xl leading-relaxed mb-10">
        Every order an agent tries to place is checked against this rulebook before anything
        happens with money. Change anything, save, and it applies immediately.
      </p>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
        className="card p-7 mb-6 bg-paper-2/60"
      >
        <p className="field-label mb-1">Describe your rules in plain English instead</p>
        <p className="field-hint mb-3 mt-0">
          AI turns this into the fields below — it only fills the form, it never saves by itself.
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
  );
}
