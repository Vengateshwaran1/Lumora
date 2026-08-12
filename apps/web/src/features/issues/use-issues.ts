import { useQuery } from "@tanstack/react-query";

import { listIssues } from "@/shared/api/issues";

/** Issues synced for one repository — shared by the repo-scoped
 * `/app/issues` (via the repo picker) and the repository detail page's
 * Issues tab. */
export function useIssues(repositoryId: string | undefined) {
  return useQuery({
    queryKey: ["repository", repositoryId, "issues"],
    queryFn: () => listIssues(repositoryId!),
    enabled: !!repositoryId,
  });
}
