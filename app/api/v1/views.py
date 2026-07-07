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
    landing_data = {
        "hero": {"power_level": 8400, "title": "Padel Scouter", "subtitle": "Análisis inteligente de jugadores con IA", "cta_text": "Empezar análisis", "cta_url": "/login", "secondary_cta_text": "Ver API docs", "secondary_cta_url": "/docs"},
        "metrics": {"players_analyzed": 15234, "matches_processed": 89240, "tournaments_tracked": 456, "active_users": 3402},
        "features": [
            {"icon": "⚡", "title": "Poder de Combate", "description": "Algoritmo propio que calcula el nivel real del jugador de 0 a 9999 según categorías FEP oficiales."},
            {"icon": "🤖", "title": "Análisis con IA", "description": "Gemini AI genera una narrativa épica del jugador, fortalezas, debilidades y plan de mejora personalizado."},
            {"icon": "📊", "title": "Reglamento FIP 2026", "description": "Sistema de puntuación actualizado con Star Point, categorías oficiales y scoring real."},
            {"icon": "🏆", "title": "Rankings en Vivo", "description": "Clasificación actualizada de jugadores por categoría, con historial de evolución y comparativas."},
            {"icon": "📈", "title": "Estadísticas Avanzadas", "description": "Métricas detalladas: efectividad, tendencias, rendimiento por superficie y análisis de compañeros."},
            {"icon": "🎯", "title": "Plan de Mejora", "description": "Recomendaciones personalizadas basadas en IA para subir tu nivel de juego con ejercicios específicos."},
        ],
        "analytics": {"radar_labels": ["Potencia", "Técnica", "Mental", "Resistencia", "Estrategia"], "radar_data": [85, 72, 68, 90, 78], "win_rate": 68, "stat_bars": [{"label": "Efectividad en Red", "value": 78}, {"label": "Precisión de Saque", "value": 82}, {"label": "Defensa", "value": 65}, {"label": "Toma de Decisiones", "value": 71}]},
        "rankings": {"top_players": [{"rank": 1, "name": "Ale Galán", "power": 9850, "change": "+2"}, {"rank": 2, "name": "Arturo Coello", "power": 9720, "change": "0"}, {"rank": 3, "name": "Agustín Tapia", "power": 9600, "change": "+1"}], "player_rank": 42, "total_players": 15234},
        "ai_analysis": {"player1": {"name": "Tú", "power": 8400, "strengths": ["Defensa", "Resistencia"], "weaknesses": ["Juego de red", "Bandeja"]}, "player2": {"name": "Jugador Top", "power": 9850, "strengths": ["Ataque", "Precisión"], "weaknesses": ["Paciencia"]}, "improvement_plan": [{"area": "Juego de Red", "priority": "Alta", "progress": 25}, {"area": "Bandeja", "priority": "Alta", "progress": 15}, {"area": "Kondicional Físico", "priority": "Media", "progress": 60}]},
        "mockups": {"images": [{"src": "/static/img/mockup-1.png", "alt": "Dashboard Padel Scouter"}, {"src": "/static/img/mockup-2.png", "alt": "Análisis IA"}, {"src": "/static/img/mockup-3.png", "alt": "Ranking de jugadores"}]},
        "cta": {"title": "Empezá a scoutear", "subtitle": "Descubrí el poder real de cada jugador con análisis impulsado por IA", "button_text": "Comenzar ahora", "button_url": "/register"},
    }
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"user": None, "landing_data": landing_data, "show_landing_nav": True}
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

@router.get("/global-stats", response_class=HTMLResponse)
def global_stats_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="global_stats.html",
        context={"user": {}},
    )


@router.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="forgot_password.html",
        context={"user": None}
    )


@router.get("/reset-password", response_class=HTMLResponse)
def reset_password_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="reset_password.html",
        context={"user": None},
    )