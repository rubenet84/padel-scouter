"""
Generador de PDF para Padel Scouter.
Usa WeasyPrint para convertir HTML+CSS a PDF de alta calidad.

Uso desde FastAPI:
    from generate_pdf import generate_player_pdf
    pdf_bytes = generate_player_pdf(player_data, analysis_data)
"""
import math
import json
from datetime import datetime
from pathlib import Path


def get_nivel_amenaza_stars(power_level: int) -> str:
    """Genera estrellas SVG según el power level."""
    if power_level >= 9000:
        n = 7
    elif power_level >= 7500:
        n = 5
    elif power_level >= 4500:
        n = 3
    else:
        n = 1
    return ''.join(['<span class="star">★</span>' for _ in range(n)])


def calc_radar_points(stats: dict) -> str:
    """
    Calcula los puntos del hexágono radar.
    6 vértices: TÉCNICA, FÍSICO, ATAQUE, MENTAL, DEFENSA, TÁCTICA
    """
    cx, cy = 100, 87
    max_r = 72  # radio máximo (de centro a vértice exterior)

    # Valores normalizados 0-100 para cada eje
    derecha = stats.get('derecha', 50)
    volea   = (stats.get('volea_derecha', 50) + stats.get('volea_reves', 50)) / 2
    bandeja = stats.get('bandeja', 50)
    remate  = stats.get('remate', 50)
    velocidad = stats.get('velocidad', 50)
    tactica_st = stats.get('tactica', 50)

    values = [derecha, volea, bandeja, remate, velocidad, tactica_st]

    # Ángulos: empezar desde arriba (-90°) y girar 60° por vértice
    angles = [-90 + 60 * i for i in range(6)]
    points = []
    for val, angle in zip(values, angles):
        r = (val / 100) * max_r
        rad = math.radians(angle)
        x = cx + r * math.cos(rad)
        y = cy + r * math.sin(rad)
        points.append(f"{x:.1f},{y:.1f}")

    return ' '.join(points)


def calc_radar_dots(stats: dict) -> str:
    """Genera círculos en los vértices del radar."""
    cx, cy = 100, 87
    max_r = 72

    derecha = stats.get('derecha', 50)
    volea   = (stats.get('volea_derecha', 50) + stats.get('volea_reves', 50)) / 2
    bandeja = stats.get('bandeja', 50)
    remate  = stats.get('remate', 50)
    velocidad = stats.get('velocidad', 50)
    tactica_st = stats.get('tactica', 50)

    values = [derecha, volea, bandeja, remate, velocidad, tactica_st]
    angles = [-90 + 60 * i for i in range(6)]
    dots = []
    for val, angle in zip(values, angles):
        r = (val / 100) * max_r
        rad = math.radians(angle)
        x = cx + r * math.cos(rad)
        y = cy + r * math.sin(rad)
        dots.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="#7c5fd6" stroke="#fff" stroke-width="1.2"/>')

    return '\n'.join(dots)


def build_stat_rows(stat_list: list, stats: dict) -> str:
    """Genera HTML de filas de estadísticas con barras."""
    rows = []
    for label, key in stat_list:
        val = stats.get(key, 50)
        rows.append(f'''
        <div class="stat-row">
            <div class="stat-name">{label}</div>
            <div class="stat-bar-track">
                <div class="stat-bar-fill" style="width:{val}%;"></div>
            </div>
            <div class="stat-val">{val}</div>
        </div>''')
    return '\n'.join(rows)


def build_plan_checks(items: list, color: str) -> str:
    """Genera checks del plan de mejora."""
    return '\n'.join([f'<div class="plan-check {color}">{item}</div>' for item in items])


