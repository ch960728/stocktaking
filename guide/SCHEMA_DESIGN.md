# DB 스키마 설계

MariaDB. 아래 모든 테이블에는 [[DEVELOPMENT_GUIDELINES.md]]에서 정의한 감사 5필드가 공통으로 붙는다 (표별 설명에서는 생략):
`created_by VARCHAR(50) NOT NULL DEFAULT 'admin'`, `created_at DATETIME NOT NULL`, `updated_by VARCHAR(50) NOT NULL DEFAULT 'admin'`, `updated_at DATETIME NOT NULL`, `is_active BOOLEAN NOT NULL DEFAULT TRUE`.

인증 기능이 없는 시스템이므로 `created_by`/`updated_by`는 항상 `"admin"` 문자열로 채운다. 삭제는 전부 논리 삭제(`is_active = false`)이며 물리 삭제는 없다.

## common_code_groups (공통코드 그룹)

관리 대상 그룹은 요구사항으로 고정된 4개뿐이므로 앱 시작 시 시드(seed)한다. 그룹 자체를 UI로 추가/삭제하지는 않는다.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | PK | |
| group_code | VARCHAR(30), UNIQUE | `UNIT`, `LOCATION`, `CATEGORY`, `SIZE_ABBR` |
| group_name | VARCHAR(50) | 화면 표시명: 단위 / 위치 / 구분 / 규격약식 |

## common_codes (공통코드)

공통코드 등록 페이지(1번 페이지)에서 그룹별로 CRUD하는 실제 값. 예: `UNIT` 그룹 아래 "EA", "BOX" / `SIZE_ABBR` 그룹 아래 "소", "중", "대".

| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | PK | |
| group_id | FK → common_code_groups.id | |
| code | VARCHAR(30) | 그룹 내 코드값 |
| name | VARCHAR(50) | 화면 표시명 |
| sort_order | INT, DEFAULT 0 | 목록/드롭다운 정렬 순서 |

제약: `UNIQUE(group_id, code)`. 인덱스: `(group_id, is_active, sort_order)` — 그룹별 활성 코드 드롭다운 조회용.

## items (품목)

품목 등록 페이지(2번 페이지) 대상. `*` 표시는 필수.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | PK | |
| item_name * | VARCHAR(200) | 품목명 |
| item_no | VARCHAR(100), NULL 허용 | 품번 |
| barcode | VARCHAR(100), NULL 허용 | 바코드 (일반 식별용, 검색만 됨 — 스캔 매칭에는 안 씀) |
| barcode_prefix | VARCHAR(100), NULL 허용, UNIQUE | 바코드구분 — 센서류 등 품목(제품 라인) 단위로 si/so/sj처럼 시작하는 접두어. 품목 1건과 1:1로 고유. 물리적 개별 바코드 전체값이 아니라 그 "앞부분"만 저장함 — 센서 재고 등록(`/scan`)이 스캔값을 접두어로 매칭해 어느 품목인지 찾는 데 씀 |
| category_id * | FK → common_codes.id (group=CATEGORY) | 구분 |
| unit_id * | FK → common_codes.id (group=UNIT) | 단위 |
| location_id | FK → common_codes.id (group=LOCATION), NULL 허용 | 위치 |
| size_abbr_id | FK → common_codes.id (group=SIZE_ABBR), NULL 허용 | 규격약식(소/중/대) |
| size_width | DECIMAL(10,2), NULL 허용 | 규격상세 - 폭 |
| size_length | DECIMAL(10,2), NULL 허용 | 규격상세 - 길이 |
| size_height | DECIMAL(10,2), NULL 허용 | 규격상세 - 높이 |

인덱스:
- `INDEX idx_items_item_name (item_name)` — 검색/자동완성 성능용
- `INDEX idx_items_item_no (item_no)`
- `INDEX idx_items_barcode (barcode)`
- `UNIQUE INDEX barcode_prefix (barcode_prefix)` — 중복 방지 + 스캔 시 빠른 조회
- `INDEX idx_items_category (category_id)`
- `INDEX idx_items_location (location_id)`

