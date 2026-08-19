from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_NAME = "conflues.db"
DB_PATH = BASE_DIR / DB_NAME
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
COUNTRIES_JSON_PATH = BASE_DIR / "data" / "tradingview_countries.json"
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
    "strategies": {
        "page_title": "Quản lý Chiến lược",
        "title": "Quản lý Chiến lược",
        "empty_state": "Chưa có chiến lược nào được tạo.",
    },
    "notifications": {
        "page_title": "Thông báo",
        "title": "Thông báo",
        "empty_state": "Chưa có thông báo mới.",
    },
    "economic_indicators": {
        "page_title": "Chỉ Số Kinh Tế",
        "detail_tab": "Bảng Chi Tiết",
        "compare_tab": "Đối Chiếu So Sánh",
        "search_placeholder": "🔍 Tìm kiếm theo tên chỉ số hoặc symbol...",
        "empty_state": "Không tìm thấy chỉ số kinh tế nào phù hợp.",
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
        "path": "/cftc",
        "label": "CFTC",
        "title": "CFTC",
        "icon": """
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>
        """,
    },
    {
        "path": "/economic-calendar",
        "label": "Lịch Kinh Tế",
        "title": "Lịch Kinh Tế",
        "icon": """
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line><path d="M8 14h3v3H8z"></path></svg>
        """,
    },
    {
        "path": "/economic-indicators",
        "label": "Chỉ Số Kinh Tế",
        "title": "Chỉ Số Kinh Tế",
        "icon": """
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 18h18"></path><path d="M7 15l3-3 3 2 5-7"></path><path d="M17 7h2v2"></path></svg>
        """,
    },
    {
        "path": "/news",
        "label": "Tin Tức",
        "title": "Tin Tức",
        "icon": """
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16v16H4z"></path><path d="M8 8h8"></path><path d="M8 12h8"></path><path d="M8 16h5"></path></svg>
        """,
    },
    {
        "path": "/notifications",
        "label": "Thông báo",
        "title": "Thông báo",
        "icon": """
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 17h5l-1.4-1.4A2 2 0 0 1 18 14.2V11a6 6 0 1 0-12 0v3.2a2 2 0 0 1-.6 1.4L4 17h5"></path><path d="M10 21a2 2 0 0 0 4 0"></path></svg>
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
