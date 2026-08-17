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


@router.get("", response_class=HTMLResponse)
async def charts_page(request: Request, symbol_id: int = None, timeframe: str = "1d"):
    try:
        symbols = SymbolService.get_all()
        settings = SettingsService.get_chart_settings()
        active_indicators = [ind for ind in IndicatorService.get_all() if ind.get("is_active") == 1]

        indicators_param = request.query_params.get("indicators")
        selected_indicator_ids = []
        if indicators_param is not None:
            raw_ids = [item.strip() for item in indicators_param.split(",") if item.strip()]
            for item in raw_ids:
                try:
                    selected_indicator_ids.append(int(item))
                except ValueError:
                    continue
        elif active_indicators:
            selected_indicator_ids = [int(ind["id"]) for ind in active_indicators]

        template = env.get_template("chart.html")
        return HTMLResponse(
            template.render(
                request=request,
                symbols=symbols,
                current_path="/charts",
                nav_items=NAV_ITEMS,
                page_title=APP_TEXT["charts"]["page_title"],
                ui=APP_TEXT,
                selected_id=symbol_id,
                selected_timeframe=timeframe,
                active_timeframes=settings["timeframes"],
                active_timeframes_json=json.dumps(settings["timeframes"]),
                active_indicators=active_indicators,
                selected_indicator_ids=selected_indicator_ids,
            )
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/view/{symbol_id}")
async def view_chart(request: Request, symbol_id: int, timeframe: str = "1d"):
    try:
        indicators_param = request.query_params.get("indicators")
        selected_indicator_ids = []

        if indicators_param:
            raw_ids = [item.strip() for item in indicators_param.split(",") if item.strip()]
            for item in raw_ids:
                try:
                    selected_indicator_ids.append(int(item))
                except ValueError:
                    continue

        chart_bytes = ChartService.render_chart(symbol_id, timeframe, selected_indicator_ids)
        return StreamingResponse(io.BytesIO(chart_bytes), media_type="image/png")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{symbol_id}")
async def view_chart_legacy(request: Request, symbol_id: int, timeframe: str = "1d"):
    return await view_chart(request, symbol_id, timeframe)