품목 등록 시 자동완성: `item_name`으로 기존 품목을 LIKE 검색해 유사 품목을 후보로 보여주고, 선택 시 구분/단위/위치/규격 값을 폼에 미리 채워준다(신규 등록 편의 목적이며 기존 품목을 수정하는 것은 아님). `item_no`/`barcode`/`barcode_prefix`는 품목마다 다른 식별값이라 이 자동완성이 폼에 대신 채워주지 않는다 — 사용자가 직접 입력.

품목 검색(품목 목록, 재고 등록 페이지의 품목 검색, 현황 페이지)은 `item_name`/`item_no`/`barcode`/`barcode_prefix` 네 컬럼을 OR로 묶어 검색한다(`crud/item.py::search_clause`, 다른 도메인에서도 재사용). `barcode_prefix`를 새로 등록/수정할 때는 저장 전에 `crud/item.py::barcode_prefix_exists`로 중복을 먼저 확인해 깔끔한 409 에러를 주고, DB의 UNIQUE 제약은 최후 방어선 역할만 한다.

**`barcode_prefix`의 UNIQUE 제약은 대소문자를 구분하지 않는다** — 테이블 collation이 `utf8mb4_uca1400_ai_ci`(ci = case-insensitive)라서 "SJ"와 "sj"는 DB 입장에서 같은 값. 또한 `barcode_prefix_exists`는 `is_active = true`인 품목만 검사하고, 품목이 삭제(비활성화)될 때 `deactivate_item`이 그 품목의 `barcode_prefix`를 같이 `NULL`로 비운다 — 삭제된 품목이 UNIQUE 값을 계속 붙들고 있어서 같은(또는 대소문자만 다른) 값의 신규 등록을 막는 걸 방지하기 위함.

## stocktake_records (재고조사기록)

재고 등록 페이지(3번 페이지) 대상. 한 품목에 대해 특정 시점에 조사한 수량 스냅샷.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | PK | |
| item_id * | FK → items.id | 조사 대상 품목 |
| quantity * | DECIMAL(12,2) | 조사 수량 |
| survey_date * | DATE | 조사일자 (기본값: 오늘) |
| note | VARCHAR(500), NULL 허용 | 비고 |

인덱스:
- `INDEX idx_stocktake_item (item_id)`
- `INDEX idx_stocktake_date (survey_date)`

재고 등록 시 품목 검색/자동완성은 `items` 테이블을 품목명/구분/위치로 필터링해 지원한다 (전용 테이블 없이 품목 검색 API를 재사용).

### 재고 등록 폼 ("재고조사 기록 추가" 카드)

구분/위치 select는 재고조사 기록에 저장되는 값이 아니다 — 순전히 UI 보조 역할이며, 의미가 시점에 따라 바뀐다:
- **품목 선택 전**: 품목 콤보박스를 좁히는 검색 필터(`GET /api/items?category_id=...&location_id=...`).
- **품목 선택 후**: 그 품목의 실제 구분/위치로 강제 동기화되어 "이 품목은 이 구분/위치다"를 보여주는 읽기용 표시로 바뀐다. 사용자가 그 뒤에 select를 다시 바꾸면 "새로 검색 시작"으로 취급되어 선택이 풀린다.

즉 구분/위치는 항상 `items` 테이블(품목 등록 데이터)이 기준이고, 재고조사 폼에서 독립적으로 입력받는 값이 아니다.

품목을 선택하면 수량 입력란에 `GET /api/stocktakes/latest/{item_id}`(→ `crud/stocktake.py::get_latest_quantity`) 값을 자동으로 채워 넣는다. `step="1"`이라 네이티브 숫자 스피너(위/아래 화살표)로 1 단위 조정이 되고, 직접 타이핑으로 정확한 값을 입력하는 것도 가능하다(별도 +/- 버튼은 넣었다가 불필요하다는 피드백으로 제거함). 여전히 "그 시점의 전체 수량"을 저장하는 스냅샷 방식 — 증감 델타를 별도로 기록하지 않음.

