from typing import Optional, List
from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from jinja2 import Environment, FileSystemLoader

from app.config.settings import APP_TEXT, NAV_ITEMS, TEMPLATES_DIR
from app.services.countries import CountryService
from app.services.economic_indicators import (
    EconomicIndicatorsService,
    CATEGORIES_MAP,
)

router = APIRouter(prefix="", tags=["economic-indicators"])
env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))


@router.get("/economic-indicators", response_class=HTMLResponse)
async def economic_indicators_page(
    request: Request,
    countries: Optional[str] = Query("US,VN", description="Danh sách mã quốc gia cách nhau bởi dấu phẩy"),
    category: Optional[str] = Query("all", description="Danh mục chỉ số"),
):
    selected_country_codes = [c.strip().upper() for c in (countries or "US,VN").split(",") if c.strip()]
    if not selected_country_codes:
        selected_country_codes = ["US"]

    all_countries = CountryService.get_all()
    country_lookup = {c["code"]: c["name"] for c in all_countries if c.get("code")}

    page_title = APP_TEXT.get("economic_indicators", {}).get("page_title", "Chỉ Số Kinh Tế")
    template = env.get_template("economic_indicators.html")

    return HTMLResponse(
        template.render(
            request=request,
            nav_items=NAV_ITEMS,
            current_path="/economic-indicators",
            page_title=page_title,
            ui=APP_TEXT,
            all_countries=all_countries,
            country_lookup=country_lookup,
            categories=CATEGORIES_MAP,
            selected_country_codes=selected_country_codes,
            selected_category=category or "all",
            # Không truyền data indicators xuống template để dùng Skeleton Loading bằng AJAX
        )
    )


@router.get("/api/economic-indicators", response_class=JSONResponse)
async def get_economic_indicators_api(
    countries: str = Query("US", description="Danh sách mã quốc gia cách nhau bởi dấu phẩy"),
    category: str = Query("all", description="Danh mục chỉ số"),
):
    selected_country_codes = [c.strip().upper() for c in countries.split(",") if c.strip()]
    if not selected_country_codes:
        selected_country_codes = ["US"]

    all_countries = CountryService.get_all()
    country_lookup = {c["code"]: c["name"] for c in all_countries if c.get("code")}

    # Lấy danh sách indicators
    indicators = EconomicIndicatorsService.get_indicators_by_countries(
        selected_country_codes,
        category=category,
    )

    indicators_by_country = {
        code: {
            "code": code,
            "name": country_lookup.get(code, code),
            "indicators": [ind for ind in indicators if ind["country_code"] == code]
        }
        for code in selected_country_codes
    }

    return {
        "status": "success",
        "selected_countries": selected_country_codes,
        "category": category,
        "indicators": indicators,
        "indicators_by_country": indicators_by_country,
    }
