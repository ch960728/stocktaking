from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common_code import CommonCodeBrief


class ItemCreate(BaseModel):
    item_name: str = Field(description="품목명 (필수)")
    item_no: str | None = Field(default=None, description="품번 (선택)")
    barcode: str | None = Field(
        default=None, description="바코드 (선택) — 자유 검색용 식별자. barcode_prefix와는 별개 필드."
    )
    barcode_prefix: str | None = Field(
        default=None,
        description=(
            "바코드구분 (선택) — 센서처럼 개체마다 고유 바코드를 갖는 품목에서, "
            "실제 스캔값의 '앞부분'만 저장하는 접두어(예: 'si'). 전체 바코드값이 "
            "아니며, 품목당 1개씩만 가질 수 있어 중복 등록 시 409로 거부된다."
        ),
    )
    category_id: int = Field(description="구분 공통코드 id (필수, group=CATEGORY)")
    unit_id: int = Field(description="단위 공통코드 id (필수, group=UNIT)")
    location_id: int | None = Field(default=None, description="위치 공통코드 id (선택, group=LOCATION)")
    size_abbr_id: int | None = Field(default=None, description="규격약식 공통코드 id (선택, group=SIZE_ABBR — 소/중/대)")
    size_width: float | None = Field(default=None, description="규격상세 - 폭 (선택)")
    size_length: float | None = Field(default=None, description="규격상세 - 길이 (선택)")
    size_height: float | None = Field(default=None, description="규격상세 - 높이 (선택)")


class ItemUpdate(BaseModel):
    item_name: str | None = Field(default=None, description="품목명. 보낸 필드만 수정된다(부분 수정).")
    item_no: str | None = None
    barcode: str | None = None
    barcode_prefix: str | None = Field(
        default=None, description="바코드구분. 다른 품목이 이미 쓰고 있으면 409."
    )
    category_id: int | None = None
    unit_id: int | None = None
    location_id: int | None = None
    size_abbr_id: int | None = None
    size_width: float | None = None
    size_length: float | None = None
    size_height: float | None = None
    is_active: bool | None = Field(default=None, description="비활성화(false)는 논리 삭제와 동일 — 보통 DELETE 엔드포인트를 통해 바뀐다.")


class ItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_name: str
    item_no: str | None
    barcode: str | None
    barcode_prefix: str | None = Field(description="바코드구분 접두어. 전체 바코드값이 아님에 유의.")
    category: CommonCodeBrief
    unit: CommonCodeBrief
    location: CommonCodeBrief | None
    size_abbr: CommonCodeBrief | None = Field(description="규격약식 (소/중/대)")
    size_width: float | None
    size_length: float | None
    size_height: float | None
    is_active: bool
