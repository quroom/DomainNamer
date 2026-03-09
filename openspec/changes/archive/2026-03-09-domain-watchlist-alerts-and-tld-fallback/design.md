## Context

현재 추천 로직은 `.com` 중심이며, 사용자가 원하는 도메인 가용성 변화를 지속 추적하는 기능이 없다. 기존 가용성 오케스트레이터를 재사용해 watchlist를 주기 점검하고, 상태 전이 기반 알림을 저장하는 구조를 추가한다.

## Goals / Non-Goals

**Goals:**
- watchlist 등록/조회 API 제공
- 배치 체크 루틴으로 watch item 상태 최신화
- `unavailable -> available` 전이에 대한 알림 이벤트 생성
- 추천 로직에 TLD fallback 대안(`.kr`, `.io`) 추가

**Non-Goals:**
- 실시간 푸시/메일 인프라 완전 구축
- 인증/권한 시스템 도입
- 외부 메시지 브로커 도입

## Decisions

1. 모델을 `DomainWatchItem`, `DomainAlertEvent` 두 개로 분리한다.
- WatchItem은 추적 대상과 마지막 상태를 보관한다.
- AlertEvent는 전이 이벤트 이력을 보관한다.

2. 알림 트리거는 상태 전이(`unavailable` -> `available`)로 제한한다.
- 노이즈를 줄이고 사용자가 실제로 필요한 순간에만 이벤트를 발생시킨다.

3. 배치 체크는 서비스 함수(`run_watchlist_check`)로 구현한다.
- 스케줄러(cron/celery) 연결이 쉬운 진입점을 제공한다.

4. 추천 fallback 순서는 `preferred_tlds` 설정을 따른다.
- 기본값은 `com,kr,io`이며 현재 후보의 TLD를 제외한 순서로 대안을 생성한다.

## Risks / Trade-offs

- [watch 항목 증가에 따른 점검 지연] -> Mitigation: 향후 배치 크기 제한/분할 실행 추가
- [registry별 응답 편차] -> Mitigation: 기존 가용성 오케스트레이터 표준 결과 재사용
- [알림 과다] -> Mitigation: 전이 이벤트만 생성하고 동일 상태 반복은 무시

## Migration Plan

1. 모델/마이그레이션 추가
2. watchlist API + check 서비스 구현
3. 추천 fallback 로직 확장
4. 테스트 추가 후 배포

Rollback: 신규 엔드포인트 비활성화 및 watchlist 체크 호출 중지. 기존 추천 기능은 영향 없이 유지.

## Open Questions

- 실제 운영에서 알림 채널 우선순위(이메일 vs 웹훅) 기본값은 무엇으로 둘 것인가?
- watchlist 점검 주기를 기본 몇 분으로 둘 것인가?
