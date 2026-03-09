## Why

`.com` 도메인이 이미 등록된 경우가 많아 사용자는 대안 TLD(`.kr` 등)를 수동으로 찾거나, 원하는 도메인이 풀릴 때까지 반복 확인해야 한다. 서비스에서 감시와 알림을 제공하면 이름 선택 비용을 줄이고 전환율을 높일 수 있다.

## What Changes

- 사용자가 원하는 도메인/TLD를 등록하는 watchlist API를 추가한다.
- 배치 체크로 watchlist 도메인 상태를 재검증하고 `unavailable -> available` 전이 시 알림 이벤트를 생성한다.
- 추천 API가 `.com` 불가 시 우선순위 TLD(`.kr`, `.io`) 대안을 자동 제시하도록 확장한다.
- 알림은 기본적으로 DB 이벤트로 저장하고, 선택적으로 콘솔/웹훅 어댑터 확장 지점을 제공한다.

## Capabilities

### New Capabilities
- `domain-watchlist-alerting`: 관심 도메인 감시 등록, 주기 점검, 상태 전이 알림 이벤트를 관리한다.

### Modified Capabilities
- `domain-duplicate-check-and-auto-recommendation`: `.com` unavailable 시 우선순위 TLD fallback 대안을 추천 응답에 포함하도록 변경한다.

## Impact

- Affected code: `domainamer/models.py`, `domainamer/views.py`, `domainamer/urls.py`, `domainamer/services/domain_recommender.py`, `domainamer/tests.py`
- API: watchlist CRUD/check 엔드포인트 추가, 추천 응답의 alternatives 생성 로직 확장
- Data: watchlist 및 alert event 테이블 추가
