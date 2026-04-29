"use client";
import { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { runTriage, type TriageResponse } from "@/lib/api";
import ExamplesPanel from "@/components/ExamplesPanel";
import ResultPanel from "@/components/ResultPanel";

const MODES = ["Flash", "Balanced", "Pro"] as const;
type Mode = (typeof MODES)[number];

const MODE_DESC: Record<Mode, string> = {
  Flash:    "Fast",
  Balanced: "General",
  Pro:      "Agentic",
};

export default function Page() {
  const [message, setMessage]   = useState("");
  const [mode, setMode]         = useState<Mode>("Balanced");
  const [loading, setLoading]   = useState(false);
  const [response, setResponse] = useState<TriageResponse | null>(null);
  const [error, setError]       = useState<string | null>(null);
  const [elapsed, setElapsed]   = useState(0);
  const resultRef               = useRef<HTMLDivElement>(null);

  const handleSubmit = async () => {
    if (!message.trim() || loading) return;
    setLoading(true);
    setResponse(null);
    setError(null);
    const t0 = Date.now();
    try {
      const res = await runTriage(message, mode.toLowerCase());
      setElapsed((Date.now() - t0) / 1000);
      setResponse(res);
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 100);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#09090b] font-sans">
      {/* Header */}
      <header className="border-b border-white/[0.05] sticky top-0 z-10 backdrop-blur-sm bg-[#09090b]/80">
        <div className="max-w-[1100px] mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[#e91e8c] to-[#f06292] flex items-center justify-center text-xs">
              🌸
            </div>
            <span className="text-base font-bold tracking-tight text-white">
              mumz<span className="text-[#e91e8c]">world</span>
            </span>
          </div>
          <span className="text-[11px] text-zinc-500 border border-white/[0.07] rounded-full px-3 py-1">
            MumzAssist
          </span>
        </div>
      </header>

      <main className="max-w-[1100px] mx-auto px-6 py-10 space-y-8">
        {/* Title */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <h1 className="text-2xl font-semibold text-white tracking-tight">MumzAssist</h1>
          <p className="text-sm text-zinc-500 mt-1">English & Arabic · AI-powered</p>
        </motion.div>

        {/* Input row */}
        <div className="grid grid-cols-[1fr_260px] gap-5 items-start">
          {/* Left: input card */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.08 }}
            className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-5 space-y-5"
          >
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleSubmit(); }}
              placeholder="Paste or type a customer message (English or Arabic)…"
              rows={5}
              className="w-full bg-white/[0.04] border border-white/[0.07] rounded-xl px-4 py-3 text-sm text-zinc-200 placeholder-zinc-600 resize-none focus:border-[#e91e8c]/40 focus:ring-1 focus:ring-[#e91e8c]/15 transition-all duration-200"
            />

            {/* Mode selector */}
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-zinc-500 mb-2.5">
                Mode
              </p>
              <div className="flex gap-2">
                {MODES.map((m) => (
                  <motion.button
                    key={m}
                    onClick={() => setMode(m)}
                    whileTap={{ scale: 0.96 }}
                    className={`flex-1 py-2 px-2 rounded-lg text-xs font-medium transition-all duration-200 ${
                      mode === m
                        ? "bg-[#e91e8c] text-white shadow-[0_0_18px_rgba(233,30,140,0.28)]"
                        : "bg-white/[0.04] text-zinc-400 hover:bg-white/[0.07] hover:text-zinc-200"
                    }`}
                  >
                    {m}
                    <span className="block text-[9px] font-normal opacity-60 mt-0.5">{MODE_DESC[m]}</span>
                  </motion.button>
                ))}
              </div>
            </div>

            <motion.button
              onClick={handleSubmit}
              disabled={loading || !message.trim()}
              whileTap={{ scale: 0.97 }}
              className="w-full py-2.5 rounded-xl bg-[#e91e8c] text-white text-sm font-semibold disabled:opacity-35 hover:bg-[#c2185b] transition-all duration-200 shadow-[0_4px_20px_rgba(233,30,140,0.22)]"
            >
              {loading ? "Analysing…" : "Triage →"}
            </motion.button>

            <p className="text-[10px] text-zinc-700 text-center">⌘ Enter to submit</p>
          </motion.div>

          {/* Right: examples panel */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.14 }}
            className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-4"
          >
            <ExamplesPanel onSelect={(text) => setMessage(text)} />
          </motion.div>
        </div>

        {/* Result / loading area */}
        <div ref={resultRef}>
          <AnimatePresence mode="wait">
            {loading && (
              <motion.div
                key="loader"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="bg-white/[0.03] border border-white/[0.06] rounded-2xl p-14 flex flex-col items-center gap-5"
              >
                <div className="flex gap-2">
                  {[0, 1, 2].map((i) => (
                    <motion.div
                      key={i}
                      className="w-2.5 h-2.5 rounded-full bg-[#e91e8c]"
                      animate={{ scale: [0.5, 1, 0.5], opacity: [0.3, 1, 0.3] }}
                      transition={{ duration: 1.3, repeat: Infinity, delay: i * 0.2 }}
                    />
                  ))}
                </div>
                <p className="text-sm text-zinc-500">Analysing message…</p>
              </motion.div>
            )}

            {error && !loading && (
              <motion.div
                key="error"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="bg-red-500/[0.07] border border-red-500/20 rounded-2xl p-5 text-sm text-red-400"
              >
                {error}
              </motion.div>
            )}

            {response && !loading && (
              <motion.div
                key="result"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
              >
                <ResultPanel
                  result={response.result}
                  model={response.meta.model}
                  elapsed={elapsed}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}
