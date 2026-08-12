import { useMutation } from "@tanstack/react-query";
import { Loader2, Plus } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { registerRepository } from "@/shared/api/repositories";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";

import { useReposStore } from "./store";

export function ConnectRepoForm() {
  const [url, setUrl] = useState("");
  const addTracked = useReposStore((state) => state.addTracked);

  const registerMutation = useMutation({
    mutationFn: registerRepository,
    onSuccess: (repo) => {
      addTracked({ id: repo.id, url: repo.url });
      setUrl("");
      toast.success(`Connected ${repo.name}`);
    },
    onError: (error) => toast.error(error.message),
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
