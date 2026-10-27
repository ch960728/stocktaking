# 개발 가이드라인

이 문서는 재고조사 시스템(stocktaking) 프로젝트의 개발 규칙을 정의한다. 서버 렌더링 + 프레임워크 없는 프론트엔드 구조를 여러 기능 추가에도 일관되게 유지하기 위한 규칙이며, 스타일에 대해 명시적으로 질문받았을 때뿐 아니라 백엔드/프론트엔드 코드를 다룰 때 항상 적용한다.

핵심 철학: **과설계 금지**(현재 요구사항을 만족하는 가장 단순한 구조), **프론트/백엔드 완전 분리**(REST API로만 통신), **중복 함수/컴포넌트/쿼리 금지**, **비즈니스 값 하드코딩 금지**. 아래 규칙과 실용성이 충돌하면 이 네 가지가 판단 기준이다.

## 아키텍처

```
Browser → Jinja2 Templates → Vanilla JS (fetch) → FastAPI Router → MariaDB
```

```
app/
├── api/        # 도메인별 APIRouter 1개 (common_codes.py, items.py, stocktakes.py, status.py)
├── core/       # 설정(config), DB 연결(database)
├── crud/       # DB 접근/쿼리 로직
├── models/     # SQLAlchemy ORM 모델
├── schemas/    # Pydantic 검증 스키마
├── static/{css,js}/
├── templates/
│   ├── components/  # 재사용 partial/macro
│   ├── pages/
│   └── layout.html
└── main.py
```

`app/`가 없다면 이 구조로 새로 만든다. 다른 구조를 임의로 고안하지 않는다.

## 백엔드 규칙

**분류/상태 값을 Python이나 템플릿에 하드코딩하지 않는다.** 단위, 위치, 구분, 규격약식 등은 반드시 공통코드 테이블(`common_code_groups` / `common_codes`, `guide/SCHEMA_DESIGN.md` 참고)을 거친다. 값이 하나 추가될 때 코드 여러 곳을 고쳐야 하는 산발적 버그를 막기 위한 장치다. (공통코드 그룹 자체(단위/위치/구분/규격약식)는 요구사항으로 고정된 구조이므로 `CommonCodeGroup` Enum으로 참조하되, 그룹 내부의 실제 값은 전부 DB로 관리한다.)

**필터 조합마다 쿼리/CRUD 함수를 새로 만들지 않는다.** `get_items_active()`를 `get_items()` 옆에 추가하고 싶어지면 멈추고, 대신 옵션 파라미터를 추가해 동적으로 필터링한다 (`get_items(search=None, category_code=None, ...)`). 같은 모듈에 WHERE절만 다른 함수가 두 개 있다면 그 신호다.

**도메인당 APIRouter 1개**, `app/api/` 아래에 둔다. `main.py`에 엔드포인트를 직접 추가하거나, 한 라우터 파일에 서로 다른 도메인을 몰아넣지 않는다.

**모든 테이블은 감사(audit) 컬럼 5개를 공유 SQLAlchemy 믹스인으로 상속**한다: `created_by`, `created_at`, `updated_by`, `updated_at`, `is_active`. 이 프로젝트는 로그인/인증 기능이 없으므로 `created_by`/`updated_by`는 고정 문자열 `"admin"`을 사용한다. 삭제는 항상 논리 삭제(`is_active` 플래그)이며, 물리적 `DELETE FROM`은 사용하지 않는다.

**검색이 잦은 컬럼에는 DB 인덱스를 건다.** 품목명 등 자동완성/검색 대상 컬럼은 조회 성능을 위해 인덱스를 명시적으로 정의한다(`guide/SCHEMA_DESIGN.md` 참고). 이는 UI 기능이 아니라 백엔드 성능 최적화다.

## 프론트엔드 규칙 (Jinja2 + Vanilla JS/CSS)

**모든 페이지는 기본 레이아웃을 상속**한다. `layout.html`이 Header / 좌측 Sidebar / Body / Footer를 정의하고, 개별 페이지는 `{% extends "layout.html" %}`로 확장한다. 반복되는 UI 조각은 `templates/components/`에 `{% include %}` 또는 `{% macro %}`로 분리한다.

**인라인 `<script>` 블록 금지.** 클라이언트 로직은 `static/js/`에 기능별 파일로 두고, `fetch`로 FastAPI와 통신한다. 프레임워크 없이 vanilla JS로 DOM과 비동기 호출을 다룬다.

**고정 색상 팔레트를 CSS 변수로 사용**한다 (`static/css/style.css`에 1회 정의):
```css
:root {
  --color-dark: #354649;      /* 주요 텍스트 / 핵심 요소 */
  --color-secondary: #6C7A89; /* 보조 텍스트 / 테두리 */
  --color-accent: #A3C6C4;    /* 강조 / 포인트 */
  --color-light: #E0E7E9;     /* 배경 / 카드 영역 */
}
```
템플릿이나 컴포넌트 CSS에 새 hex 값을 즉흥적으로 넣지 않는다. 정말 새 색이 필요하면 변수 세트를 확장한다.

**타이포그래피**: 한글/본문은 Pretendard, 숫자/표 데이터(대시보드, 테이블)는 Inter. 둘 다 OFL 라이선스이므로 라이선스가 불명확한 폰트로 대체하지 않는다.

**여백**: margin/padding은 8px 배수 그리드를 따르고, 인터랙티브 요소에는 부드러운 hover/transition을 준다. 아이콘은 단순하게 유지한다.

**사용자 액션으로 생성/수정/삭제가 일어나면 반드시 성공/실패 알림(toast/snackbar)을 보여준다.** 조용히 실패하는 저장을 막기 위한 필수 UX 요구사항이다.

**UI/문서 텍스트에는 이모지를 쓰지 않는다.**

## Git 컨벤션

- 브랜치: `main`(배포), `develop`(통합), `feature/<기능명>`(기능 개발)
- 커밋 프리픽스: `feat:`, `fix:`, `refactor:`, `style:`, `chore:` — 변경 유형에 맞춘다.

## 규칙과 요청이 충돌할 때

요청이 이 규칙을 위반한다면(예: "일단 상태값 하드코딩해줘") 기본적으로 규칙을 지키는 방식으로 구현하고 이유를 간단히 남긴다. 이후에도 사용자가 다른 방식을 원하면 그때 따른다.
