# Player Comparison Specification

## Purpose

Side-by-side comparison of two selected players showing full stats: matches, wins, losses, win %, sets won/lost, games won/lost, tournaments played, current streak, ranking position, FEP points. Handle same-category and different-category comparison displays.

## Requirements

### Requirement: Side-by-side stat comparison

The system MUST accept two player IDs and return their respective stats side by side.

#### Scenario: Two valid players compared

- GIVEN Player A has 10 wins / 2 losses / 1 tournament / 80% win rate
- AND Player B has 5 wins / 5 losses / 3 tournaments / 50% win rate
- WHEN the comparison endpoint is called with `player_id=A&other_id=B`
- THEN the response MUST include both players' full stat blocks

#### Scenario: One player ID is invalid

- GIVEN player_id="abc" exists and other_id="999" does not exist
- WHEN the comparison endpoint is called
- THEN the system MUST return HTTP 404 with an error message identifying the missing player

### Requirement: Same-category comparison shows position diff

If both players belong to the same category, the system MUST show each player's position within that category and the point difference between them.

#### Scenario: Same category with point difference

- GIVEN Player A and Player B are both "Profesional"
- AND Player A has 2000 pts (rank #1), Player B has 1500 pts (rank #3)
- WHEN the comparison endpoint is called
- THEN response MUST include `category: "Profesional"`, `position_A: 1`, `position_B: 3`, `point_difference: 500`

#### Scenario: Same category, tied points

- GIVEN Player A and Player B are both "1ª" with 1000 pts each
- WHEN the comparison endpoint is called
- THEN `point_difference` MUST be 0 and both positions MUST be the same rank

### Requirement: Different-category comparison shows notice

If the two players belong to different categories, the system MUST NOT apply coefficient adjustments and MUST display the notice "Distinta categoría — los puntos no son directamente comparables".

#### Scenario: Different categories with notice

- GIVEN Player A is "Profesional" and Player B is "2ª"
- WHEN the comparison endpoint is called
- THEN the response MUST include `same_category: false`
- AND MUST include a notice field with value "Distinta categoría — los puntos no son directamente comparables"
- AND both category labels MUST remain unchanged

#### Scenario: Different categories still show all stats

- GIVEN Player A (Profesional) and Player B (Iniciación)
- WHEN the comparison endpoint is called
- THEN all stat fields (matches, wins, losses, win %, streak, etc.) MUST still be returned for both players
- BUT `point_difference` MUST be null or absent
