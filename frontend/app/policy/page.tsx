"use client";

import { useEffect, useState } from "react";
import { getPolicy, savePolicy, MERCHANT_ID, type Policy } from "@/lib/api";

const DEFAULT_POLICY: Policy = {
  merchant_id: MERCHANT_ID,
  max_order_value: 1000000, // Rs 10,000 in paise
  deny_categories: ["gift_card"],
  max_units_per_sku: 5,
  escalate_above: null,
  require_signed_identity: true,
};

export default function PolicyPage() {
  const [policy, setPolicy] = useState<Policy>(DEFAULT_POLICY);
  const [categoriesText, setCategoriesText] = useState(DEFAULT_POLICY.deny_categories.join(", "));
  const [status, setStatus] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getPolicy(MERCHANT_ID)
      .then((p) => {
        setPolicy(p);
        setCategoriesText(p.deny_categories.join(", "));
      })
      .catch(() => {
        // no policy saved yet -- keep the sensible defaults shown above
      })
      .finally(() => setLoading(false));
  }, []);

  async function handleSave() {
    setStatus("saving...");
    try {
      const toSave: Policy = {
        ...policy,
        deny_categories: categoriesText
          .split(",")
          .map((c) => c.trim())
          .filter(Boolean),
      };
      await savePolicy(toSave);
      setStatus("Saved. These rules are now live.");
    } catch (e) {
      setStatus(`Failed to save: ${(e as Error).message}`);
    }
  }

  if (loading) return <div className="max-w-2xl mx-auto px-6 py-16">Loading…</div>;

  return (
    <div className="max-w-2xl mx-auto px-6 py-16">
      <h1 className="text-2xl font-semibold mb-2">Your rules for AI agents</h1>
      <p className="text-sm text-zinc-500 mb-8">
        Every order an AI agent tries to place gets checked against these rules before anything
        happens with money. Change anything, save, and it applies immediately.
      </p>

      <div className="space-y-6 bg-white border border-zinc-200 rounded-lg p-6">
        <div>
          <label className="block text-sm font-medium mb-1">
            Maximum order value (rupees)
          </label>
          <input
            type="number"
            className="w-full rounded border border-zinc-300 px-3 py-2"
            value={policy.max_order_value / 100}
            onChange={(e) =>
              setPolicy({ ...policy, max_order_value: Math.round(Number(e.target.value) * 100) })
            }
          />
          <p className="text-xs text-zinc-400 mt-1">
            Any single order above this amount is blocked (or escalated, see below).
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">
            Banned categories (comma separated)
          </label>
          <input
            type="text"
            className="w-full rounded border border-zinc-300 px-3 py-2"
            value={categoriesText}
            onChange={(e) => setCategoriesText(e.target.value)}
            placeholder="gift_card, clearance"
          />
          <p className="text-xs text-zinc-400 mt-1">
            An order containing any item in these categories is blocked, no matter how small.
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">
            Max units of one item per order
          </label>
          <input
            type="number"
            className="w-full rounded border border-zinc-300 px-3 py-2"
            value={policy.max_units_per_sku}
            onChange={(e) => setPolicy({ ...policy, max_units_per_sku: Number(e.target.value) })}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">
            Escalate to human review above (rupees, optional)
          </label>
          <input
            type="number"
            className="w-full rounded border border-zinc-300 px-3 py-2"
            value={policy.escalate_above ? policy.escalate_above / 100 : ""}
            placeholder="leave blank to disable"
            onChange={(e) =>
              setPolicy({
                ...policy,
                escalate_above: e.target.value ? Math.round(Number(e.target.value) * 100) : null,
              })
            }
          />
          <p className="text-xs text-zinc-400 mt-1">
            Orders above this value that otherwise pass every rule get flagged for a human to
            approve instead of going straight through.
          </p>
        </div>

        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={policy.require_signed_identity}
            onChange={(e) => setPolicy({ ...policy, require_signed_identity: e.target.checked })}
          />
          Require every agent to prove its identity with a signature
        </label>

        <button
          onClick={handleSave}
          className="rounded bg-zinc-900 text-white px-4 py-2 text-sm font-medium hover:bg-zinc-700"
        >
          Save rules
        </button>
        {status && <p className="text-sm text-zinc-500">{status}</p>}
      </div>
    </div>
  );
}
