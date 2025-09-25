import hashlib
import hmac
import urllib.parse
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .services.wb_http_client import WBHttpClient
from .settings import settings
from .storage.repo import UserRepo

app = FastAPI()

BASE_DIR = Path.cwd()
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


def _verify_init_data(init_data: str, bot_token: str) -> dict:
    """Validate Telegram WebApp initData."""

    parsed = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
    hash_recv: Optional[str] = parsed.pop("hash", None)
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret_key = hashlib.sha256(f"WebAppData{bot_token}".encode()).digest()
    h = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if h != hash_recv:
        raise HTTPException(status_code=401, detail="Invalid initData hash")
    if "user" in parsed:
        import json

        try:
            parsed["user"] = json.loads(parsed["user"])
        except Exception:
            pass
    return parsed


@app.get("/app/profile", response_class=HTMLResponse)
async def app_profile(request: Request, init_data: str):  # noqa: ARG001
    _ = _verify_init_data(init_data, settings.bot_token)
    template = env.get_template("profile_app.html")
    return template.render(webapp_public_url=settings.webapp_public_url, init_data=init_data)


@app.get("/api/profile/list")
async def api_profile_list(init_data: str):
    data = _verify_init_data(init_data, settings.bot_token)
    tg_id = int(data["user"]["id"])
    repo = UserRepo()

    profiles = await repo.get_profiles(tg_id)
    if not profiles:
        client = WBHttpClient(tg_id)
        try:
            # TODO: заменить на реальное API WB Seller
            # пример:
            # js = await client.get_json("api/organizations")
            # profiles = [
            #     {
            #         "id": x["id"],
            #         "name": x["name"],
            #         "inn": x.get("inn", ""),
            #         "status": x.get("status", ""),
            #     }
            #     for x in js
            # ]
            profiles = [
                {"id": "default", "name": "Аккаунт WB Seller", "inn": "", "status": "active"}
            ]
        finally:
            await client.aclose()
        await repo.set_profiles(tg_id, profiles)

    active_id = await repo.get_active_profile(tg_id)
    return JSONResponse({"profiles": profiles, "active_profile_id": active_id})


@app.post("/api/profile/select")
async def api_profile_select(request: Request):
    body = await request.json()
    init_data = body.get("init_data")
    profile_id = body.get("profile_id")
    if not init_data:
        raise HTTPException(status_code=400, detail="init_data required")
    if not profile_id:
        raise HTTPException(status_code=400, detail="profile_id required")

    data = _verify_init_data(init_data, settings.bot_token)
    tg_id = int(data["user"]["id"])

    repo = UserRepo()
    await repo.set_active_profile(tg_id, profile_id)
    return JSONResponse({"ok": True})
