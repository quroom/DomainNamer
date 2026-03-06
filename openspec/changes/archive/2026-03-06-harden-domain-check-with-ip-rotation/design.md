## Context

현재 도메인 가용성 판정은 단일 체크 결과를 중심으로 동작하며, 네트워크 타임아웃/429/응답 편차가 발생할 때 오탐 가능성이 있다. 이번 변경은 다중 provider와 IP rotation을 조합한 오케스트레이터를 추가해 판정 신뢰도를 개선하고, 판정 실패를 `uncertain` 상태로 명시적으로 표현한다.

## Goals / Non-Goals

**Goals:**
- `available/unavailable/uncertain` 3상태 판정 모델을 도입한다.
- provider 호출을 IP pool 기반으로 분산하고 헬스 점수/쿨다운으로 failover 한다.
- 다중 응답을 quorum 규칙으로 합의해 최종 상태를 결정한다.
- 응답에 `confidence`와 `evidence`를 포함해 판정 근거를 노출한다.
- 실패/레이트리밋/응답충돌을 재현 가능한 테스트로 검증한다.

**Non-Goals:**
- 외부 provider 상용 계약/빌링 자동화
- LLM 기반 추천 품질 고도화
- 대시보드 UI 완성

## Decisions

1. 도메인 체크는 오케스트레이터 계층(`availability_orchestrator`)에서 수행한다.
- 이유: provider별 구현 세부사항과 판정 정책을 분리해 확장성을 확보한다.
- 대안: 기존 단일 서비스 내부에서 분기 처리. 복잡도와 테스트 결합도가 증가한다.

2. IP rotation은 헬스 기반 선택 정책을 사용한다.
- 기준: 최근 성공률, 최근 429 비율, p95 지연, cooldown 만료 여부.
- 이유: 무작위 선택보다 장애 회피가 빠르고 안정적이다.
- 대안: 랜덤 라운드로빈. 장애 IP 재사용 빈도가 높아진다.

3. 최종 판정은 quorum 기반으로 확정한다.
- 규칙: 2개 이상 동일 판정이면 확정, 그 외는 `uncertain`.
- 이유: 단일 provider 오탐을 줄인다.
- 대안: 1차 응답 우선. 저지연이지만 신뢰도 저하 위험이 크다.

4. 캐시는 상태별 TTL을 다르게 둔다.
- `available/unavailable`: 중간 TTL, `uncertain`: 짧은 TTL.
- 이유: 불확실 결과를 빠르게 재검증하기 위함.

5. confidence는 "판정 신뢰도"로 계산하며 상태와 분리한다.
- 계산식:
  `confidence = clamp(0, 1, 0.45*agreement + 0.20*source_quality + 0.15*ip_health + 0.10*freshness - 0.10*error_penalty)`
- `uncertain` 상태는 계산값과 무관하게 `confidence <= 0.49` 캡 적용.
- 이유: availability 자체와 판정 확실도를 분리해 운영 튜닝 가능성을 확보한다.

6. 운영 기본 파라미터를 설정 키로 고정한다.
- `AVAILABILITY_PROVIDER_TIMEOUT_MS=1200`
- `AVAILABILITY_BUDGET_TIMEOUT_MS=1800`
- `AVAILABILITY_QUORUM_MIN=2`
- `AVAILABILITY_UNCERTAIN_CONFIDENCE_CAP=0.49`
- `IP_POOL_COOLDOWN_BASE_SEC=60`
- `IP_POOL_COOLDOWN_MAX_SEC=600`
- `CONFIDENCE_WEIGHT_AGREEMENT=0.45`
- `CONFIDENCE_WEIGHT_SOURCE=0.20`
- `CONFIDENCE_WEIGHT_HEALTH=0.15`
- `CONFIDENCE_WEIGHT_FRESHNESS=0.10`
- `CONFIDENCE_WEIGHT_ERROR=0.10`

## Risks / Trade-offs

- [지연 증가] -> Mitigation: 병렬 요청 + quorum 조기 종료
- [운영비 증가(IP/proxy/provider)] -> Mitigation: 상태별 캐시 TTL, 저신뢰 케이스만 재시도
- [provider 정책 위반 가능성] -> Mitigation: 레이트리밋 가드, 약관 준수 설정 강제
- [`uncertain` 비율 과다] -> Mitigation: provider 수 조정, timeout 튜닝, 사후 재검증 큐 도입

## Migration Plan

1. provider 추상화 인터페이스/오케스트레이터/판정기 추가
2. IP pool/헬스 상태 저장소(메모리 기반 시작) 추가
3. 기존 추천 API 응답 확장(`confidence`, `evidence`, `uncertain`) 적용
4. 테스트(단위/통합/실패 주입) 추가
5. shadow mode로 결과만 기록하고 사용자 응답에는 미반영
6. 10% 카나리 -> 50% 확장 -> 100% 전환
7. 운영 기준 충족 시 기본값 전환, 미충족 시 즉시 fallback

Rollback: 기능 플래그 off로 단일 provider 경로로 즉시 복귀.

## Open Questions

- provider 조합(RDAP vs WHOIS) 기본 우선순위는 어떻게 둘 것인가?
- IP pool 상태를 다중 인스턴스 간 공유할 필요가 있는가?
