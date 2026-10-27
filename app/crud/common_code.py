from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.common_code import CommonCode, CommonCodeGroup, CommonCodeGroupEnum

GROUP_SEED = {
    CommonCodeGroupEnum.UNIT: "단위",
    CommonCodeGroupEnum.LOCATION: "위치",
    CommonCodeGroupEnum.CATEGORY: "구분",
    CommonCodeGroupEnum.SIZE_ABBR: "규격약식",
}


def seed_groups(db: Session) -> None:
    """Ensure the four fixed code groups exist. Idempotent, safe to call on
    every app startup."""
    existing = {g.group_code for g in db.scalars(select(CommonCodeGroup))}
    for group_code, group_name in GROUP_SEED.items():
        if group_code.value not in existing:
            db.add(CommonCodeGroup(group_code=group_code.value, group_name=group_name))
    db.commit()


def get_groups(db: Session) -> list[CommonCodeGroup]:
    return list(db.scalars(select(CommonCodeGroup).order_by(CommonCodeGroup.id)))


def get_group_by_code(db: Session, group_code: str) -> CommonCodeGroup | None:
    return db.scalar(select(CommonCodeGroup).where(CommonCodeGroup.group_code == group_code))


def get_codes(
    db: Session,
    group_code: str | None = None,
    keyword: str | None = None,
    is_active: bool | None = True,
) -> list[CommonCode]:
    query = select(CommonCode).options(joinedload(CommonCode.group))
    if group_code is not None:
        query = query.join(CommonCodeGroup).where(CommonCodeGroup.group_code == group_code)
    if keyword:
        query = query.where(CommonCode.name.ilike(f"%{keyword}%"))
    if is_active is not None:
        query = query.where(CommonCode.is_active == is_active)
    query = query.order_by(CommonCode.group_id, CommonCode.sort_order, CommonCode.id)
    return list(db.scalars(query).unique())


def get_code(db: Session, code_id: int) -> CommonCode | None:
    return db.scalar(
        select(CommonCode).options(joinedload(CommonCode.group)).where(CommonCode.id == code_id)
    )


def create_code(db: Session, group_id: int, code: str, name: str, sort_order: int) -> CommonCode:
    row = CommonCode(group_id=group_id, code=code, name=name, sort_order=sort_order)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_code(db: Session, row: CommonCode, **fields) -> CommonCode:
    """`fields` should already be filtered to only the keys the client
    explicitly sent (e.g. via Pydantic's `exclude_unset`), so an explicit
    None is a real value to write, not a "no change" placeholder."""
    for key, value in fields.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


def deactivate_code(db: Session, row: CommonCode) -> CommonCode:
    row.is_active = False
    db.commit()
    db.refresh(row)
    return row


def code_exists_in_group(
    db: Session, group_id: int, code: str, exclude_id: int | None = None
) -> bool:
    query = select(CommonCode).where(CommonCode.group_id == group_id, CommonCode.code == code)
    if exclude_id is not None:
        query = query.where(CommonCode.id != exclude_id)
    return db.scalar(query) is not None
