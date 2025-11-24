"""
Betting metrics and ROI/ATS simulation utilities.

Provides ROI calculation, ATS (Against The Spread) performance tracking, and
simulation tools for evaluating betting strategies over historical game data.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_PATH = PROJECT_ROOT / "model_pack" / "updated_training_data.csv"
BETTING_METRICS_VERSION = "0.1.0"


@dataclass
class BettingSimConfig:
    """Configuration for betting simulation."""

    initial_bankroll: float = 10000.0
    unit_size: float = 100.0
    max_bet_pct: float = 0.05  # Max 5% of bankroll per bet
    vig: float = -110.0  # Standard -110 odds
    min_confidence: float = 0.0  # Minimum confidence to place bet
    kelly_fraction: Optional[float] = None  # Use Kelly criterion if set
    data_path: Path = DEFAULT_DATA_PATH
    output_dir: Optional[Path] = None

    def resolved_output_dir(self) -> Path:
        if self.output_dir:
            return self.output_dir
        return PROJECT_ROOT / "reports" / "betting_simulation"


@dataclass
class BettingResult:
    """Result of a single bet."""

    game_id: int
    season: int
    week: int
    home_team: str
    away_team: str
    bet_side: str  # "home" or "away"
    predicted_margin: float
    actual_margin: float
    spread: float
    bet_amount: float
    payout: float
    profit: float
    won: bool
    covered: bool


@dataclass
class BettingPerformance:
    """Aggregate betting performance metrics."""

    total_bets: int
    wins: int
    losses: int
    pushes: int
    win_rate: float
    roi: float
    total_profit: float
    final_bankroll: float
    max_drawdown: float
    sharpe_ratio: float
    ats_accuracy: float
    avg_bet_size: float
    largest_win: float
    largest_loss: float


def _calculate_kelly_bet_size(
    win_prob: float, odds: float, bankroll: float, fraction: float = 1.0
) -> float:
    """Calculate optimal bet size using Kelly criterion."""
    if win_prob <= 0 or win_prob >= 1:
        return 0.0

    # Convert American odds to decimal
    if odds < 0:
        decimal_odds = abs(odds) / 100.0
    else:
        decimal_odds = odds / 100.0

    # Kelly formula: f = (bp - q) / b
    # where b = decimal_odds - 1, p = win_prob, q = 1 - p
    b = decimal_odds - 1.0
    p = win_prob
    q = 1.0 - p

    kelly_fraction = (b * p - q) / b
    kelly_fraction = max(0.0, min(kelly_fraction, 1.0))  # Clamp to [0, 1]
    kelly_fraction *= fraction  # Apply fractional Kelly

    return bankroll * kelly_fraction


def _calculate_payout(bet_amount: float, odds: float, won: bool) -> float:
    """Calculate payout for a bet given odds."""
    if not won:
        return 0.0

    if odds < 0:
        # American odds (e.g., -110)
        payout = bet_amount * (100.0 / abs(odds))
    else:
        # Positive odds (e.g., +150)
        payout = bet_amount * (odds / 100.0)

    return bet_amount + payout


def _simulate_single_bet(
    game: pd.Series,
    predicted_margin: float,
    bankroll: float,
    config: BettingSimConfig,
    confidence: Optional[float] = None,
) -> Optional[BettingResult]:
    """Simulate a single bet on a game."""
    if "spread" not in game or pd.isna(game["spread"]):
        return None

    spread = float(game["spread"])
    actual_margin = float(game["home_points"] - game["away_points"])

    # Determine bet side based on prediction
    if predicted_margin > spread:
        bet_side = "home"
        win_prob = 0.5 + min(0.45, (predicted_margin - spread) / 30.0)
    else:
        bet_side = "away"
        win_prob = 0.5 + min(0.45, (spread - predicted_margin) / 30.0)

    # Apply confidence threshold
    if confidence is not None and confidence < config.min_confidence:
        return None

    # Calculate bet size
    if config.kelly_fraction is not None:
        bet_amount = _calculate_kelly_bet_size(
            win_prob, config.vig, bankroll, config.kelly_fraction
        )
    else:
        bet_amount = config.unit_size

    # Apply max bet percentage
    max_bet = bankroll * config.max_bet_pct
    bet_amount = min(bet_amount, max_bet, bankroll)

    if bet_amount < 1.0:  # Minimum bet threshold
        return None

    # Determine if bet won
    if bet_side == "home":
        covered = actual_margin > spread
        won = actual_margin > spread
    else:
        covered = actual_margin < spread
        won = actual_margin < spread

    # Handle push (exact spread)
    if abs(actual_margin - spread) < 0.5:
        won = False
        covered = False
        payout = bet_amount  # Push returns bet
    else:
        payout = _calculate_payout(bet_amount, config.vig, won)

    profit = payout - bet_amount

    return BettingResult(
        game_id=int(game.get("id", 0)),
        season=int(game["season"]),
        week=int(game["week"]),
        home_team=str(game["home_team"]),
        away_team=str(game["away_team"]),
        bet_side=bet_side,
        predicted_margin=predicted_margin,
        actual_margin=actual_margin,
        spread=spread,
        bet_amount=bet_amount,
        payout=payout,
        profit=profit,
        won=won,
        covered=covered,
    )


def simulate_betting_strategy(
    config: BettingSimConfig,
    predictions_df: pd.DataFrame,
    games_df: Optional[pd.DataFrame] = None,
) -> Tuple[pd.DataFrame, BettingPerformance]:
    """
    Simulate a betting strategy over historical games.

    Args:
        config: Betting simulation configuration.
        predictions_df: DataFrame with columns: game_id, predicted_margin,
            confidence (optional).
        games_df: Optional games DataFrame with spreads. If None, loads from
            config.data_path.

    Returns:
        Tuple of (bet_results_df, performance_metrics).
    """
    if games_df is None:
        if not config.data_path.exists():
            raise FileNotFoundError(f"Data not found at {config.data_path}")
        games_df = pd.read_csv(config.data_path)

    required_cols = {"id", "season", "week", "home_team", "away_team", "home_points", "away_points"}
    missing = required_cols - set(games_df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    # Merge predictions with games
    merged = games_df.merge(
        predictions_df[["game_id", "predicted_margin", "confidence"]].rename(
            columns={"game_id": "id"}
        ),
        on="id",
        how="inner",
    )

    if merged.empty:
        raise ValueError("No games matched between predictions and games dataframes.")

    merged = merged.sort_values(["season", "week"]).reset_index(drop=True)

    bankroll = config.initial_bankroll
    bet_results = []
    running_profit = []

    for _, game in merged.iterrows():
        predicted_margin = float(game["predicted_margin"])
        confidence = float(game.get("confidence", 1.0)) if "confidence" in game else None

        bet_result = _simulate_single_bet(game, predicted_margin, bankroll, config, confidence)

        if bet_result is not None:
            bankroll += bet_result.profit
            running_profit.append(bankroll - config.initial_bankroll)
            bet_results.append(bet_result)

    if not bet_results:
        raise ValueError("No bets were placed. Check min_confidence and other filters.")

    results_df = pd.DataFrame([vars(b) for b in bet_results])

    # Calculate performance metrics
    total_bets = len(bet_results)
    wins = sum(1 for b in bet_results if b.won)
    losses = sum(1 for b in bet_results if not b.won and not (abs(b.actual_margin - b.spread) < 0.5))
    pushes = total_bets - wins - losses

    total_profit = sum(b.profit for b in bet_results)
    final_bankroll = bankroll
    roi = (total_profit / sum(b.bet_amount for b in bet_results)) * 100.0 if bet_results else 0.0

    # Drawdown calculation
    running_profit_array = np.array(running_profit)
    if len(running_profit_array) > 0:
        peak = np.maximum.accumulate(running_profit_array)
        drawdown = peak - running_profit_array
        max_drawdown = float(np.max(drawdown)) if len(drawdown) > 0 else 0.0
    else:
        max_drawdown = 0.0

    # Sharpe ratio (simplified, using profit volatility)
    if len(running_profit_array) > 1:
        returns = np.diff(running_profit_array) / (running_profit_array[:-1] + 1e-6)
        sharpe = float(np.mean(returns) / (np.std(returns) + 1e-6) * np.sqrt(252))  # Annualized
    else:
        sharpe = 0.0

    # ATS accuracy
    ats_wins = sum(1 for b in bet_results if b.covered)
    ats_accuracy = (ats_wins / total_bets) * 100.0 if total_bets > 0 else 0.0

    performance = BettingPerformance(
        total_bets=total_bets,
        wins=wins,
        losses=losses,
        pushes=pushes,
        win_rate=(wins / total_bets) * 100.0 if total_bets > 0 else 0.0,
        roi=roi,
        total_profit=total_profit,
        final_bankroll=final_bankroll,
        max_drawdown=max_drawdown,
        sharpe_ratio=sharpe,
        ats_accuracy=ats_accuracy,
        avg_bet_size=float(np.mean([b.bet_amount for b in bet_results])),
        largest_win=float(max((b.profit for b in bet_results), default=0.0)),
        largest_loss=float(min((b.profit for b in bet_results), default=0.0)),
    )

    results_df["version"] = BETTING_METRICS_VERSION
    results_df["created_at"] = dt.datetime.now(dt.timezone.utc).isoformat()

    return results_df, performance


__all__ = [
    "BettingSimConfig",
    "BettingResult",
    "BettingPerformance",
    "simulate_betting_strategy",
]

