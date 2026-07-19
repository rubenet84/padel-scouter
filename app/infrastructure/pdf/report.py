"""ReportLab PDF — reliable, no system deps, professional output."""
import json, re
from io import BytesIO
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors as rc
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
from reportlab.graphics.shapes import Drawing, Rect

W, H = A4
M = 18*mm
INNER = W - 2*M

PURPLE   = rc.HexColor("#7c5fd6")
LIGHT    = rc.HexColor("#a78bfa")
DARK     = rc.HexColor("#1e1b4b")
GRAY     = rc.HexColor("#64748b")
LGRAY    = rc.HexColor("#f1f5f9")
WHITE    = rc.white
BLACK    = rc.HexColor("#0f172a")
YELLOW   = rc.HexColor("#eab308")
BLUE     = rc.HexColor("#0ea5e9")
GREEN    = rc.HexColor("#22c55e")
RED      = rc.HexColor("#ef4444")
BORDER   = rc.HexColor("#e5e7eb")

STATS = {
    "derecha":"Derecha","reves":"Revés","volea_derecha":"Volea Der.","volea_reves":"Volea Rev.",
    "bandeja":"Bandeja","vibora":"Víbora","remate":"Remate","globo":"Globo","saque":"Saque",
    "bajada_pared":"Bajada Pared","velocidad":"Velocidad","resistencia":"Resistencia","reflejos":"Reflejos",
    "tactica":"Táctica","presion":"Presión","trabajo_en_pareja":"Trab. Pareja",
}

def S(h=4): return Spacer(1, h*mm)
def HR(): return HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=5*mm, spaceBefore=3*mm)

def H1(t): return Paragraph(t, ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=16, textColor=PURPLE, spaceAfter=4*mm, spaceBefore=8*mm))
def H2(t): return Paragraph(t, ParagraphStyle("H2", fontName="Helvetica-Bold", fontSize=12, textColor=DARK, spaceAfter=3*mm, spaceBefore=4*mm))
def H3(t,c=PURPLE): return Paragraph(f'<font color="{c.hexval()}">{t}</font>', ParagraphStyle("H3", fontName="Helvetica-Bold", fontSize=11, textColor=c, spaceAfter=3*mm, spaceBefore=4*mm))
def BODY(t): return Paragraph(t, ParagraphStyle("Body", fontName="Helvetica", fontSize=9, textColor=BLACK, leading=14, spaceAfter=2*mm))
def MUTED(t): return Paragraph(t, ParagraphStyle("Muted", fontName="Helvetica", fontSize=8, textColor=GRAY, leading=12))

def stat_bar(name, val, color):
    pct = max(0, min(1, (val or 0)/100))
    row = Table([[
        Paragraph(name, ParagraphStyle("SN", fontName="Helvetica", fontSize=9, textColor=BLACK, leading=12)),
        Paragraph(str(val), ParagraphStyle("SV", fontName="Helvetica-Bold", fontSize=9, textColor=BLACK, alignment=2, leading=12)),
    ]], colWidths=[48*mm, 14*mm])
    row.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE"),("TOPPADDING",(0,0),(-1,-1),1),("BOTTOMPADDING",(0,0),(-1,-1),1)]))
    d = Drawing(170*mm, 7*mm)
    d.add(Rect(62*mm, 1.5*mm, 105*mm, 4.5*mm, fillColor=LGRAY, strokeColor=None, rx=2, ry=2))
    if pct > 0:
        d.add(Rect(62*mm, 1.5*mm, 105*mm*pct, 4.5*mm, fillColor=color, strokeColor=None, rx=2, ry=2))
    return [row, d]


