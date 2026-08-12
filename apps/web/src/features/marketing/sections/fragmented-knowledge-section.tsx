import { CodeCitationPanel } from "./code-citation-panel";
import { SectionBand } from "./section-band";
import { SectionHeading } from "./section-heading";

export function FragmentedKnowledgeSection() {
  return (
    <SectionBand grid>
      <div className="grid gap-12 lg:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)] lg:items-center lg:gap-16">
        <SectionHeading
          index="01"
          eyebrow="Fragmented knowledge"
          title="Your codebase already knows the answer."
          subtitle="Code, commits, issues, pull requests, docs, and tests — Lumora connects what's already there instead of asking your team to explain it again."
        />
        <CodeCitationPanel />
      </div>
    </SectionBand>
  );
}
