from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader

router = APIRouter(tags=["views"])

# Deshabilitamos caché de Jinja2 (fix para Python 3.14)
env = Environment(
    loader=FileSystemLoader("app/templates"),
    cache_size=0,
)
templates = Jinja2Templates(env=env)


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"user": None}
    )


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"user": None}
    )


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"user": {}}
    )


@router.get("/player/{player_id}", response_class=HTMLResponse)
def player_detail(request: Request, player_id: str):
    return templates.TemplateResponse(
        request=request,
        name="player_detail.html",
        context={"user": {}, "player": {"id": player_id, "name": ""}}
    )

@router.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="forgot_password.html",
        context={"user": None}
    )


@router.get("/reset-password", response_class=HTMLResponse)
def reset_password_page(request: Request, token: str = ""):
    return templates.TemplateResponse(
        request=request,
        name="reset_password.html",
        context={"user": None, "token": token}
    )