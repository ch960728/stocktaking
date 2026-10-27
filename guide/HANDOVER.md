# 인수인계 자료

이 프로젝트를 처음 맡게 된 사람을 위한 개요 문서. 세부 내용은 중복 없이 다른 문서로 링크만 하고, 여기서는 "전체 그림"만 잡는다.

## 한 줄 요약

기존에 엑셀로 관리하던 재고조사(재고 입출고/현황 파악) 업무를 대체하는 사내 전용 웹 앱. 로그인 없는 단일 사용자용 도구이며, 사용자 1인(현업 담당자)이 PC/휴대폰 브라우저로 접속해 쓴다.

## 기술 스택

| 영역 | 선택 | 비고 |
|---|---|---|
| 백엔드 | Python 3 + FastAPI | REST API 서버 |
| ORM | SQLAlchemy 2.0 | `app/models/` |
| 검증 | Pydantic v2 + pydantic-settings | `app/schemas/`, `.env` 설정 |
| DB | MariaDB | 로컬은 Docker Compose로 기동 |
| DB 드라이버 | PyMySQL | |
| 템플릿 | Jinja2 (서버 렌더링) | `app/templates/` |
| 프론트엔드 | 프레임워크 없는 Vanilla JS + CSS | `app/static/js`, `app/static/css` — React/Vue 등 전혀 없음 |
| 외부 라이브러리(CDN) | `html5-qrcode@2.3.8`, Pretendard/Inter 웹폰트 | 둘 다 빌드 없이 `<script>`/`<link>` 태그로 직접 로드 |
| TLS | `cryptography` 패키지로 자체 서명 인증서 직접 생성 | `scripts/generate_dev_cert.py` |
| 빌드/번들러 | 없음 | 프론트는 정적 파일을 그대로 서빙 |
| 테스트/린트 | 없음 | 저장소에 구성되어 있지 않음 (`pytest`/`ruff` 등 가정 금지) |
| 마이그레이션 | 없음 (Alembic 미사용) | `Base.metadata.create_all`이 없는 테이블만 생성 — 기존 테이블에 컬럼 추가 시 수동 `ALTER TABLE` 필요 |

의존성 전체 목록: [requirements.txt](../requirements.txt).

## 프로젝트 구조

```
app/
├── api/            # 도메인별 APIRouter — common_codes.py, items.py, stocktakes.py, sensor_barcodes.py, pages.py(5개 HTML 페이지 렌더링)
├── core/           # config.py(.env 설정), database.py(engine/session), templates.py(Jinja2Templates, 캐시버스팅)
├── models/         # SQLAlchemy 모델 — mixins.py(감사 5필드), common_code.py, item.py, stocktake.py, sensor_barcode.py
├── schemas/        # Pydantic 요청/응답 모델, 도메인별 1파일
├── crud/           # DB 쿼리 함수 — 도메인별 1모듈, 필터는 옵션 kwargs로 (중복 함수 금지)
├── static/{css,js}/
├── templates/
│   ├── components/  # nav.html, toast.html
│   ├── pages/        # common_codes.html, items.html, stocktakes.html, scan.html, status.html
│   └── layout.html
└── main.py

guide/              # 문서 (아래 "문서 안내" 참고)
scripts/            # generate_dev_cert.py (1회성 유틸)
example/            # 원본 엑셀 데이터 (이미 1회 이전 완료, 참고용으로만 보관)
certs/              # 로컬 HTTPS 인증서 (gitignore, 커밋 안 됨)
run_server.bat       # 로컬 서버 실행 단축 스크립트
```

데이터 흐름: `Browser → Jinja2 Templates → Vanilla JS(fetch) → FastAPI Router → MariaDB` (5개 페이지 모두 동일 패턴).

## 관리 대상 데이터 (4종) / 페이지 (5개)

