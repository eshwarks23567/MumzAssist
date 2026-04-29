"use client";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CATEGORIZED_EXAMPLES } from "@/lib/examples";

interface Props {
  onSelect: (text: string) => void;
}

export default function ExamplesPanel({ onSelect }: Props) {
  const categories = Object.keys(CATEGORIZED_EXAMPLES);
  const [activeCategory, setActiveCategory] = useState(categories[0]);
  const [activeExample, setActiveExample] = useState<string | null>(null);

  const handleCategory = (cat: string) => {
    setActiveCategory(cat);
    setActiveExample(null);
  };

  const handleExample = (key: string) => {
    setActiveExample(key);
    onSelect(CATEGORIZED_EXAMPLES[activeCategory][key]);
  };

  const examples = Object.entries(CATEGORIZED_EXAMPLES[activeCategory]);

  return (
    <div className="flex flex-col h-full">
      <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-zinc-500 mb-3">
        Examples
      </p>

      {/* Category list */}
      <div className="flex flex-col gap-0.5 mb-3">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => handleCategory(cat)}
            className={`text-left px-3 py-2 rounded-lg text-xs font-medium transition-all duration-150 ${
              activeCategory === cat
                ? "bg-[#e91e8c]/10 text-[#e91e8c] border border-[#e91e8c]/20"
                : "text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.04]"
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      <div className="border-t border-white/[0.06] pt-3 flex-1 overflow-y-auto">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeCategory}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.15 }}
            className="flex flex-col gap-0.5"
          >
            {examples.map(([key]) => (
              <button
                key={key}
                onClick={() => handleExample(key)}
                className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-all duration-150 leading-snug ${
                  activeExample === key
                    ? "bg-[#e91e8c]/10 text-[#e91e8c] border border-[#e91e8c]/20"
                    : "text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.04]"
                }`}
              >
                {key}
              </button>
            ))}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
