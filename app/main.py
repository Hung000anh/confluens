from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import matplotlib

from app.config.settings import STATIC_DIR
from app.db.base import init_db
from app.routes.charts import router as charts_router
from app.routes.economic_calendar import router as economic_calendar_router
from app.routes.economic_indicators import router as economic_indicators_router
from app.routes.indicators import router as indicators_router
from app.routes.settings import router as settings_router
from app.routes.symbols import router as symbols_router

matplotlib.use('Agg')
init_db()

app = FastAPI(
    title="Conflues",
    description="Trading codes and charts management system",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.include_router(symbols_router, tags=["symbols"])
app.include_router(charts_router, tags=["charts"])
app.include_router(economic_calendar_router, tags=["economic-calendar"])
app.include_router(economic_indicators_router, tags=["economic-indicators"])
app.include_router(indicators_router, tags=["indicators"])
app.include_router(settings_router, tags=["settings"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
