## Why

단일 소스 기반 도메인 확인은 네트워크 장애, 레이트 리밋, 지역별 응답 편차 때문에 오탐 가능성이 있다. IP rotation과 다중 소스 합의(quorum)를 도입해 판정 신뢰도를 높이고 운영 중 불확실 상태를 명시적으로 처리해야 한다.

## What Changes

- 도메인 가용성 판정을 `available/unavailable/uncertain` 3상태로 확장한다.
- 회전 가능한 IP 풀과 헬스 기반 선택/쿨다운 정책을 도메인 체크 경로에 도입한다.
- 다중 provider 응답을 수집해 quorum 기반으로 최종 판정을 수행한다.
- 응답에 `confidence` 및 `evidence`(provider 결과 요약)를 포함한다.
- `uncertain` 상태에서 confidence 상한(`<= 0.49`)을 적용해 불확실 판정을 명시한다.
- 장애/429/타임아웃/응답충돌 케이스를 검증하는 테스트 세트를 추가한다.
- shadow -> 10% -> 50% -> 100% 점진 롤아웃과 SLO 기반 모니터링 기준을 포함한다.

## Capabilities

### New Capabilities
- `domain-availability-hardening-with-rotation`: 다중 provider와 IP rotation, quorum 판정을 통해 신뢰도 기반 도메인 가용성 판정을 제공한다.

### Modified Capabilities
- `domain-duplicate-check-and-auto-recommendation`: 기존 중복 체크 및 추천 흐름에서 가용성 판정 필드(`status`, `reason`)를 3상태 모델과 신뢰도 정보에 맞게 확장한다.

## Impact

- Affected code: 도메인 체크 서비스 계층(체커/오케스트레이터), API 응답 직렬화, 테스트 코드
- APIs: 추천/가용성 확인 응답 스키마에 `uncertain`, `confidence`, `evidence`, `checked_at` 추가
- Dependencies: RDAP/WHOIS provider 클라이언트 추상화 및 운영 설정(IP pool, timeout, retry) 필요
- Systems: 관측 지표(`false_available_rate`, `uncertain_rate`, `p95_latency`, provider_error_rate`) 수집 경로 필요
