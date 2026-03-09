## 1. Data Model

- [x] 1.1 Add `DomainWatchItem` and `DomainAlertEvent` models with migration
- [x] 1.2 Register models in admin for inspection

## 2. Watchlist Service and API

- [x] 2.1 Implement watchlist check routine that updates status and creates transition alerts
- [x] 2.2 Add API endpoints to create/list watch items and trigger check run
- [x] 2.3 Add input validation for base name and TLD list

## 3. Recommendation Fallback

- [x] 3.1 Extend recommendation alternative generation to include preferred TLD fallbacks
- [x] 3.2 Ensure `.com` unavailable path prioritizes `.kr`/`.io` alternatives before suffix variants

## 4. Tests

- [x] 4.1 Add unit tests for watchlist transition alert creation and deduplication
- [x] 4.2 Add API tests for watch create/list/check endpoints
- [x] 4.3 Add recommendation tests for TLD fallback ordering
- [x] 4.4 Run full test suite and mark all tasks complete
