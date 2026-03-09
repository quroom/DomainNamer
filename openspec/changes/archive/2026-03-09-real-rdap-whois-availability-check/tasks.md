## 1. Provider Adapters

- [x] 1.1 Implement `RdapProvider` adapter with real HTTP request and response normalization
- [x] 1.2 Implement `WhoisProvider` adapter (library or HTTP bridge) with normalized outcomes
- [x] 1.3 Add provider timeout/retry settings and request metadata capture for evidence

## 2. Orchestrator Integration

- [x] 2.1 Wire real providers into availability orchestrator behind feature flag
- [x] 2.2 Preserve quorum/confidence/uncertain behavior with real provider outcomes
- [x] 2.3 Map network failures to standard error codes (`timeout`, `rate_limited`, `error`)
- [x] 2.4 Ensure IP cooldown/failover logic reacts to real provider HTTP/network errors

## 3. Recommendation Path

- [x] 3.1 Update recommendation flow to expose real provider evidence payloads
- [x] 3.2 Keep duplicate normalization behavior unchanged while upgrading availability source
- [x] 3.3 Verify fallback and shadow mode behavior with real-provider path enabled

## 4. Testing

- [x] 4.1 Add unit tests for RDAP/WHOIS response parsing and normalization
- [x] 4.2 Add integration tests using mocked HTTP responses for success/conflict/error cases
- [x] 4.3 Add failure tests for timeout/429 bursts and IP cooldown transitions
- [x] 4.4 Run full test suite and confirm duplicate-check regression coverage remains green
