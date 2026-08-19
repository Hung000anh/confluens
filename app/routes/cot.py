from typing import Optional
from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from jinja2 import Environment, FileSystemLoader

from app.config.settings import APP_TEXT, NAV_ITEMS, TEMPLATES_DIR
from app.services.cot import CotService, COT_REPORT_TYPES

router = APIRouter(prefix="", tags=["cot"])
env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))

@router.get("/cftc", response_class=HTMLResponse)
async def cot_page(request: Request):
    page_title = APP_TEXT.get("cot", {}).get("page_title", "Báo Cáo COT")
    template = env.get_template("cot.html")
    
    return HTMLResponse(
        template.render(
            request=request,
            nav_items=NAV_ITEMS,
            current_path="/cftc",
            page_title=page_title,
            ui=APP_TEXT,
            report_types=COT_REPORT_TYPES
        )
    )

@router.get("/api/cot", response_class=JSONResponse)
async def get_cot_data(
    report_type: str = Query("legacy_fut", description="Loại báo cáo COT"),
    limit: int = Query(500, description="Số lượng record cần lấy")
):
    try:
        data = CotService.get_cot_data(report_type, limit=limit)
        return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "error": str(e)}
