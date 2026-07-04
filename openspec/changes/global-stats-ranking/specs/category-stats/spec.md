# Category Stats Specification

## Purpose

Per-category aggregate statistics across the seven defined categories: Profesional, 1ª, 2ª, 3ª, 4ª, 5ª, Iniciación. Each category shows player count, total matches, total wins, total losses, average win %, and average FEP points.

## Requirements

### Requirement: All seven categories listed

The system MUST return stats for all seven categories. Categories with no players MUST appear with zero values.

#### Scenario: All categories populated

- GIVEN the user has players in Profesional, 1ª, 2ª, and 3ª categories
- WHEN the category-stats endpoint is called
- THEN Profesional, 1ª, 2ª, 3ª MUST have their computed stats
- AND 4ª, 5ª, Iniciación MUST appear with `player_count: 0` and zeroes for all other fields

#### Scenario: Only one category populated

- GIVEN the user has 5 players all in "Iniciación"
- WHEN the category-stats endpoint is called
- THEN Iniciación MUST show `player_count: 5` with computed aggregates
- AND all other 6 categories MUST show zeroes

### Requirement: Computed aggregates per category

Each category MUST include: `player_count`, `total_matches`, `total_wins`, `total_losses`, `avg_win_pct`, `avg_fep_points`.

#### Scenario: Single category aggregates

- GIVEN 2 Profesional players: Player A (10W/2L, 1500 pts), Player B (5W/5L, 800 pts)
- WHEN the category-stats endpoint is called
- THEN Profesional MUST show `player_count: 2`, `total_matches: 22`, `total_wins: 15`, `total_losses: 7`, `avg_win_pct: 68.5`, `avg_fep_points: 1150.0`

#### Scenario: Player with no matches has 0 win %

- GIVEN 1 player in "1ª" with 0 matches and 0 points
- WHEN the category-stats endpoint is called
- THEN 1ª MUST show `player_count: 1`, `total_matches: 0`, `avg_win_pct: 0.0`, `avg_fep_points: 0.0`

### Requirement: Global filters affect category stats

The system MUST respect `season`, `competition_type`, `date_from`, `date_to` when computing per-category aggregates.

#### Scenario: Filter by competition_type=friendly

- GIVEN Profesional players have 50 tournament matches and 20 friendly matches
- WHEN the category-stats endpoint is called with `competition_type=friendly`
- THEN Profesional `total_matches` MUST be 20

#### Scenario: Filter by date range

- GIVEN 1ª players played 30 matches before June 2026 and 20 after
- WHEN the category-stats endpoint is called with `date_to=2026-06-01`
- THEN `total_matches` MUST be 30
