## 1. Availability Architecture

- [x] 1.1 Add provider interface and result model for multi-source availability checks
- [x] 1.2 Implement quorum decision function for `available/unavailable/uncertain`
- [x] 1.3 Add response metadata fields (`confidence`, `evidence`) to availability output contract
- [x] 1.4 Implement confidence calculation formula with configurable weights and uncertain cap (`<= 0.49`)

## 2. IP Rotation and Resilience

- [x] 2.1 Implement IP pool model with health score and cooldown metadata
- [x] 2.2 Add IP selection strategy that prioritizes healthy IPs and excludes cooldown IPs
- [x] 2.3 Add retry/failover flow for timeout/429/provider errors
- [x] 2.4 Implement cooldown trigger rules (429 x3, timeout x4) and exponential cooldown backoff

## 3. API Integration

- [x] 3.1 Integrate orchestrator into domain recommendation endpoint while preserving duplicate detection flow
- [x] 3.2 Extend response serialization to include `uncertain` status, `confidence`, `evidence`, and `checked_at`
- [x] 3.3 Add feature flag/config toggles for rollout and fallback to legacy checker
- [x] 3.4 Add shadow mode path that records hardened results without affecting user-visible status

## 4. Verification

- [x] 4.1 Add unit tests for quorum decisions and confidence calculation
- [x] 4.2 Add unit tests for IP pool health scoring, cooldown, and failover behavior
- [x] 4.3 Add integration tests covering conflicting provider responses and `uncertain` output
- [x] 4.4 Add failure-injection tests for timeout/429 spikes and verify no false `available` leaks
- [x] 4.5 Add tests for confidence thresholds (`>=0.90`, `0.60-0.89`, `<=0.49`) and uncertain cap enforcement

## 5. Rollout and SLO

- [x] 5.1 Add telemetry for `false_available_rate`, `uncertain_rate`, `p95_latency`, and provider error rate
- [x] 5.2 Add rollout playbook for shadow -> 10% -> 50% -> 100% and fallback criteria
- [x] 5.3 Define alert thresholds (`uncertain_rate > 7%` warning, `false_available_rate > 0.3%` critical)