**바코드 추적 품목(`barcode_prefix` 있는 품목, 또는 과거 바코드가 등록된 적 있어 `barcode_count > 0`인 품목)은 이 수량이 "전체 현재고"가 아니라 "바코드 없는 보유 수량"만 의미한다.** 품목을 선택하면 폼이 이를 감지해(`static/js/stocktakes.js::isSensorTracked`) 라벨을 "수량 *"에서 "바코드 없는 보유 수량 *"으로 바꾼다. 처음엔 안내 문구 한 줄("바코드 추적 N개 + 바코드없음 M개 = 현재고 N+M개")로만 보여줬는데, "수량을 바꾸면 전체가 그 값이 되는 것 아니냐"고 오해하기 쉽다는 문제가 실제로 드러나서(아래 쪽 발견/교정 기록 참고) **`#stock-breakdown` 카드로 세 숫자를 명확히 분리**해서 보여주도록 바꿈: 바코드 수량 / 바코드 없는 수량 / 총 현재고(굵게 강조) 세 줄. 일반 품목은 이 카드 자체가 안 보이고 기존처럼 "선택된 품목: XXX / 현재고 N" 한 줄만 쓴다. 일반 품목은 이 수량 자체가 곧 현재고이므로 입력 동작은 그대로다. 이 구분이 왜 필요한지는 바로 아래 "sensor_barcodes"/"현황" 절 참고 — 바코드로 추적되는 수량과 수동 입력 수량이 서로 무관하게 따로 노는 게 실제 문제로 지적되어, 두 숫자를 더해 하나의 "현재고"로 합치도록 재설계됨.

## sensor_barcodes (센서 바코드)

센서 재고 등록 페이지(5번 페이지, `/scan`)가 쓰는 테이블. **센서 하나하나(물리적 개체)는 자기만의 고유한 전체 바코드 문자열을 가지며, 그 앞부분(접두어)이 `items.barcode_prefix`와 일치해 어느 품목(제품 라인)인지 결정된다.** 즉 `barcode_prefix`="si"인 품목 하나에, 실제로는 "si-0001", "si-0002", ... 처럼 서로 다른 바코드를 가진 센서가 여러 개 등록될 수 있다 — `barcode_prefix` 자체가 스캔값 전체와 같은 게 아니다 (이 부분이 처음엔 "품목 1건과 1:1로 고유"로 잘못 이해되어 한 차례 재설계됨, [[PLAN.md]] 히스토리 참고).

| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | PK | |
| item_id * | FK → items.id | 어느 품목(제품 라인)의 센서인지 |
| barcode * | VARCHAR(100), UNIQUE | 스캔한 바코드 전체 값 (개체별로 고유) |

인덱스: `INDEX ix_sensor_barcodes_item (item_id)`, `UNIQUE` 제약은 `barcode` 컬럼 자체에.

`/scan` 페이지에는 **입고(등록)/출고(제거)** 두 모드가 있다 — "재고 감소는 어떻게 처리하나"에 대한 답: 일반 재고 등록(수량 입력)으로 뭉뚱그려 줄이는 게 아니라, **빠지는 센서의 바코드를 직접 스캔**해서 그 개체 하나를 정확히 제거한다(그래서 "어떤 센서가 없는지" 항상 알 수 있음).

입고 — `POST /api/sensor-barcodes/scan {barcode}`:
1. 이미 **활성** 상태로 등록된 `barcode`면 409(중복) — 새로 만들지 않음.
2. 같은 `barcode`가 과거에 등록됐다가 제거(비활성)된 상태라면, 새 행을 만들지 않고 그 행을 다시 활성화한다(`barcode`가 전역 UNIQUE라 같은 값으로 새 행을 또 만들 수 없음 — 현장에서 나갔다가 다시 들어오는 개체를 위한 재활성화 경로, `crud/sensor_barcode.py::reactivate_barcode`).
3. 둘 다 아니면(완전히 새로운 값), `items.barcode_prefix`가 설정된 모든 품목 중 스캔값이 그 `barcode_prefix`로 **시작하는** 품목을 찾는다(`crud/item.py::find_item_by_scanned_barcode`). 여러 접두어가 겹칠 수 있는 경우(예: "s"와 "si") 가장 긴 접두어가 우선. 매칭되는 품목이 없으면 404 — 임의로 새 품목을 만들거나 추측 매칭하지 않음.
4. 매칭/재활성화된 품목으로 `sensor_barcodes` 행을 만들거나 되살린다. `stocktake_records`는 건드리지 않는다 — 센서 개수는 `stocktake_records`의 "+1 누적"이 아니라 `sensor_barcodes`에서 활성 상태인 행 개수로 집계한다 (바로 아래 "현황" 절 참고).

