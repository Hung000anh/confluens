# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- **Run app**: `python run.py` (runs Uvicorn on http://127.0.0.1:8000 with reload)
- **Install dependencies**: `pip install -r requirements.txt` (if present) or `pip install fastapi uvicorn matplotlib sqlite3`

## Architecture & Structure

- **Framework**: FastAPI with Jinja2 templates (`/templates`) and static assets (`/static`).
- **Database**: SQLite database stored at root as `conflues.db`. Handled via `app/db/` modules using raw SQL connection/cursor helpers.
- **Settings & Config**: `app/config/settings.py` manages `NAV_ITEMS`, `APP_TEXT`, path definitions (`BASE_DIR`, `DB_PATH`, `STATIC_DIR`, `TEMPLATES_DIR`), and default chart settings.
- **Routes & Services**:
  - `app/routes/`: Route definitions for `symbols`, `charts`, `economic_indicators`, `indicators`, and `settings`.
  - `app/services/`: Core logic for fetching/saving data, generating chart images/data, and managing indicators/symbols.
- **Data & Seeds**: External json sources like `data/tradingview_countries.json` supply static/seed metadata for symbols and indicators.
