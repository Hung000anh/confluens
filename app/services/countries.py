from typing import List

from app.db.countries import get_all_countries, resolve_country_code


class CountryService:
    @staticmethod
    def get_all() -> List[dict]:
        return get_all_countries()

    @staticmethod
    def resolve_code(code: str) -> str:
        return resolve_country_code(code)
