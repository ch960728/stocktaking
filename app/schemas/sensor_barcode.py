from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.item import ItemOut


class SensorBarcodeScanRequest(BaseModel):
    barcode: str = Field(description="스캔(또는 수동 입력)한 바코드 전체 값")


class SensorBarcodeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item: ItemOut = Field(description="이 바코드가 속한 품목 — barcode_prefix 매칭으로 결정됨")
    barcode: str = Field(description="개체별로 고유한 바코드 전체 값")
    created_at: datetime
    is_active: bool = Field(description="false면 출고(제거)된 상태. 물리 삭제가 아니라 같은 barcode로 재입고 시 재사용됨.")
