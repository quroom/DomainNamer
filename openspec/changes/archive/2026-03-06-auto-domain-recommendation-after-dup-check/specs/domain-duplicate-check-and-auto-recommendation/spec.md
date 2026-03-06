## ADDED Requirements

### Requirement: Candidate duplicate normalization
The system SHALL normalize candidate names before duplicate checks using lowercase and removal of hyphens and spaces.

#### Scenario: Duplicate detected after normalization
- **WHEN** candidate list includes `my-app.com` and `My App.com`
- **THEN** the second candidate SHALL be marked as `duplicate`

### Requirement: Availability-based decisioning
The system SHALL check normalized non-duplicate candidates for domain availability and classify each candidate as `available` or `unavailable`.

#### Scenario: Unavailable candidate classification
- **WHEN** an availability check reports `brandhub.com` is registered
- **THEN** the candidate result SHALL be marked as `unavailable`

### Requirement: Automatic alternatives for blocked candidates
The system SHALL generate alternative candidates for each `duplicate` or `unavailable` candidate and include them in the response.

#### Scenario: Alternatives returned for unavailable candidate
- **WHEN** `brandhub.com` is classified as `unavailable`
- **THEN** the response SHALL include one or more alternatives for `brandhub.com`

### Requirement: Recommendation response contract
The system SHALL return a structured recommendation payload containing candidate, status, reason, and alternatives for every submitted candidate.

#### Scenario: Structured response shape
- **WHEN** a recommendation request is completed
- **THEN** the response SHALL contain `results[]` entries with `candidate`, `status`, `reason`, and `alternatives`
