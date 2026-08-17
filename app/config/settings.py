from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_NAME = "conflues.db"
DB_PATH = BASE_DIR / DB_NAME
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
HOST = "127.0.0.1"
PORT = 8000
APP_TITLE = "Conflues"
DEFAULT_PAGE_TITLE = "Quản lý Mã Giao Dịch"
APP_TEXT = {
    "common": {
        "app_name": "Conflues",
        "save": "Lưu",
        "cancel": "Hủy",
        "edit": "Sửa",
        "delete": "Xóa",
        "add": "Thêm",
    },
    "symbols": {
        "page_title": "Quản lý Mã Giao Dịch",
        "add_button": "Thêm Mã Mới",
        "search_placeholder": "🔍 Tìm kiếm theo Symbol...",
        "all_asset_types": "Tất cả Loại tài sản",
        "all_exchanges": "Tất cả Sàn giao dịch",
        "all_countries": "Tất cả Quốc gia",
        "table": {
            "symbol": "Symbol",
            "exchange": "Sàn giao dịch",
            "country": "Quốc gia (Base / Quote)",
            "asset_type": "Loại tài sản",
            "actions": "Thao tác",
        },
    },
    "charts": {
        "page_title": "Biểu đồ",
        "layout_label": "Bố cục:",
        "layout_auto": "Tự động",
        "layout_1": "1 Cột",
        "layout_2": "2 Cột",
        "layout_3": "3 Cột",
        "loading": "Đang tải",
    },
    "indicators": {
        "page_title": "Quản Lý Chỉ Báo Giao Dịch",
        "section_title": "Quản Lý Chỉ Báo",
        "add_button": "+ Thêm Chỉ Báo",
        "add_modal_title": "Thêm Chỉ Báo Mới",
        "edit_modal_title": "Sửa Chỉ Báo",
        "save_button": "Lưu chỉ báo",
        "list_title": "Danh Sách Chỉ Báo Cấu Hình",
        "empty_state": "Chưa có chỉ báo nào được thêm.",
    },
    "settings": {
        "page_title": "Cài Đặt Cấu Hình Biểu Đồ",
        "save_button": "Lưu Cài Đặt",
        "section_title": "Cấu hình Nến & Màu sắc",
        "success_message": "Cấu hình đã được lưu thành công!",
    },
}
NAV_ITEMS = [
    {
        "path": "/charts",
        "label": "Biểu Đồ",
        "title": "Biểu Đồ",
        "icon": """
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
        """,
    },
    {
        "path": "/",
        "label": "Mã Giao Dịch",
        "title": "Mã Giao Dịch",
        "icon": """
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>
        """,
    },
    {
        "path": "/indicators",
        "label": "Chỉ Báo",
        "title": "Chỉ Báo",
        "icon": """
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
        """,
    },
    {
        "path": "/settings",
        "label": "Cài đặt",
        "title": "Cài đặt",
        "icon": """
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
        """,
    },
]
DEFAULT_TIMEFRAMES = [
    "1m", "3m", "5m", "15m", "30m", "45m",
    "1h", "2h", "3h", "4h", "1d", "1w", "1M", "3M", "6M", "12M"
]
DEFAULT_CHART_SETTINGS = {
    "candle_count": "100",
    "bull_color": "#10b981",
    "bear_color": "#ffffff",
    "timeframes": "1m,3m,5m,15m,30m,45m,1h,2h,3h,4h,1d,1w,1m"
}
