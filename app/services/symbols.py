from typing import List
from app.models.base import SymbolCreate, SymbolUpdate
from app.db.symbols import create_symbol, get_all_symbols, get_symbol_by_id, update_symbol, delete_symbol, create_multiple_symbols


class SymbolService:
    @staticmethod
    def create_symbol(symbol: SymbolCreate) -> int:
        return create_symbol(symbol)

    @staticmethod
    def create_multiple(symbols: List[str], exchange: str, asset_type: str,
                       country: str = "", base_country: str = "", quote_country: str = ""):
        create_multiple_symbols(symbols, exchange, asset_type, country, base_country, quote_country)

    @staticmethod
    def get_all() -> List[dict]:
        return get_all_symbols()

    @staticmethod
    def get_by_id(symbol_id: int) -> dict:
        symbol = get_symbol_by_id(symbol_id)
        if not symbol:
            raise ValueError(f"Symbol with ID {symbol_id} not found")
        return symbol

    @staticmethod
    def update(symbol_id: int, symbol: SymbolUpdate):
        if not get_symbol_by_id(symbol_id):
            raise ValueError(f"Symbol with ID {symbol_id} not found")
        update_symbol(symbol_id, symbol)

    @staticmethod
    def delete(symbol_id: int):
        if not get_symbol_by_id(symbol_id):
            raise ValueError(f"Symbol with ID {symbol_id} not found")
        delete_symbol(symbol_id)
