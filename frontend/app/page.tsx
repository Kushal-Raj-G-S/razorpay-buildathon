import Link from "next/link";

export default function Home() {
  return (
    <div className="max-w-3xl mx-auto px-6 py-16">
      <h1 className="text-4xl font-semibold tracking-tight mb-4">Warrant</h1>
      <p className="text-lg text-zinc-600 mb-8">
        AI agents are starting to shop on Razorpay merchants. Every protocol out there lets the
        <em> buyer</em> put a leash on the agent. None of them let the <em>merchant</em> say what
        it will accept — or prove what it decided. Warrant is that missing half.
      </p>

      <div className="grid gap-4 sm:grid-cols-3">
        <Link
          href="/policy"
          className="rounded-lg border border-zinc-200 bg-white p-5 hover:border-zinc-400 transition"
        >
          <div className="font-medium mb-1">1. Write the rules</div>
          <div className="text-sm text-zinc-500">
            Set what agents may buy, spending limits, banned categories.
          </div>
        </Link>
        <Link
          href="/demo"
          className="rounded-lg border border-zinc-200 bg-white p-5 hover:border-zinc-400 transition"
        >
          <div className="font-medium mb-1">2. Try it</div>
          <div className="text-sm text-zinc-500">
            Send a cart as an AI agent and watch the bouncer decide.
          </div>
        </Link>
        <Link
          href="/receipts"
          className="rounded-lg border border-zinc-200 bg-white p-5 hover:border-zinc-400 transition"
        >
          <div className="font-medium mb-1">3. See the proof</div>
          <div className="text-sm text-zinc-500">
            Every decision, signed, with the exact rule that fired.
          </div>
        </Link>
      </div>

      <p className="text-xs text-zinc-400 mt-10">
        Backend must be running on http://127.0.0.1:8000 — see backend/README for how to start it.
      </p>
    </div>
  );
}
