import { createBrowserRouter } from "react-router-dom";

import { AppLayout } from "@/app/layout";
import { NotFoundPage } from "@/app/not-found-page";
import { AgentRunsPage } from "@/features/agent-runs/agent-runs-page";
import { ChatPage } from "@/features/chat/chat-page";
import { DashboardPage } from "@/features/dashboard/dashboard-page";
import { IssuesPage } from "@/features/issues/issues-page";
import { PrReviewPage } from "@/features/pr-review/pr-review-page";
import { ReposPage } from "@/features/repos/repos-page";
import { SettingsPage } from "@/features/settings/settings-page";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "repos", element: <ReposPage /> },
      { path: "chat", element: <ChatPage /> },
      { path: "issues", element: <IssuesPage /> },
      { path: "pr-review", element: <PrReviewPage /> },
      { path: "agent-runs", element: <AgentRunsPage /> },
      { path: "settings", element: <SettingsPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);
