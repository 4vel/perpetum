from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.auth import AuthManager, COOKIE_NAME
from app.schemas import AskRequest, AskResponse, HealthResponse, LoginRequest
from app.services import (
    AnswerGenerator,
    OfferCatalog,
    ServiceConfigurationError,
    UpstreamServiceError,
    YandexSearchClient,
)


BASE_DIR = Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http = httpx.AsyncClient(timeout=settings.request_timeout)
    app.state.offers = OfferCatalog(BASE_DIR / "data" / "ofrs_merge.xlsx")
    app.state.auth = AuthManager(settings)
    yield
    await app.state.http.aclose()


app = FastAPI(title="Perpetum", version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/", include_in_schema=False)
async def index(request: Request):
    if not current_user(request):
        return RedirectResponse("/login", status_code=303)
    return FileResponse(BASE_DIR / "static" / "index.html")


def current_user(request: Request):
    return request.app.state.auth.verify_session(request.cookies.get(COOKIE_NAME))


@app.get("/login", include_in_schema=False)
async def login_page(request: Request):
    if current_user(request):
        return RedirectResponse("/", status_code=303)
    return FileResponse(BASE_DIR / "static" / "login.html")


@app.post("/api/auth/login")
async def login(payload: LoginRequest, request: Request, response: Response):
    auth = request.app.state.auth
    if not auth.configured:
        raise HTTPException(
            status_code=503,
            detail="Авторизация не настроена: заполните AUTH_USERNAME, AUTH_PASSWORD и AUTH_SECRET",
        )
    if not auth.authenticate(payload.username, payload.password):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    response.set_cookie(
        key=COOKIE_NAME,
        value=auth.create_session(payload.username),
        max_age=auth.session_seconds,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="strict",
        path="/",
    )
    return {"username": payload.username}


@app.post("/api/auth/logout", status_code=204)
async def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")


@app.get("/api/auth/me")
async def me(request: Request):
    username = current_user(request)
    if not username:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    return {"username": username}


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(BASE_DIR / "static" / "favicon.svg", media_type="image/svg+xml")


@app.get("/api/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        search_configured=bool(settings.yandex_search_api_key and settings.yandex_folder_id),
        llm_configured=bool(settings.ai_api_key and settings.yandex_folder_id),
    )


@app.post("/api/ask", response_model=AskResponse)
async def ask(payload: AskRequest, request: Request):
    if not current_user(request):
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    try:
        search = YandexSearchClient(settings, request.app.state.http)
        sources = await search.search(payload.query.strip())
        offers = request.app.state.offers.search(payload.query.strip(), limit=3)
        answer = await AnswerGenerator(settings, request.app.state.http).generate(
            payload.query.strip(), sources
        )
        return AskResponse(
            query=payload.query.strip(), answer=answer, sources=sources, offers=offers
        )
    except ServiceConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except UpstreamServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
