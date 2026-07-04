# Global Stats Summary Specification

## Purpose

Aggregate totals for the dashboard top-level summary cards: total players, matches, tournaments, friendlies, sets, games, ranking leader (name + points), and best win % (name + %). ALL data MUST be scoped to `current_user.id`.

## Requirements

### Requirement: Aggregate totals scoped to current user

The system MUST compute and return aggregate totals for all data belonging to the authenticated user (`current_user.id`). Data from other users MUST NOT be included.

#### Scenario: User with complete data sees correct aggregates

- GIVEN a user owns 3 players, 10 matches, 4 tournaments, 2 friendlies
- WHEN the summary endpoint is called without filters
- THEN the response MUST include `total_players: 3`, `total_matches: 10`, `total_tournaments: 4`, `total_friendlies: 2`

#### Scenario: User with no data sees zeroes

- GIVEN a user owns no players and no matches
- WHEN the summary endpoint is called
- THEN the response MUST return `total_players: 0`, `total_matches: 0`, and all other totals as 0

### Requirement: Ranking leader and best win %

The system MUST return the ranking leader (name + FEP points) and the player with the best win % (name + percentage) from the current user's data.

#### Scenario: Leader and best win % are different players

- GIVEN user has Player A with 1500 points / 60% and Player B with 1200 points / 80%
- WHEN the summary endpoint is called
- THEN `ranking_leader.name` MUST be "Player A" with `ranking_leader.points: 1500`
- AND `best_win_pct.name` MUST be "Player B" with `best_win_pct.pct: 80.0`

#### Scenario: Player with most points also has best win %

- GIVEN user has Player A with 1500 points / 75% and Player B with 500 points / 40%
- WHEN the summary endpoint is called
- THEN `ranking_leader.id` and `best_win_pct.id` MAY refer to the same player (Player A)

### Requirement: Global filters affect all aggregates

The summary MUST respect all global filter parameters: `season`, `competition_type`, `category`, `date_from`, `date_to`.

#### Scenario: Filtering by competition_type=friendly

- GIVEN user has 10 tournament matches and 5 friendly matches
- WHEN the summary endpoint is called with `competition_type=friendly`
- THEN `total_matches` MUST be 5 and `total_tournaments` MUST be 0

#### Scenario: Filtering by season excludes out-of-range data

- GIVEN user has 8 matches in 2025 and 12 matches in 2026
- WHEN the summary endpoint is called with `season=2026`
- THEN `total_matches` MUST be 12 (only 2026 matches counted)

### Requirement: Clickable player navigation (cross-cutting)

Every player name displayed in ANY section of the global stats dashboard (ranking tables, top player lists, comparison selectors, pair stats, head-to-head, evolution) MUST be a clickable link that opens that player's individual profile page (`/player/{player_id}`).

#### Scenario: Clicking a player in the ranking table navigates to their profile

- GIVEN the ranking table shows "Player A" at position 1
- WHEN the user clicks on "Player A"
- THEN the browser MUST navigate to `/player/{player_a_id}`

#### Scenario: Clicking a player in top-players cards navigates to their profile

- GIVEN the "Most wins" top list shows "Player B" with 15 wins
- WHEN the user clicks on "Player B"
- THEN the browser MUST navigate to `/player/{player_b_id}`
