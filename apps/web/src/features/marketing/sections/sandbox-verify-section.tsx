import { SandboxConsolePanel } from "./sandbox-console-panel";
import { SectionBand } from "./section-band";
import { SectionHeading } from "./section-heading";

export function SandboxVerifySection() {
  return (
    <SectionBand>
      <div className="flex flex-col items-center gap-14">
        <SectionHeading
          align="center"
          index="06"
          eyebrow="Sandboxed execution"
          title="Code is only half the job."
          subtitle="Every patch runs in an isolated sandbox against your real test suite — failures loop back to debugging, not to a pull request."
        />
        <SandboxConsolePanel />
      </div>
    </SectionBand>
  );
}
