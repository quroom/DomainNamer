## Why

watchlist 기능이 공개 API로 노출될 경우 인증 부재, 동기식 체크, 중복 등록 문제로 보안/성능/운영 비용 리스크가 커진다. 운영 가능한 수준으로 올리기 위해 접근 제어와 비동기 실행, 등록 정책을 우선 정비해야 한다.

## What Changes

- watchlist API에 인증/권한 검증을 추가한다.
- `watchlist/check`를 동기 실행에서 비동기 잡 enqueue 방식으로 전환한다.
- 동일 watch 중복 등록을 방지하고 사용자별 watch 개수 제한을 추가한다.
- check job 상태 조회 API를 추가해 운영 가시성을 제공한다.

## Capabilities

### New Capabilities
- `watchlist-check-job-orchestration`: watchlist 점검을 job 기반으로 예약/실행/상태조회한다.

### Modified Capabilities
- `domain-watchlist-alerting`: watchlist 등록/조회/점검 API의 인증/권한 및 dedupe/quota 정책 요구사항을 강화한다.

## Impact

- Affected code: `domainamer/views.py`, `domainamer/models.py`, `domainamer/urls.py`, `domainamer/services/watchlist.py`
- API: watchlist endpoint 인증 필요, check endpoint는 job id 반환
- Data: check job 상태 저장 모델 및 unique/quota 관련 제약 추가
