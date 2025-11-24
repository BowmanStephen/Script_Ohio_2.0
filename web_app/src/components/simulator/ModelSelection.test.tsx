import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '../../test-utils';
import userEvent from '@testing-library/user-event';
import { ModelSelection } from './ModelSelection';
import { modelPerformance } from '../../utils/predictionLogic';

describe('ModelSelection', () => {
  it('renders all model options', () => {
    render(
      <ModelSelection
        selectedModel="Ridge Regression"
        onSelectModel={vi.fn()}
        modelPerformance={modelPerformance}
      />
    );

    expect(screen.getByRole('button', { name: /ridge regression/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /xgboost/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /fastai neural net/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /ensemble/i })).toBeInTheDocument();
  });

  it('calls onSelectModel when a model is clicked', async () => {
    const user = userEvent.setup();
    const onSelectModel = vi.fn();
    render(
      <ModelSelection
        selectedModel="Ridge Regression"
        onSelectModel={onSelectModel}
        modelPerformance={modelPerformance}
      />
    );

    const xgboostButton = screen.getByRole('button', { name: /xgboost/i });
    await user.click(xgboostButton);

    expect(onSelectModel).toHaveBeenCalledWith('XGBoost');
  });

  it('highlights the selected model', () => {
    render(
      <ModelSelection
        selectedModel="XGBoost"
        onSelectModel={vi.fn()}
        modelPerformance={modelPerformance}
      />
    );

    const selectedButton = screen.getByRole('button', { name: /xgboost/i });
    expect(selectedButton).toHaveAttribute('aria-pressed', 'true');
  });

  it('displays ensemble weights when Ensemble is selected', () => {
    render(
      <ModelSelection
        selectedModel="Ensemble"
        onSelectModel={vi.fn()}
        modelPerformance={modelPerformance}
      />
    );

    expect(screen.getByText(/ensemble weights/i)).toBeInTheDocument();
    expect(screen.getByText(/ridge/i)).toBeInTheDocument();
    expect(screen.getByText(/xgboost/i)).toBeInTheDocument();
    expect(screen.getByText(/fastai/i)).toBeInTheDocument();
  });

  it('does not display ensemble weights for non-ensemble models', () => {
    render(
      <ModelSelection
        selectedModel="Ridge Regression"
        onSelectModel={vi.fn()}
        modelPerformance={modelPerformance}
      />
    );

    expect(screen.queryByText(/ensemble weights/i)).not.toBeInTheDocument();
  });
});


