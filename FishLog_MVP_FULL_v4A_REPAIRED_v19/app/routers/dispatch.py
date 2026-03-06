from __future__ import annotations
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from ..core.session import get_session
from ..services.dispatch import assign_order

router = APIRouter()

def require_owner(request: Request):
    s = get_session(request)
    if not s or s.get("role") != "owner":
        return None
    return s

@router.post("/admin/dispatch/assign")
def assign(request: Request, order_id: int = Form(...), driver_user_id: int = Form(...), vehicle_id: int = Form(...), date: str = Form(...)):
    s = require_owner(request)
    if not s:
        return RedirectResponse("/admin/login", status_code=303)
    assign_order(order_id, driver_user_id, vehicle_id)
    return RedirectResponse(f"/admin/dispatch?date={date}", status_code=303)