1. **공통코드 등록** — 단위/위치/구분/규격약식 4개 그룹의 코드값 CRUD
2. **품목등록** — 품목 마스터 (이름/품번/바코드/구분/단위/위치/규격)
3. **재고등록** — 품목별 조사 수량 스냅샷 기록
4. **센서 재고 등록** (`/scan`) — 개체마다 고유 바코드를 갖는 품목 전용, 스캔 기반
5. **현황** — 전체 품목의 최근 수량 + 바코드 집계를 한눈에

데이터 모델/API 동작의 세부 로직(테이블 스키마, 센서 바코드 매칭 규칙, `current_stock` 합산 로직 등)은 전부 **[SCHEMA_DESIGN.md](SCHEMA_DESIGN.md)** 에 정리되어 있다 — 코드를 보기 전에 먼저 읽을 것.

## 로컬 실행

가장 빠른 길: 저장소 루트의 `run_server.bat` 더블클릭 (Docker Desktop이 켜져 있고 MariaDB 컨테이너가 떠 있어야 함).

전체 절차(최초 셋업 포함)와 왜 HTTPS로 서빙하는지, IP가 바뀌면 뭘 해야 하는지는 **[PLAN.md](PLAN.md)의 "실행 방법"** 절 참고.

## 코드를 고치기 전에 반드시 읽어야 할 것

- **[DEVELOPMENT_GUIDELINES.md](DEVELOPMENT_GUIDELINES.md)** — 코딩 규칙(하드코딩 금지, 중복 함수 금지, 감사 믹스인 등), CSS 팔레트, Git 브랜치/커밋 컨벤션. `.claude/skills/guidelines/SKILL.md`로도 동일 내용이 자동 로드됨.
- **[CLAUDE.md](../CLAUDE.md)의 "Key design points"** — 이 코드베이스에서 실제로 부딪혔던 함정/설계 이유들을 전부 모아둔 목록. 특히 아래 세 가지는 코드만 읽어서는 알기 어려우므로 꼭 미리 숙지:
  - `barcode`와 `barcode_prefix`는 서로 다른 필드다 (후자는 전체 바코드가 아니라 접두어).
  - `current_stock`(현재고)은 `barcode_count + last_quantity`로 계산되는 합성값이다 — 둘 중 하나만 보고 "진짜 재고"로 착각하면 안 됨.
  - `create_all`은 기존 테이블을 변경하지 않는다 — 컬럼 추가 시 수동 `ALTER TABLE` 필요.

## 알려진 제약 / 남은 작업

**[PLAN.md](PLAN.md)의 "남은 작업 / 향후 개선 후보"** 절이 최신 상태로 유지된다 — 현재는: 공통코드에 일부 위치 코드("4-1"/"4-2"/"4-4"/"4-5") 미등록, 품목 2건 수량 미입력, 인증 없음(단일 사용자 전제), 페이지네이션 UI 없음 등.

과거에 무엇을 왜 그렇게 결정했는지 전체 맥락이 필요하면 **[PLAN.md](PLAN.md)의 "히스토리"** 절(날짜별로 모든 변경/버그/재설계 기록)을 처음부터 읽으면 된다.

## 문서 안내

| 문서 | 용도 |
|---|---|
| [CLAUDE.md](../CLAUDE.md) | 프로젝트 전체 요약 + 명령어 + 설계 핵심 포인트 모음 (AI 코딩 도구용으로 작성됐지만 사람이 읽어도 동일하게 유용) |
| [PLAN.md](PLAN.md) | 요구사항, 실행 방법, 남은 작업, 날짜별 히스토리 |
| [SCHEMA_DESIGN.md](SCHEMA_DESIGN.md) | DB 테이블/컬럼/인덱스, 비즈니스 로직(현황 집계 등) 상세 |
| [DEVELOPMENT_GUIDELINES.md](DEVELOPMENT_GUIDELINES.md) | 코딩 스타일, Git 컨벤션 |
| 이 문서(HANDOVER.md) | 신규 투입자용 전체 그림 — 위 문서들로 가는 지도 역할 |
