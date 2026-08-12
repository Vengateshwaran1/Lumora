const CAPABILITIES = [
  "Hybrid RAG search",
  "Dependency-aware retrieval",
  "Git history context",
  "Incremental re-indexing",
  "Symbol-level chunking",
  "Sandboxed execution",
  "Human-in-the-loop approval",
  "Multi-agent orchestration",
];

/** Pure-CSS infinite strip of platform capabilities — social-proof-shaped,
 * but honest about what it lists since Lumora has no logo-wall to show yet. */
export function TechMarquee() {
  return (
    <div className="marquee">
      <div className="marquee-track">
        {[...CAPABILITIES, ...CAPABILITIES].map((item, index) => (
          <span
            key={`${item}-${index}`}
            className="text-muted-foreground/70 flex items-center gap-2 px-6 text-sm font-medium whitespace-nowrap"
          >
            <span className="bg-primary/50 size-1 rounded-full" />
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}
