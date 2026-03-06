## 1. Service and Domain Logic

- [x] 1.1 Create `domainamer/services/domain_recommender.py` with candidate normalization and duplicate detection
- [x] 1.2 Implement availability-check integration via injectable checker and candidate status decisioning
- [x] 1.3 Implement automatic alternatives generator for `duplicate`/`unavailable` candidates

## 2. API and Routing

- [x] 2.1 Add Django view endpoint that accepts candidate list and returns structured JSON recommendation payload
- [x] 2.2 Wire URL routes for recommendation endpoint under `domainamer/` paths

## 3. Verification

- [x] 3.1 Add unit tests for normalization, duplicate classification, and alternatives generation
- [x] 3.2 Add integration-style view test to verify response contract (`results[].candidate/status/reason/alternatives`)
- [x] 3.3 Run test suite and adjust implementation for deterministic passing behavior
