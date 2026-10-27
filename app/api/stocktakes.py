from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud import stocktake as crud
from app.core.database import get_db
from app.schemas.stocktake import (
    LatestQuantityOut,
    StatusRow,
    StocktakeCreate,
    StocktakeOut,
    StocktakeUpdate,
)

router = APIRouter(prefix="/api/stocktakes", tags=["stocktakes"])


@router.get(
    "",
    response_model=list[StocktakeOut],
    summary="재고조사 기록 목록 조회",
    description="날짜 범위(`date_from`/`date_to`)와 품목 검색/구분/위치로 필터링한 재고조사 기록(수량 스냅샷) 목록. 최신순 정렬.",
)
def list_stocktakes(
    search: str | None = None,
    category_id: int | None = None,
    location_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    is_active: bool | None = True,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    return crud.get_stocktakes(
        db,
        search=search,
        category_id=category_id,
        location_id=location_id,
        date_from=date_from,
        date_to=date_to,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/status",
    response_model=list[StatusRow],
    summary="현황 조회 (품목별 현재고 요약)",
    description=(
        "전용 테이블 없이, 전체 활성 품목 각각에 가장 최근 재고조사 기록과 "
        "활성 센서 바코드 개수를 집계해서 보여준다. 품목별 '진짜 보유 수량'은 "
        "각 행의 current_stock 필드를 봐야 한다 — last_quantity만 보면 바코드 "
        "추적 품목에서는 실제 수량보다 적게 보일 수 있다."
    ),
)
def status_view(
    search: str | None = None,
    category_id: int | None = None,
    location_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    rows = crud.get_status(
        db, search=search, category_id=category_id, location_id=location_id,
        limit=limit, offset=offset,
    )
    return [
        StatusRow(
            item=item,
            last_quantity=quantity,
            last_survey_date=survey_date,
            barcode_count=count,
            current_stock=current_stock,
        )
        for item, quantity, survey_date, count, current_stock in rows
    ]


@router.get(
    "/latest/{item_id}",
    response_model=LatestQuantityOut,
    summary="품목의 가장 최근 조사 수량 조회",
)
def latest_quantity(item_id: int, db: Session = Depends(get_db)):
    """Backs the 재고 등록 form's quantity prefill: once an item is picked,
    show its current known stock rather than starting from blank/zero."""
    return LatestQuantityOut(quantity=crud.get_latest_quantity(db, item_id))


@router.post(
    "",
    response_model=StocktakeOut,
    status_code=201,
    summary="재고조사 기록 등록",
    description="새로운 수량 스냅샷을 기록한다. survey_date를 생략하면 오늘 날짜로 저장된다.",
)
def create_stocktake(payload: StocktakeCreate, db: Session = Depends(get_db)):
    data = payload.model_dump()
    if data["survey_date"] is None:
        data["survey_date"] = date.today()
    return crud.create_stocktake(db, **data)


@router.put(
    "/{record_id}",
    response_model=StocktakeOut,
    summary="재고조사 기록 수정",
    description="요청 본문에 보낸 필드만 수정된다(부분 수정).",
    responses={404: {"description": "해당 id의 재고조사기록이 없음"}},
)
def update_stocktake(record_id: int, payload: StocktakeUpdate, db: Session = Depends(get_db)):
    row = crud.get_stocktake(db, record_id)
    if row is None:
        raise HTTPException(404, "재고조사기록을 찾을 수 없습니다")
    return crud.update_stocktake(db, row, **payload.model_dump(exclude_unset=True))


@router.delete(
    "/{record_id}",
    status_code=204,
    summary="재고조사 기록 삭제 (논리 삭제)",
    responses={404: {"description": "해당 id의 재고조사기록이 없음"}},
)
def delete_stocktake(record_id: int, db: Session = Depends(get_db)):
    row = crud.get_stocktake(db, record_id)
    if row is None:
        raise HTTPException(404, "재고조사기록을 찾을 수 없습니다")
    crud.deactivate_stocktake(db, row)
