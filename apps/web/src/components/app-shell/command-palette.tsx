import { FolderGit2 } from "lucide-react";
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

import { useRepositories } from "@/shared/api/repositories";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/shared/components/ui/command";

import { useCommandPaletteStore } from "./command-palette-store";
import { NAV_ITEMS } from "./nav-items";

export function CommandPalette() {
  const open = useCommandPaletteStore((state) => state.open);
  const setOpen = useCommandPaletteStore((state) => state.setOpen);
  const toggle = useCommandPaletteStore((state) => state.toggle);
  const navigate = useNavigate();
  const reposQuery = useRepositories();
  const repos = reposQuery.data ?? [];

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "k" && (event.metaKey || event.ctrlKey)) {
        event.preventDefault();
        toggle();
      }
    }
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [toggle]);

  function go(to: string) {
    setOpen(false);
    void navigate(to);
  }

  return (
    <CommandDialog open={open} onOpenChange={setOpen} title="Command palette">
      <CommandInput placeholder="Search pages, repositories…" />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>
        <CommandGroup heading="Navigate">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <CommandItem key={to} value={label} onSelect={() => go(to)}>
              <Icon />
              {label}
            </CommandItem>
          ))}
        </CommandGroup>
        {repos.length > 0 ? (
          <>
            <CommandSeparator />
            <CommandGroup heading="Repositories">
              {repos.map((repo) => (
                <CommandItem
                  key={repo.id}
                  value={repo.url}
                  onSelect={() => go(`/app/repositories/${repo.id}`)}
                >
                  <FolderGit2 />
                  {repo.url}
                </CommandItem>
              ))}
            </CommandGroup>
          </>
        ) : null}
      </CommandList>
    </CommandDialog>
  );
}
