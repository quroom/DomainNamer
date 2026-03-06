## Why

현재는 도메인 후보가 이미 사용 중이거나 내부 후보 목록과 중복될 때 사용자에게 즉시 대체안을 제공하는 흐름이 명확하지 않아 탐색 효율이 떨어진다. 중복 체크 직후 자동 추천을 제공하면 후보 재탐색 반복을 줄이고 생성 성공률을 높일 수 있다.

## What Changes

- 도메인 후보 생성 시 중복 체크(내부 후보 중복 + 외부 사용 가능 여부)를 수행한다.
- 중복 또는 사용 불가로 판정된 후보에 대해 즉시 대체 추천 후보를 자동 생성한다.
- 추천 결과에 원인(중복/사용 불가)과 함께 대체 후보 목록을 반환하는 응답 구조를 추가한다.
- 중복 체크와 자동 추천 동작을 검증하는 테스트를 추가한다.

## Capabilities

### New Capabilities
- `domain-duplicate-check-and-auto-recommendation`: 생성된 도메인 후보의 중복 및 사용 가능 여부를 확인하고, 불가한 경우 대체 추천 후보를 자동으로 제공한다.

### Modified Capabilities
- 없음

## Impact

- Affected code: `domainamer/views.py`, 신규 서비스/유틸 모듈(도메인 중복 체크 및 추천 로직), `domainamer/tests.py`
- APIs: 도메인 생성/검증 응답에 추천 후보 및 판정 사유 필드가 추가될 수 있음
- Dependencies: 기존 도메인 확인 라이브러리(WHOIS 등) 사용 경로 정리 필요
- Systems: 도메인 후보 생성 흐름과 결과 렌더링(HTMX 포함) 업데이트 필요
