import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2, Plus } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { ApiError } from "@/shared/lib/api-client";
import { registerRepository } from "@/shared/api/repositories";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";

export function ConnectRepoForm() {
  const [url, setUrl] = useState("");
  const queryClient = useQueryClient();

  const registerMutation = useMutation({
    mutationFn: registerRepository,
    onSuccess: (repo) => {
      void queryClient.invalidateQueries({ queryKey: ["repositories"] });
      setUrl("");
      toast.success(`Connected ${repo.name}`);
    },
    onError: (error) => {
      if (error instanceof ApiError && error.status === 409) {
        toast.error("That repository is already connected.");
      } else {
        toast.error(error.message);
      }
    },
  });

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        if (url.trim()) registerMutation.mutate(url.trim());
      }}
      className="surface-card ring-gradient flex items-center gap-2 p-1.5"
    >
      <Input
        type="text"
        value={url}
        onChange={(event) => setUrl(event.target.value)}
        placeholder="https://github.com/owner/repo.git"
        className="flex-1 border-0 bg-transparent shadow-none focus-visible:ring-0"
      />
      <Button type="submit" disabled={registerMutation.isPending || !url.trim()}>
        {registerMutation.isPending ? (
          <Loader2 className="size-4 animate-spin" />
        ) : (
          <Plus className="size-4" />
        )}
        Connect
      </Button>
    </form>
  );
}
