## ADDED Requirements

### Requirement: Asynchronous check dispatch
The system SHALL enqueue watchlist check execution and return a job reference immediately.

#### Scenario: Dispatch returns job id
- **WHEN** a client requests watchlist check run
- **THEN** the system SHALL create a check job in `queued` state and return `job_id`

### Requirement: Job lifecycle tracking
The system SHALL track job status transitions for watchlist check runs.

#### Scenario: Job status progresses
- **WHEN** worker starts processing a queued job
- **THEN** job status SHALL transition `queued -> running -> succeeded|failed`

### Requirement: Job result visibility
The system SHALL expose check job summary and recent alerts through a job-status endpoint.

#### Scenario: Read completed job summary
- **WHEN** client requests a completed job status
- **THEN** response SHALL include processed item count, checked domain count, alerts created count, and completion timestamp
