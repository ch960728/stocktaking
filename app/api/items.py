from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud import item as crud
from app.core.database import get_db
from app.schemas.item import ItemCreate, ItemOut, ItemUpdate

router = APIRouter(prefix="/api/items", tags=["items"])


@router.get(
    "",
    response_model=list[ItemOut],
    summary="품목 목록 조회",
    description=(
        "활성 품목을 검색/필터링해 조회한다. `search`는 품목명/품번/바코드/바코드구분을 "
        "모두 OR로 묶어 검색한다. 품목 등록 페이지의 유사 품목 자동완성, 재고 등록 "
        "페이지의 품목 선택 콤보박스도 이 엔드포인트를 그대로 사용한다."
    ),
)
def list_items(
    search: str | None = None,
    category_id: int | None = None,
    location_id: int | None = None,
    is_active: bool | None = True,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Also backs the item-registration autocomplete and the stocktake
    item-picker: both call this with `search` and a small `limit`."""
    return crud.get_items(
        db,
        search=search,
        category_id=category_id,
        location_id=location_id,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/count",
    summary="품목 개수 조회",
    description="`list_items`와 동일한 필터 조건으로 건수만 센다. 품목 목록 화면의 '전체 N개 · 조회결과 M개' 배지에 쓰인다.",
)
def count_items(
    search: str | None = None,
    category_id: int | None = None,
    location_id: int | None = None,
    is_active: bool | None = True,
    db: Session = Depends(get_db),
):
    """`/count` must stay registered before `/{item_id}` or FastAPI will try
    to parse "count" as an item_id."""
    return {"count": crud.count_items(db, search=search, category_id=category_id, location_id=location_id, is_active=is_active)}


@router.get(
    "/{item_id}",
    response_model=ItemOut,
    summary="품목 단건 조회",
    responses={404: {"description": "해당 id의 품목이 없음"}},
)
def get_item(item_id: int, db: Session = Depends(get_db)):
    row = crud.get_item(db, item_id)
    if row is None:
        raise HTTPException(404, "품목을 찾을 수 없습니다")
    return row


@router.post(
    "",
    response_model=ItemOut,
    status_code=201,
    summary="품목 등록",
    responses={409: {"description": "바코드구분(barcode_prefix)이 이미 다른 품목에 등록되어 있음"}},
)
def create_item(payload: ItemCreate, db: Session = Depends(get_db)):
    if payload.barcode_prefix and crud.barcode_prefix_exists(db, payload.barcode_prefix):
        raise HTTPException(409, f"이미 등록된 바코드구분입니다: {payload.barcode_prefix}")
    return crud.create_item(db, **payload.model_dump())


@router.put(
    "/{item_id}",
    response_model=ItemOut,
    summary="품목 수정",
    description="요청 본문에 보낸 필드만 수정된다(부분 수정, PATCH와 유사하게 동작).",
    responses={
        404: {"description": "해당 id의 품목이 없음"},
        409: {"description": "바코드구분(barcode_prefix)이 이미 다른 품목에 등록되어 있음"},
    },
)
def update_item(item_id: int, payload: ItemUpdate, db: Session = Depends(get_db)):
    row = crud.get_item(db, item_id)
    if row is None:
        raise HTTPException(404, "품목을 찾을 수 없습니다")
    if payload.barcode_prefix and crud.barcode_prefix_exists(db, payload.barcode_prefix, exclude_id=item_id):
        raise HTTPException(409, f"이미 등록된 바코드구분입니다: {payload.barcode_prefix}")
    return crud.update_item(db, row, **payload.model_dump(exclude_unset=True))


@router.delete(
    "/{item_id}",
    status_code=204,
    summary="품목 삭제 (논리 삭제)",
    description="실제로 행을 지우지 않고 is_active를 false로 바꾼다. 이후 목록 조회에서 기본적으로 제외된다.",
    responses={404: {"description": "해당 id의 품목이 없음"}},
)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    row = crud.get_item(db, item_id)
    if row is None:
        raise HTTPException(404, "품목을 찾을 수 없습니다")
    crud.deactivate_item(db, row)
