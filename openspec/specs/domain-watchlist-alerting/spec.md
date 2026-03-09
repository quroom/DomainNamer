## ADDED Requirements

### Requirement: Watchlist registration
The system SHALL allow clients to register a domain watch item with base name and one or more TLDs.

#### Scenario: Create watch item
- **WHEN** client submits `base_name=quroom` and `tlds=["com","kr"]`
- **THEN** system SHALL persist a watch item and return its identifier

### Requirement: Scheduled availability check
The system SHALL provide an executable check routine that evaluates each active watch item against the availability pipeline.

#### Scenario: Batch check updates latest status
- **WHEN** check routine runs for active watch items
- **THEN** system SHALL update per-domain latest status and checked timestamp

### Requirement: Availability transition alerting
The system SHALL create an alert event when a watched domain transitions from unavailable to available.

#### Scenario: Transition creates one alert event
- **WHEN** prior status is `unavailable` and current status is `available`
- **THEN** system SHALL create one alert event for that domain check cycle

### Requirement: Alert deduplication per cycle
The system SHALL avoid duplicate alert events for unchanged available status.

#### Scenario: No duplicate alert on repeated available
- **WHEN** prior status is `available` and current status remains `available`
- **THEN** system SHALL NOT create an additional alert event
