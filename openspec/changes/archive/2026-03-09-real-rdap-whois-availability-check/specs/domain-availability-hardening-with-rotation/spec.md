## MODIFIED Requirements

### Requirement: Evidence and confidence in response
The system SHALL return confidence and provider evidence with the final status, where evidence is sourced from real RDAP/WHOIS network checks.

#### Scenario: Evidence sourced from real provider response
- **WHEN** a domain check completes through RDAP/WHOIS providers
- **THEN** each evidence entry SHALL include provider identity, normalized outcome, and request metadata derived from real network responses

### Requirement: Confidence scoring model
The system SHALL compute `confidence` from real provider outcomes, preserving existing weighting/cap behavior for `uncertain`.

#### Scenario: Confidence with mixed real provider results
- **WHEN** RDAP and WHOIS providers return mixed availability/error outcomes
- **THEN** the system SHALL compute confidence using configured weights and keep `uncertain` confidence at or below configured cap

### Requirement: IP cooldown policy
The system SHALL apply cooldown and failover rules based on real network error signals from provider requests.

#### Scenario: Cooldown triggered by HTTP 429
- **WHEN** repeated provider HTTP 429 responses are observed from the same outbound IP
- **THEN** that IP SHALL be placed in cooldown and excluded from selection until cooldown expiry

### Requirement: Quorum-based final decision
The system SHALL determine final status by quorum using normalized real provider outcomes.

#### Scenario: Real provider disagreement
- **WHEN** RDAP and WHOIS providers disagree and quorum is not satisfied
- **THEN** the system SHALL return `uncertain`
