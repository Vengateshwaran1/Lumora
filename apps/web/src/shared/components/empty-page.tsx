interface EmptyPageProps {
  title: string;
  description: string;
}

/** Placeholder content for a routed feature page pending implementation. */
export function EmptyPage({ title, description }: EmptyPageProps) {
  return (
    <div className="flex flex-col gap-2">
      <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
      <p className="text-muted-foreground text-sm">{description}</p>
    </div>
  );
}
