# 개발 계획 / 히스토리

기존에 엑셀로 관리하던 재고조사 업무를 간단한 웹 시스템으로 대체한다. 관리 대상 데이터는 품목, 조사기록, 공통코드 세 가지.

## 페이지 요구사항

1. **공통코드 등록 페이지** — 단위/위치/구분/규격약식 4개 그룹의 코드 CRUD
2. **품목등록 페이지** — 품목명*/품번/바코드/구분*/단위*/위치/규격약식/규격상세(폭·길이·높이) 등록. 검색 기능. 품목명 입력 시 기존 유사 품목 자동완성. `item_name`/`item_no`/`barcode`에 DB 인덱스(내부 성능 최적화, UI 요소 아님).
3. **재고 등록 페이지** — 품목별 조사 수량/조사일자/비고 기록. 구분/위치는 "검색 필터"가 아니라 **품목 등록 데이터 기준**: 품목 선택 전엔 콤보박스를 좁히는 필터 역할, 품목을 선택하면 그 품목의 실제 구분/위치 값으로 자동 동기화된다. 품목 콤보박스는 포커스만 해도 목록이 열리고(타이핑 없이도 탐색 가능), 선택 시 수량 입력란에 현재고를 자동으로 채워준다(1단위 step, 직접 입력도 가능). 상세: [[SCHEMA_DESIGN.md]]의 "재고 등록 폼" 절.
4. **현황 페이지** — 품목별 최근 조사 수량/일자 + (센서류는) 등록된 바코드 개수/목록 조회. 검색 기능.
5. **센서 재고 등록 페이지(`/scan`)** — 센서 등 개체마다 고유 바코드를 가진 품목 전용. 바코드를 스캔하면 접두어(`barcode_prefix`, si/so/sj 등)로 어느 품목인지 찾아 그 바코드 자체를 개별 레코드로 저장(수량 +1이 아님). 물리 스캐너 입력 외에 모바일 카메라로도 스캔 가능(`html5-qrcode` 라이브러리, HTTPS 필요 — 아래 "모바일/카메라" 항목 참고). 상세: [[SCHEMA_DESIGN.md]]의 "sensor_barcodes" 절.

전체 페이지는 모바일 해상도에서도 쓸 수 있도록 반응형으로 되어 있다(좌측 사이드바 네비게이션은 좁은 화면에서 상단 가로 스크롤 탭으로 바뀌고, 폭이 넓은 테이블은 페이지 전체가 아니라 테이블만 가로 스크롤됨). 상세: `app/static/css/style.css`의 `@media (max-width: 768px)` 블록.

세부 결정 사항(사용자 확인 완료):
- "인덱싱 기능" = UI 기능이 아니라 품목명 컬럼에 대한 DB 검색 인덱스.
- MariaDB는 Docker Compose로 로컬 구성.
- 로그인/인증 없음. `created_by`/`updated_by`는 항상 `"admin"`으로 고정.

스키마 상세: [[SCHEMA_DESIGN.md]]. 코드/스타일 규칙: [[DEVELOPMENT_GUIDELINES.md]].

## 구현 순서

1. [x] `guide/` 문서화 (본 파일, DEVELOPMENT_GUIDELINES.md, SCHEMA_DESIGN.md)
2. [x] 프로젝트 스캐폴딩 — `requirements.txt`, `docker-compose.yml`(MariaDB), `.env.example`, `app/core/config.py`, `app/core/database.py`
3. [x] SQLAlchemy 모델 — 감사 믹스인, `common_code_groups`/`common_codes`/`items`/`stocktake_records`
4. [x] Pydantic 스키마
5. [x] CRUD 계층
6. [x] API 라우터 (`common_codes`, `items`, `stocktakes` + `stocktakes/status`) + `main.py`에서 앱 시작 시 공통코드 그룹 시드
7. [x] Jinja2 템플릿 (layout + 4개 페이지 + 공통 컴포넌트) + `static/css/style.css` + 페이지별 `static/js/*.js` (검색, 자동완성, toast)
8. [x] 로컬 실행 확인 — Docker Compose로 MariaDB 기동 후 API(curl/Python)와 실제 브라우저(Playwright, 스크린샷 확인)로 4개 페이지를 끝까지 조작해 검증: 공통코드 4그룹 등록 → 품목 등록(자동완성 포함) → 재고조사 등록(품목 검색/자동완성 포함) → 현황 조회. 콘솔 에러 없음 확인. 부분수정 시 값 삭제(예: 위치를 다시 "선택 안함"으로)가 씹히던 버그를 찾아 `exclude_unset` 기반으로 수정. 테스트 데이터는 정리하고 DB는 `docker compose down -v`로 초기화해둠

