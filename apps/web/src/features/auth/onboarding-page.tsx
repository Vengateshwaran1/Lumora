import { ArrowRight, Bot, FolderGit2, Search } from "lucide-react";
import { Link } from "react-router-dom";

import { Reveal } from "@/components/motion/reveal";

const STEPS = [
  {
    icon: FolderGit2,
    title: "Connect a repository",
    description:
      "Paste a Git URL — Lumora clones it and builds a searchable, cited knowledge base.",
  },
  {
    icon: Search,
    title: "Search and ask",
    description:
      "Query your codebase with hybrid retrieval, or chat with Lumora for cited answers.",
  },
  {
    icon: Bot,
    title: "Let agents help",
    description:
      "Planning, coding, and review agents arrive in upcoming milestones — foundations are already in place.",
  },
];

export function OnboardingPage() {
  return (
    <div className="bg-background relative flex min-h-svh items-center justify-center px-4 py-12">
      <div className="w-full max-w-lg">
        <Reveal>
          <div className="mb-8 text-center">
            <h1 className="text-2xl font-semibold tracking-tight">Welcome to Lumora</h1>
            <p className="text-muted-foreground mt-1 text-sm">
              Software engineering, with context. Here's how to get started.
            </p>
          </div>
        </Reveal>

        <div className="flex flex-col gap-3">
          {STEPS.map((step, index) => (
            <Reveal key={step.title} delay={index * 0.06}>
              <div className="surface-card flex items-start gap-3 p-4">
                <div className="bg-secondary flex size-8 shrink-0 items-center justify-center rounded-md">
                  <step.icon className="text-primary size-4" />
                </div>
                <div>
                  <p className="text-sm font-medium">{step.title}</p>
                  <p className="text-muted-foreground text-xs">{step.description}</p>
                </div>
              </div>
            </Reveal>
          ))}
        </div>

        <Link
          to="/app/repositories"
          className="bg-primary text-primary-foreground mt-6 flex w-full items-center justify-center gap-1.5 rounded-md px-4 py-2.5 text-sm font-medium"
        >
          Connect your first repository
          <ArrowRight className="size-4" />
        </Link>
      </div>
    </div>
  );
}
