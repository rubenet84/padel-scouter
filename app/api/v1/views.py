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
        "hero": {
            "player_name": "Ruben Rebollo Rua",
            "player_title": "1ª Categoría — Nivel 4.75",
            "player_avatar": "https://picsum.photos/seed/padel-player-warrior/128/128.jpg",
            "signature_ability": "Rayo Fulminante del Saque",
            "badge_text": "Scouter Activo — Analizando en Tiempo Real",
            "power_level": 8999,
            "win_rate": 75,
            "fep_points": 316,
            "stats": {"tecnica": 81, "fisico": 75, "mental": 77},
            "title": "PADEL",
            "brand": "SCOUTER",
            "subtitle": "Analiza tu nivel de combate. Detecta debilidades del rival. Evoluciona como guerrero en cada partido.",
            "cta_text": "ACTIVAR SCOUTER",
        },
        "metrics": {
            "players": {"value": "12K+", "label": "Jugadores Activos"},
            "matches": {"value": "85K+", "label": "Partidos Analizados"},
            "accuracy": {"value": "98.7%", "label": "Precisión IA"},
            "clubs": {"value": "340+", "label": "Clubes"},
            "rating": {"value": "4.9", "label": "Valoración"},
        },
        "features": [
            {"icon": "mdi:lightning-bolt", "title": "Power Level", "desc": "Calcula tu nivel de poder real basado en técnica, físico, mental y táctica. Algoritmo inspirado en el sistema de medición de combatientes.", "stat": "9,200"},
            {"icon": "mdi:chart-box-outline", "title": "Análisis de Partidos", "desc": "Desglose total de cada encounter: sets, games, puntos break, rachas y patrones de juego detectados automáticamente.", "stat": "75%"},
            {"icon": "mdi:chart-areaspline", "title": "Estadísticas Completas", "desc": "32+ métricas divididas en Técnica, Físico y Mental/Táctico. Cada aspecto de tu juego cuantificado con precisión.", "stat": "80"},
            {"icon": "mdi:trophy-outline", "title": "Rankings FEP", "desc": "Sistema de ranking dinámico con puntos FEP, clasificación por categoría, temporada y filtros avanzados de rendimiento.", "stat": "#1"},
            {"icon": "mdi:sword-cross", "title": "Fortalezas vs Debilidades", "desc": "Detección automática de tus armas letales y puntos débiles. Como un scouter que revela el perfil completo del combatiente.", "stat": "H2H"},
            {"icon": "mdi:robot-outline", "title": "Plan de Mejora IA", "desc": "Inteligencia artificial que genera un plan de entrenamiento personalizado. Tu sensei digital para alcanzar el siguiente nivel.", "stat": "IA"},
        ],
        "analytics": {
            "win_rate": 75,
            "total_matches": 8,
            "wins": 6,
            "losses": 2,
            "sets_won": 12,
            "sets_total": 16,
            "categories": [
                {
                    "label": "Técnica", "color": "orange", "icon": "mdi:sword",
                    "items": [
                        {"label": "Derecha", "value": 80, "color": "orange"},
                        {"label": "Revés", "value": 72, "color": "orange"},
                        {"label": "Saque", "value": 100, "color": "gold"},
                        {"label": "Volea", "value": 68, "color": "orange"},
                    ]
                },
                {
                    "label": "Físico", "color": "blue", "icon": "mdi:run-fast",
                    "items": [
                        {"label": "Velocidad", "value": 80, "color": "blue"},
                        {"label": "Resistencia", "value": 65, "color": "blue"},
                        {"label": "Fuerza", "value": 75, "color": "blue"},
                    ]
                },
                {
                    "label": "Mental / Táctico", "color": "purple", "icon": "mdi:brain",
                    "items": [
                        {"label": "Concentración", "value": 78, "color": "purple"},
                        {"label": "Trabajo pareja", "value": 80, "color": "purple"},
                        {"label": "Presión", "value": 72, "color": "purple"},
                    ]
                },
            ],
            "match_performance": [
                {"label": "P1", "value": 60, "win": True},
                {"label": "P2", "value": 80, "win": True},
                {"label": "P3", "value": 30, "win": False},
                {"label": "P4", "value": 90, "win": True},
                {"label": "P5", "value": 75, "win": True},
                {"label": "P6", "value": 40, "win": False},
                {"label": "P7", "value": 85, "win": True},
                {"label": "P8", "value": 100, "win": True},
            ],
            "radar_labels": ["SAQUE", "DERECHA", "REVÉS", "RED", "VEL.", "MENTAL"],
            "radar_values": [100, 80, 72, 68, 80, 78],
        },
        "rankings": {
            "top_players": [
                {"rank": 1, "name": "Ruben Rebollo Rua", "category": "PRIMERA — Nivel 4.75", "power_bar": 100, "color": "gold", "icon": "mdi:crown", "pts": 316, "wins": 6, "losses": 2, "avatar": "https://picsum.photos/seed/warrior-1/80/80.jpg"},
                {"rank": 2, "name": "Araceli Rodriguez Guglielmone", "category": "INICIACIÓN — Nivel 3.50", "power_bar": 88, "color": "blue", "icon": "mdi:medal-outline", "pts": 280, "wins": 4, "losses": 0, "avatar": "https://picsum.photos/seed/warrior-2/80/80.jpg"},
                {"rank": 3, "name": "Carlos Martínez Fernández", "category": "SEGUNDA — Nivel 4.00", "power_bar": 78, "color": "purple", "icon": "mdi:medal-outline", "pts": 245, "wins": 5, "losses": 3, "avatar": "https://picsum.photos/seed/warrior-3/80/80.jpg"},
                {"rank": 4, "name": "Laura Sánchez Pérez", "category": "PRIMERA — Nivel 4.25", "power_bar": 66, "color": "neon", "icon": "", "pts": 210, "wins": 3, "losses": 2, "avatar": "https://picsum.photos/seed/warrior-4/80/80.jpg"},
            ],
            "top_cards": [
                {"label": "Mayor Power Level", "name": "Ruben Rebollo Rua", "value": "8,999", "icon": "mdi:star-four-points", "color": "gold"},
                {"label": "Mejor % Victorias", "name": "Araceli Rodriguez G.", "value": "100%", "icon": "mdi:percent-circle", "color": "neon"},
                {"label": "Mejor Racha", "name": "Carlos Martínez F.", "value": "5 Wins", "icon": "mdi:fire", "color": "blue"},
            ],
        },
        "ai_analysis": {
            "player_name": "Ruben Rebollo Rua",
            "avatar": "https://picsum.photos/seed/padel-player-warrior/80/80.jpg",
            "rival_avatar": "https://picsum.photos/seed/rival-warrior/80/80.jpg",
            "signature_ability": "Rayo Fulminante del Saque",
            "signature_level": "MUY ALTO",
            "signature_stat": "Saque ganador en 23% de los puntos",
            "pattern_detected": "Tu rival tiende a atacar el revés en puntos clave (deuce). Tu tasa de éxito en ese escenario es del 42%.",
            "tactical_recommendation": "Posiciónate 20cm más al centro en situaciones de deuce para anticipar el ataque al revés.",
            "strengths": [
                {"label": "Ataque perfecto", "icon": "mdi:check"},
                {"label": "Ejecución de pasos", "icon": "mdi:check"},
                {"label": "Saque dominante", "icon": "mdi:check"},
            ],
            "weaknesses": [
                {"label": "Resistencia física", "icon": "mdi:alert"},
                {"label": "Revés presión", "icon": "mdi:alert"},
                {"label": "Amplitud golpeo", "icon": "mdi:alert"},
            ],
            "h2h": [
                {"metric": "Saque", "player": 100, "rival": 75},
                {"metric": "Derecha", "player": 80, "rival": 85},
                {"metric": "Velocidad", "player": 80, "rival": 90},
                {"metric": "Mental", "player": 78, "rival": 65},
            ],
            "advantage_text": "Tu ventaja clave: Saque +15pts | Mental +13pts",
            "improvement_plan": [
                {"step": 1, "title": "Resistencia de Revés", "desc": "3 sesiones/semana — Ejercicios de resistencia bajo presión en revés", "progress": 30, "color": "orange"},
                {"step": 2, "title": "Velocidad de Desplazamiento", "desc": "2 sesiones/semana — Intervalos de sprint lateral y cambio de dirección", "progress": 15, "color": "blue"},
                {"step": 3, "title": "Amplitud de Golpe", "desc": "Trabajo de elasticidad y rango de movimiento en golpeo", "progress": 8, "color": "purple"},
            ],
            "projection_label": "Proyección Power Level",
            "projection_from": 8999,
            "projection_to": 9450,
        },
        "cta": {
            "title": "Activa tu Scouter",
            "subtitle": "Únete a miles de guerreros del pádel que ya analizan su juego con la precisión de un scouter de combate profesional.",
            "button_text": "COMENZAR AHORA — GRATIS",
            "button_url": "/login",
        },
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
        context={"user": None, "show_landing_nav": True, "landing_nav_links": False}
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
