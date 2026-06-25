import json
from google import genai
from google.genai import types
from app.core.config import settings


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
- Volea: {volea}
- Bandeja: {bandeja}
- Víbora: {vibora}
- Smash: {smash}
- Lob: {lob}
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

HISTORIAL COMPETITIVO:
- Torneos jugados: {torneos_jugados}
- Victorias: {victorias}
- Puntos ranking FEP: {puntos_ranking_fep}

Responde ÚNICAMENTE con un JSON válido con esta estructura exacta:
{{
  "descripcion_epica": "Descripción narrativa épica del jugador (2-3 frases emocionantes)",
  "fortalezas": ["fortaleza 1", "fortaleza 2", "fortaleza 3"],
  "debilidades": ["debilidad 1", "debilidad 2"],
  "plan_mejora": "Plan de mejora específico y detallado para subir al siguiente nivel",
  "golpe_definitivo": "El golpe más característico y peligroso de este jugador",
  "nivel_amenaza": "BAJO | MEDIO | ALTO | EXTREMO"
}}
"""


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

    except json.JSONDecodeError:
        return {
            "descripcion_epica": f"Jugador de categoría {player_data['category']} con gran potencial.",
            "fortalezas": ["Técnica sólida", "Buen físico", "Mentalidad competitiva"],
            "debilidades": ["Necesita más experiencia competitiva"],
            "plan_mejora": "Participar en más torneos y trabajar los golpes defensivos.",
            "golpe_definitivo": "Por determinar",
            "nivel_amenaza": "MEDIO",
        }
    except Exception as e:
        raise RuntimeError(f"Error llamando a Gemini API: {e}")