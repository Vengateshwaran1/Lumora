import { ReviewDiffPanel } from "./review-diff-panel";
import { SectionBand } from "./section-band";
import { SectionHeading } from "./section-heading";

export function HumanApprovalSection() {
  return (
    <SectionBand grid>
      <div className="grid gap-12 lg:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)] lg:items-center lg:gap-16">
        <SectionHeading
          index="07"
          eyebrow="Human in the loop"
          title="Autonomous does not mean uncontrolled."
          subtitle="Every agent-authored change waits for a human approval gate before it ships — full autonomy is a setting, not a default."
        />
        <ReviewDiffPanel />
      </div>
    </SectionBand>
  );
}
