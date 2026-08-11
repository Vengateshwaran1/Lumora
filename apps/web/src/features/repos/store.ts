import { create } from "zustand";
import { persist } from "zustand/middleware";

interface TrackedRepo {
  id: string;
  url: string;
}

interface ReposStore {
  tracked: TrackedRepo[];
  addTracked: (repo: TrackedRepo) => void;
  removeTracked: (id: string) => void;
}

/** Which repositories this browser has connected — ephemeral client state
 * (app/providers.tsx's rule: no backend "list my repos" endpoint exists
 * yet, so there's no server state to duplicate here; this is genuinely
 * local bookkeeping, persisted so a page refresh doesn't lose it). */
export const useReposStore = create<ReposStore>()(
  persist(
    (set) => ({
      tracked: [],
      addTracked: (repo) =>
        set((state) => ({
          tracked: state.tracked.some((r) => r.id === repo.id)
            ? state.tracked
            : [...state.tracked, repo],
        })),
      removeTracked: (id) =>
        set((state) => ({ tracked: state.tracked.filter((r) => r.id !== id) })),
    }),
    { name: "lumora.repos" },
  ),
);
