# Ranking Evolution Specification

## Purpose

Show ranking position changes over time: which players moved up most, moved down most. Show point evolution and win evolution over time. Respect global filter parameters.

## Requirements

### Requirement: Position change tracking

The system MUST compute and return ranking position changes for players. Must identify players who moved up most and moved down most between two ranking snapshots (defined by date range).

#### Scenario: Players with clear position changes

- GIVEN Player A moved from #5 to #2 (+3), Player B moved from #1 to #4 (-3)
- WHEN the ranking-evolution endpoint is called
- THEN `moved_up_most` MUST list Player A with `position_change: 3`
- AND `moved_down_most` MUST list Player B with `position_change: -3`

#### Scenario: No position changes in period

- GIVEN all players maintained their same positions
- WHEN the ranking-evolution endpoint is called
- THEN `moved_up_most` and `moved_down_most` MUST be empty arrays (or show zero-change entries at the end)

### Requirement: Point and win evolution

The system MUST show how each player's FEP points and wins evolved over time, with data points grouped by a configurable time granularity.

#### Scenario: Point evolution over months

- GIVEN Player A had 500 pts in Jan, 800 pts in Feb, 1200 pts in Mar
- WHEN the ranking-evolution endpoint is called
- THEN `evolution.points` MUST include data points for each month with cumulative or per-period values

#### Scenario: Win evolution with upward trend

- GIVEN Player A won 2 matches in Jan, 5 in Feb, 3 in Mar
- WHEN the ranking-evolution endpoint is called
- THEN `evolution.wins` MUST reflect these per-period win counts

### Requirement: Global filter support

Ranking evolution MUST respect `season`, `competition_type`, `category`, `date_from`, `date_to`.

#### Scenario: Filter by competition_type=tournament

- GIVEN Player A's ranking change was driven by 3 tournament wins and 5 friendlies
- WHEN the ranking-evolution endpoint is called with `competition_type=tournament`
- THEN `evolution.points` MUST include only tournament-sourced points

#### Scenario: Filter by category limits scope

- GIVEN user has Profesional and 1ª players
- WHEN the ranking-evolution endpoint is called with `category=Profesional`
- THEN only Profesional players MUST appear in position change lists and evolution data
