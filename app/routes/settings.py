from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Environment, FileSystemLoader

from app.config.settings import APP_TEXT, DEFAULT_PAGE_TITLE, NAV_ITEMS, TEMPLATES_DIR
from app.services.settings import SettingsService

router = APIRouter(prefix="/settings", tags=["settings"])
env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))


@router.get("", response_class=HTMLResponse)
async def settings_page(request: Request, msg: str = ""):
    settings = SettingsService.get_all()
    template = env.get_template("settings.html")
    return HTMLResponse(
        template.render(
            request=request,
            current_path="/settings",
            nav_items=NAV_ITEMS,
            page_title=APP_TEXT["settings"]["page_title"],
            ui=APP_TEXT,
            candle_count=settings.get("candle_count", "100"),
            bull_color=settings.get("bull_color", "#10b981"),
            bear_color=settings.get("bear_color", "#ffffff"),
            message=msg,
        )
    )


@router.post("", response_class=HTMLResponse)
async def save_settings_endpoint(
    request: Request,
    candle_count: str = Form("100"),
    bull_color: str = Form("#10b981"),
    bear_color: str = Form("#ffffff"),
):
    SettingsService.update_chart_settings(candle_count, bull_color, bear_color)
    return RedirectResponse(url="/settings?msg=C%E1%BA%A5u%20h%C3%ACnh%20%C4%91%C3%A3%20%C4%91%C6%B0%E1%BB%A3c%20l%C6%B0u%20th%C3%A0nh%20c%C3%B4ng!", status_code=303)
