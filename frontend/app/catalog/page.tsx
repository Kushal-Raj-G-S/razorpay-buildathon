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
    <div className="max-w-3xl mx-auto px-6 py-16 sm:py-20">
      <p className="label-eyebrow mb-3">Catalog</p>
      <h1 className="display text-3xl sm:text-4xl font-medium mb-3">Your product list, cleaned up</h1>
      <p className="text-ink-muted max-w-xl leading-relaxed mb-10">
        Paste your products however they&apos;re written — messy prices, mixed formats, whatever
        you&apos;ve got. AI turns it into a clean, structured catalog an AI shopping agent can
        actually read.
      </p>

      <div className="card p-7 mb-8">
        <label className="field-label">Raw product text</label>
        <textarea
          className="field-input font-mono text-[0.83rem] resize-none"
          rows={6}
          value={rawText}
          onChange={(e) => setRawText(e.target.value)}
        />
        <div className="flex items-center gap-3 mt-4">
          <button onClick={handleIngest} disabled={loading || !rawText.trim()} className="btn btn-primary">
            {loading ? "Reading your products…" : "Turn this into a catalog"}
          </button>
          {error && <p className="text-sm text-danger">{error}</p>}
        </div>
      </div>

      {products && (
        <div>
          <p className="label-eyebrow mb-4">
            {products.length} product{products.length !== 1 ? "s" : ""} found
          </p>
          <div className="card divide-y divide-border overflow-hidden">
            {products.map((p) => {
              const v = p.variants[0];
              const isRisky = v.category === "gift_card" || v.category === "clearance";
              return (
                <div key={p.id} className="flex items-center justify-between gap-6 px-6 py-4">
                  <div className="min-w-0">
                    <p className="text-sm font-medium truncate">{p.title}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`badge ${isRisky ? "badge-block" : "badge-neutral"}`}>
                        {v.category || "uncategorized"}
                      </span>
                      {isRisky && (
                        <span className="text-xs text-danger">
                          would be blocked if this category is on your deny list
                        </span>
                      )}
                    </div>
                  </div>
                  <span className="mono-num text-sm font-medium shrink-0">
                    ₹{(v.price / 100).toFixed(2)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
