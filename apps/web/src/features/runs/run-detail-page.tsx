import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Check, Loader2, X } from "lucide-react";
import { useCallback, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";

import { useRunEvents } from "@/shared/api/run-events";
import { approveRun, getRun, regenerateRun, rejectRun } from "@/shared/api/runs";
import { ACTIVE_RUN_STATUSES, type RunEvent, type RunStatus } from "@/shared/api/types";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/shared/components/ui/accordion";
import { Button } from "@/shared/components/ui/button";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { Textarea } from "@/shared/components/ui/textarea";
import { cn } from "@/shared/lib/utils";

import { RunStatusBadge } from "./run-status-badge";

const BASE_STEPS: { key: RunStatus; label: string }[] = [
  { key: "queued", label: "Queued" },
  { key: "running", label: "Running" },
  { key: "awaiting_approval", label: "Awaiting approval" },
];

const BASE_INDEX: Record<RunStatus, number> = {
  queued: 0,
  running: 1,
  awaiting_approval: 2,
  plan_approved: 3,
  rejected: 3,
  failed: 1,
};

function StringList({ items }: { items: string[] }) {
  if (items.length === 0) return <p className="text-muted-foreground text-sm">None.</p>;
  return (
    <ul className="list-inside list-disc space-y-1 text-sm">
      {items.map((item, i) => (
        <li key={i}>{item}</li>
      ))}
    </ul>
  );
}

function FileChips({ files }: { files: string[] }) {
  if (files.length === 0) return <p className="text-muted-foreground text-sm">None.</p>;
  return (
    <div className="flex flex-wrap gap-1.5">
      {files.map((file) => (
        <code key={file} className="bg-muted rounded px-1.5 py-0.5 text-xs">
          {file}
        </code>
      ))}
    </div>
  );
}

export function RunDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [reason, setReason] = useState("");

  const runQuery = useQuery({
    queryKey: ["run", id],
    queryFn: () => getRun(id!),
    enabled: !!id,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && ACTIVE_RUN_STATUSES.includes(status) ? 2000 : false;
    },
  });

  const status = runQuery.data?.status;
  const isActive = !!status && ACTIVE_RUN_STATUSES.includes(status);

  const handleEvent = useCallback((event: RunEvent) => {
    if (event.event === "run.queued") {
      toast.info("Run queued for processing");
    }
  }, []);

  useRunEvents(id, isActive, handleEvent);

  const approveMutation = useMutation({
    mutationFn: () => approveRun(id!, reason.trim() || undefined),
    onSuccess: (data) => {
      queryClient.setQueryData(["run", id], data);
      toast.success("Plan approved");
    },
    onError: (error) => toast.error(error.message),
  });

  const rejectMutation = useMutation({
    mutationFn: () => rejectRun(id!, reason.trim() || undefined),
    onSuccess: (data) => {
      queryClient.setQueryData(["run", id], data);
      toast.success("Plan rejected");
    },
    onError: (error) => toast.error(error.message),
  });

  const regenerateMutation = useMutation({
    mutationFn: () => regenerateRun(id!),
    onSuccess: (data) => {
      toast.success("Regenerating plan in a new run");
      void navigate(`/app/runs/${data.run_id}`);
    },
    onError: (error) => toast.error(error.message),
  });

  const anyPending =
    approveMutation.isPending || rejectMutation.isPending || regenerateMutation.isPending;

  if (runQuery.isPending) return <Skeleton className="h-96 rounded-lg" />;
  if (runQuery.isError)
    return <p className="text-destructive text-sm">{runQuery.error.message}</p>;

  const run = runQuery.data;
  const plan = run.implementation_plan;
  const currentIndex = BASE_INDEX[run.status];
  const isTerminalDecision = run.status === "plan_approved" || run.status === "rejected";

  return (
    <div className="flex max-w-3xl flex-col gap-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Planning run</h1>
          <p className="text-muted-foreground text-sm">
            {run.created_at ? `Created ${new Date(run.created_at).toLocaleString()}` : null}
          </p>
        </div>
        <RunStatusBadge status={run.status} />
      </div>

      {run.status === "failed" ? (
        <div className="border-destructive/30 bg-destructive/5 rounded-lg border p-4">
          <div className="flex items-center gap-2">
            <AlertTriangle className="text-destructive size-4" />
            <p className="text-destructive text-sm font-medium">Run failed</p>
          </div>
          {run.error_message ? (
            <p className="text-muted-foreground mt-1 text-xs">{run.error_message}</p>
          ) : null}
        </div>
      ) : null}

      <ol className="flex flex-col gap-0">
        {BASE_STEPS.map((step, index) => {
          const isFailedHere = run.status === "failed" && index === currentIndex;
          const stepStatus: "done" | "active" | "pending" | "failed" = isFailedHere
            ? "failed"
            : index < currentIndex || isTerminalDecision
              ? "done"
              : index === currentIndex
                ? "active"
                : "pending";

          return (
            <li key={step.key} className="flex gap-3">
              <div className="flex flex-col items-center">
                <div
                  className={cn(
                    "flex size-6 items-center justify-center rounded-full border text-xs",
                    stepStatus === "done" && "bg-success border-success text-success-foreground",
                    stepStatus === "active" && "border-ai-activity text-ai-activity",
                    stepStatus === "pending" && "border-border text-muted-foreground",
                    stepStatus === "failed" && "bg-destructive border-destructive text-white",
                  )}
                >
                  {stepStatus === "done" ? (
                    <Check className="size-3.5" />
                  ) : stepStatus === "active" ? (
                    <Loader2 className="size-3.5 animate-spin" />
                  ) : stepStatus === "failed" ? (
                    <X className="size-3.5" />
                  ) : (
                    index + 1
                  )}
                </div>
                {index < BASE_STEPS.length - 1 ? (
                  <div
                    className={cn(
                      "w-px flex-1",
                      stepStatus === "done" ? "bg-success" : "bg-border",
                    )}
                  />
                ) : null}
              </div>
              <div className="flex-1 pb-6">
                <p
                  className={cn(
                    "text-sm font-medium",
                    stepStatus === "active" && "text-ai-activity",
                    stepStatus === "pending" && "text-muted-foreground",
                  )}
                >
                  {step.label}
                </p>
              </div>
            </li>
          );
        })}
        {isTerminalDecision ? (
          <li className="flex gap-3">
            <div className="flex flex-col items-center">
              <div
                className={cn(
                  "flex size-6 items-center justify-center rounded-full border text-xs",
                  run.status === "plan_approved" &&
                    "bg-success border-success text-success-foreground",
                  run.status === "rejected" && "bg-destructive border-destructive text-white",
                )}
              >
                {run.status === "plan_approved" ? (
                  <Check className="size-3.5" />
                ) : (
                  <X className="size-3.5" />
                )}
              </div>
            </div>
            <div className="flex-1 pb-2">
              <p className="text-sm font-medium">
                {run.status === "plan_approved" ? "Plan approved" : "Plan rejected"}
              </p>
            </div>
          </li>
        ) : null}
      </ol>

      {run.validation_errors.length > 0 ? (
        <div className="border-destructive/30 bg-destructive/5 rounded-lg border p-4">
          <div className="flex items-center gap-2">
            <AlertTriangle className="text-destructive size-4" />
            <p className="text-destructive text-sm font-medium">Plan validation issues</p>
          </div>
          <ul className="text-muted-foreground mt-2 list-inside list-disc space-y-1 text-xs">
            {run.validation_errors.map((error, i) => (
              <li key={i}>{error}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {plan ? (
        <div className="flex flex-col gap-4">
          <div className="surface-card p-4">
            <p className="text-sm font-medium">Summary</p>
            <p className="text-muted-foreground mt-1 text-sm leading-relaxed">{plan.summary}</p>
            <div className="mt-3 flex items-center gap-2">
              <span className="text-muted-foreground text-xs">Confidence</span>
              <div className="bg-muted h-1.5 w-32 overflow-hidden rounded-full">
                <div
                  className="bg-primary h-full"
                  style={{ width: `${Math.round(plan.confidence * 100)}%` }}
                />
              </div>
              <span className="text-xs font-medium tabular-nums">
                {Math.round(plan.confidence * 100)}%
              </span>
            </div>
          </div>

          <Accordion
            type="multiple"
            defaultValue={["understanding", "implementation-steps"]}
            className="surface-card px-4"
          >
            <AccordionItem value="understanding">
              <AccordionTrigger>Understanding</AccordionTrigger>
              <AccordionContent>
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{plan.understanding}</p>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="affected-files">
              <AccordionTrigger>Affected Files ({plan.affected_files.length})</AccordionTrigger>
              <AccordionContent>
                <FileChips files={plan.affected_files} />
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="affected-components">
              <AccordionTrigger>
                Affected Components ({plan.affected_components.length})
              </AccordionTrigger>
              <AccordionContent>
                <StringList items={plan.affected_components} />
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="implementation-steps">
              <AccordionTrigger>
                Implementation Steps ({plan.implementation_steps.length})
              </AccordionTrigger>
              <AccordionContent>
                <div className="flex flex-col gap-3">
                  {plan.implementation_steps.map((step) => (
                    <div key={step.step_number} className="border-border rounded-md border p-3">
                      <p className="text-sm font-medium">
                        Step {step.step_number}: {step.description}
                      </p>
                      <p className="text-muted-foreground mt-1 text-xs">{step.reason}</p>
                      <dl className="mt-2 grid grid-cols-1 gap-1.5 text-xs sm:grid-cols-2">
                        <div>
                          <dt className="text-muted-foreground">Affected files</dt>
                          <dd className="mt-0.5">
                            <FileChips files={step.affected_files} />
                          </dd>
                        </div>
                        <div>
                          <dt className="text-muted-foreground">Affected symbols</dt>
                          <dd className="mt-0.5">
                            <FileChips files={step.affected_symbols} />
                          </dd>
                        </div>
                        <div>
                          <dt className="text-muted-foreground">Depends on steps</dt>
                          <dd className="mt-0.5">
                            {step.depends_on_steps.length > 0
                              ? step.depends_on_steps.join(", ")
                              : "None"}
                          </dd>
                        </div>
                        <div>
                          <dt className="text-muted-foreground">Verification</dt>
                          <dd className="mt-0.5">{step.verification_method}</dd>
                        </div>
                      </dl>
                    </div>
                  ))}
                </div>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="dependencies">
              <AccordionTrigger>Dependencies ({plan.dependencies.length})</AccordionTrigger>
              <AccordionContent>
                <StringList items={plan.dependencies} />
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="database-changes">
              <AccordionTrigger>Database Changes ({plan.database_changes.length})</AccordionTrigger>
              <AccordionContent>
                <StringList items={plan.database_changes} />
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="api-changes">
              <AccordionTrigger>API Changes ({plan.api_changes.length})</AccordionTrigger>
              <AccordionContent>
                <StringList items={plan.api_changes} />
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="frontend-changes">
              <AccordionTrigger>Frontend Changes ({plan.frontend_changes.length})</AccordionTrigger>
              <AccordionContent>
                <StringList items={plan.frontend_changes} />
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="testing-strategy">
              <AccordionTrigger>Testing Strategy</AccordionTrigger>
              <AccordionContent>
                <p className="text-sm leading-relaxed whitespace-pre-wrap">
                  {plan.testing_strategy}
                </p>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="security-considerations">
              <AccordionTrigger>
                Security Considerations ({plan.security_considerations.length})
              </AccordionTrigger>
              <AccordionContent>
                <StringList items={plan.security_considerations} />
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="performance-considerations">
              <AccordionTrigger>
                Performance Considerations ({plan.performance_considerations.length})
              </AccordionTrigger>
              <AccordionContent>
                <StringList items={plan.performance_considerations} />
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="risks">
              <AccordionTrigger>Risks ({plan.risks.length})</AccordionTrigger>
              <AccordionContent>
                <StringList items={plan.risks} />
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="assumptions">
              <AccordionTrigger>Assumptions ({plan.assumptions.length})</AccordionTrigger>
              <AccordionContent>
                <StringList items={plan.assumptions} />
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="acceptance-criteria">
              <AccordionTrigger>
                Acceptance Criteria ({plan.acceptance_criteria.length})
              </AccordionTrigger>
              <AccordionContent>
                <StringList items={plan.acceptance_criteria} />
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="citations">
              <AccordionTrigger>Citations ({plan.citations.length})</AccordionTrigger>
              <AccordionContent>
                {plan.citations.length === 0 ? (
                  <p className="text-muted-foreground text-sm">None.</p>
                ) : (
                  <ul className="space-y-1.5 text-sm">
                    {plan.citations.map((citation, i) => (
                      <li key={i}>
                        <code className="bg-muted rounded px-1.5 py-0.5 text-xs">
                          {citation.file_path}:{citation.start_line}-{citation.end_line}
                        </code>{" "}
                        — {citation.claim}
                      </li>
                    ))}
                  </ul>
                )}
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </div>
      ) : run.status === "running" || run.status === "queued" ? (
        <p className="text-muted-foreground text-sm">
          The Planning Agent hasn't produced a plan yet — this page updates automatically.
        </p>
      ) : null}

      {run.status === "awaiting_approval" ? (
        <div className="border-approval/30 bg-approval/5 flex flex-col gap-3 rounded-lg border p-4">
          <div>
            <p className="text-approval text-sm font-medium">Awaiting human approval</p>
            <p className="text-muted-foreground mt-1 text-xs">
              Autonomous does not mean uncontrolled — review the plan above before approving,
              rejecting, or asking for a regenerated plan.
            </p>
          </div>
          <Textarea
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            placeholder="Optional reason (used for approve or reject)"
            className="min-h-16"
          />
          <div className="flex flex-wrap gap-2">
            <Button
              size="sm"
              onClick={() => approveMutation.mutate()}
              disabled={anyPending}
            >
              {approveMutation.isPending ? (
                <Loader2 className="size-3.5 animate-spin" />
              ) : (
                <Check className="size-3.5" />
              )}
              Approve
            </Button>
            <Button
              variant="destructive"
              size="sm"
              onClick={() => rejectMutation.mutate()}
              disabled={anyPending}
            >
              {rejectMutation.isPending ? (
                <Loader2 className="size-3.5 animate-spin" />
              ) : (
                <X className="size-3.5" />
              )}
              Reject
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => regenerateMutation.mutate()}
              disabled={anyPending}
            >
              {regenerateMutation.isPending ? <Loader2 className="size-3.5 animate-spin" /> : null}
              Regenerate
            </Button>
          </div>
        </div>
      ) : null}

      <Link
        to="/app/issues"
        className="text-muted-foreground hover:text-foreground text-xs underline"
      >
        Back to issues
      </Link>
    </div>
  );
}
