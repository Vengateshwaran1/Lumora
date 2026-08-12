import { screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ActivityPage } from "@/features/activity/activity-page";
import { CodePage } from "@/features/code/code-page";
import { ChatPage } from "@/features/chat/chat-page";
import { DashboardPage } from "@/features/dashboard/dashboard-page";
import { IssueDetailPage } from "@/features/issues/issue-detail-page";
import { IssuesPage } from "@/features/issues/issues-page";
import { KnowledgePage } from "@/features/knowledge/knowledge-page";
import { ReposPage } from "@/features/repos/repos-page";
import { ReviewsPage } from "@/features/reviews/reviews-page";
import { SettingsPage } from "@/features/settings/settings-page";

import { renderPage } from "./render-with-providers";

describe("application pages render without throwing", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("Dashboard (Overview)", async () => {
    renderPage(<DashboardPage />);
    expect(await screen.findByText("Overview")).toBeInTheDocument();
  });

  it("Repositories", () => {
    renderPage(<ReposPage />);
    expect(screen.getByText("Repositories")).toBeInTheDocument();
  });

  it("Issues", async () => {
    renderPage(<IssuesPage />);
    expect(await screen.findByText(/Payment retry creates duplicate orders/)).toBeInTheDocument();
  });

  it("Issue detail", async () => {
    renderPage(<IssueDetailPage />, { path: "/issues/:id", route: "/issues/issue-1" });
    expect(await screen.findByText(/Payment retry creates duplicate orders/)).toBeInTheDocument();
  });

  it("Knowledge (no repos connected)", () => {
    renderPage(<KnowledgePage />);
    expect(screen.getByText("No repositories connected")).toBeInTheDocument();
  });

  it("Code", () => {
    renderPage(<CodePage />);
    expect(screen.getByText("Code")).toBeInTheDocument();
  });

  it("AI Chat (no repo selected)", () => {
    renderPage(<ChatPage />);
    expect(screen.getByText("AI Chat")).toBeInTheDocument();
  });

  it("Reviews", async () => {
    renderPage(<ReviewsPage />);
    expect(await screen.findByText(/Fix duplicate-order race/)).toBeInTheDocument();
  });

  it("Activity", async () => {
    renderPage(<ActivityPage />);
    expect(await screen.findByText(/Agent run awaiting approval/)).toBeInTheDocument();
  });

  it("Settings", () => {
    renderPage(<SettingsPage />);
    expect(screen.getByText("Settings")).toBeInTheDocument();
  });
});

describe("landing page renders with motion disabled", () => {
  it("shows the hero headline", async () => {
    vi.stubGlobal(
      "matchMedia",
      (query: string) =>
        ({
          matches: query.includes("prefers-reduced-motion"),
          media: query,
          onchange: null,
          addListener: () => {},
          removeListener: () => {},
          addEventListener: () => {},
          removeEventListener: () => {},
          dispatchEvent: () => false,
        }) as MediaQueryList,
    );

    const { LandingPage } = await import("@/features/marketing/landing-page");
    renderPage(<LandingPage />);
    expect(
      await screen.findByRole("heading", { level: 1, name: /Software engineering/ }),
    ).toBeInTheDocument();

    vi.unstubAllGlobals();
  });
});
