import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import '@testing-library/jest-dom';

// Polyfill ResizeObserver for Radix Slider usage in tests
if (typeof globalThis.ResizeObserver === 'undefined') {
  // Minimal no-op implementation
  // eslint-disable-next-line @typescript-eslint/ban-ts-comment
  // @ts-ignore
  globalThis.ResizeObserver = class {
    disconnect() {}
    observe() {}
    unobserve() {}
  };
}

/**
 * Custom render function that wraps components with any providers
 * needed for testing (e.g., theme providers, context providers)
 * 
 * @param ui - The React component to render
 * @param options - Additional render options
 * @returns Render result with testing utilities
 */
function customRender(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>,
) {
  return render(ui, {
    ...options,
  });
}

// Re-export everything from @testing-library/react
export * from '@testing-library/react';
export { customRender as render };

