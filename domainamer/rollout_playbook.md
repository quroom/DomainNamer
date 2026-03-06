# Hardened Availability Rollout Playbook

## Stages

1. `shadow`: Run hardened checker for telemetry only.
2. `canary_10`: Enable hardened response for 10% traffic.
3. `canary_50`: Expand to 50% traffic if canary metrics are healthy.
4. `full_100`: Enable for all traffic.

## Fallback Criteria

- Roll back to legacy immediately when:
  - `false_available_rate > 0.003`
  - `p95_latency_ms > 2000` for sustained 15m
  - provider error rate spikes above expected baseline

- Use `DOMAIN_HARDENED_FALLBACK_TO_LEGACY=True` and set
  `DOMAIN_HARDENED_CHECK_ENABLED=False` for full fallback.

## Alert Thresholds

- Warning: `uncertain_rate > 0.07` for 15m.
- Critical: `false_available_rate > 0.003` at any point.
