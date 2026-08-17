from app.db.settings import get_setting, set_setting, get_all_settings


class SettingsService:
    @staticmethod
    def get(key: str, default: str = "") -> str:
        return get_setting(key, default)

    @staticmethod
    def set(key: str, value: str):
        set_setting(key, value)

    @staticmethod
    def get_all() -> dict:
        return get_all_settings()

    @staticmethod
    def get_chart_settings() -> dict:
        settings = SettingsService.get_all()
        candle_count = int(settings.get("candle_count", "100"))
        return {
            "candle_count": candle_count,
            "bull_color": settings.get("bull_color", "#10b981"),
            "bear_color": settings.get("bear_color", "#ffffff"),
            "timeframes": settings.get("timeframes", "1d,1w,1m").split(",")
        }

    @staticmethod
    def update_chart_settings(candle_count: str, bull_color: str, bear_color: str):
        SettingsService.set("candle_count", candle_count)
        SettingsService.set("bull_color", bull_color)
        SettingsService.set("bear_color", bear_color)
