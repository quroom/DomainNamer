## Context

도메인 추천 흐름의 핵심은 중복 체크 이후 실제 등록 여부를 정확히 판정하는 것이다. 현재는 `RuleBasedProvider` 기반 시뮬레이션으로 구조를 검증했지만, 운영 신뢰도를 위해 RDAP/WHOIS 실조회 provider를 도입해야 한다. 기존 quorum/confidence/IP rotation 구조는 유지하고 provider 어댑터만 교체 가능하도록 설계한다.

## Goals / Non-Goals

**Goals:**
- RDAP/WHOIS 기반 실조회 provider 인터페이스를 구현한다.
- provider 응답을 공통 결과 모델(`available/unavailable/error`)로 정규화한다.
- timeout/429/network 오류 시 retry/failover/cooldown 정책을 유지한다.
- mock HTTP 테스트로 실조회 경로를 결정론적으로 검증한다.

**Non-Goals:**
- 신규 AI 추천 알고리즘 추가
- UI/프론트엔드 리디자인
- 외부 유료 도메인 API 계약 자동화

## Decisions

1. provider 구현은 adapter 패턴으로 분리한다.
- `RdapProvider`, `WhoisProvider`를 `AvailabilityProvider` 프로토콜 구현체로 작성한다.
- 이유: 오케스트레이터 정책을 변경하지 않고 provider 교체/확장 가능.

2. RDAP 우선, WHOIS 보조로 운용한다.
- RDAP가 structured JSON 기반이라 파싱 안정성이 높다.
- WHOIS는 fallback/교차검증 소스로 사용한다.

3. 네트워크 오류는 `error_code` 표준화 후 기존 정책 재사용.
- timeout -> `timeout`, 429 -> `rate_limited`, 기타 -> `error`
- 이유: confidence/cooldown/telemetry 계산식 재사용.

4. 테스트는 실네트워크 대신 mock transport를 사용한다.
- HTTP 응답 본문/상태코드/지연을 fixture로 고정한다.
- 이유: CI 안정성과 재현성 확보.

## Risks / Trade-offs

- [레지스트리별 RDAP 응답 스키마 편차] -> Mitigation: 파서 계층에 필드 유무 허용 및 fallback 규칙 추가
- [WHOIS 파싱 불안정] -> Mitigation: WHOIS는 보조 신호로만 반영, 단독 확정 금지
- [네트워크 비용/지연 증가] -> Mitigation: 상태별 캐시 TTL 및 quorum 조기 종료
- [외부 정책 위반 가능성] -> Mitigation: 요청 빈도 제한, User-Agent/약관 준수

## Migration Plan

1. provider adapter(실조회) 추가 및 시뮬레이션 provider 분리
2. feature flag로 실조회 provider 활성화 경로 추가
3. mock HTTP 테스트 세트 추가 및 기존 테스트 리팩터링
4. shadow 모드에서 비교 기록 후 canary 전환
5. 지표 안정화 후 기본 provider를 실조회로 전환

Rollback: 실조회 flag off로 즉시 시뮬레이션 provider로 복귀.

## Open Questions

- 기본 RDAP endpoint 매핑 전략(TLD별 registry vs 중앙 endpoint)은 어떻게 둘 것인가?
- WHOIS 사용 시 라이브러리/CLI 중 어떤 경로가 운영 환경에서 더 안정적인가?
