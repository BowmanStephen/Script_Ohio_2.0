# Testing Guide

This document describes the testing setup, patterns, and best practices for the Script Ohio web app.

## Test Framework

The project uses **Vitest** as the test runner with **React Testing Library** for component testing.

### Setup

- **Test Runner**: Vitest 2.1.8
- **Testing Library**: @testing-library/react 16.1.0
- **DOM Environment**: jsdom 25.0.1
- **Coverage**: @vitest/coverage-istanbul 2.1.8

### Configuration

Test configuration is in `vite.config.ts`:

```typescript
test: {
  globals: true,
  environment: "jsdom",
  setupFiles: ["./src/test-utils.tsx"],
  coverage: {
    provider: "istanbul",
    reporter: ["text", "json", "html"],
  },
}
```

## Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm test -- --coverage
```

## Test Utilities

Custom test utilities are available in `src/test-utils.tsx`:

```typescript
import { render, screen } from '../test-utils';
```

The `render` function wraps React Testing Library's render with any necessary providers.

## Writing Tests

### Component Tests

Example component test:

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '../test-utils';
import userEvent from '@testing-library/user-event';
import { MyComponent } from './MyComponent';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });

  it('handles user interaction', async () => {
    const user = userEvent.setup();
    const onAction = vi.fn();
    render(<MyComponent onAction={onAction} />);
    
    await user.click(screen.getByRole('button'));
    expect(onAction).toHaveBeenCalled();
  });
});
```

### Utility Function Tests

Example utility test:

```typescript
import { describe, it, expect } from 'vitest';
import { myFunction } from './myFunction';

describe('myFunction', () => {
  it('returns expected result', () => {
    const result = myFunction('input');
    expect(result).toBe('expected');
  });
});
```

## Test Coverage

Target coverage: **60% minimum** for critical paths.

Coverage reports are generated in the `coverage/` directory:

- `coverage/index.html` - HTML report
- `coverage/coverage-final.json` - JSON report

## Testing Patterns

### 1. Test User Interactions

Use `@testing-library/user-event` for realistic user interactions:

```typescript
const user = userEvent.setup();
await user.click(button);
await user.type(input, 'text');
await user.keyboard('{Enter}');
```

### 2. Test Accessibility

Use semantic queries and ARIA attributes:

```typescript
screen.getByRole('button', { name: /submit/i });
screen.getByLabelText(/email/i);
screen.getByTestId('custom-element'); // Last resort
```

### 3. Test Error Boundaries

Test error boundaries by throwing errors in components:

```typescript
const ThrowError = () => {
  throw new Error('Test error');
};

it('catches errors', () => {
  render(
    <ErrorBoundary>
      <ThrowError />
    </ErrorBoundary>
  );
  expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
});
```

### 4. Mock Functions

Use Vitest's `vi.fn()` for mocking:

```typescript
const mockFn = vi.fn();
render(<Component onAction={mockFn} />);
expect(mockFn).toHaveBeenCalledWith('expected-arg');
```

## Test File Organization

- Component tests: `src/components/**/*.test.tsx`
- Utility tests: `src/utils/**/*.test.ts`
- Integration tests: `src/__tests__/**/*.test.ts`

## Best Practices

1. **Test behavior, not implementation**: Focus on what users see and do
2. **Use semantic queries**: Prefer `getByRole`, `getByLabelText` over `getByTestId`
3. **Keep tests isolated**: Each test should be independent
4. **Test edge cases**: Include error conditions and boundary cases
5. **Maintain test readability**: Clear test names and organized structure
6. **Avoid testing implementation details**: Don't test internal state or methods

## Common Issues

### jsdom Environment

If you encounter DOM-related errors, ensure `environment: "jsdom"` is set in `vite.config.ts`.

### Async Operations

Always use `await` with user interactions and async operations:

```typescript
await user.click(button);
await waitFor(() => {
  expect(screen.getByText('Result')).toBeInTheDocument();
});
```

### Coverage Gaps

If coverage is low, check:
- Are all branches tested?
- Are error cases covered?
- Are edge cases included?

## Continuous Integration

Tests run automatically in CI/CD pipelines. Ensure all tests pass before merging.

## Resources

- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [Testing Library User Event](https://testing-library.com/docs/user-event/intro)


