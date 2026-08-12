import { IssuePlanPanel } from "./issue-plan-panel";
import { SectionBand } from "./section-band";
import { SectionHeading } from "./section-heading";

export function IssueToPlanSection() {
  return (
    <SectionBand>
      <div className="flex flex-col items-center gap-14">
        <SectionHeading
          align="center"
          index="04"
          eyebrow="Planning"
          title="From issue to implementation plan."
          subtitle="Every plan traces back to the issue, the relevant code, and its dependencies — reviewable before any code is written."
        />
        <IssuePlanPanel />
      </div>
    </SectionBand>
  );
}
