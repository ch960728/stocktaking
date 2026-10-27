from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.core.templates import templates

router = APIRouter(tags=["pages"])


@router.get("/")
def index():
    return RedirectResponse(url="/items")


@router.get("/common-codes")
def common_codes_page(request: Request):
    return templates.TemplateResponse(
        request, "pages/common_codes.html", {"active_nav": "common-codes"}
    )


@router.get("/items")
def items_page(request: Request):
    return templates.TemplateResponse(request, "pages/items.html", {"active_nav": "items"})


@router.get("/stocktakes")
def stocktakes_page(request: Request):
    return templates.TemplateResponse(
        request, "pages/stocktakes.html", {"active_nav": "stocktakes"}
    )


@router.get("/status")
def status_page(request: Request):
    return templates.TemplateResponse(request, "pages/status.html", {"active_nav": "status"})


@router.get("/scan")
def scan_page(request: Request):
    return templates.TemplateResponse(request, "pages/scan.html", {"active_nav": "scan"})
