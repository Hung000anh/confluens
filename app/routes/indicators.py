from typing import List

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Environment, FileSystemLoader

from app.config.settings import APP_TEXT, DEFAULT_PAGE_TITLE, NAV_ITEMS, TEMPLATES_DIR
from app.models.base import IndicatorCreate, IndicatorUpdate
from app.services.indicators import IndicatorService

router = APIRouter(prefix="/indicators", tags=["indicators"])
env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))


@router.get("", response_class=HTMLResponse)
async def indicators_page(request: Request):
    indicators = IndicatorService.get_all()
    template = env.get_template("indicators.html")
    return HTMLResponse(
        template.render(
            request=request,
            current_path="/indicators",
            indicators=indicators,
            nav_items=NAV_ITEMS,
            page_title=APP_TEXT["indicators"]["page_title"],
            ui=APP_TEXT,
        )
    )


@router.post("/add_indicator", response_class=HTMLResponse)
async def add_indicator_endpoint(
    request: Request,
    name: str = Form(...),
    type: str = Form(...),
    timeframe: List[str] = Form(...),
    period: int = Form(...),
    color: str = Form("#10b981"),
):
    indicator = IndicatorCreate(name=name, type=type, timeframe=timeframe, period=period, color=color)
    IndicatorService.create(indicator)
    return RedirectResponse(url="/indicators", status_code=303)


@router.post("/update_indicator/{indicator_id}", response_class=HTMLResponse)
async def update_indicator_endpoint(
    indicator_id: int,
    request: Request,
    name: str = Form(...),
    type: str = Form(...),
    timeframe: List[str] = Form(...),
    period: int = Form(...),
    color: str = Form("#10b981"),
):
    indicator = IndicatorUpdate(name=name, type=type, timeframe=timeframe, period=period, color=color)
    IndicatorService.update(indicator_id, indicator)
    return RedirectResponse(url="/indicators", status_code=303)


@router.post("/delete_indicator/{indicator_id}")
async def delete_indicator_endpoint(indicator_id: int):
    IndicatorService.delete(indicator_id)
    return RedirectResponse(url="/indicators", status_code=303)


@router.post("/toggle_indicator/{indicator_id}")
async def toggle_indicator_endpoint(indicator_id: int):
    IndicatorService.toggle(indicator_id)
    return RedirectResponse(url="/indicators", status_code=303)