출고 — `POST /api/sensor-barcodes/remove {barcode}`: `barcode` 값으로 정확히 일치하는 **활성** 행을 찾아 논리 삭제. 등록된 적이 없거나 이미 제거된 값이면 404.

현황 페이지에서도 개별 바코드 옆의 "제거" 버튼으로 같은 논리 삭제를 호출할 수 있다(`DELETE /api/sensor-barcodes/{id}`, id 기준) — 스캐너가 없거나 바코드를 다시 스캔하기 어려운 상황에서 목록을 직접 보며 바로잡는 경로.

바코드 자체를 잃어버린 센서는 이 테이블로 추적되지 않으며, 그런 경우는 일반 재고 등록(3번 페이지)에서 "바코드 없는 보유 수량"으로 수동 입력한다 — 그 수동 수량이 이 테이블의 활성 개수와 합쳐져(`current_stock`) 하나의 현재고로 집계되므로(바로 아래 "현황" 절), 더 이상 서로 무관한 두 숫자로 남지 않는다.

## 현황(4번 페이지) 조회 로직

별도 "현황" 테이블은 없음. `items`를 기준으로 두 가지를 LEFT JOIN한다:
- 각 품목의 **가장 최근 `stocktake_records`**(같은 `item_id` 중 `survey_date`, `id` 내림차순 1건) → "최근 조사수량(수동) / 최근 조사일자". 바코드 추적 품목이면 이 값은 "바코드 없는 보유 수량"을 뜻한다 (위 "재고 등록 폼" 절).
- 각 품목의 **활성 `sensor_barcodes` 개수** → "바코드 추적" 열(`barcode_count`). 버튼 노출 여부는 `item.barcode_prefix` 유무가 아니라 이 개수 자체로 판단한다(`static/js/status.js::renderStatusRow`) — 바코드구분이 나중에 비워져도 이미 등록된 바코드는 남아있을 수 있기 때문. 0보다 크면 버튼을 눌러 실제 바코드 값 목록을 펼쳐볼 수 있고(`GET /api/sensor-barcodes?item_id=...`를 그때서야 호출), 목록의 각 바코드 옆 "제거" 버튼으로 바로 삭제할 수도 있다.

**이 둘을 합친 `current_stock`("현재고" 열)이 그 품목의 진짜 보유 수량을 나타내는 단일 숫자다**(`crud/stocktake.py::get_status`): `current_stock = (barcode_count) + (last_quantity ?? 0)`, 단 둘 다 아예 없으면(조사기록도 없고 바코드도 없음) `NULL`로 "-" 표시. 일반 품목(바코드 추적이 전혀 없는 품목)은 `barcode_count`가 항상 0이라 `current_stock`이 `last_quantity`와 그대로 같다 — 기존 동작과 동일. "최근 조사수량(수동)"과 "바코드 추적"을 별개로 두는 이유는 각각 서로 다른 입력 경로(수동 재고 등록 / 바코드 스캔)에서 들어온 값이라는 걸 투명하게 보여주기 위함이고, "현황에서 두 숫자가 따로 놀아서 뭐가 맞는지 모르겠다"는 피드백으로 `current_stock`을 추가해 하나의 대표 숫자를 만들었다.

아직 조사기록이 없는 품목도 목록에는 나오되 수량은 비어있게(NULL) 표시한다. 품목명/구분/위치로 검색 필터를 지원한다.
