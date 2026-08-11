import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import { registerRepository } from "./api";
import { useReposStore } from "./store";

export function ConnectRepoForm() {
  const [url, setUrl] = useState("");
  const addTracked = useReposStore((state) => state.addTracked);

  const registerMutation = useMutation({
    mutationFn: registerRepository,
    onSuccess: (repo) => {
      addTracked({ id: repo.id, url: repo.url });
      setUrl("");
    },
  });

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        if (url.trim()) registerMutation.mutate(url.trim());
      }}
      className="flex items-center gap-2"
    >
      <input
        type="text"
        value={url}
        onChange={(event) => setUrl(event.target.value)}
        placeholder="https://github.com/owner/repo.git"
        className="border-input bg-background flex-1 rounded-md border px-3 py-1.5 text-sm"
      />
      <button
        type="submit"
        disabled={registerMutation.isPending || !url.trim()}
        className="bg-primary text-primary-foreground rounded-md px-3 py-1.5 text-sm font-medium disabled:opacity-50"
      >
        {registerMutation.isPending ? "Connecting…" : "Connect"}
      </button>
      {registerMutation.isError ? (
        <span className="text-destructive text-xs">{registerMutation.error.message}</span>
      ) : null}
    </form>
  );
}
