# Head-to-Head Specification

## Purpose

Match history and aggregated statistics between two selected players. Show total matches, wins per player, sets won/lost per player, games won/lost per player, last match date and result, and a chronological history list of all matches between them. Respect global filter parameters.

## Requirements

### Requirement: Head-to-head aggregate stats

The system MUST accept two player IDs and return aggregated stats for all matches between them: total matches, wins for each player, sets won/lost each, games won/lost each, and last match result.

#### Scenario: Players with multiple head-to-head matches

- GIVEN Player A and Player B played 5 matches: Player A won 3, Player B won 2
- WHEN the head-to-head endpoint is called with `player_id=A&other_id=B`
- THEN `total_matches` MUST be 5, `wins_A: 3`, `wins_B: 2`

#### Scenario: Players who never faced each other

- GIVEN Player A and Player B have no matches against each other
- WHEN the head-to-head endpoint is called
- THEN `total_matches` MUST be 0, `wins_A: 0`, `wins_B: 0`
- AND `history` MUST be an empty array

### Requirement: Last match result

The system MUST return details of the most recent match between the two players: date, winner, and score.

#### Scenario: Recent match with clear winner

- GIVEN last match was on 2026-03-15, Player A won 2-0 (6-3, 6-4)
- WHEN the head-to-head endpoint is called
- THEN `last_match.date` MUST be `"2026-03-15"`, `last_match.winner` MUST be `"Player A"`, `last_match.sets_A: 2`, `last_match.sets_B: 0`

#### Scenario: No matches exist

- GIVEN Player A and Player B have never played
- WHEN the head-to-head endpoint is called
- THEN `last_match` MUST be null or absent

### Requirement: Match history list

The system MUST return a chronological list (newest first) of all matches between the two players.

#### Scenario: History list with multiple matches

- GIVEN Player A and Player B played 3 matches on different dates
- WHEN the head-to-head endpoint is called
- THEN `history` MUST contain 3 entries ordered by date descending (most recent first)
- AND each entry MUST include `date`, `winner`, `sets_A`, `sets_B`, `games_A`, `games_B`

#### Scenario: Filter by date range reduces history

- GIVEN 5 matches total, 3 within date range
- WHEN the head-to-head endpoint is called with `date_from=2026-01-01&date_to=2026-06-30`
- THEN `history` MUST contain only the 3 matches within range
- AND `total_matches` MUST be 3
