from datetime import date, timedelta
import json
from typing import Dict, Any

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from ..services.customers import get_customer_by_token
from ..services.pricing import get_catalog, get_prices
from ..services.orders import create_order, list_orders

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _nested_prices(prices: Dict[tuple, Any]) -> Dict[str, Dict[str, Any]]:
    """Convert {(fish_type, fish_size): price} -> {fish_type: {fish_size: price}} for safe JSON."""
    out: Dict[str, Dict[str, Any]] = {}
    for (ft, sz), v in (prices or {}).items():
        ft = str(ft)
        sz = str(sz)
        out.setdefault(ft, {})[sz] = v
    return out


def _flat_catalog(catalog: Dict[tuple, Any]) -> Dict[str, Any]:
    """Convert {(fish_type, fish_size): enabled} -> {"fish_type|fish_size": enabled}.

    Jinja2's tojson filter can't serialize dicts with tuple keys, so we normalize
    the keys for the public order page JavaScript.
    """
    out: Dict[str, Any] = {}
    for (ft, sz), v in (catalog or {}).items():
        out[f"{ft}|{sz}"] = bool(v)
    return out

def _flat_prices(prices: Dict[tuple, Any]) -> Dict[str, Any]:
    """Convert {(fish_type, fish_size): price} -> {"fish_type|fish_size": price} for JS."""
    out: Dict[str, Any] = {}
    for (ft, sz), v in (prices or {}).items():
        out[f"{ft}|{sz}"] = v
    return out



@router.get("/o/{token}", response_class=HTMLResponse)
def order_page(request: Request, token: str):
    customer = get_customer_by_token(token)
    if not customer:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "title": "문제가 발생했어요", "message": "유효하지 않은 주문 링크입니다. 대표에게 연락해주세요."},
            status_code=404,
        )

    today = date.today()
    date_str = request.query_params.get("date") or (today + timedelta(days=1)).strftime("%Y-%m-%d")

    # get_catalog() returns a dict keyed by tuple (fish_type, fish_size).
    # Normalize to a JSON-safe dict with string keys for the template.
    catalog = _flat_catalog(get_catalog(date_str))
    catalog_json = json.dumps(catalog, ensure_ascii=False)
    prices_raw = get_prices(date_str)
    prices = _flat_prices(prices_raw)
    prices_json = json.dumps(prices, ensure_ascii=False)

    return templates.TemplateResponse(
        "order.html",
        {
            "request": request,
            "customer": customer,
            "date": date_str,
            "today": today.strftime("%Y-%m-%d"),
            "yesterday": (today - timedelta(days=1)).strftime("%Y-%m-%d"),
            "tomorrow": (today + timedelta(days=1)).strftime("%Y-%m-%d"),
            "delivery_date": date_str,
            "catalog": catalog,
            "catalog_json": catalog_json,
            "prices": prices,
            "prices_json": prices_json,
        },
    )


@router.post("/o/{token}")
def place_order(
    request: Request,
    token: str,
    delivery_date: str = Form(...),
    fish_type: str = Form(...),
    fish_size: str = Form(""),
    qty_kg: float = Form(0),
    note: str = Form(""),
):
    customer = get_customer_by_token(token)
    if not customer:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "title": "문제가 발생했어요", "message": "유효하지 않은 주문 링크입니다. 대표에게 연락해주세요."},
            status_code=404,
        )

    create_order(
        customer_id=customer["id"],
        fish_type=fish_type,
        fish_size=fish_size,
        qty_kg=qty_kg,
        note=note,
        delivery_date=delivery_date,
    )
    return RedirectResponse(url=f"/o/{token}/done", status_code=303)


@router.get("/o/{token}/done", response_class=HTMLResponse)
def order_done(request: Request, token: str):
    customer = get_customer_by_token(token)
    if not customer:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "title": "문제가 발생했어요", "message": "유효하지 않은 주문 링크입니다. 대표에게 연락해주세요."},
            status_code=404,
        )
    return templates.TemplateResponse("order_done.html", {"request": request, "customer": customer})


@router.get("/o/{token}/history", response_class=HTMLResponse)
def customer_history(request: Request, token: str):
    customer = get_customer_by_token(token)
    if not customer:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "title": "문제가 발생했어요", "message": "유효하지 않은 주문 링크입니다. 대표에게 연락해주세요."},
            status_code=404,
        )

    # Show today's orders by default
    today = date.today().strftime("%Y-%m-%d")
    date_str = request.query_params.get("date") or today
    orders = list_orders(date_str)
    # filter to this customer
    orders = [o for o in orders if o.get("customer_id") == customer["id"]]

    return templates.TemplateResponse(
        "customer_history.html",
        {"request": request, "customer": customer, "orders": orders, "date": date_str},
    )