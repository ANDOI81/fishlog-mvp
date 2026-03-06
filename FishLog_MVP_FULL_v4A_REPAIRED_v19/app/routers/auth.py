from __future__ import annotations
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from ..db import connect
from ..core.security import verify_password
from ..core.session import set_session, clear_session

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/admin/login")
def admin_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "role": "owner"})

@router.post("/admin/login")
def admin_login(request: Request, username: str = Form(...), password: str = Form(...)):
    conn = connect(); cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=? AND role='owner'", (username,))
    u = cur.fetchone()
    conn.close()
    if not u or not verify_password(password, u["password_hash"]):
        return templates.TemplateResponse("login.html", {"request": request, "role": "owner", "error": "아이디/비밀번호가 올바르지 않습니다."})
    resp = RedirectResponse("/admin", status_code=303)
    set_session(resp, {"user_id": u["id"], "role": "owner", "display_name": u["display_name"]})
    return resp

@router.get("/driver/login")
def driver_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "role": "driver"})

@router.post("/driver/login")
def driver_login(request: Request, username: str = Form(...), password: str = Form(...)):
    conn = connect(); cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=? AND role='driver'", (username,))
    u = cur.fetchone()
    conn.close()
    if not u or not verify_password(password, u["password_hash"]):
        return templates.TemplateResponse("login.html", {"request": request, "role": "driver", "error": "아이디/비밀번호가 올바르지 않습니다."})
    resp = RedirectResponse("/driver", status_code=303)
    set_session(resp, {"user_id": u["id"], "role": "driver", "display_name": u["display_name"]})
    return resp

@router.get("/logout")
def logout():
    resp = RedirectResponse("/", status_code=303)
    clear_session(resp)
    return resp
