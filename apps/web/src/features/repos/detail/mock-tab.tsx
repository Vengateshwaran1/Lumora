import type { LucideIcon } from "lucide-react";

import { PreviewBadge } from "@/shared/components/preview-badge";

interface MockTabProps {
  icon: LucideIcon;
  title: string;
  description: string;
}

/** Designed empty-state for repo-detail tabs with no backing endpoint yet
 * (Files/Symbols/Dependencies/Issues/Pull Requests/Activity). */
export function MockTab({ icon: Icon, title, description }: MockTabProps) {
  return (
    <div className="border-border flex flex-col items-center gap-3 rounded-lg border border-dashed py-16 text-center">
      <Icon className="text-muted-foreground size-8" />
      <div className="flex items-center gap-2">
        <p className="text-foreground text-sm font-medium">{title}</p>
        <PreviewBadge />
      </div>
      <p className="text-muted-foreground max-w-sm text-xs">{description}</p>
    </div>
  );
}
