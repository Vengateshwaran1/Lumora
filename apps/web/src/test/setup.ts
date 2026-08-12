import "@testing-library/jest-dom/vitest";

// jsdom has no ResizeObserver/IntersectionObserver/matchMedia by default —
// Radix, framer-motion's useInView, and our own useReducedMotion all touch
// these unconditionally.
if (typeof window !== "undefined") {
  // eslint-disable-next-line @typescript-eslint/unbound-method -- assigning a mock implementation, not detaching a bound method
  window.matchMedia ??= (query: string) =>
    ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }) as MediaQueryList;

  class MockResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  window.ResizeObserver ??= MockResizeObserver;

  class MockIntersectionObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
    takeRecords() {
      return [];
    }
  }
  // @ts-expect-error -- jsdom doesn't implement IntersectionObserver
  window.IntersectionObserver ??= MockIntersectionObserver;
}
