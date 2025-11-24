import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '../../test-utils';
import userEvent from '@testing-library/user-event';
import { ViewSelector } from './ViewSelector';

describe('ViewSelector', () => {
  it('renders all view options', () => {
    const onSelectView = vi.fn();
    render(<ViewSelector selectedView="predictions" onSelectView={onSelectView} />);

    expect(screen.getByRole('tab', { name: /all predictions/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /wcfl strategy/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /value opportunities/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /model performance/i })).toBeInTheDocument();
  });

  it('calls onSelectView when a view is clicked', async () => {
    const user = userEvent.setup();
    const onSelectView = vi.fn();
    render(<ViewSelector selectedView="predictions" onSelectView={onSelectView} />);

    const wcflButton = screen.getByRole('tab', { name: /wcfl strategy/i });
    await user.click(wcflButton);

    expect(onSelectView).toHaveBeenCalledWith('wcfl');
  });

  it('marks the selected view as selected', () => {
    render(<ViewSelector selectedView="wcfl" onSelectView={vi.fn()} />);

    const selectedTab = screen.getByRole('tab', { name: /wcfl strategy/i });
    expect(selectedTab).toHaveAttribute('aria-selected', 'true');
  });

  it('supports keyboard navigation with arrow keys', async () => {
    const user = userEvent.setup();
    const onSelectView = vi.fn();
    render(<ViewSelector selectedView="predictions" onSelectView={onSelectView} />);

    const predictionsTab = screen.getByRole('tab', { name: /all predictions/i });
    predictionsTab.focus();

    // Press right arrow
    await user.keyboard('{ArrowRight}');
    expect(onSelectView).toHaveBeenCalledWith('wcfl');

    // Press left arrow
    await user.keyboard('{ArrowLeft}');
    expect(onSelectView).toHaveBeenCalledWith('predictions');
  });

  it('supports Enter key to select view', async () => {
    const user = userEvent.setup();
    const onSelectView = vi.fn();
    render(<ViewSelector selectedView="predictions" onSelectView={onSelectView} />);

    const wcflTab = screen.getByRole('tab', { name: /wcfl strategy/i });
    wcflTab.focus();
    await user.keyboard('{Enter}');

    expect(onSelectView).toHaveBeenCalledWith('wcfl');
  });

  it('wraps around when navigating with arrow keys', async () => {
    const user = userEvent.setup();
    const onSelectView = vi.fn();
    render(<ViewSelector selectedView="performance" onSelectView={onSelectView} />);

    const performanceTab = screen.getByRole('tab', { name: /model performance/i });
    performanceTab.focus();

    // Press right arrow from last item should wrap to first
    await user.keyboard('{ArrowRight}');
    expect(onSelectView).toHaveBeenCalledWith('predictions');
  });
});


