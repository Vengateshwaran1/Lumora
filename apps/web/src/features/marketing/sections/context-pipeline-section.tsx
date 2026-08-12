import { RetrievalConsolePanel } from "./retrieval-console-panel";
import { SectionBand } from "./section-band";
import { SectionHeading } from "./section-heading";

export function ContextPipelineSection() {
  return (
    <SectionBand grid>
      <div className="grid gap-12 lg:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)] lg:items-center lg:gap-16">
        <SectionHeading
          index="02"
          eyebrow="Retrieval, not guessing"
          title="Give AI the context it was missing."
          subtitle="Every answer is grounded in retrieval across your actual codebase — semantic search, symbol graph, and git history combined and reranked, not the model's memory."
        />
        <RetrievalConsolePanel />
      </div>
    </SectionBand>
  );
}