## 실행 방법

```
docker compose up -d               # MariaDB 기동
cp .env.example .env               # 최초 1회 (이미 되어있으면 생략) — 복사 후 DB_PASSWORD/DB_ROOT_PASSWORD를 반드시 바꿀 것 (코드/compose에 기본 비밀번호가 없어 미설정 시 기동 실패)
.venv 생성 후 pip install -r requirements.txt
python scripts/generate_dev_cert.py   # 최초 1회 + LAN IP가 바뀔 때마다 재실행
uvicorn app.main:app --reload --port 8010 --ssl-keyfile certs/dev-key.pem --ssl-certfile certs/dev-cert.pem
```
`https://<이 PC의 LAN IP>:8010` 로 접속(휴대폰 포함). 자체 서명 인증서라 브라우저가 "안전하지 않음" 경고를 띄우는데, "고급"→"이동(안전하지 않음)"으로 넘어가면 정상 접속된다 — 센서 재고 등록의 카메라 스캔은 보안 연결(HTTPS)에서만 동작하므로 이 경고를 넘어가야 카메라 버튼이 실제로 작동한다. 인증서는 생성 시점의 LAN IP를 기준으로 만들어지므로, IP가 바뀌면(이 PC는 DHCP라 자주 바뀜) `scripts/generate_dev_cert.py`를 다시 실행하고 서버를 재시작해야 한다. `certs/`는 개인키가 들어있어 `.gitignore`에 포함됨 — 커밋되지 않는다.

매번 긴 uvicorn 명령을 치기 번거로워서 `run_server.bat`(저장소 루트)를 만들어둠 — 더블클릭하거나 터미널에서 `run_server`만 치면 위 uvicorn 명령 그대로 실행된다(IP가 바뀌어 인증서를 재생성해야 하는 경우는 여전히 `generate_dev_cert.py`를 먼저 수동 실행해야 함, bat파일이 대신해주지 않음).

앱 시작 시 공통코드 4개 그룹이 자동 시드되지만, 그룹별 실제 코드값(단위/위치/구분/규격약식 항목)은 비어있으므로 공통코드 등록 페이지에서 먼저 등록해야 품목 등록이 가능하다.

**포트 8000은 이 PC에서 seeErp가 이미 쓰고 있으므로(Docker Desktop/WSL로 포워딩됨) 이 프로젝트는 기본적으로 8010을 쓴다.** 코드 어디에도 포트가 하드코딩되어 있지 않으니, 필요하면 `uvicorn app.main:app --port <다른포트>`로 자유롭게 바꿔도 된다.

## 남은 작업 / 향후 개선 후보

- 인증이 필요해지면 감사필드 하드코딩("admin")을 실제 로그인 사용자로 교체.
- 데이터가 많아지면 `items`/`stocktake_records` 페이지네이션 UI(현재는 API에 limit/offset은 있으나 프론트는 고정 limit로만 조회).
- 공통코드 > 위치에 "4-1"/"4-2"/"4-4"/"4-5"가 아직 없음(2026-10-13 엑셀 재점검 항목 참고) — 등록되면 서지보호기/안테나 연장케이블/열튜브(소)/조립식 단자대 세트/조립식 단자대 세트 B/호스클램프(대) 6개 품목의 위치를 채울 수 있음.
- `단자대 4P`, `전기함박스` 품목은 수량이 아직 한 번도 등록되지 않음(엑셀에 동일한 이름이 없어 자동 매칭 대상에서 빠짐) — 재고 등록 페이지에서 직접 입력 필요.

## 히스토리

변경 이력은 [HISTORY.md](HISTORY.md)에 있다. 새 변경 기록은 이 파일이 아니라 HISTORY.md 맨 끝에 추가한다.
