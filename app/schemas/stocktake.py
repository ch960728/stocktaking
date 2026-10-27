from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.item import ItemOut


class StocktakeCreate(BaseModel):
    item_id: int = Field(description="조사 대상 품목 id")
    quantity: float = Field(
        description=(
            "조사 수량. 증감 델타가 아니라 '그 시점의 전체 수량' 스냅샷. "
            "단, 품목이 바코드로 추적되는 경우(barcode_prefix 설정됨 또는 "
            "바코드가 1개 이상 등록됨)에는 이 값이 '바코드 없는 보유 수량'만 "
            "의미하며, 전체 현재고는 GET /api/stocktakes/status의 "
            "current_stock(= 이 값 + 바코드 집계 개수)으로 확인해야 한다."
        )
    )
    survey_date: date | None = Field(default=None, description="조사일자. 생략하면 오늘 날짜로 기록된다.")
    note: str | None = Field(default=None, description="비고 (선택)")


class StocktakeUpdate(BaseModel):
    quantity: float | None = Field(default=None, description="보낸 필드만 수정된다(부분 수정)")
    survey_date: date | None = None
    note: str | None = None
    is_active: bool | None = Field(default=None, description="false로 바꾸면 논리 삭제와 동일")


class StocktakeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item: ItemOut
    quantity: float
    survey_date: date
    note: str | None
    is_active: bool


class StatusRow(BaseModel):
    """현황 페이지 한 줄 — 품목마다, 저장된 전용 테이블이 아니라 조회 시점에
    stocktake_records/sensor_barcodes를 집계해서 만든다."""

    model_config = ConfigDict(from_attributes=True)

    item: ItemOut
    last_quantity: float | None = Field(
        description="가장 최근 재고조사 수량(수동 기록). 바코드 추적 품목이면 '바코드 없는 보유 수량'만 의미함."
    )
    last_survey_date: date | None = Field(description="가장 최근 조사일자. 조사 기록이 한 번도 없으면 null.")
    barcode_count: int = Field(description="이 품목에 등록된 활성 센서 바코드 개수")
    current_stock: float | None = Field(
        description=(
            "실제 보유 수량을 나타내는 대표값 = barcode_count + (last_quantity 또는 0). "
            "조사 기록도 바코드도 전혀 없으면 null."
        )
    )


class LatestQuantityOut(BaseModel):
    quantity: float | None = Field(description="해당 품목의 가장 최근 조사 수량. 재고 등록 폼의 수량 입력란 자동 채움에 쓰인다.")
