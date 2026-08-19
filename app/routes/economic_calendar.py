from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from jinja2 import Environment, FileSystemLoader

from app.config.settings import APP_TEXT, NAV_ITEMS, TEMPLATES_DIR
from app.services.economic_calendar import EconomicCalendarService, TARGET_CURRENCIES

router = APIRouter(prefix="", tags=["economic-calendar"])
env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))

@router.get("/economic-calendar", response_class=HTMLResponse)
async def economic_calendar_page(
    request: Request,
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
):
    now = datetime.now()
    req_year = year or now.year
    req_month = month or now.month

    template = env.get_template("economic_calendar.html")
    page_title = "Lịch Kinh Tế"

    return HTMLResponse(
        template.render(
            request=request,
            nav_items=NAV_ITEMS,
            current_path="/economic-calendar",
            page_title=page_title,
            ui=APP_TEXT,
            year=req_year,
            month=req_month,
            target_currencies=sorted(list(TARGET_CURRENCIES)),
        )
    )

@router.get("/api/economic-calendar", response_class=JSONResponse)
async def get_economic_calendar_api(
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
):
    now = datetime.now()
    req_year = year or now.year
    req_month = month or now.month

    events = EconomicCalendarService.scrape_month(req_year, req_month)

    return {
        "status": "success",
        "year": req_year,
        "month": req_month,
        "count": len(events),
        "events": events,
    }
