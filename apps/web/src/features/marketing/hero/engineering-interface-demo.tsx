import { motion } from "framer-motion";
import { FileCode2, GitBranch, Layers, MessageSquare, Search, Sparkles } from "lucide-react";

import { Counter } from "@/components/motion/counter";
import { useReducedMotion } from "@/shared/hooks/use-reduced-motion";

const STATS = [
  { label: "files", value: 1842 },
  { label: "symbols", value: 12421 },
  { label: "issues", value: 284 },
  { label: "PRs", value: 917 },
];

const PIPELINE = [
  { label: "Query", icon: MessageSquare },
  { label: "Retrieval", icon: Search },
  { label: "Relevant files", icon: FileCode2 },
  { label: "Symbols", icon: Layers },
  { label: "Git history", icon: GitBranch },
  { label: "Context", icon: Sparkles },
];

const CITATIONS = ["retry_handler.py:88", "idempotency.py:41", "orders/service.py:212"];

const PIPELINE_STAGGER = 0.12;
const PIPELINE_START = 0.5;
const ANSWER_START = PIPELINE_START + PIPELINE.length * PIPELINE_STAGGER + 0.35;

export function EngineeringInterfaceDemo() {
  const reducedMotion = useReducedMotion();

  return (
    <div className="relative z-10 p-5 sm:p-7">
      <div className="border-border flex flex-wrap items-center justify-between gap-3 border-b pb-4">
        <span className="font-mono text-sm font-medium">acme/payments</span>
        <div className="flex flex-wrap gap-4">
          {STATS.map((stat) => (
            <span key={stat.label} className="text-muted-foreground text-xs">
              <Counter to={stat.value} duration={1.6} className="text-foreground font-semibold" />{" "}
              {stat.label}
            </span>
          ))}
        </div>
      </div>

      <motion.p
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.3 }}
        className="text-foreground mt-5 flex items-center font-mono text-sm"
      >
        "Why does payment retry create duplicate orders?"
        {reducedMotion ? null : (
          <motion.span
            aria-hidden
            className="bg-primary ml-1 inline-block h-[1em] w-[2px]"
            animate={{ opacity: [1, 1, 0, 0] }}
            transition={{ duration: 0.9, repeat: Infinity, ease: "linear", times: [0, 0.5, 0.5, 1] }}
          />
        )}
      </motion.p>

      <div className="mt-6 flex flex-wrap items-center gap-2">
        {PIPELINE.map((step, index) => (
          <motion.div
            key={step.label}
            initial={reducedMotion ? false : { opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              duration: 0.45,
              delay: reducedMotion ? 0 : PIPELINE_START + index * PIPELINE_STAGGER,
            }}
            className="border-engineering/30 bg-engineering/5 text-engineering flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium"
          >
            <step.icon className="size-3.5" />
            {step.label}
          </motion.div>
        ))}
      </div>

      <motion.div
        initial={reducedMotion ? false : { opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: reducedMotion ? 0 : ANSWER_START }}
        className="border-ai-activity/20 bg-ai-activity/5 mt-5 rounded-lg border p-4"
      >
        <p className="text-foreground text-sm leading-relaxed">
          The idempotency key is checked before the retry queue commits, but under a network
          partition the retry consumer can re-enter before the first commit lands — creating a
          duplicate order.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          {CITATIONS.map((citation) => (
            <span
              key={citation}
              className="bg-secondary text-secondary-foreground rounded px-2 py-0.5 font-mono text-[11px]"
            >
              {citation}
            </span>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
