import { CheckCircle2, Loader2 } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { Reveal } from "@/components/motion/reveal";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";

export function ForgotPasswordPage() {
  const [sent, setSent] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    window.setTimeout(() => {
      setSubmitting(false);
      setSent(true);
    }, 550);
  }

  if (sent) {
    return (
      <Reveal>
        <div className="flex flex-col items-center gap-3 text-center">
          <div className="bg-success/10 flex size-10 items-center justify-center rounded-full">
            <CheckCircle2 className="text-success size-5" />
          </div>
          <h1 className="text-lg font-semibold tracking-tight">Check your email</h1>
          <p className="text-muted-foreground text-sm">
            If an account exists, a reset link would be sent — authentication isn't enabled yet, so
            this is a preview of the flow.
          </p>
          <Link to="/login" className="text-primary text-sm">
            Back to sign in
          </Link>
        </div>
      </Reveal>
    );
  }

  return (
    <div className="flex flex-col gap-5">
      <Reveal>
        <div>
          <h1 className="text-lg font-semibold tracking-tight">Reset your password</h1>
          <p className="text-muted-foreground text-sm">
            Enter your email and we'll send you a reset link.
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
          <Button type="submit" disabled={submitting} className="mt-2 w-full">
            {submitting ? <Loader2 className="size-4 animate-spin" /> : null}
            {submitting ? "Sending…" : "Send reset link"}
          </Button>
        </Reveal>
      </form>
      <Link to="/login" className="text-muted-foreground hover:text-foreground text-center text-xs">
        Back to sign in
      </Link>
    </div>
  );
}
