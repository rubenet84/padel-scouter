# Partner Stats Specification

## Purpose

Aggregate statistics for partner pairs. Compute matches played together, wins, losses, win % per pair. Provide rankings: most matches, best win %, most wins. Respect global filter parameters.

## Requirements

### Requirement: Partner pair aggregation

The system MUST aggregate stats by partner pair (identified by `partner_id` or `partner_nombre`). Each pair MUST include both player names, matches together, wins, losses, and win %.

#### Scenario: Multiple matches with same partner

- GIVEN Player A played 8 matches with Partner X (6 wins, 2 losses)
- WHEN the partner-stats endpoint is called
- THEN the pair "Player A & Partner X" MUST show `matches: 8`, `wins: 6`, `losses: 2`, `win_pct: 75.0`

#### Scenario: Partner with a single match

- GIVEN Player A played 1 match with Partner Y and won
- WHEN the partner-stats endpoint is called
- THEN "Player A & Partner Y" MUST show `matches: 1`, `wins: 1`, `win_pct: 100.0`

### Requirement: Pair rankings

The system MUST provide three rankings: most matches played together, best win % (minimum 3 matches), most wins.

#### Scenario: Most wins ranking

- GIVEN Pair A has 10 wins, Pair B has 7 wins, Pair C has 7 wins
- WHEN the partner-stats endpoint is called
- THEN `most_wins` MUST list: Pair A first, then Pair B and Pair C (order may be by most matches or alphabetical for ties)

#### Scenario: Best win % excludes low-match pairs

- GIVEN Pair A has 1W/0L (100% in 1 match) and Pair B has 8W/2L (80% in 10 matches)
- WHEN the partner-stats endpoint is called
- THEN `best_win_pct` MUST rank Pair B above Pair A (Pair A has fewer than 3 matches minimum)

### Requirement: Global filter support

Partner stats MUST respect `season`, `competition_type`, `date_from`, `date_to`.

#### Scenario: Seasonal filtering

- GIVEN Pair A played 15 matches in 2025 and 5 in 2026
- WHEN the partner-stats endpoint is called with `season=2025`
- THEN only the 15 matches from 2025 MUST be counted

#### Scenario: Competition type filtering

- GIVEN Pair A has 10 tournament matches and 3 friendlies
- WHEN the partner-stats endpoint is called with `competition_type=tournament`
- THEN `matches` MUST be 10
