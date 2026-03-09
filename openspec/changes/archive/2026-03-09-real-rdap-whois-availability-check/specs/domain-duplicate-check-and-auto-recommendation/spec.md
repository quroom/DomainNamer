## MODIFIED Requirements

### Requirement: Recommendation response contract
The system SHALL return recommendation evidence fields populated from the real availability-check pipeline.

#### Scenario: Recommendation contains provider evidence
- **WHEN** recommendation response includes availability metadata
- **THEN** `evidence` SHALL reference normalized RDAP/WHOIS provider outcomes instead of simulation-only markers
