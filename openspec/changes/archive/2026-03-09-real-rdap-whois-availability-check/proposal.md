## Why

현재 가용성 판정은 내부 시뮬레이션 provider에 의존하므로 실제 도메인 등록 상태를 신뢰성 있게 반영하지 못한다. RDAP/WHOIS 기반의 실제 네트워크 조회로 전환해 중복 체크 이후 판정 정확도를 운영 수준으로 끌어올려야 한다.

## What Changes

- 시뮬레이션 provider를 실제 RDAP/WHOIS HTTP 요청 provider로 교체한다.
- provider별 타임아웃/재시도/429 처리와 IP rotation failover를 실제 네트워크 호출 경로에 적용한다.
- provider 응답을 공통 모델로 파싱해 quorum/uncertain/confidence 판정 파이프라인에 연결한다.
- 테스트를 mock HTTP 기반으로 재구성해 성공/실패/충돌 응답을 재현 가능하게 검증한다.
- 운영 안전장치(캐시 TTL, fallback, shadow 모드)를 유지한 채 실제 체크 전환을 지원한다.

## Capabilities

### New Capabilities
- 없음

### Modified Capabilities
- `domain-availability-hardening-with-rotation`: provider 체크 방식을 시뮬레이션에서 실제 RDAP/WHOIS 네트워크 조회로 변경한다.
- `domain-duplicate-check-and-auto-recommendation`: 실제 provider 근거를 recommendation evidence에 반영하도록 응답 의미를 보강한다.

## Impact

- Affected code: `domainamer/services/availability.py`, `domainamer/views.py`, `domainamer/tests.py`
- APIs: 응답 스키마는 유지하되 `evidence` 항목의 provider/source 데이터가 실조회 결과로 채워짐
- Dependencies: HTTP 클라이언트(`requests` 또는 `httpx`) 및 provider endpoint 구성 필요
- Systems: 네트워크 실패율/latency 모니터링 및 캐시 정책 튜닝 필요