def build_report(player_dict, analysis_dict):
    buf = BytesIO()

    def page_bg(c, doc):
        c.saveState()
        c.setStrokeColor(PURPLE); c.setLineWidth(1.5)
        c.line(M, H-14*mm, W-M, H-14*mm)
        c.setFillColor(GRAY); c.setFont("Helvetica", 7)
        c.drawString(M, H-21*mm, "PADEL SCOUTER · INFORME DE SCOUTING")
        c.drawRightString(W-M, H-21*mm, datetime.now(timezone.utc).strftime("%d/%m/%Y"))
        c.setFont("Helvetica", 7); c.setFillColor(GRAY)
        c.drawCentredString(W/2, 10*mm, f"Pág. {c.getPageNumber()}")
        c.restoreState()

    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=M, rightMargin=M, topMargin=18*mm, bottomMargin=18*mm)
    E = []
    cat = player_dict.get("category", "—")
    pl = analysis_dict.get("power_level", 0)
    strengths = analysis_dict.get("strengths", []) or []
    weaknesses = analysis_dict.get("weaknesses", []) or []
    avatar = player_dict.get("avatar_url")
    name = player_dict.get("name", "Jugador").upper()

    TEC = ["derecha","reves","volea_derecha","volea_reves","bandeja","vibora","remate","globo","saque","bajada_pared"]
    FIS = ["velocidad","resistencia","reflejos"]
    MEN = ["tactica","presion","trabajo_en_pareja"]

    if isinstance(strengths, str): strengths = json.loads(strengths)
    if isinstance(weaknesses, str): weaknesses = json.loads(weaknesses)

    # ═══════════ PAGE 1: HERO ═══════════
    E += [S(6), Paragraph("INFORME DE SCOUTING", ParagraphStyle("Sub", fontName="Helvetica", fontSize=10, textColor=GRAY, alignment=1, letterSpacing=4, spaceAfter=4*mm))]
    # Avatar
    if avatar:
        E.append(Paragraph(f'<img src="{avatar}" width="60" height="60"/>', ParagraphStyle("Av", alignment=1, spaceAfter=4*mm)))
    else:
        E.append(Paragraph(f'<font size="36" color="#7c5fd6">{name[:2]}</font>', ParagraphStyle("AvInit", alignment=1, spaceAfter=4*mm)))
    E.append(Paragraph(name, ParagraphStyle("Hero", fontName="Helvetica-Bold", fontSize=36, textColor=BLACK, alignment=1, leading=42, spaceAfter=2*mm)))
    if pl:
        E.append(Paragraph(str(pl), ParagraphStyle("Power", fontName="Helvetica-Bold", fontSize=64, textColor=PURPLE, alignment=1, leading=70)))
        E.append(Paragraph("POWER LEVEL", ParagraphStyle("PLabel", fontName="Helvetica", fontSize=10, textColor=GRAY, alignment=1, letterSpacing=6, spaceAfter=3*mm)))
    E.append(Paragraph(cat.upper(), ParagraphStyle("Cat", fontName="Helvetica-Bold", fontSize=14, textColor=PURPLE, alignment=1, spaceAfter=10*mm)))
    E.append(HR())

    # Summary
    E.append(H2("RESUMEN"))
    E.append(BODY(f'<font color="#64748b">Categoría:</font> <b>{cat}</b>'))
    if pl: E.append(BODY(f'<font color="#64748b">Power Level:</font> <b>{pl}</b>'))

    # Strengths + Weaknesses
    if strengths or weaknesses:
        E.append(S(2))
        if strengths:
            E.append(H3("🏆 FORTALEZAS", GREEN))
            for s in strengths[:3]: E.append(BODY(f'<font color="#22c55e">▸</font> {s}'))
        if weaknesses:
            E.append(H3("⚠ DEBILIDADES", RED))
            for w in weaknesses[:3]: E.append(BODY(f'<font color="#ef4444">▸</font> {w}'))

    # ═══════════ PAGE 2: STATS ═══════════
    E += [S(4), HR(), H1("ESTADÍSTICAS")]
    for lbl, keys, clr in [("⚡ TÉCNICA", TEC, YELLOW), ("💪 FÍSICO", FIS, BLUE), ("🧠 MENTAL", MEN, GREEN)]:
        E.append(H3(lbl, clr))
        for k in keys:
            v = player_dict.get(k, 0) or 0
            E.extend(stat_bar(STATS.get(k, k.replace("_"," ").title()), v, clr))
        E.append(S(1))

    # ═══════════ PAGE 3: AI ═══════════
    ai = analysis_dict.get("ai_description", "")
    plan = analysis_dict.get("improvement_plan", "")
    if ai or plan:
        E += [S(4), HR(), H1("ANÁLISIS IA")]
        if ai:
            clean = re.sub(r"<[^>]+>", " ", ai); clean = re.sub(r"\s+", " ", clean).strip()
            for p in clean.split(". "):
                if p.strip(): E.append(BODY(p.strip()+"."))
        if plan:
            E += [S(2), H1("PLAN DE MEJORA")]
            clean = re.sub(r"<[^>]+>", " ", plan); clean = re.sub(r"\s+", " ", clean).strip()
            E.append(BODY(clean[:2000]))

    # Projection
    if pl:
        E += [S(4), HR(), H1("PROYECCIÓN")]
        proj = pl + max(100, round(pl*0.04))
        E.append(Paragraph(f'<font size="28" color="#7c5fd6"><b>{pl}</b></font>  <font size="28" color="#cbd5e1">→</font>  <font size="28" color="#22c55e"><b>{proj}</b></font>',
            ParagraphStyle("Proj", alignment=1, spaceBefore=2*mm)))
        E.append(Paragraph(f'+{proj-pl} pts estimados', ParagraphStyle("PE", fontName="Helvetica", fontSize=9, textColor=GRAY, alignment=1)))

    doc.build(E, onFirstPage=page_bg, onLaterPages=page_bg)
    buf.seek(0)
    return buf
