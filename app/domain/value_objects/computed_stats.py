"""Competitive stats dataclass — pure domain.

The get_computed_stats() function moved to app.services.computed_stats_service.
"""

from dataclasses import dataclass


@dataclass
class ComputedStats:
    """Competitive stats computed from match + tournament data."""

    torneos: int = 0
    win_rate: float = 0.0  # 0–100 percentage
    fep_points: int = 0
