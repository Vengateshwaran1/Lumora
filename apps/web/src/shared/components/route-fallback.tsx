import { Loader2 } from "lucide-react";

/** Suspense fallback for lazy-loaded route chunks — brief by design, since
 * each route chunk is small; not a substitute for in-page loading states. */
export function RouteFallback() {
  return (
    <div className="flex min-h-svh items-center justify-center">
      <Loader2 className="text-muted-foreground size-5 animate-spin" />
    </div>
  );
}
