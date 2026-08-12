import {
  Activity,
  Bot,
  CircleDot,
  Code2,
  FolderGit2,
  GitPullRequest,
  LayoutDashboard,
  MessageSquare,
  Search,
  ShieldCheck,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  end?: boolean;
}

/** Primary sidebar nav — same shell across every `/app/*` route. */
export const NAV_ITEMS: NavItem[] = [
  { to: "/app", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/app/repositories", label: "Repositories", icon: FolderGit2 },
  { to: "/app/issues", label: "Issues", icon: CircleDot },
  { to: "/app/knowledge", label: "Knowledge", icon: Search },
  { to: "/app/code", label: "Code", icon: Code2 },
  { to: "/app/chat", label: "AI Chat", icon: MessageSquare },
  { to: "/app/runs", label: "Agent Runs", icon: Bot },
  { to: "/app/pull-requests", label: "Pull Requests", icon: GitPullRequest },
  { to: "/app/reviews", label: "Reviews", icon: ShieldCheck },
  { to: "/app/activity", label: "Activity", icon: Activity },
];
