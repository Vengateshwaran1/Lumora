import { motion } from "framer-motion";

interface AnimatedTabsProps<T extends string> {
  tabs: { value: T; label: string }[];
  value: T;
  onChange: (value: T) => void;
  className?: string;
}

/** Tab strip with a sliding active-pill indicator (shared layoutId). Used
 * for lightweight app-level tab switches that don't need shadcn's Tabs. */
export function AnimatedTabs<T extends string>({
  tabs,
  value,
  onChange,
  className,
}: AnimatedTabsProps<T>) {
  return (
    <div className={`bg-muted inline-flex items-center gap-1 rounded-lg p-1 ${className ?? ""}`}>
      {tabs.map((tab) => (
        <button
          key={tab.value}
          type="button"
          onClick={() => onChange(tab.value)}
          className="relative rounded-md px-3 py-1.5 text-sm font-medium transition-colors"
        >
          {value === tab.value ? (
            <motion.span
              layoutId="animated-tabs-indicator"
              className="bg-background absolute inset-0 rounded-md shadow-sm"
              transition={{ type: "spring", stiffness: 500, damping: 35 }}
            />
          ) : null}
          <span
            className={`relative z-10 ${value === tab.value ? "text-foreground" : "text-muted-foreground"}`}
          >
            {tab.label}
          </span>
        </button>
      ))}
    </div>
  );
}