def generate_player_html(player: dict, analysis: dict) -> str:
    """
    Genera el HTML completo del informe a partir de los datos del jugador y análisis.

    Args:
        player: dict con campos del PlayerModel/PlayerPublicSchema
        analysis: dict con campos del AnalysisPublicSchema

    Returns:
        str: HTML completo listo para convertir a PDF
    """
    template = Path('app/templates/pdf/informe_jugador.html').read_text(encoding='utf-8')

    stats = {
        'derecha':      player.get('derecha', 50),
        'reves':        player.get('reves', 50),
        'volea_derecha': player.get('volea_derecha', 50),
        'volea_reves':  player.get('volea_reves', 50),
        'bandeja':      player.get('bandeja', 50),
        'vibora':       player.get('vibora', 50),
        'remate':       player.get('remate', 50),
        'globo':        player.get('globo', 50),
        'saque':        player.get('saque', 50),
        'bajada_pared': player.get('bajada_pared', 50),
        'velocidad':    player.get('velocidad', 50),
        'resistencia':  player.get('resistencia', 50),
        'reflejos':     player.get('reflejos', 50),
        'tactica':      player.get('tactica', 50),
        'presion':      player.get('presion', 50),
        'trabajo_en_pareja': player.get('trabajo_en_pareja', 50),
    }

    power_level = analysis.get('power_level', 0)
    torneos = player.get('torneos_jugados', 0)
    victorias = player.get('victorias', 0)
    win_rate = player.get('win_rate', '—')

    # Proyección: estimar mejora basada en plan de mejora
    proy_diff = max(100, round(power_level * 0.04))
    proy_num = min(9999, power_level + proy_diff)
    proy_num_display = f"{proy_num}+" if proy_num >= 9999 else str(proy_num)
    proy_diff = proy_num - power_level

    # Categoría display
    cat_map = {
        'INICIACION': 'Iniciación', 'QUINTA': '5ª Categoría',
        'CUARTA': '4ª Categoría', 'TERCERA': '3ª Categoría',
        'SEGUNDA': '2ª Categoría', 'PRIMERA': '1ª Categoría',
        'PRO': 'Profesional',
    }
    categoria = cat_map.get(player.get('category', ''), player.get('category', '—'))

    # ── Plan de mejora: parsear el texto de la IA ───────────────
    plan_intro = ""
    plan_titles = ['Fortaleza principal', 'Segunda fortaleza', 'Tercera fortaleza']
    plan_freqs = ['3 sesiones / semana', '2 sesiones / semana', '1 sesión / semana']
    plan_descs = ['', '', '']

    raw_plan = analysis.get('improvement_plan', '')
    if raw_plan:
        # Dividir por "---" para separar intro y objetivos
        parts = [p.strip() for p in raw_plan.split('---') if p.strip()]
        if len(parts) >= 1:
            plan_intro = parts[0]
        for i, part in enumerate(parts[1:4]):
            # Intentar extraer: [número] [título] [frecuencia] — [descripción]
            text = part.strip()
            # Extraer frecuencia si existe
            import re
            freq_match = re.search(r'(\d+\s*sesi[oó]n(?:es)?\s*/\s*semana)', text, re.IGNORECASE)
            if freq_match:
                plan_freqs[i] = freq_match.group(1)
                text = text.replace(freq_match.group(1), '').strip()
            # Extraer descripción tras "—" o "-"
            desc_parts = re.split(r'\s*[—–-]\s*', text, maxsplit=1)
            if len(desc_parts) > 1:
                plan_descs[i] = desc_parts[1].strip()[:300]
                text = desc_parts[0].strip()
            # Limpiar número inicial
            text = re.sub(r'^\d+[\.\)\-]?\s*', '', text).strip()
            plan_titles[i] = text[:60].upper() if text else plan_titles[i]

    # Usar strengths/weaknesses como fallback si no hay plan IA
    if not any(plan_descs):
        strengths = analysis.get('strengths', [])
        weaknesses = analysis.get('weaknesses', [])
        if isinstance(strengths, str): strengths = json.loads(strengths)
        if isinstance(weaknesses, str): weaknesses = json.loads(weaknesses)
        plan_titles = [
            strengths[0] if len(strengths) > 0 else 'Fortaleza principal',
            strengths[1] if len(strengths) > 1 else 'Segunda fortaleza',
            strengths[2] if len(strengths) > 2 else 'Tercera fortaleza',
        ]
        plan_descs = [
            weaknesses[0] if len(weaknesses) > 0 else 'Área de mejora principal.',
            weaknesses[1] if len(weaknesses) > 1 else 'Segunda área de mejora.',
            weaknesses[2] if len(weaknesses) > 2 else 'Tercera área de mejora.',
        ]

    # Pasar el intro del plan (sin los --- objetivos)
    improvement_plan_display = plan_intro if plan_intro else raw_plan[:500]

    # Perfil general basado en stats
    top_stat = max(stats, key=stats.get)
    stat_labels_perfil = {
        'remate': 'remate', 'bandeja': 'bandeja', 'vibora': 'víbora',
        'saque': 'servicio', 'derecha': 'derecha',
        'reves': 'revés', 'bajada_pared': 'bajada de pared', 'globo': 'globo',
        'volea_derecha': 'volea', 'volea_reves': 'volea',
    }
    top_label = stat_labels_perfil.get(top_stat, top_stat)
    perfil = f"Jugador de {categoria.lower()} con {stats[top_stat]}/100 en {top_label} como golpe más destacado. Win rate del {win_rate} en {torneos} torneos disputados."

    # Stats rows
    stats_tecnica = build_stat_rows([
        ('Derecha', 'derecha'), ('Revés', 'reves'),
        ('Volea Der.', 'volea_derecha'), ('Volea Rev.', 'volea_reves'),
        ('Bandeja', 'bandeja'), ('Víbora', 'vibora'), ('Remate', 'remate'),
        ('Globo', 'globo'), ('Saque', 'saque'), ('Bajada de pared', 'bajada_pared'),
    ], stats)

    stats_fisico = build_stat_rows([
        ('Velocidad', 'velocidad'), ('Resistencia', 'resistencia'), ('Reflejos', 'reflejos'),
    ], stats)

    stats_mental = build_stat_rows([
        ('Táctica', 'tactica'), ('Presión', 'presion'), ('Trabajo en pareja', 'trabajo_en_pareja'),
    ], stats)

    # Reemplazar placeholders
    html = template
    def get_initials(name):
        parts = name.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        return (name[:2]).upper() if name else '??'

    avatar_html = '<div class="hero-photo">🎾</div>'
    avatar_url = player.get('avatar_url')
    if avatar_url:
        fpath = Path("app") / avatar_url.lstrip("/")
        if fpath.exists():
            avatar_html = f'<div class="hero-photo"><img src="file:///{fpath.resolve()}" alt=""></div>'
        else:
            initials = get_initials(player.get('name', '?'))
            avatar_html = f'<div class="hero-photo" style="display:flex;align-items:center;justify-content:center;font-size:36px;font-weight:900;color:#7c5fd6;">{initials}</div>'
    else:
        initials = get_initials(player.get('name', '?'))
        avatar_html = f'<div class="hero-photo" style="display:flex;align-items:center;justify-content:center;font-size:36px;font-weight:900;color:#7c5fd6;">{initials}</div>'

    replacements = {
        '{{FECHA}}':          datetime.now().strftime('%d/%m/%Y'),
        '{{AVATAR}}':         avatar_html,
        '{{NOMBRE}}':         player.get('name', 'Jugador').upper(),
        '{{CATEGORIA}}':      categoria.upper(),
        '{{POWER_LEVEL}}':    str(power_level),
        '{{STARS}}':          get_nivel_amenaza_stars(power_level),
        '{{MANO}}':           player.get('mano', 'Derecha'),
        '{{TORNEOS}}':        str(torneos),
        '{{VICTORIAS}}':      str(victorias),
        '{{WIN_RATE}}':       win_rate,
        '{{PTS_FEP}}':        str(player.get('puntos_ranking_fep', 0)),
        '{{PERFIL_GENERAL}}': perfil,
        '{{RADAR_POINTS}}':   calc_radar_points(stats),
        '{{RADAR_DOTS}}':     calc_radar_dots(stats),
        '{{STATS_TECNICA}}':  stats_tecnica,
        '{{STATS_FISICO}}':   stats_fisico,
        '{{STATS_MENTAL}}':   stats_mental,
        '{{AI_DESCRIPTION}}': analysis.get('ai_description', 'Análisis no disponible.'),
        '{{IMPROVEMENT_PLAN}}': improvement_plan_display,
        '{{PLAN1_TITULO}}':   plan_titles[0][:60].upper(),
        '{{PLAN1_FREQ}}':     plan_freqs[0],
        '{{PLAN1_DESC}}':     plan_descs[0],
        '{{PLAN1_CHECKS}}':   build_plan_checks(['Sesiones enfocadas', 'Práctica específica', 'Seguimiento semanal'], 'purple'),
        '{{PLAN2_TITULO}}':   plan_titles[1][:60].upper(),
        '{{PLAN2_FREQ}}':     plan_freqs[1],
        '{{PLAN2_DESC}}':     plan_descs[1],
        '{{PLAN2_CHECKS}}':   build_plan_checks(['Análisis de partidos', 'Situaciones de presión', 'Control emocional'], 'blue'),
        '{{PLAN3_TITULO}}':   plan_titles[2][:60].upper(),
        '{{PLAN3_FREQ}}':     plan_freqs[2],
        '{{PLAN3_DESC}}':     plan_descs[2],
        '{{PLAN3_CHECKS}}':   build_plan_checks(['Técnica específica', 'Variedad de golpes', 'Efectos y velocidad'], 'orange'),
        '{{PROY_NUM}}':       str(proy_num_display),
        '{{PROY_DIFF}}':      str(proy_diff),
    }

    for placeholder, value in replacements.items():
        html = html.replace(placeholder, str(value))

    return html


