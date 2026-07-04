# Player Ranking Specification

## Purpose

Rank players by FEP points (tournament_points × round_weight) with support for sorting, filtering, and global filter parameters. Friendly matches count for stats columns (wins, losses, streak) but NOT for ranking points.

## Requirements

### Requirement: Ranking by FEP points

The system MUST rank players by total FEP points (sum of `tournament_points × round_weight` across all tournament matches). Friendly matches MUST be excluded from point calculation.

#### Scenario: Players ranked by points descending

- GIVEN Player A has 2000 FEP points, Player B has 1500, Player C has 800
- WHEN the ranking endpoint is called
- THEN position 1 MUST be Player A, position 2 Player B, position 3 Player C

#### Scenario: Zero-point players appear at the bottom

- GIVEN Player A has 0 points (no tournaments played) and Player B has 500 points
- WHEN the ranking endpoint is called
- THEN Player B MUST be positioned above Player A

### Requirement: Friendly matches in stats only

Friendly matches MUST contribute to wins, losses, win %, and streak calculation but MUST NOT contribute to ranking FEP points.

#### Scenario: Player with only friendlies has 0 ranking points but positive stats

- GIVEN Player A has 5 friendly wins, 0 tournament matches
- WHEN the ranking endpoint is called
- THEN Player A MUST have `points: 0`, `wins: 5`, `losses: 0`, `win_pct: 100.0`

#### Scenario: Player with both tournament and friendly matches

- GIVEN Player A won 2 tournaments (1000 FEP) and 3 friendlies
- WHEN the ranking endpoint is called
- THEN Player A MUST have `points: 1000` (friendlies excluded from points)
- AND `wins` MUST include all 5 wins

### Requirement: Sortable columns

The system MUST support sorting by points (default), wins, win %, matches played, sets won, games won, streak, and player name. The `sort_by` parameter accepts any of these column names. The `order` parameter accepts `asc` or `desc`.

#### Scenario: Sort by wins ascending

- GIVEN Player A has 10 wins, Player B has 5 wins, Player C has 20 wins
- WHEN the ranking endpoint is called with `sort_by=wins&order=asc`
- THEN order MUST be Player B (5), Player A (10), Player C (20)

#### Scenario: Sort by streak descending

- GIVEN Player A has a 7-win streak, Player B has 3-win streak
- WHEN the ranking endpoint is called with `sort_by=streak&order=desc`
- THEN Player A MUST be first, Player B second

#### Scenario: Sort by name ascending

- GIVEN Player A ("Ana"), Player B ("Bea"), Player C ("Carlos")
- WHEN the ranking endpoint is called with `sort_by=name&order=asc`
- THEN order MUST be Ana, Bea, Carlos

### Requirement: Filterable ranking

The system MUST support filtering by `season`, `competition_type`, `category`, `date_from`, `date_to`.

#### Scenario: Filter by category returns only that category

- GIVEN Player A (Profesional, 2000 pts), Player B (1ª, 1500 pts), Player C (Profesional, 1000 pts)
- WHEN the ranking endpoint is called with `category=Profesional`
- THEN only Player A and Player C MUST appear

#### Scenario: Filter by date range excludes matches outside range

- GIVEN Player A has points from matches in Jan 2026 and Dec 2026
- WHEN the ranking endpoint is called with `date_from=2026-06-01&date_to=2026-12-31`
- THEN only Dec 2026 points MUST be included
