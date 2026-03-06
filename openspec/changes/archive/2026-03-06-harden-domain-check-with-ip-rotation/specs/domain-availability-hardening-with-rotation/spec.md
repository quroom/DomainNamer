## ADDED Requirements

### Requirement: Three-state availability classification
The system SHALL classify each domain candidate as `available`, `unavailable`, or `uncertain`.

#### Scenario: Conflicting provider responses
- **WHEN** providers return conflicting outcomes without quorum
- **THEN** the system SHALL mark the candidate as `uncertain`

### Requirement: IP rotation with health-aware selection
The system SHALL select outbound checker IPs from a rotation pool using health score and cooldown status.

#### Scenario: Cooldown exclusion
- **WHEN** an IP is in cooldown due to repeated 429 responses
- **THEN** the system SHALL exclude that IP from selection until cooldown expires

### Requirement: Quorum-based final decision
The system SHALL determine final availability by quorum from multiple provider results.

#### Scenario: Quorum unavailable
- **WHEN** at least two providers report the domain as registered
- **THEN** the final status SHALL be `unavailable`

#### Scenario: Quorum available
- **WHEN** at least two providers report the domain as available and no provider reports registered
- **THEN** the final status SHALL be `available`

#### Scenario: Quorum not reached
- **WHEN** provider outcomes are split without at least two matching non-error outcomes
- **THEN** the final status SHALL be `uncertain`

### Requirement: Evidence and confidence in response
The system SHALL return confidence and provider evidence with the final status.

#### Scenario: Evidence present in API response
- **WHEN** a domain check completes
- **THEN** each result SHALL include `confidence` and `evidence`

### Requirement: Confidence scoring model
The system SHALL compute `confidence` in range `[0.0, 1.0]` using agreement, source quality, IP health, freshness, and error penalty signals with configurable weights.

#### Scenario: Full agreement confidence
- **WHEN** all providers return the same non-error result
- **THEN** the system SHALL produce `confidence >= 0.90`

#### Scenario: Partial agreement with one provider error
- **WHEN** two providers agree and one provider times out or is rate-limited
- **THEN** the system SHALL produce `0.60 <= confidence < 0.90`

### Requirement: Uncertain confidence cap
The system SHALL enforce an upper bound for uncertain confidence.

#### Scenario: Cap uncertain confidence
- **WHEN** final status is `uncertain`
- **THEN** the system SHALL set `confidence <= 0.49`

### Requirement: IP cooldown policy
The system SHALL move unhealthy IPs into cooldown and exclude them from selection until cooldown expires.

#### Scenario: Cooldown on repeated 429
- **WHEN** an IP receives three consecutive HTTP 429 responses
- **THEN** the IP SHALL be placed in cooldown for at least the configured base cooldown duration