def generate_player_pdf(player: dict, analysis: dict) -> bytes:
    """
    Genera el PDF como bytes.
    
    Returns:
        bytes: PDF listo para enviar como response o guardar.
    """
    from weasyprint import HTML
    html_content = generate_player_html(player, analysis)
    pdf_bytes = HTML(string=html_content, base_url=str(Path.cwd())).write_pdf()
    return pdf_bytes


# ── Test local ────────────────────────────────────────────────
if __name__ == '__main__':
    # Datos de ejemplo para probar
    test_player = {
        'name': 'Rubén Rebollo Rua',
        'category': 'PRIMERA',
        'derecha': 80, 'reves': 90, 'volea_derecha': 85, 'bandeja': 85,
        'vibora': 80, 'remate': 95, 'globo': 85, 'saque': 100,
        'bajada_pared': 95, 'velocidad': 85, 'resistencia': 75,
        'reflejos': 85, 'tactica': 80, 'presion': 80,
        'trabajo_en_pareja': 90, 'torneos_jugados': 15,
        'victorias': 12, 'puntos_ranking_fep': 1500,
    }
    test_analysis = {
        'power_level': 8999,
        'ai_description': 'Un aura de poder inconfundible emana de este jugador, cuyo Poder de Combate lo sitúa entre la élite. Su presencia en la pista es la de un depredador aéreo, un maestro del remate y el servicio, capaz de desatar una devastación sin precedentes que perfora cualquier defensa.',
        'improvement_plan': 'Para trascender y romper la barrera de los 9000 puntos de poder, es crucial fortalecer los cimientos físicos y pulir la mente estratégica. Un enfoque intensivo en la resistencia y la adaptabilidad táctica desbloqueará el verdadero potencial.',
        'strengths': ['Saque devastador que quiebra la resistencia inicial del rival', 'Bajada de pared quirúrgica', 'Reflejos sobrehumanos en la red'],
        'weaknesses': ['Resistencia física mejorable para batallas maratonianas', 'Revés como punto de ataque potencial para los más astutos'],
    }

    html = generate_player_html(test_player, test_analysis)
    Path('/home/claude/test_informe.html').write_text(html, encoding='utf-8')

    pdf = generate_player_pdf(test_player, test_analysis)
    Path('/home/claude/test_informe.pdf').write_bytes(pdf)
    print(f"PDF generado: {len(pdf):,} bytes")
