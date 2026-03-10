## MODIFIED Requirements

### Requirement: Watchlist registration
The system SHALL allow authenticated clients to register a domain watch item with base name and one or more TLDs.

#### Scenario: Authenticated user creates watch item
- **WHEN** an authenticated client submits `base_name=quroom` and `tlds=["com","kr"]`
- **THEN** the system SHALL persist a watch item scoped to that client and return its identifier

#### Scenario: Unauthenticated request is rejected
- **WHEN** an unauthenticated client calls watchlist create endpoint
- **THEN** the system SHALL return an authorization error and SHALL NOT create a watch item

### Requirement: Alert deduplication per cycle
The system SHALL avoid duplicate watch item registrations and duplicate alert events for unchanged available status.

#### Scenario: Duplicate watch registration blocked
- **WHEN** a client attempts to create the same `base_name + tlds` watch item twice
- **THEN** the system SHALL return a duplicate conflict and SHALL keep only one active watch item

#### Scenario: No duplicate alert on repeated available
- **WHEN** prior status is `available` and current status remains `available`
- **THEN** system SHALL NOT create an additional alert event

### Requirement: Watchlist quota policy
The system SHALL enforce a per-client maximum number of active watch items.

#### Scenario: Quota exceeded
- **WHEN** client tries to create a watch item beyond configured quota
- **THEN** the system SHALL reject the request with a quota-exceeded error
