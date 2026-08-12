/** Fake async accessors over the M3+ preview data — deliberately shaped
 * like a real API module (Promise-returning, id lookups) so swapping in
 * real endpoints later is a one-file change. Every page consuming these
 * must render `<PreviewBadge />` alongside. */

import {
  MOCK_ACTIVITY,
  MOCK_AGENT_RUNS,
  MOCK_ISSUES,
  MOCK_PULL_REQUESTS,
  MOCK_REVIEWS,
} from "./data";
import type {
  MockActivityEvent,
  MockAgentRun,
  MockIssue,
  MockPullRequest,
  MockReview,
} from "./types";

const LATENCY_MS = 220;

function delay<T>(value: T): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), LATENCY_MS));
}

export function listMockIssues(): Promise<MockIssue[]> {
  return delay(MOCK_ISSUES);
}

export function getMockIssue(id: string): Promise<MockIssue | undefined> {
  return delay(MOCK_ISSUES.find((issue) => issue.id === id));
}

export function listMockPullRequests(): Promise<MockPullRequest[]> {
  return delay(MOCK_PULL_REQUESTS);
}

export function getMockPullRequest(id: string): Promise<MockPullRequest | undefined> {
  return delay(MOCK_PULL_REQUESTS.find((pr) => pr.id === id));
}

export function listMockAgentRuns(): Promise<MockAgentRun[]> {
  return delay(MOCK_AGENT_RUNS);
}

export function getMockAgentRun(id: string): Promise<MockAgentRun | undefined> {
  return delay(MOCK_AGENT_RUNS.find((run) => run.id === id));
}

export function listMockReviews(): Promise<MockReview[]> {
  return delay(MOCK_REVIEWS);
}

export function listMockActivity(): Promise<MockActivityEvent[]> {
  return delay(MOCK_ACTIVITY);
}
