## MODIFIED Requirements

### Requirement: Automatic alternatives for blocked candidates
The system SHALL generate alternative candidates for each `duplicate` or `unavailable` candidate and include them in the response, including prioritized TLD fallback alternatives.

#### Scenario: Alternatives returned for unavailable candidate
- **WHEN** `brandhub.com` is classified as `unavailable`
- **THEN** the response SHALL include one or more alternatives for `brandhub.com`

#### Scenario: Preferred TLD fallback for unavailable .com
- **WHEN** `brandhub.com` is classified as `unavailable`
- **THEN** alternatives SHALL include fallback TLD candidates such as `brandhub.kr` before synthetic suffix variants when available
