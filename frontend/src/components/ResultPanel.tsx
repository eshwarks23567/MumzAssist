"use client";
import { motion } from "framer-motion";
import type { TriageResult } from "@/lib/api";

const fadeUp = (delay = 0) => ({
  initial: { opacity: 0, y: 14 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.3, delay },
});

const SENTIMENT_COLOR: Record<string, string> = {
  positive: "#22c55e",
  neutral: "#a1a1aa",
  negative: "#f97316",
  very_negative: "#ef4444",
};

const URG_COLOR: Record<number, { bg: string; border: string; text: string; dot: string }> = {
  1: { bg: "#052e16", border: "#166534", text: "#86efac", dot: "#22c55e" },
  2: { bg: "#1a2e05", border: "#3f6212", text: "#bef264", dot: "#84cc16" },
  3: { bg: "#2d1b00", border: "#92400e", text: "#fcd34d", dot: "#eab308" },
  4: { bg: "#2d0d00", border: "#9a3412", text: "#fdba74", dot: "#f97316" },
  5: { bg: "#2d0011", border: "#9f1239", text: "#fca5a5", dot: "#f43f5e" },
};

const URG_LABEL: Record<number, string> = {
  1: "Low", 2: "Slightly Elevated", 3: "Moderate", 4: "High", 5: "Critical",
};

interface Props { result: TriageResult; model: string; elapsed: number }

export default function ResultPanel({ result, model, elapsed }: Props) {
  const urg = URG_COLOR[result.urgency] ?? URG_COLOR[3];
  const sc = SENTIMENT_COLOR[result.sentiment] ?? "#a1a1aa";
  const { extracted_entities: ent } = result;

  const pills = [
    { label: "Language",   value: result.message_language.toUpperCase() },
    { label: "Intent",     value: result.intent.replace(/_/g, " ") },
    { label: "Urgency",    value: `${result.urgency}/5` },
    { label: "Confidence", value: `${(result.confidence * 100).toFixed(0)}%` },
    { label: "Sentiment",  value: result.sentiment.replace(/_/g, " "), color: sc },
    { label: "Time",       value: `${elapsed.toFixed(1)}s`, color: "#71717a" },
  ];

  return (
    <motion.div {...fadeUp()} className="space-y-4">
      {/* Escalation alert */}
      {result.should_escalate && (
        <motion.div
          {...fadeUp(0.05)}
          className="flex gap-3 items-start p-4 rounded-xl border"
          style={{ background: "rgba(239,68,68,0.07)", borderColor: "rgba(239,68,68,0.2)" }}
        >
          <span className="text-lg">🚨</span>
          <div>
            <p className="text-[10px] font-bold uppercase tracking-wider text-red-400 mb-1">Escalate to human agent</p>
            <p className="text-sm text-red-300/80 leading-relaxed">{result.escalation_reason}</p>
          </div>
        </motion.div>
      )}

      {/* Metric pills */}
      <motion.div {...fadeUp(0.08)} className="grid grid-cols-3 sm:grid-cols-6 gap-2">
        {pills.map(({ label, value, color }) => (
          <div
            key={label}
            className="bg-white/[0.03] border border-white/[0.06] rounded-xl p-3 text-center"
          >
            <p className="text-[9px] font-bold uppercase tracking-wider text-[#e91e8c] mb-1">{label}</p>
            <p className="text-sm font-semibold capitalize" style={{ color: color ?? "#fafafa" }}>
              {value}
            </p>
          </div>
        ))}
      </motion.div>

      {/* Urgency bar */}
      <motion.div
        {...fadeUp(0.12)}
        className="flex items-start gap-3 px-4 py-3 rounded-xl border text-sm"
        style={{ background: urg.bg + "99", borderColor: urg.border, color: urg.text }}
      >
        <span
          className="w-2 h-2 rounded-full flex-shrink-0 mt-1.5"
          style={{ background: urg.dot }}
        />
        <p className="leading-relaxed">
          <strong>Urgency {result.urgency} — {URG_LABEL[result.urgency]}:</strong>{" "}
          {result.urgency_reasoning}
        </p>
      </motion.div>

      {/* Action + entities row */}
      <div className="grid grid-cols-2 gap-4">
        <motion.div {...fadeUp(0.16)} className="bg-white/[0.03] border border-white/[0.06] rounded-xl p-4">
          <p className="text-[9px] font-bold uppercase tracking-wider text-zinc-500 mb-3">Action & Tools</p>
          <span className="inline-block px-3 py-1 rounded-full text-xs font-semibold bg-[#e91e8c]/10 border border-[#e91e8c]/20 text-[#e91e8c] mb-3">
            {result.suggested_action.replace(/_/g, " ")}
          </span>
          <div className="flex flex-wrap gap-1.5 mb-3">
            {result.tools_used.length > 0 ? result.tools_used.map(t => (
              <span key={t} className="px-2 py-0.5 rounded-full text-[11px] bg-violet-500/10 border border-violet-500/20 text-violet-300">
                ⚙ {t}
              </span>
            )) : (
              <span className="text-xs text-zinc-600">No tools called</span>
            )}
          </div>
          <p className={`text-xs font-semibold ${result.grounded_on_data ? "text-green-400" : "text-amber-400"}`}>
            {result.grounded_on_data ? "✓ Grounded on live data" : "⚠ Heuristic reply"}
          </p>
        </motion.div>

        <motion.div {...fadeUp(0.18)} className="bg-white/[0.03] border border-white/[0.06] rounded-xl p-4">
          <p className="text-[9px] font-bold uppercase tracking-wider text-zinc-500 mb-3">Extracted Entities</p>
          <div className="flex flex-wrap gap-1.5">
            {ent.order_ids.map(x =>    <Tag key={x} color="pink"  label={`⊞ ${x}`} />)}
            {ent.product_names.map(x => <Tag key={x} color="green" label={`· ${x}`} />)}
            {ent.dates_mentioned.map(x => <Tag key={x} color="amber" label={`◷ ${x}`} />)}
            {ent.amount_mentioned &&    <Tag color="violet" label={`◈ ${ent.amount_mentioned}`} />}
            {ent.customer_name &&       <Tag color="sky"    label={`◎ ${ent.customer_name}`} />}
            {!ent.order_ids.length && !ent.product_names.length && !ent.dates_mentioned.length && !ent.amount_mentioned && !ent.customer_name && (
              <span className="text-xs text-zinc-600">None detected</span>
            )}
          </div>
        </motion.div>
      </div>

      {/* Reply tabs */}
      <motion.div {...fadeUp(0.22)} className="bg-white/[0.03] border border-white/[0.06] rounded-xl p-4">
        <ReplyBlock result={result} />
      </motion.div>

      {/* Model info */}
      <motion.div {...fadeUp(0.26)}>
        <p className="text-[11px] text-zinc-600 text-right">
          <span className="text-[#e91e8c]">●</span> {model}
        </p>
      </motion.div>
    </motion.div>
  );
}

