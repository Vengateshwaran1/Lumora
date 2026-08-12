import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { Slot } from "radix-ui";

import { cn } from "@/shared/lib/utils";

const buttonVariants = cva(
  "relative inline-flex shrink-0 cursor-pointer items-center justify-center gap-2 overflow-hidden rounded-md text-sm font-medium whitespace-nowrap outline-none transition-[transform,box-shadow,background-color,border-color,filter] duration-200 ease-[var(--ease-premium)] focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 active:scale-[0.97] active:duration-100 disabled:pointer-events-none disabled:opacity-50 disabled:active:scale-100 aria-invalid:border-destructive aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
  {
    variants: {
      variant: {
        default:
          "shine-sweep bg-[image:var(--primary-gradient)] text-primary-foreground shadow-[var(--shadow-glow-primary)] hover:-translate-y-px hover:shadow-[var(--shadow-glow-primary-hover)] active:translate-y-0",
        destructive:
          "bg-destructive text-white shadow-[0_0_0_1px_rgba(255,107,107,0.3)] hover:bg-destructive/90 hover:shadow-[0_0_0_1px_rgba(255,107,107,0.5),0_8px_20px_-6px_rgba(255,107,107,0.35)] focus-visible:ring-destructive/20 dark:bg-destructive/60 dark:focus-visible:ring-destructive/40",
        outline:
          "shine-sweep border-border bg-background text-foreground border shadow-[var(--shadow-card)] hover:-translate-y-px hover:border-primary/40 hover:shadow-[var(--shadow-card-hover)] active:translate-y-0",
        secondary:
          "shine-sweep bg-secondary text-secondary-foreground border-border/60 border shadow-[var(--shadow-card)] hover:-translate-y-px hover:border-border-strong hover:shadow-[var(--shadow-card-hover)] active:translate-y-0",
        ghost: "hover:bg-surface-hover hover:text-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-9 px-4 py-2 has-[>svg]:px-3",
        xs: "h-6 gap-1 rounded-md px-2 text-xs has-[>svg]:px-1.5 [&_svg:not([class*='size-'])]:size-3",
        sm: "h-8 gap-1.5 rounded-md px-3 has-[>svg]:px-2.5",
        lg: "h-10 rounded-md px-6 has-[>svg]:px-4",
        icon: "size-9",
        "icon-xs": "size-6 rounded-md [&_svg:not([class*='size-'])]:size-3",
        "icon-sm": "size-8",
        "icon-lg": "size-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

function Button({
  className,
  variant = "default",
  size = "default",
  asChild = false,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean;
  }) {
  const Comp = asChild ? Slot.Root : "button";

  return (
    <Comp
      data-slot="button"
      data-variant={variant}
      data-size={size}
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  );
}

export { Button, buttonVariants };
