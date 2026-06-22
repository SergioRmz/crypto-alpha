"""
Decimal string formatter for crypto-alpha scoring engine v1.

Single source of truth for converting internal float64 values to the
decimal-string representation required by P0 Invariant 2 ("money-like
fields use Decimal-compatible string representation in JSON; never float").

Different precisions for different field types:
  - Prices (entry, stop, TP): 8 decimal places (crypto precision)
  - Score contributions and total_score: 4 decimal places
  - R-multiples: 1 decimal place
  - Percentages (volatility, etc.): 1 decimal place
"""
from __future__ import annotations


def price(value: float) -> str:
    """Format a price as a decimal string with 8 decimal places."""
    return f"{value:.8f}"


def score(value: float) -> str:
    """Format a score as a decimal string with 4 decimal places.

    Note: scores are emitted as JSON numbers in the output (per
    scoring-output schema), not as strings. This helper is unused
    for scores but kept for symmetry.
    """
    return f"{value:.4f}"


def score_value(value: float) -> float:
    """Round a score to 4 decimal places, returned as a number."""
    return round(float(value), 4)


def r_multiple(value: float) -> float:
    """Round an R-multiple to 1 decimal place, returned as a number."""
    return round(float(value), 1)


__all__ = ["price", "score", "score_value", "r_multiple"]
