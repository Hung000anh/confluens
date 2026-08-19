from typing import List
from app.models.base import IndicatorCreate, IndicatorUpdate
from app.db.indicators import (
    create_indicator, get_all_indicators, get_indicator_by_id,
    update_indicator, delete_indicator, toggle_indicator,
    get_all_active_indicators, get_active_indicators_by_timeframe
)


class IndicatorService:
    @staticmethod
    def create(indicator: IndicatorCreate) -> int:
        return create_indicator(indicator)

    @staticmethod
    def get_all() -> List[dict]:
        return get_all_indicators()

    @staticmethod
    def get_by_id(indicator_id: int) -> dict:
        indicator = get_indicator_by_id(indicator_id)
        if not indicator:
            raise ValueError(f"Indicator with ID {indicator_id} not found")
        return indicator

    @staticmethod
    def get_all_active() -> List[dict]:
        return get_all_active_indicators()

    @staticmethod
    def get_active_by_timeframe(timeframe: str) -> List[dict]:
        return get_active_indicators_by_timeframe(timeframe)

    @staticmethod
    def update(indicator_id: int, indicator: IndicatorUpdate):
        if not get_indicator_by_id(indicator_id):
            raise ValueError(f"Indicator with ID {indicator_id} not found")
        update_indicator(indicator_id, indicator)

    @staticmethod
    def delete(indicator_id: int):
        if not get_indicator_by_id(indicator_id):
            raise ValueError(f"Indicator with ID {indicator_id} not found")
        delete_indicator(indicator_id)

    @staticmethod
    def toggle(indicator_id: int):
        if not get_indicator_by_id(indicator_id):
            raise ValueError(f"Indicator with ID {indicator_id} not found")
        toggle_indicator(indicator_id)
