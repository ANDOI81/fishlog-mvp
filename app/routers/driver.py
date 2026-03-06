from __future__ import annotations
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta
from ..core.session import get_session
from ..services.dispatch import list_assignments_by_driver, is_assigned_to_driver
from ..services.orders import set_status

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def require_driver(request: Request):
    s = get_session(request)
    if not s or s.get("role") != "driver":
        return None
    return s


@router.get("/driver")
def driver_home(request: Request, date: str | None = None):
    s = require_driver(request)
    if not s:
        return RedirectResponse("/driver/login", status_code=303)

    base = datetime.now().date()
    today = base.isoformat()
    yesterday = (base - timedelta(days=1)).isoformat()
    tomorrow = (base + timedelta(days=1)).isoformat()

    if not date:
        date = today

    orders = list_assignments_by_driver(s["user_id"], date)
    return templates.TemplateResponse(
        "driver_dashboard.html",
        {
            "request": request,
            "session": s,
            "date": date,
            "today": today,
            "yesterday": yesterday,
            "tomorrow": tomorrow,
            "orders": orders,
        },
    )


@router.post("/driver/status")
def driver_status(request: Request, order_id: int = Form(...), status: str = Form(...), date: str = Form(...)):
    s = require_driver(request)
    if not s:
        return RedirectResponse("/driver/login", status_code=303)

    # Allow delivery completion and rollback from delivered -> assigned.
    if status not in ("delivered", "assigned"):
        return RedirectResponse(f"/driver?date={date}", status_code=303)

    # Prevent cross-driver updates by verifying assignment ownership.
    if not is_assigned_to_driver(order_id, s["user_id"]):
        return RedirectResponse(f"/driver?date={date}", status_code=303)

    set_status(order_id, status)
    return RedirectResponse(f"/driver?date={date}", status_code=303)
