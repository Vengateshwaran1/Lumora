/** Fake async accessors over the M4+ preview data — deliberately shaped
 * like a real API module (Promise-returning, id lookups) so swapping in
 * real endpoints later is a one-file change. Every page consuming these
 * must render `<PreviewBadge />` alongside. */

import { MOCK_ACTIVITY, MOCK_PULL_REQUESTS, MOCK_REVIEWS } from "./data";
import type { MockActivityEvent, MockPullRequest, MockReview } from "./types";

const LATENCY_MS = 220;

function delay<T>(value: T): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), LATENCY_MS));
}

export function listMockPullRequests(): Promise<MockPullRequest[]> {
  return delay(MOCK_PULL_REQUESTS);
}

export function getMockPullRequest(id: string): Promise<MockPullRequest | undefined> {
  return delay(MOCK_PULL_REQUESTS.find((pr) => pr.id === id));
}

export function listMockReviews(): Promise<MockReview[]> {
  return delay(MOCK_REVIEWS);
}

export function listMockActivity(): Promise<MockActivityEvent[]> {
  return delay(MOCK_ACTIVITY);
}
