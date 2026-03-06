from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .core.config import settings
from .db import init_db, is_postgres
from .routers import auth, public, admin, dispatch, driver

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fishlog")

app = FastAPI(title="FishLog MVP", version="1.0")
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.middleware("http")
async def log_request_errors(request: Request, call_next):
    try:
        response = await call_next(request)
        if response.status_code >= 500:
            logger.error("HTTP %s %s -> %s", request.method, request.url.path, response.status_code)
        return response
    except Exception:
        logger.exception("Unhandled error at %s %s", request.method, request.url.path)
        raise


@app.on_event("startup")
def _startup():
    logger.info(
        "startup: env=%s backend=%s base_url=%s",
        settings.APP_ENV,
        "postgres" if is_postgres() else "sqlite",
        settings.BASE_URL or "(request base url fallback)",
    )
    init_db()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


app.include_router(auth.router)
app.include_router(public.router)
app.include_router(admin.router)
app.include_router(dispatch.router)
app.include_router(driver.router)
