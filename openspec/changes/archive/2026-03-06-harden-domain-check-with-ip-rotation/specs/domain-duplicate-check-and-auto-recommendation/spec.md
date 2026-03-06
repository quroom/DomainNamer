## MODIFIED Requirements

### Requirement: Availability-based decisioning
The system SHALL check normalized non-duplicate candidates for domain availability and classify each candidate as `available`, `unavailable`, or `uncertain`.

#### Scenario: Unavailable candidate classification
- **WHEN** an availability check reports `brandhub.com` is registered
- **THEN** the candidate result SHALL be marked as `unavailable`

#### Scenario: Uncertain candidate classification
- **WHEN** availability providers return conflicting results or only error responses
- **THEN** the candidate result SHALL be marked as `uncertain`

### Requirement: Recommendation response contract
The system SHALL return a structured recommendation payload containing candidate, status, reason, alternatives, confidence, and evidence for every submitted candidate.

#### Scenario: Structured response shape
- **WHEN** a recommendation request is completed
- **THEN** the response SHALL contain `results[]` entries with `candidate`, `status`, `reason`, `alternatives`, `confidence`, and `evidence`

#### Scenario: Uncertain recommendation exposure
- **WHEN** availability resolution returns `uncertain`
- **THEN** the recommendation response SHALL preserve `uncertain` status and include non-empty `evidence` describing provider outcomes
