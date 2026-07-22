"""Cliente de Google Gemini para análisis de jugadores.

Envía las estadísticas del jugador a Gemini 2.5 Flash y recibe una respuesta
estructurada con descripción épica, fortalezas, debilidades, plan de mejora
y golpe definitivo. Incluye fallback para errores de API (503, 429, quota).
"""

import json
import logging
from google import genai
from google.genai import types
from app.core.config import settings

logger = logging.getLogger(__name__)


client = genai.Client(api_key=settings.google_api_key.get_secret_value())


ANALYSIS_PROMPT = """
Eres un experto analizador de jugadores de pádel con profundo conocimiento del 
reglamento FIP 2026 y el sistema de categorías de la Federación Española de Pádel (FEP).

Analiza las siguientes estadísticas del jugador y genera un análisis épico estilo 
"Scouter de Dragon Ball" pero aplicado al pádel profesional.

JUGADOR: {name}
CATEGORÍA: {category}
PODER DE COMBATE: {power_level}

ESTADÍSTICAS TÉCNICAS (0-100):
- Derecha: {derecha}
- Revés: {reves}
- Volea de Derecha: {volea_derecha}
- Volea de Revés: {volea_reves}
- Bandeja: {bandeja}
- Víbora: {vibora}
- Remate: {remate}
- Globo: {globo}
- Saque: {saque}
- Bajada de pared: {bajada_pared}

ESTADÍSTICAS FÍSICAS (0-100):
- Velocidad: {velocidad}
- Resistencia: {resistencia}
- Reflejos: {reflejos}

ESTADÍSTICAS MENTALES (0-100):
- Táctica: {tactica}
- Presión: {presion}
- Trabajo en pareja: {trabajo_en_pareja}

GOLPE DEFINITIVO DETECTADO POR EL SCOUTER:
- Habilidad más potente: {golpe_stat_label} ({golpe_stat_categoria})
- Puntuación: {golpe_puntuacion}/100
- Nivel de amenaza calculado: {nivel_amenaza}

Responde ÚNICAMENTE con un JSON válido con esta estructura exacta:
{{
  "descripcion_epica": "Descripción narrativa épica del jugador (2-3 frases emocionantes)",
  "fortalezas": ["fortaleza 1", "fortaleza 2", "fortaleza 3"],
  "debilidades": ["debilidad 1", "debilidad 2"],
  "plan_mejora": "Plan de mejora generado con el siguiente formato exacto:\n\n[PARRAFO DESCRIPTIVO del plan de mejora (2-3 frases)]\n\n---\n1\n[NOMBRE del área de mejora]\n3 sesiones/semana — [DESCRIPCIÓN del ejercicio]\n\n---\n2\n[NOMBRE del área de mejora]\n2 sesiones/semana — [DESCRIPCIÓN del ejercicio]\n\n---\n3\n[NOMBRE del área de mejora]\n1 sesión/semana — [DESCRIPCIÓN del ejercicio]\n\n---\nProyección Power Level\n{power_level} → [PROYECCIÓN A 8 SEMANAS]\nEn 8 semanas siguiendo el plan",
  "golpe_definitivo": "Nombre épico estilo Dragon Ball para el golpe basado en {golpe_stat_label} (ej: Kamehameha de Bandeja, Remate del Infinito)",
  "descripcion_golpe": "Descripción cinematográfica de 2-3 frases estilo Dragon Ball del golpe {golpe_stat_label}, mencionando su poder destructivo, aura de energía y sensación de amenaza nivel {nivel_amenaza}. Sé espectacular y dramático."
}}
"""

FALLBACK_RESPONSE = {
    "descripcion_epica": "Jugador con potencial detectado. Análisis IA temporalmente no disponible.",
    "fortalezas": ["Técnica en desarrollo", "Actitud competitiva", "Potencial de mejora"],
    "debilidades": ["Análisis IA no disponible temporalmente"],
    "plan_mejora": "El servicio de IA está saturado o no disponible. Inténtalo de nuevo en unos minutos.",
    "golpe_definitivo": "Golpe en análisis",
    "descripcion_golpe": "El Scouter detecta un golpe definitivo en desarrollo. Análisis IA temporalmente no disponible.",
}


def analyze_player_with_ai(player_data: dict) -> dict:
    """
    Llama a Gemini para generar el análisis narrativo del jugador.
    Retorna un dict con el análisis estructurado.
    """
    prompt = ANALYSIS_PROMPT.format(**player_data)

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        raw_text = response.text.strip()

        # Limpiar posibles bloques markdown
        if raw_text.startswith("```"):
            lines = raw_text.split("\n")
            raw_text = "\n".join(lines[1:-1])

        return json.loads(raw_text)

    except json.JSONDecodeError as e:
        logger.warning("Gemini JSON parse error: %s", e)
        return FALLBACK_RESPONSE

    except Exception as e:
        error_str = str(e)
        logger.error("Gemini API error (%s): %s", type(e).__name__, error_str[:200])
        # Errores temporales — devolver fallback en lugar de crashear
        if any(code in error_str for code in ["503", "429", "UNAVAILABLE", "EXHAUSTED", "ServerError", "ClientError"]):
            return FALLBACK_RESPONSE
        raise RuntimeError(f"Error llamando a Gemini API: {e}")