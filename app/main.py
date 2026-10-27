from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import common_codes, items, pages, sensor_barcodes, stocktakes
from app.core.database import Base, SessionLocal, engine
from app.crud.common_code import seed_groups
import app.models  # noqa: F401  (registers models on Base.metadata)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_groups(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="재고조사 시스템 API",
    description=(
        "엑셀로 관리하던 재고조사 업무를 대체하는 사내 전용 API. "
        "로그인/인증이 없는 단일 사용자용 시스템이며, 모든 생성/수정 기록의 "
        "작성자(`created_by`/`updated_by`)는 항상 고정 문자열 `admin`으로 남는다.\n\n"
        "삭제는 전부 논리 삭제다 — `DELETE` 요청은 실제로 행을 지우지 않고 "
        "`is_active`를 `false`로만 바꾸며, 목록 조회는 기본적으로 활성 항목만 반환한다.\n\n"
        "공통코드(단위/위치/구분/규격약식), 품목, 재고조사기록, 센서 바코드 "
        "4가지 데이터를 다룬다 — 각 태그 설명과 `guide/SCHEMA_DESIGN.md` 참고."
    ),
    version="1.0.0",
    openapi_tags=[
        {
            "name": "common-codes",
            "description": (
                "단위/위치/구분/규격약식 4개 그룹의 코드값 관리. "
                "그룹 자체(`UNIT`/`LOCATION`/`CATEGORY`/`SIZE_ABBR`)는 고정이며 "
                "이 API로 추가/삭제할 수 없다 — 그룹 '안'의 코드값만 CRUD 대상."
            ),
        },
        {
            "name": "items",
            "description": (
                "품목(제품) 마스터 데이터. 품목명/구분/단위는 필수, 위치·규격·"
                "품번·바코드 관련 필드는 선택. `barcode`는 자유 검색용 식별자, "
                "`barcode_prefix`는 센서 재고 등록 스캔 매칭에 쓰이는 접두어로 "
                "서로 다른 필드이니 혼동하지 말 것."
            ),
        },
        {
            "name": "stocktakes",
            "description": (
                "품목별 재고조사 기록(특정 시점의 수량 스냅샷)과, 품목 전체의 "
                "현재 상태를 한눈에 보는 현황(`/status`) 조회. 바코드로 추적되는 "
                "품목은 여기 기록되는 수량이 '전체 수량'이 아니라 '바코드 없는 "
                "보유 수량'만 의미하며, 전체 현재고는 `/status`의 `current_stock`"
                "(바코드 집계 + 이 수량의 합)으로 확인한다."
            ),
        },
        {
            "name": "sensor-barcodes",
            "description": (
                "개체마다 고유한 전체 바코드를 가진 품목(센서 등) 전용. 바코드 "
                "하나하나가 물리적 개체 1개에 대응하는 개별 레코드로 저장되며, "
                "수량을 직접 더하고 빼는 방식이 아니다. `/scan`은 입고(등록), "
                "`/remove`는 출고(해당 개체 제거)."
            ),
        },
    ],
    lifespan=lifespan,
    docs_url=None,       # Swagger UI (/docs) 끔
    redoc_url=None,      # ReDoc (/redoc) 끔
    openapi_url=None,    # /openapi.json까지 끔 (이걸 끄면 위 둘도 못 씀)
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(pages.router, include_in_schema=False)
app.include_router(common_codes.router)
app.include_router(items.router)
app.include_router(stocktakes.router)
app.include_router(sensor_barcodes.router)
