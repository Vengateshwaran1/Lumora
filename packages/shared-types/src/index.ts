/**
 * Types and constants shared between apps/web and apps/api.
 *
 * Hand-written for now — the API surface in Milestone 0 is just `/health`.
 * From Milestone 1 onward, request/response types are generated from the
 * backend's OpenAPI schema (see docs/architecture/ARCHITECTURE.md §10)
 * rather than maintained here by hand.
 */

export const API_V1_PREFIX = "/api/v1";

export interface HealthResponse {
  status: string;
  environment: "development" | "test" | "production";
}
