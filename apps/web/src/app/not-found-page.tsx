import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <div className="flex flex-col gap-2">
      <h1 className="text-2xl font-semibold tracking-tight">Page not found</h1>
      <p className="text-muted-foreground text-sm">
        <Link to="/" className="underline underline-offset-4">
          Return to the dashboard
        </Link>
        .
      </p>
    </div>
  );
}
