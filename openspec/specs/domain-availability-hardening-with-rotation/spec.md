## Purpose

Define hardened domain availability checking with multi-provider quorum, IP rotation, and confidence-based output.

## Requirements

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
The system SHALL determine final status by quorum using normalized real provider outcomes.

#### Scenario: Quorum unavailable
- **WHEN** at least two providers report the domain as registered
- **THEN** the final status SHALL be `unavailable`

#### Scenario: Quorum available
- **WHEN** at least two providers report the domain as available and no provider reports registered
- **THEN** the final status SHALL be `available`

#### Scenario: Quorum not reached
- **WHEN** provider outcomes are split without at least two matching non-error outcomes
- **THEN** the final status SHALL be `uncertain`

#### Scenario: Real provider disagreement
- **WHEN** RDAP and WHOIS providers disagree and quorum is not satisfied
- **THEN** the system SHALL return `uncertain`

### Requirement: Evidence and confidence in response
The system SHALL return confidence and provider evidence with the final status, where evidence is sourced from real RDAP/WHOIS network checks.

#### Scenario: Evidence present in API response
- **WHEN** a domain check completes
- **THEN** each result SHALL include `confidence` and `evidence`

#### Scenario: Evidence sourced from real provider response
- **WHEN** a domain check completes through RDAP/WHOIS providers
- **THEN** each evidence entry SHALL include provider identity, normalized outcome, and request metadata derived from real network responses

### Requirement: Confidence scoring model
The system SHALL compute `confidence` from real provider outcomes, preserving existing weighting/cap behavior for `uncertain`.

#### Scenario: Full agreement confidence
- **WHEN** all providers return the same non-error result
- **THEN** the system SHALL produce `confidence >= 0.90`

#### Scenario: Partial agreement with one provider error
- **WHEN** two providers agree and one provider times out or is rate-limited
- **THEN** the system SHALL produce `0.60 <= confidence < 0.90`

#### Scenario: Confidence with mixed real provider results
- **WHEN** RDAP and WHOIS providers return mixed availability/error outcomes
- **THEN** the system SHALL compute confidence using configured weights and keep `uncertain` confidence at or below configured cap

### Requirement: Uncertain confidence cap
The system SHALL enforce an upper bound for uncertain confidence.

#### Scenario: Cap uncertain confidence
- **WHEN** final status is `uncertain`
- **THEN** the system SHALL set `confidence <= 0.49`

### Requirement: IP cooldown policy
The system SHALL apply cooldown and failover rules based on real network error signals from provider requests.

#### Scenario: Cooldown on repeated 429
- **WHEN** an IP receives three consecutive HTTP 429 responses
- **THEN** the IP SHALL be placed in cooldown for at least the configured base cooldown duration

#### Scenario: Cooldown triggered by HTTP 429
- **WHEN** repeated provider HTTP 429 responses are observed from the same outbound IP
- **THEN** that IP SHALL be placed in cooldown and excluded from selection until cooldown expiry
