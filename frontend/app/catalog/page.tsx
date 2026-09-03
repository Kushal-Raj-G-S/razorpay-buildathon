"use client";

import { useState } from "react";
import { catalogFromText, MERCHANT_ID, type CatalogProduct } from "@/lib/api";

const EXAMPLE = `Blue Tshirt L 499/-
Red shirt medium size rs450
Gift voucher worth 2000 rupees
leather wallet brown 899 rs
denim jeans size 32 waist rupees 1299`;

export default function CatalogPage() {
  const [rawText, setRawText] = useState(EXAMPLE);
  const [products, setProducts] = useState<CatalogProduct[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleIngest() {
    setLoading(true);
    setError("");
    try {
      const result = await catalogFromText(MERCHANT_ID, rawText);
      setProducts(result.catalog.products);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-16">
      <h1 className="text-2xl font-semibold mb-2">Your product list</h1>
      <p className="text-sm text-zinc-500 mb-8">
        Paste your products however they&apos;re written — messy prices, mixed formats, whatever
        you&apos;ve got. AI turns it into a clean, structured catalog an AI shopping agent can
        actually read. This is saved immediately for the demo.
      </p>

      <div className="bg-white border border-zinc-200 rounded-lg p-6 mb-6">
        <textarea
          className="w-full rounded border border-zinc-300 px-3 py-2 text-sm font-mono"
          rows={6}
          value={rawText}
          onChange={(e) => setRawText(e.target.value)}
        />
        <button
          onClick={handleIngest}
          disabled={loading || !rawText.trim()}
          className="mt-3 rounded bg-zinc-900 text-white px-4 py-2 text-sm font-medium hover:bg-zinc-700 disabled:opacity-50"
        >
          {loading ? "Reading your products…" : "Turn this into a catalog"}
        </button>
        {error && <p className="text-sm text-red-600 mt-2">{error}</p>}
      </div>

      {products && (
        <div className="space-y-2">
          <p className="text-sm text-zinc-500 mb-2">
            {products.length} product{products.length !== 1 ? "s" : ""} found:
          </p>
          {products.map((p) => (
            <div key={p.id} className="rounded border border-zinc-200 bg-white p-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="font-medium">{p.title}</span>
                <span>Rs {(p.variants[0].price / 100).toFixed(2)}</span>
              </div>
              <div className="text-xs text-zinc-400 mt-1">
                category: {p.variants[0].category || "none"}
                {p.variants[0].category === "gift_card" && (
                  <span className="text-red-500 ml-2">
                    ← this would be blocked if your rules deny gift_card
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
