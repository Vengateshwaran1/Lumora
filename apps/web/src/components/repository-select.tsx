import { useQueries } from "@tanstack/react-query";

import { useReposStore } from "@/features/repos/store";
import { getIndexStatus } from "@/shared/api/repositories";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/shared/components/ui/select";

interface RepositorySelectProps {
  value: string | null;
  onChange: (repositoryId: string) => void;
  placeholder?: string;
}

/** Repo picker shared by the repo-scoped `/app/knowledge` and `/app/chat`
 * pages — those APIs are per-repository (`POST /repositories/{id}/search|chat`),
 * there's no global search/chat endpoint. */
export function RepositorySelect({
  value,
  onChange,
  placeholder = "Select a repository",
}: RepositorySelectProps) {
  const tracked = useReposStore((state) => state.tracked);

  const results = useQueries({
    queries: tracked.map((repo) => ({
      queryKey: ["repository", repo.id, "index-status"],
      queryFn: () => getIndexStatus(repo.id),
    })),
  });

  return (
    <Select value={value ?? undefined} onValueChange={onChange}>
      <SelectTrigger className="w-full sm:w-72">
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {tracked.map((repo, index) => (
          <SelectItem key={repo.id} value={repo.id}>
            {results[index]?.data?.name ?? repo.url}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
