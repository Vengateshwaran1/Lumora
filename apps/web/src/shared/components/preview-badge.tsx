import { Sparkles } from "lucide-react";

import { Badge } from "@/shared/components/ui/badge";

/** Marks any surface backed by `shared/mocks/*` instead of a live endpoint.
 * Never omit this on mock-backed UI — see ARCHITECTURE.md §14, M3-M5. */
export function PreviewBadge({ className }: { className?: string }) {
  return (
    <Badge
      variant="outline"
      className={`border-ai-activity/40 text-ai-activity gap-1 ${className ?? ""}`}
    >
      <Sparkles className="h-3 w-3" />
      Preview — arrives in M3+
    </Badge>
  );
}
