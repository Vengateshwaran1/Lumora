import { CommitTimeline } from "./commit-timeline";
import { SectionBand } from "./section-band";
import { SectionHeading } from "./section-heading";

export function EngineeringMemorySection() {
  return (
    <SectionBand grid>
      <div className="flex flex-col gap-14">
        <SectionHeading
          index="08"
          eyebrow="Memory"
          title="Engineering has a memory."
          subtitle="Current code connects back to the commits, issues, pull requests, and decisions that shaped it — context that compounds instead of evaporating."
        />
        <CommitTimeline />
      </div>
    </SectionBand>
  );
}
