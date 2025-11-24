import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import '@testing-library/jest-dom';

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


