# Top Players Specification

## Purpose

Ten independent "Top 5" lists: most FEP points, most wins, best win %, most matches played, most tournaments won, most finals reached, most semifinals reached, most sets won, most games won, longest current streak. All lists respect global filter parameters.

## Requirements

### Requirement: Ten independent top-5 lists

The system MUST return all ten top-N lists, each containing exactly 5 entries (or fewer if insufficient data) and sorted appropriately for each metric.

#### Scenario: Full data produces all 10 lists with 5 entries each

- GIVEN the user has 20+ players with diverse stats
- WHEN the top-players endpoint is called
- THEN the response MUST contain all 10 list keys
- AND each list MUST have exactly 5 entries (ordered by the metric descending)

#### Scenario: Fewer than 5 players exist

- GIVEN the user has only 3 players
- WHEN the top-players endpoint is called
- THEN each list MUST contain only those 3 players (no padding or errors)

### Requirement: Independent list ordering

Each list MUST be sorted independently by its specific metric. A player appearing in multiple lists MUST show the value relevant to that list.

#### Scenario: Player appears in multiple lists with different values

- GIVEN Player A has 1500 points, 20 wins, 70% win rate
- WHEN the top-players endpoint is called
- THEN Player A MUST appear in `top_points` with `points: 1500`
- AND in `top_wins` with `wins: 20`
- AND in `top_win_pct` with `win_pct: 70.0`

#### Scenario: Ties in a ranking show both players

- GIVEN 6 players with 10 wins each and 2 players with 5 wins
- WHEN the top-players endpoint is called with `sort_by=wins`
- THEN the top 5 MUST include any 5 of the 6 tied players (order among ties is undefined but deterministic)

### Requirement: Global filters affect all lists

All 10 lists MUST respect `season`, `competition_type`, `category`, `date_from`, `date_to` filters uniformly.

#### Scenario: Filter by competition_type=tournament

- GIVEN Player A has 10 tournament wins and 5 friendly wins
- AND Player B has 3 tournament wins and 12 friendly wins
- WHEN the top-players endpoint is called with `competition_type=tournament`
- THEN `top_wins` MUST show Player A first (10 wins), Player B second (3 wins)

#### Scenario: Filter by season excludes out-of-season data

- GIVEN Player A won 8 tournaments in 2025 and 2 in 2026
- WHEN the top-players endpoint is called with `season=2025`
- THEN `top_tournaments_won` MUST count only the 8 from 2025
