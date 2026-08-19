import io
import json
from typing import List

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from jinja2 import Environment, FileSystemLoader

from app.config.settings import APP_TEXT, DEFAULT_PAGE_TITLE, NAV_ITEMS, TEMPLATES_DIR
from app.services.charts import ChartService
from app.services.indicators import IndicatorService
from app.services.settings import SettingsService
from app.services.symbols import SymbolService

router = APIRouter(prefix="/charts", tags=["charts"])
env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))


from typing import Optional, List

@router.get("", response_class=HTMLResponse)
async def charts_page(
    request: Request,
    symbol_id: Optional[str] = None,
    symbol: Optional[str] = None,
    timeframe: str = "1d",
):
    try:
        symbols = SymbolService.get_all()
        settings = SettingsService.get_chart_settings()
        selected_symbol = symbol or symbol_id

        template = env.get_template("chart.html")
        return HTMLResponse(
            template.render(
                request=request,
                symbols=symbols,
                current_path="/charts",
                nav_items=NAV_ITEMS,
                page_title=APP_TEXT["charts"]["page_title"],
                ui=APP_TEXT,
                selected_id=selected_symbol,
                selected_timeframe=timeframe,
                active_timeframes=settings["timeframes"],
                active_timeframes_json=json.dumps(settings["timeframes"]),
            )
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/view/{symbol_id:path}")
async def view_chart(request: Request, symbol_id: str, timeframe: str = "1d"):
    try:
        chart_bytes = ChartService.render_chart(symbol_id, timeframe, [])
        return StreamingResponse(io.BytesIO(chart_bytes), media_type="image/png")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/view_chart/{symbol_id:path}")
async def view_chart_compat(request: Request, symbol_id: str, timeframe: str = "1d"):
    return await view_chart(request, symbol_id, timeframe)


@router.get("/{symbol_id:path}")
async def view_chart_legacy(request: Request, symbol_id: str, timeframe: str = "1d"):
    return await view_chart(request, symbol_id, timeframe)
