## 1. Auth and Ownership

- [x] 1.1 Add owner association to watch items and enforce authenticated access on watchlist APIs
- [x] 1.2 Add tests for unauthorized access and owner-scoped listing

## 2. Dedupe and Quota

- [x] 2.1 Add canonical TLD normalization and unique constraint for duplicate watch prevention
- [x] 2.2 Enforce per-user active watch quota via setting and validation
- [x] 2.3 Add tests for duplicate conflict and quota exceeded behavior

## 3. Async Check Job Orchestration

- [x] 3.1 Add `WatchlistCheckJob` model with lifecycle states (`queued`, `running`, `succeeded`, `failed`)
- [x] 3.2 Convert check endpoint to enqueue job and return `job_id`
- [x] 3.3 Add worker entrypoint to process queued jobs and persist summaries
- [x] 3.4 Add job status endpoint and tests for lifecycle transitions

## 4. Regression and Rollout Safety

- [x] 4.1 Ensure existing recommendation and alert transition behavior remains correct
- [x] 4.2 Run full test suite and document rollout/backfill steps
