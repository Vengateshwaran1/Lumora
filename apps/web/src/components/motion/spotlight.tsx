import { useRef, type PointerEvent, type ReactNode } from "react";

import { cn } from "@/shared/lib/utils";

interface SpotlightProps {
  children: ReactNode;
  className?: string;
}

/** Wraps content in a cursor-tracking radial glow (paired with the
 * `.spotlight` CSS class in index.css, which reads the `--sx`/`--sy`
 * custom properties written here). Reserve for a small number of featured
 * surfaces — not every card. */
export function Spotlight({ children, className }: SpotlightProps) {
  const ref = useRef<HTMLDivElement>(null);

  function handlePointerMove(event: PointerEvent<HTMLDivElement>) {
    const node = ref.current;
    if (!node) return;
    const rect = node.getBoundingClientRect();
    node.style.setProperty("--sx", `${((event.clientX - rect.left) / rect.width) * 100}%`);
    node.style.setProperty("--sy", `${((event.clientY - rect.top) / rect.height) * 100}%`);
  }

  return (
    <div ref={ref} onPointerMove={handlePointerMove} className={cn("spotlight", className)}>
      {children}
    </div>
  );
}
