import { lazy, Suspense, type ComponentType } from "react";
import { createBrowserRouter } from "react-router-dom";

import { NotFoundPage } from "@/app/not-found-page";
import { RouteFallback } from "@/shared/components/route-fallback";

function lazyRoute(loader: () => Promise<{ [key: string]: ComponentType }>, exportName: string) {
  const LazyComponent = lazy(() => loader().then((module) => ({ default: module[exportName]! })));
  return (
    <Suspense fallback={<RouteFallback />}>
      <LazyComponent />
    </Suspense>
  );
}

export const router = createBrowserRouter([
  {
    path: "/",
    element: lazyRoute(() => import("@/features/marketing/landing-page"), "LandingPage"),
  },

  {
    element: lazyRoute(() => import("@/features/auth/auth-layout"), "AuthLayout"),
    children: [
      {
        path: "login",
        element: lazyRoute(() => import("@/features/auth/login-page"), "LoginPage"),
      },
      {
        path: "signup",
        element: lazyRoute(() => import("@/features/auth/signup-page"), "SignupPage"),
      },
      {
        path: "forgot-password",
        element: lazyRoute(
          () => import("@/features/auth/forgot-password-page"),
          "ForgotPasswordPage",
        ),
      },
    ],
  },
  {
    path: "onboarding",
    element: lazyRoute(() => import("@/features/auth/onboarding-page"), "OnboardingPage"),
  },

  {
    path: "/app",
    element: lazyRoute(() => import("@/components/app-shell/app-shell"), "AppShell"),
    children: [
      {
        index: true,
        element: lazyRoute(() => import("@/features/dashboard/dashboard-page"), "DashboardPage"),
      },
      {
        path: "repositories",
        element: lazyRoute(() => import("@/features/repos/repos-page"), "ReposPage"),
      },
      {
        path: "repositories/:id",
        element: lazyRoute(
          () => import("@/features/repos/detail/repository-detail-page"),
          "RepositoryDetailPage",
        ),
      },
      {
        path: "issues",
        element: lazyRoute(() => import("@/features/issues/issues-page"), "IssuesPage"),
      },
      {
        path: "issues/:id",
        element: lazyRoute(() => import("@/features/issues/issue-detail-page"), "IssueDetailPage"),
      },
      {
        path: "knowledge",
        element: lazyRoute(() => import("@/features/knowledge/knowledge-page"), "KnowledgePage"),
      },
      { path: "code", element: lazyRoute(() => import("@/features/code/code-page"), "CodePage") },
      { path: "chat", element: lazyRoute(() => import("@/features/chat/chat-page"), "ChatPage") },
      { path: "runs", element: lazyRoute(() => import("@/features/runs/runs-page"), "RunsPage") },
      {
        path: "runs/:id",
        element: lazyRoute(() => import("@/features/runs/run-detail-page"), "RunDetailPage"),
      },
      {
        path: "pull-requests",
        element: lazyRoute(
          () => import("@/features/pull-requests/pull-requests-page"),
          "PullRequestsPage",
        ),
      },
      {
        path: "pull-requests/:id",
        element: lazyRoute(
          () => import("@/features/pull-requests/pull-request-detail-page"),
          "PullRequestDetailPage",
        ),
      },
      {
        path: "reviews",
        element: lazyRoute(() => import("@/features/reviews/reviews-page"), "ReviewsPage"),
      },
      {
        path: "activity",
        element: lazyRoute(() => import("@/features/activity/activity-page"), "ActivityPage"),
      },
      {
        path: "settings",
        element: lazyRoute(() => import("@/features/settings/settings-page"), "SettingsPage"),
      },
      { path: "*", element: <NotFoundPage /> },
    ],
  },

  { path: "*", element: <NotFoundPage /> },
]);
