import { useRepositories } from "@/shared/api/repositories";
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

/** Repo picker shared by the repo-scoped `/app/knowledge`, `/app/chat`, and
 * `/app/issues` pages — those APIs are per-repository, there's no global
 * search/chat/issues endpoint. */
export function RepositorySelect({
  value,
  onChange,
  placeholder = "Select a repository",
}: RepositorySelectProps) {
  const reposQuery = useRepositories();
  const repos = reposQuery.data ?? [];

  return (
    <Select value={value ?? undefined} onValueChange={onChange}>
      <SelectTrigger className="w-full sm:w-72">
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {repos.map((repo) => (
          <SelectItem key={repo.id} value={repo.id}>
            {repo.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