function Tag({ color, label }: { color: string; label: string }) {
  const map: Record<string, string> = {
    pink:   "bg-pink-500/10 border-pink-500/20 text-pink-300",
    green:  "bg-green-500/10 border-green-500/20 text-green-300",
    amber:  "bg-amber-500/10 border-amber-500/20 text-amber-300",
    violet: "bg-violet-500/10 border-violet-500/20 text-violet-300",
    sky:    "bg-sky-500/10 border-sky-500/20 text-sky-300",
  };
  return (
    <span className={`px-2 py-0.5 rounded-full text-[11px] border ${map[color]}`}>{label}</span>
  );
}

function ReplyBlock({ result }: { result: TriageResult }) {
  const isAr = result.message_language === "ar";
  return (
    <div>
      <p className="text-[9px] font-bold uppercase tracking-wider text-zinc-500 mb-4">Suggested Reply · Maya</p>
      <div className="space-y-4">
        <div>
          <p className="text-[10px] text-zinc-600 mb-2">
            {isAr ? "Arabic — customer language" : "English — customer language"}
          </p>
          <div className="flex gap-3">
            <div className="w-8 h-8 flex-shrink-0 rounded-full bg-gradient-to-br from-[#e91e8c] to-[#f06292] flex items-center justify-center text-sm">🌸</div>
            <div
              className="flex-1 bg-zinc-800/60 rounded-[2px_12px_12px_12px] px-4 py-3 text-sm text-zinc-200 leading-relaxed"
              style={isAr ? { direction: "rtl", textAlign: "right", borderRadius: "12px 2px 12px 12px" } : {}}
            >
              {result.suggested_reply_original_language}
            </div>
          </div>
        </div>

        {isAr && (
          <div>
            <p className="text-[10px] text-zinc-600 mb-2">English — supervisor copy</p>
            <div className="flex gap-3">
              <div className="w-8 h-8 flex-shrink-0 rounded-full bg-gradient-to-br from-purple-600 to-fuchsia-600 flex items-center justify-center text-sm">🌸</div>
              <div className="flex-1 bg-purple-900/20 border border-purple-500/15 rounded-[2px_12px_12px_12px] px-4 py-3 text-sm text-zinc-300 leading-relaxed">
                {result.suggested_reply_english}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
