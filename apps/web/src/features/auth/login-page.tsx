import { Loader2 } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { Reveal } from "@/components/motion/reveal";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { PasswordInput } from "@/shared/components/ui/password-input";

export function LoginPage() {
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    window.setTimeout(() => void navigate("/app"), 550);
  }

  return (
    <div className="flex flex-col gap-5">
      <Reveal>
        <div>
          <h1 className="text-lg font-semibold tracking-tight">Sign in</h1>
          <p className="text-muted-foreground text-sm">
            Authentication isn't enabled yet — continue to explore the app.
          </p>
        </div>
      </Reveal>
      <form className="flex flex-col gap-3" onSubmit={handleSubmit}>
        <Reveal delay={0.05}>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" placeholder="you@company.com" autoComplete="email" />
          </div>
        </Reveal>
        <Reveal delay={0.1}>
          <div className="flex flex-col gap-1.5">
            <div className="flex items-center justify-between">
              <Label htmlFor="password">Password</Label>
              <Link to="/forgot-password" className="text-primary text-xs">
                Forgot?
              </Link>
            </div>
            <PasswordInput id="password" autoComplete="current-password" />
          </div>
        </Reveal>
        <Reveal delay={0.15}>
          <Button type="submit" disabled={submitting} className="mt-2 w-full">
            {submitting ? <Loader2 className="size-4 animate-spin" /> : null}
            {submitting ? "Signing in…" : "Continue to Lumora"}
          </Button>
        </Reveal>
      </form>
      <p className="text-muted-foreground text-center text-xs">
        No account?{" "}
        <Link to="/signup" className="text-primary">
          Sign up
        </Link>
      </p>
    </div>
  );
}
