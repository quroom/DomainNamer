## Context

현재 watchlist는 인증 없이 접근 가능하고, `watchlist/check`가 요청-응답 경로에서 즉시 전체 점검을 수행한다. watch 항목이 증가하면 API latency와 timeout 위험이 커지고, 중복 등록으로 체크 비용이 불필요하게 증가할 수 있다.

## Goals / Non-Goals

**Goals:**
- watchlist API 인증/권한 적용
- check 실행을 비동기 job 방식으로 분리
- watch 중복 등록 방지 + 사용자별 quota 적용
- job 상태/결과 조회 API 제공

**Non-Goals:**
- 외부 메시지 브로커 대규모 도입
- 멀티테넌트 권한 모델 전면 개편
- 알림 채널 확장(email/webhook/slack) 구현

## Decisions

1. 인증 우선순위
- Django session/auth를 기본으로 적용하고, 미인증 요청은 401/403 처리.
- 이유: 현재 코드베이스와 가장 낮은 통합 비용.

2. 비동기 실행 모델
- `WatchlistCheckJob` 모델 기반 DB queue를 우선 채택.
- API는 job enqueue만 담당, 실행은 management command/worker가 poll.
- 이유: 추가 인프라 없이 빠른 운영 안정화 가능.

3. 중복 등록 정책
- `owner + base_name + canonical_tlds` 유니크 제약 적용.
- canonical_tlds는 정렬/정규화 문자열로 저장.
- 이유: 순서가 다른 동일 의미 입력도 중복으로 차단.

4. quota 정책
- 설정값 `WATCHLIST_MAX_ITEMS_PER_USER` 도입.
- 생성 시 active 개수를 확인해 초과 시 reject.

## Risks / Trade-offs

- [DB queue 처리 지연] -> Mitigation: worker 주기/배치 크기 설정 가능하게 제공
- [권한 변경으로 기존 클라이언트 깨짐] -> Mitigation: rollout 기간 동안 명시적 에러 문서화
- [유니크 제약 마이그레이션 충돌] -> Mitigation: 기존 중복 데이터 정리 스크립트 제공

## Migration Plan

1. owner/job/canonical_tlds 필드 추가 및 마이그레이션
2. 중복 레코드 정리
3. API 인증/quota/중복 검사 반영
4. check endpoint를 job enqueue로 전환
5. worker + status endpoint 배포

Rollback: check endpoint를 동기 실행으로 복원하고, job worker 중지.

## Open Questions

- 기본 worker polling 주기(예: 5s/15s/30s)는 무엇이 적절한가?
- job retention 기간(예: 7일/30일)은 얼마로 할 것인가?
