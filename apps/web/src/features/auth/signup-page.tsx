import { Loader2 } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { Reveal } from "@/components/motion/reveal";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { PasswordInput } from "@/shared/components/ui/password-input";

export function SignupPage() {
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    window.setTimeout(() => void navigate("/onboarding"), 550);
  }

  return (
    <div className="flex flex-col gap-5">
      <Reveal>
        <div>
          <h1 className="text-lg font-semibold tracking-tight">Create your account</h1>
          <p className="text-muted-foreground text-sm">
            Authentication isn't enabled yet — continue to explore the app.
          </p>
        </div>
      </Reveal>
      <form className="flex flex-col gap-3" onSubmit={handleSubmit}>
        <Reveal delay={0.05}>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="name">Name</Label>
            <Input id="name" type="text" autoComplete="name" />
          </div>
        </Reveal>
        <Reveal delay={0.1}>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="email">Work email</Label>
            <Input id="email" type="email" placeholder="you@company.com" autoComplete="email" />
          </div>
        </Reveal>
        <Reveal delay={0.15}>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="password">Password</Label>
            <PasswordInput id="password" autoComplete="new-password" />
          </div>
        </Reveal>
        <Reveal delay={0.2}>
          <Button type="submit" disabled={submitting} className="mt-2 w-full">
            {submitting ? <Loader2 className="size-4 animate-spin" /> : null}
            {submitting ? "Creating account…" : "Create account"}
          </Button>
        </Reveal>
      </form>
      <p className="text-muted-foreground text-center text-xs">
        Already have an account?{" "}
        <Link to="/login" className="text-primary">
          Sign in
        </Link>
      </p>
    </div>
  );
}
