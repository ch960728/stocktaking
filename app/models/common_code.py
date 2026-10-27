import enum

from sqlalchemy import ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import AuditMixin


class CommonCodeGroupEnum(str, enum.Enum):
    """The four code groups are fixed by requirements (not evolving business
    data), so the group identifiers live in code. The values inside each
    group are fully managed via the common_codes table/UI."""

    UNIT = "UNIT"
    LOCATION = "LOCATION"
    CATEGORY = "CATEGORY"
    SIZE_ABBR = "SIZE_ABBR"


class CommonCodeGroup(Base, AuditMixin):
    __tablename__ = "common_code_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    group_name: Mapped[str] = mapped_column(String(50), nullable=False)

    codes: Mapped[list["CommonCode"]] = relationship(back_populates="group")


class CommonCode(Base, AuditMixin):
    __tablename__ = "common_codes"
    __table_args__ = (
        UniqueConstraint("group_id", "code", name="uq_common_codes_group_code"),
        Index("ix_common_codes_group_active_sort", "group_id", "is_active", "sort_order"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("common_code_groups.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    group: Mapped["CommonCodeGroup"] = relationship(back_populates="codes")
