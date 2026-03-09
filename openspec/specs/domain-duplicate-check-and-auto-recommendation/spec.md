## Purpose

Define requirements for domain duplicate detection and automatic alternative recommendation.

## Requirements

### Requirement: Candidate duplicate normalization
The system SHALL normalize candidate names before duplicate checks using lowercase and removal of hyphens and spaces.

#### Scenario: Duplicate detected after normalization
- **WHEN** candidate list includes `my-app.com` and `My App.com`
- **THEN** the second candidate SHALL be marked as `duplicate`

### Requirement: Availability-based decisioning
The system SHALL check normalized non-duplicate candidates for domain availability and classify each candidate as `available`, `unavailable`, or `uncertain`.

#### Scenario: Unavailable candidate classification
- **WHEN** an availability check reports `brandhub.com` is registered
- **THEN** the candidate result SHALL be marked as `unavailable`

#### Scenario: Uncertain candidate classification
- **WHEN** availability providers return conflicting results or only error responses
- **THEN** the candidate result SHALL be marked as `uncertain`

### Requirement: Automatic alternatives for blocked candidates
The system SHALL generate alternative candidates for each `duplicate` or `unavailable` candidate and include them in the response.

#### Scenario: Alternatives returned for unavailable candidate
- **WHEN** `brandhub.com` is classified as `unavailable`
- **THEN** the response SHALL include one or more alternatives for `brandhub.com`

### Requirement: Recommendation response contract
The system SHALL return a structured recommendation payload containing candidate, status, reason, alternatives, confidence, and evidence for every submitted candidate, with evidence fields populated from the real availability-check pipeline.

#### Scenario: Structured response shape
- **WHEN** a recommendation request is completed
- **THEN** the response SHALL contain `results[]` entries with `candidate`, `status`, `reason`, `alternatives`, `confidence`, and `evidence`

#### Scenario: Uncertain recommendation exposure
- **WHEN** availability resolution returns `uncertain`
- **THEN** the recommendation response SHALL preserve `uncertain` status and include non-empty `evidence` describing provider outcomes

#### Scenario: Recommendation contains provider evidence
- **WHEN** recommendation response includes availability metadata
- **THEN** `evidence` SHALL reference normalized RDAP/WHOIS provider outcomes instead of simulation-only markers
