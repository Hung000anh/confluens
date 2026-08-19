from typing import List

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Environment, FileSystemLoader

from app.config.settings import APP_TEXT, NAV_ITEMS, TEMPLATES_DIR, DEFAULT_PAGE_TITLE
from app.models.base import SymbolUpdate, VerifySymbolRequest
from app.services.countries import CountryService
from app.services.symbols import SymbolService
from app.services.verify import VerificationService

router = APIRouter(prefix="", tags=["symbols"])
env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))


@router.get("/", response_class=HTMLResponse)
async def list_symbols(request: Request):
    symbols = SymbolService.get_all()
    countries = CountryService.get_all()
    template = env.get_template("index.html")
    return HTMLResponse(
        template.render(
            request=request,
            symbols=symbols,
            countries=countries,
            countries_by_code={item["code"]: item["name"] for item in countries},
            current_path="/",
            nav_items=NAV_ITEMS,
            page_title=APP_TEXT["symbols"]["page_title"],
            ui=APP_TEXT,
        )
    )


@router.post("/verify_symbol")
async def verify_symbol(req: VerifySymbolRequest):
    results = VerificationService.verify_symbols(req.symbols, req.exchange)
    return {"results": results}


@router.post("/add_symbol", response_class=HTMLResponse)
async def add_symbol(
    request: Request,
    symbol: List[str] = Form(...),
    exchange: str = Form(""),
    asset_type: str = Form(...),
    country: str = Form(""),
    base_country: str = Form(""),
    quote_country: str = Form("")
):
    symbols_list = []
    for sym_group in symbol:
        for s in sym_group.split(','):
            if s.strip():
                symbols_list.append(s.strip())

    try:
        SymbolService.create_multiple(symbols_list, exchange, asset_type, country, base_country, quote_country)
        return RedirectResponse(url="/", status_code=303)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/delete_symbol/{symbol_id}")
async def delete_symbol(symbol_id: int):
    try:
        SymbolService.delete(symbol_id)
        return {"status": "success"}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/edit_symbol/{symbol_id}", response_class=HTMLResponse)
async def edit_symbol(
    symbol_id: int,
    request: Request,
    symbol: str = Form(...),
    exchange: str = Form(""),
    asset_type: str = Form(...),
    country: str = Form(""),
    base_country: str = Form(""),
    quote_country: str = Form("")
):
    try:
        symbol_update = SymbolUpdate(
            symbol=symbol,
            exchange=exchange,
            type=asset_type,
            country=country,
            base_country=base_country,
            quote_country=quote_country,
        )
        SymbolService.update(symbol_id, symbol_update)
        return RedirectResponse(url="/", status_code=303)
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if "not found" in detail.lower() else 400
        raise HTTPException(status_code=status_code, detail=detail)
