import sys
import json
import os
import textwrap
import time
import csv
import re
from datetime import datetime, timezone, timedelta

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import zoneinfo
except ImportError:
    zoneinfo = None
import requests
from PIL import Image, ImageDraw, ImageFont

def obtener_zona_argentina():
    """Retorna la zona horaria oficial de Argentina (America/Argentina/Buenos_Aires)."""
    if zoneinfo is not None:
        try:
            return zoneinfo.ZoneInfo("America/Argentina/Buenos_Aires")
        except Exception:
            pass
    return timezone(timedelta(hours=-3))

def obtener_paleta_editorial(post, es_efemeride_hoy=False):
    """
    Determina la paleta cromática y la etiqueta de portada según la jerarquía editorial:
    1. Modo Efeméride (Prioridad 1): Dorado / Ámbar (245, 158, 11)
    2. Modo Fin de Semana (Prioridad 2): Sábado (5) o Domingo (6) -> Verde Esmeralda (16, 185, 129)
    3. Modo Estándar Lunes a Viernes (Por defecto) -> Celeste Eléctrico HDE (14, 165, 233)
    """
    tz_ar = obtener_zona_argentina()
    ahora_ar = datetime.now(tz_ar)
    fecha_hist = post.get("fecha_historica", "") if isinstance(post, dict) else str(post)
    categoria = post.get("categoria", "HISTORIA ECONÓMICA").upper() if isinstance(post, dict) else "HISTORIA ECONÓMICA"

    if es_efemeride_hoy:
        return {
            "tipo": "efemeride",
            "color_acento": (245, 158, 11),       # Dorado / Ámbar
            "color_acento_sec": (14, 165, 233),   # Celeste secundario
            "color_tarjeta": (25, 23, 21),
            "color_tarjeta_alt": (30, 27, 23),
            "borde_tarjeta": (76, 60, 34),
            "etiqueta_portada": f"TAL DÍA COMO HOY  ·  {fecha_hist.upper()}"
        }

    if ahora_ar.weekday() in (5, 6):
        return {
            "tipo": "fin_de_semana",
            "color_acento": (16, 185, 129),       # Verde Esmeralda editorial
            "color_acento_sec": (245, 158, 11),   # Dorado secundario
            "color_tarjeta": (17, 26, 25),
            "color_tarjeta_alt": (21, 31, 30),
            "borde_tarjeta": (38, 66, 56),
            "etiqueta_portada": f"{categoria}  ·  {fecha_hist.upper()}"
        }

    return {
        "tipo": "estandar",
        "color_acento": (14, 165, 233),           # Celeste Eléctrico HDE
        "color_acento_sec": (245, 158, 11),       # Dorado secundario
        "color_tarjeta": (19, 24, 34),
        "color_tarjeta_alt": (23, 29, 41),
        "borde_tarjeta": (45, 58, 78),
        "etiqueta_portada": f"{categoria}  ·  {fecha_hist.upper()}"
    }

def limpiar_secreto(val: str) -> str:
    s = val.strip().strip("\"'").strip()
    if s.lower().startswith("bearer "):
        s = s[7:].strip()
    return s

IG_USER_ID = limpiar_secreto(os.environ.get("IG_USER_ID", ""))
IG_ACCESS_TOKEN = limpiar_secreto(os.environ.get("IG_ACCESS_TOKEN", ""))
IMGBB_API_KEY = limpiar_secreto(os.environ.get("IMGBB_API_KEY", ""))

X_API_KEY = limpiar_secreto(os.environ.get("X_API_KEY", ""))
X_API_SECRET = limpiar_secreto(os.environ.get("X_API_SECRET", ""))
X_ACCESS_TOKEN = limpiar_secreto(os.environ.get("X_ACCESS_TOKEN", ""))
X_ACCESS_SECRET = limpiar_secreto(os.environ.get("X_ACCESS_SECRET", ""))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def obtener_fuente(tipo="sans", tamano=40):
    """Carga fuentes del repositorio (Oswald) y fallbacks nativos de Linux/Windows."""
    rutas_repo = {
        "oswald_bold": os.path.join(BASE_DIR, "assets", "fonts", "Oswald-Bold.ttf"),
        "oswald_reg": os.path.join(BASE_DIR, "assets", "fonts", "Oswald-Regular.ttf"),
    }
    rutas_linux = {
        "oswald_bold": rutas_repo["oswald_bold"],
        "oswald_reg": rutas_repo["oswald_reg"],
        "sans_bold": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "serif_bold": "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "sans": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    }
    rutas_windows = {
        "oswald_bold": rutas_repo["oswald_bold"],
        "oswald_reg": rutas_repo["oswald_reg"],
        "sans_bold": "C:/Windows/Fonts/arialbd.ttf",
        "serif_bold": "C:/Windows/Fonts/georgiab.ttf",
        "sans": "C:/Windows/Fonts/arial.ttf",
    }
    for ruta in [
        rutas_repo.get(tipo),
        rutas_linux.get(tipo),
        rutas_windows.get(tipo),
        rutas_linux.get("sans_bold" if "bold" in tipo else "sans"),
        rutas_windows.get("sans_bold" if "bold" in tipo else "sans"),
    ]:
        if ruta and os.path.exists(ruta):
            try:
                return ImageFont.truetype(ruta, tamano)
            except IOError:
                pass
    return ImageFont.load_default()

# ========================================================
# CORTAFUEGOS DE PRIVACIDAD DE ÚLTIMA MILLA (MODO LOW PROFILE)
# ========================================================
import base64

_B64_PATRON_ID = b"XGIoZ2FzcGFyfHRyZXBbYcOhXXxnYXNwaSg/OnRyZTk5fHRyZSk/KVxifGdhc3BhclwnP3M/XHMqbm90aW9ufFxibWlccytjYW5hbFxifFxibWlccytpbnZlc3RpZ2FjaVtvw7Ndblxi"
REGEX_PATRONES_IDENTIDAD = re.compile(
    base64.b64decode(_B64_PATRON_ID).decode("utf-8"),
    re.IGNORECASE
)

_REEMPLAZOS_RAW = [
    (b"Z2FzcGFyXCc/cz9ccypub3Rpb24=", "Archivo Editorial HDE"),
    (b"XGJwb3JccytnYXNwYXIoXHMrdHJlcFthw6FdKT9cYg==", "por el Equipo Editorial HDE"),
    (b"XGJkZVxzK2dhc3Bhcihccyt0cmVwW2HDoV0pP1xi", "del Equipo Editorial HDE"),
    (b"XGJpbnZlc3RpZ2FjaVtvw7NdblxzK2RlXHMrZ2FzcGFyKFxzK3RyZXBbYcOhXSk/XGI=", "investigación del Equipo Editorial HDE"),
    (b"XGJnYXNwYXJccyt0cmVwW2HDoV1cYg==", "Equipo Editorial HDE"),
    (b"XGJnYXNwYXJcYg==", "Equipo Editorial HDE"),
    (b"XGJnYXNwaXRyZSg5OSk/XGI=", "hablemosdeeco"),
    (b"XGJnYXNwaVxi", "hablemosdeeco"),
    (b"XGJ0cmVwYVxzK2FccytjYXNpXGI=", "asciende a casi"),
    (b"XGJ0cmVwYVxzK2FsXGI=", "asciende al"),
    (b"XGJ0cmVwYVxzK2FcYg==", "asciende a"),
    (b"XGJhbFxzK3RyZXBhclxzK2FsXGI=", "al saltar al"),
    (b"XGJhbFxzK3RyZXBhclxzK2FcYg==", "al saltar a"),
    (b"XGJ0cmVwYXJcYg==", "escalar"),
    (b"XGJ0cmVwW2HDoV1cYg==", "asciende"),
    (b"XGJtaVxzK2NhbmFsXGI=", "nuestro canal"),
    (b"XGJtaXNccytndWlvbmVzXGI=", "nuestros informes"),
    (b"XGJtaVxzK2ludmVzdGlnYWNpW2/Ds11uXGI=", "nuestra investigación"),
    (b"XGJpbnZlc3RpZ3VbZcOpXVxi", "analizamos"),
    (b"XGJtaVxzK2N1ZW50YVxi", "nuestra cuenta"),
]

PATRONES_REEMPLAZO_CALIENTE = [
    (re.compile(base64.b64decode(b_pat).decode("utf-8"), re.IGNORECASE), repl)
    for b_pat, repl in _REEMPLAZOS_RAW
]

PATRON_PRIMERA_PERSONA = re.compile(
    r"\b(yo|conmigo|investigué|escribí|hice)\b|\b(mi|mis)\s+(canal|video|guion|investigaci[oó]n|redacci[oó]n|opini[oó]n|criterio)\b",
    re.IGNORECASE,
)

CAMPOS_TEXTO_POST = [
    "titular", "cifra_hero", "etiqueta_cifra", "teaser_portada",
    "dato_clave", "fuente_oficial", "tipo_valor", "titulo_contexto",
    "subtitulo_b1", "bloque_1", "subtitulo_b2", "bloque_2",
    "pregunta_debate", "bajada_debate", "youtube_titulo", "palabra_clave",
    "caption", "origen_guion", "fecha_historica", "categoria",
]


def validar_y_sanitizar_post(post: dict) -> dict:
    """
    Cortafuegos de Privacidad de Última Milla.
    Inspecciona y sanitiza todos los campos de texto del post para garantizar 0
    filtraciones de identidad personal antes de dibujar en Pillow o publicar en Instagram.
    """
    if not isinstance(post, dict):
        return post

    for c in CAMPOS_TEXTO_POST:
        val = post.get(c, "")
        if isinstance(val, str) and (REGEX_PATRONES_IDENTIDAD.search(val) or PATRON_PRIMERA_PERSONA.search(val)):
            val_limpio = val
            for pat, repl in PATRONES_REEMPLAZO_CALIENTE:
                val_limpio = pat.sub(repl, val_limpio)
            post[c] = val_limpio

            if REGEX_PATRONES_IDENTIDAD.search(post[c]) or PATRON_PRIMERA_PERSONA.search(post[c]):
                raise ValueError(
                    f"CRITICAL PRIVACY ALERT: Intento de publicar rastro de identidad personal en campo '{c}'. Publicación abortada."
                )
    return post


def _wrap_px(draw, text: str, font, max_width_px: int) -> list[str]:
    """Envuelve texto midiendo ancho real en píxeles para evitar desbordes."""
    words = str(text or "").split()
    lines, curr = [], ""
    for w in words:
        test = f"{curr} {w}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width_px:
            curr = test
        else:
            if curr:
                lines.append(curr)
            curr = w
    if curr:
        lines.append(curr)
    return lines


def _fit_font_px(draw, text: str, tipo: str, max_width_px: int, start_size: int, min_size: int = 20):
    """Ajusta el tamaño de fuente hacia abajo solo si una línea única supera max_width_px."""
    size = start_size
    while size > min_size:
        f = obtener_fuente(tipo, size)
        bbox = draw.textbbox((0, 0), str(text or ""), font=f)
        if bbox[2] - bbox[0] <= max_width_px:
            return f
        size -= 2
    return obtener_fuente(tipo, min_size)


def _draw_wrapped_px(draw, text: str, x: int, y: int, font, fill, max_width_px: int, line_spacing: int) -> tuple[int, int]:
    lines = _wrap_px(draw, text, font, max_width_px)
    curr_y = y
    for line in lines:
        draw.text((x, curr_y), line, font=font, fill=fill)
        curr_y += line_spacing
    return curr_y, len(lines)


def _draw_grid_bg(img, width: int, height: int, step: int = 90):
    draw = ImageDraw.Draw(img)
    grid_color = (20, 25, 34)
    for x in range(0, width, step):
        draw.line([(x, 0), (x, height)], fill=grid_color, width=1)
    for y in range(0, height, step):
        draw.line([(0, y), (width, y)], fill=grid_color, width=1)
    return draw


def _draw_brand_diamond(draw, cx: int, cy: int, r: int, color):
    draw.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=color)


def _draw_vector_arrow(draw, x: int, y: int, color, size: int = 14):
    draw.line([(x, y), (x + int(size * 1.4), y)], fill=color, width=3)
    draw.polygon([
        (x + int(size * 1.4) + 2, y),
        (x + int(size * 0.85), y - int(size * 0.5)),
        (x + int(size * 0.85), y + int(size * 0.5)),
    ], fill=color)


def _draw_header(draw, slide_num: int, total_slides: int, accent, muted):
    f_brand = obtener_fuente("oswald_bold", 26)
    f_num = obtener_fuente("sans_bold", 22)

    _draw_brand_diamond(draw, 102, 92, 10, accent)
    draw.text((126, 75), "HABLEMOS DE ECONOMÍA", font=f_brand, fill=(241, 245, 249))

    dot_x_start = 835
    for i in range(1, total_slides + 1):
        cx = dot_x_start + (i - 1) * 22
        r = 5 if i == slide_num else 4
        col = accent if i == slide_num else (55, 65, 81)
        draw.ellipse([(cx - r, 92 - r), (cx + r, 92 + r)], fill=col)

    draw.text((938, 79), f"{slide_num}/{total_slides}", font=f_num, fill=muted)


def _draw_footer_cta(draw, text: str, accent, card_bg, border, show_arrow: bool = True):
    f_cta = _fit_font_px(draw, text, "oswald_bold", 760 if show_arrow else 840, 25, 19)
    draw.rounded_rectangle([(90, 1185), (990, 1265)], radius=14, fill=card_bg, outline=border, width=2)
    draw.text((125, 1207), text, font=f_cta, fill=accent)
    if show_arrow:
        bbox = draw.textbbox((125, 1207), text, font=f_cta)
        _draw_vector_arrow(draw, bbox[2] + 22, 1225, accent, size=14)


def _extract_year(fecha_str: str) -> str:
    m = re.search(r"\b(1[89]\d{2}|20\d{2})\b", str(fecha_str or ""))
    return m.group(1) if m else ""


def crear_placas_carrusel(post_o_fecha, titular=None, dato_clave=None, es_efemeride_hoy=False, prefijo_archivo="slide"):
    """
    Genera el carrusel editorial HDE (4 placas en formato V2: Portada, Dato Clave, Contexto 01/02 y Debate/CTA).
    Mantiene retrocompatibilidad si recibe strings sueltos o un post V1 sin campos de contexto.
    """
    if isinstance(post_o_fecha, dict):
        post = validar_y_sanitizar_post(dict(post_o_fecha))
    else:
        post = validar_y_sanitizar_post({
            "fecha_historica": str(post_o_fecha),
            "titular": str(titular or ""),
            "dato_clave": str(dato_clave or ""),
        })

    fecha = post.get("fecha_historica", "")
    titular_txt = post.get("titular", "")
    dato_txt = post.get("dato_clave", "")
    caption_raw = post.get("caption", "")
    parrafos_cap = [p.strip() for p in caption_raw.split("\n\n") if p.strip()] if caption_raw else []

    paleta = obtener_paleta_editorial(post, es_efemeride_hoy=es_efemeride_hoy)
    accent = paleta["color_acento"]
    accent_sec = paleta["color_acento_sec"]
    card_bg = paleta["color_tarjeta"]
    card_bg_alt = paleta["color_tarjeta_alt"]
    border = paleta["borde_tarjeta"]
    etiqueta_portada = paleta["etiqueta_portada"]

    W, H = 1080, 1350
    bg = (11, 13, 18)
    white = (248, 250, 252)
    off_white = (218, 226, 238)
    muted = (140, 154, 175)
    subtle_year = (26, 33, 46)

    f_cat = obtener_fuente("sans_bold", 22)
    f_label = obtener_fuente("oswald_bold", 24)
    f_source = obtener_fuente("sans", 21)

    anio = str(post.get("anio") or _extract_year(fecha)).strip()
    cifra_hero = str(post.get("cifra_hero") or anio or fecha.upper()).strip()
    etiqueta_cifra = str(post.get("etiqueta_cifra") or post.get("tipo_valor") or "DATO CLAVE VERIFICADO").upper().strip()
    teaser = str(post.get("teaser_portada") or (parrafos_cap[0] if parrafos_cap else dato_txt)).strip()

    bloque_1 = str(post.get("bloque_1") or (parrafos_cap[0] if len(parrafos_cap) > 0 else "")).strip()
    bloque_2 = str(post.get("bloque_2") or (parrafos_cap[1] if len(parrafos_cap) > 1 else "")).strip()
    has_slide_3 = bool(bloque_1 and bloque_2)
    total_slides = 4 if has_slide_3 else 3

    rutas_salida = []

    # ==========================
    # SLIDE 1: PORTADA GANCHO
    # ==========================
    img1 = Image.new("RGB", (W, H), bg)
    d1 = _draw_grid_bg(img1, W, H)
    _draw_header(d1, 1, total_slides, accent, muted)

    if anio:
        f_yr = obtener_fuente("oswald_bold", 128)
        yr_box = d1.textbbox((0, 0), anio, font=f_yr)
        yr_w = yr_box[2] - yr_box[0]
        d1.text((990 - yr_w, 128), anio, font=f_yr, fill=subtle_year)

    f_pill = _fit_font_px(d1, etiqueta_portada, "sans_bold", 845, 22, 16)
    cat_bbox = d1.textbbox((0, 0), etiqueta_portada, font=f_pill)
    pill_w = min(900, (cat_bbox[2] - cat_bbox[0]) + 44)
    d1.rounded_rectangle([(90, 175), (90 + pill_w, 227)], radius=10, fill=card_bg, outline=accent, width=2)
    d1.text((112, 188), etiqueta_portada, font=f_pill, fill=accent)

    # Titular autoajustado para no invadir la tarjeta inferior
    t_size = 72
    while t_size > 54:
        f_title = obtener_fuente("oswald_bold", t_size)
        t_lines = _wrap_px(d1, titular_txt, f_title, 880)
        line_sp = int(t_size * 1.18)
        if 268 + len(t_lines) * line_sp <= 565:
            break
        t_size -= 4
    f_title = obtener_fuente("oswald_bold", t_size)
    y_after_title, _ = _draw_wrapped_px(d1, titular_txt, 90, 268, f_title, white, 880, int(t_size * 1.18))

    bar_y = y_after_title + 24
    d1.rounded_rectangle([(90, bar_y), (210, bar_y + 7)], radius=4, fill=accent)

    hook_y = max(bar_y + 42, 625)
    hook_bottom = 1135
    d1.rounded_rectangle([(90, hook_y), (990, hook_bottom)], radius=20, fill=card_bg, outline=border, width=2)
    d1.rounded_rectangle([(116, hook_y + 30), (124, hook_bottom - 30)], radius=4, fill=accent)

    f_lbl_hero = _fit_font_px(d1, etiqueta_cifra, "oswald_bold", 800, 24, 18)
    d1.text((155, hook_y + 38), etiqueta_cifra, font=f_lbl_hero, fill=muted)

    f_hero = _fit_font_px(d1, cifra_hero, "oswald_bold", 800, 82, 50)
    d1.text((155, hook_y + 80), cifra_hero, font=f_hero, fill=accent)

    f_teaser = obtener_fuente("sans", 32)
    _draw_wrapped_px(d1, teaser, 155, hook_y + 195, f_teaser, off_white, 790, 46)

    _draw_footer_cta(d1, "DESLIZÁ PARA VER QUÉ PASÓ", accent, card_bg, border, show_arrow=True)

    ruta_s1 = f"{prefijo_archivo}_1_portada.jpg"
    img1.save(ruta_s1, quality=95)
    rutas_salida.append(ruta_s1)

    # ==========================
    # SLIDE 2: EL DATO CLAVE
    # ==========================
    img2 = Image.new("RGB", (W, H), bg)
    d2 = _draw_grid_bg(img2, W, H)
    _draw_header(d2, 2, total_slides, accent, muted)

    sub_s2 = "EL DATO CLAVE  ·  EFEMÉRIDE DE HOY" if es_efemeride_hoy else "EL DATO CLAVE  ·  FUENTE VERIFICADA"
    d2.text((90, 175), sub_s2, font=f_cat, fill=accent)

    d2.rounded_rectangle([(90, 240), (990, 1085)], radius=20, fill=card_bg, outline=border, width=2)
    d2.rounded_rectangle([(140, 282), (240, 289)], radius=4, fill=accent)

    f_hero_2 = _fit_font_px(d2, cifra_hero, "oswald_bold", 800, 84, 52)
    d2.text((140, 315), cifra_hero, font=f_hero_2, fill=accent)

    f_lbl_2 = _fit_font_px(d2, etiqueta_cifra, "oswald_bold", 800, 24, 18)
    d2.text((140, 422), etiqueta_cifra, font=f_lbl_2, fill=muted)
    d2.line([(140, 472), (940, 472)], fill=border, width=2)

    dato_size = 38
    while dato_size > 28:
        f_d2 = obtener_fuente("sans", dato_size)
        if len(_wrap_px(d2, dato_txt, f_d2, 790)) * int(dato_size * 1.48) <= 370:
            break
        dato_size -= 2
    _draw_wrapped_px(d2, dato_txt, 140, 512, obtener_fuente("sans", dato_size), white, 790, int(dato_size * 1.48))

    d2.line([(140, 912), (940, 912)], fill=border, width=1)
    fuente_txt = f"FUENTE: {str(post.get('fuente_oficial', 'ARCHIVO HDE')).upper()}"
    tipo_txt = f"INDICADOR: {str(post.get('tipo_valor', 'SERIE HISTÓRICA')).upper()}"
    y_f, _ = _draw_wrapped_px(d2, fuente_txt, 140, 938, f_source, muted, 800, 28)
    _draw_wrapped_px(d2, tipo_txt, 140, max(y_f + 6, 998), f_source, (108, 122, 144), 800, 26)

    cta_s2 = "DESLIZÁ: LA TRAMA COMPLETA" if has_slide_3 else "DESLIZÁ PARA OPINAR"
    _draw_footer_cta(d2, cta_s2, accent, card_bg, border, show_arrow=True)

    ruta_s2 = f"{prefijo_archivo}_2_dato.jpg"
    img2.save(ruta_s2, quality=95)
    rutas_salida.append(ruta_s2)

    # ==========================
    # SLIDE 3: CONTEXTO [01] Y [02]
    # ==========================
    if has_slide_3:
        img3 = Image.new("RGB", (W, H), bg)
        d3 = _draw_grid_bg(img3, W, H)
        _draw_header(d3, 3, total_slides, accent, muted)

        d3.text((90, 175), "CONTEXTO  ·  POR QUÉ IMPORTÓ", font=f_cat, fill=accent)
        tit_ctx = str(post.get("titulo_contexto") or titular_txt)
        f_ctx_t = _fit_font_px(d3, tit_ctx, "oswald_bold", 900, 52, 34)
        d3.text((90, 218), tit_ctx, font=f_ctx_t, fill=white)

        sub1 = str(post.get("subtitulo_b1") or "EL DETONANTE").upper()
        sub2 = str(post.get("subtitulo_b2") or "EL IMPACTO").upper()

        # Escala automáticamente fuente del bloque si ambos párrafos juntos se acercan al pie
        ctx_size = 27
        while ctx_size > 21:
            f_ctx = obtener_fuente("sans", ctx_size)
            lh = int(ctx_size * 1.44)
            l1 = _wrap_px(d3, bloque_1, f_ctx, 820)
            l2 = _wrap_px(d3, bloque_2, f_ctx, 820)
            total_h = (98 + len(l1) * lh + 26) + 28 + (98 + len(l2) * lh + 26)
            if 308 + total_h <= 1145:
                break
            ctx_size -= 2

        f_ctx = obtener_fuente("sans", ctx_size)
        lh = int(ctx_size * 1.44)
        l1 = _wrap_px(d3, bloque_1, f_ctx, 820)
        l2 = _wrap_px(d3, bloque_2, f_ctx, 820)

        b1_y = 308
        b1_h = 98 + len(l1) * lh + 24
        d3.rounded_rectangle([(90, b1_y), (990, b1_y + b1_h)], radius=18, fill=card_bg, outline=border, width=2)
        d3.rounded_rectangle([(125, b1_y + 28), (190, b1_y + 68)], radius=8, fill=accent)
        d3.text((144, b1_y + 33), "01", font=f_label, fill=bg)
        d3.text((210, b1_y + 33), sub1, font=_fit_font_px(d3, sub1, "oswald_bold", 750, 24, 18), fill=accent)
        cy = b1_y + 94
        for ln in l1:
            d3.text((125, cy), ln, font=f_ctx, fill=off_white)
            cy += lh

        b2_y = b1_y + b1_h + 26
        b2_h = 98 + len(l2) * lh + 24
        d3.rounded_rectangle([(90, b2_y), (990, b2_y + b2_h)], radius=18, fill=card_bg_alt, outline=border, width=2)
        d3.rounded_rectangle([(125, b2_y + 28), (190, b2_y + 68)], radius=8, fill=accent_sec)
        d3.text((144, b2_y + 33), "02", font=f_label, fill=bg)
        d3.text((210, b2_y + 33), sub2, font=_fit_font_px(d3, sub2, "oswald_bold", 750, 24, 18), fill=accent_sec)
        cy = b2_y + 94
        for ln in l2:
            d3.text((125, cy), ln, font=f_ctx, fill=off_white)
            cy += lh

        has_yt = bool(post.get("youtube_titulo") and post.get("palabra_clave"))
        _draw_footer_cta(d3, "DESLIZÁ PARA DEBATE & VIDEO" if has_yt else "DESLIZÁ PARA DEBATE", accent, card_bg, border, show_arrow=True)

        ruta_s3 = f"{prefijo_archivo}_3_contexto.jpg"
        img3.save(ruta_s3, quality=95)
        rutas_salida.append(ruta_s3)

    # ==========================
    # SLIDE FINAL: DEBATE + CTA HUMANO
    # ==========================
    img_last = Image.new("RGB", (W, H), bg)
    dl = _draw_grid_bg(img_last, W, H)
    _draw_header(dl, total_slides, total_slides, accent, muted)

    dl.text((90, 175), "DEBATE ABIERTO", font=f_cat, fill=accent)

    preg = str(post.get("pregunta_debate") or "¿Qué opinás de este dato?").strip()
    bajada = str(post.get("bajada_debate") or "Dejá tu respuesta corta abajo y sumate al intercambio.").strip()

    q_size = 64
    while q_size > 46:
        f_q = obtener_fuente("oswald_bold", q_size)
        q_lines = _wrap_px(dl, preg, f_q, 880)
        if 240 + len(q_lines) * int(q_size * 1.2) <= 520:
            break
        q_size -= 4
    f_q = obtener_fuente("oswald_bold", q_size)
    y_q, _ = _draw_wrapped_px(dl, preg, 90, 240, f_q, white, 880, int(q_size * 1.2))

    y_baj, _ = _draw_wrapped_px(dl, bajada, 90, y_q + 26, obtener_fuente("sans", 34), off_white, 860, 48)

    card_y = max(y_baj + 46, 700)
    card_bottom = 1125
    dl.rounded_rectangle([(90, card_y), (990, card_bottom)], radius=20, fill=card_bg, outline=accent, width=2)

    yt_tit = str(post.get("youtube_titulo") or "").strip()
    kw = str(post.get("palabra_clave") or "").strip().upper()
    if yt_tit and kw:
        dl.text((135, card_y + 42), "INFORME COMPLETO EN YOUTUBE", font=f_cat, fill=accent)
        dl.text((135, card_y + 88), yt_tit, font=_fit_font_px(dl, yt_tit, "oswald_bold", 780, 48, 30), fill=white)
        _draw_wrapped_px(
            dl,
            f"Si querés ver el video completo sin buscar el link, comentá {kw} y te lo paso por mensaje.",
            135,
            card_y + 172,
            obtener_fuente("sans", 29),
            off_white,
            790,
            42,
        )
        btn_txt = f'COMENTÁ "{kw}"'
    else:
        dl.text((135, card_y + 42), "ARCHIVO EDITORIAL  ·  @hablemosdeeco", font=f_cat, fill=accent)
        dl.text((135, card_y + 88), "Datos verificados sin relleno", font=obtener_fuente("oswald_bold", 44), fill=white)
        _draw_wrapped_px(
            dl,
            "Guardá este informe para tener la cita oficial a mano o compartilo con alguien que discuta este tema.",
            135,
            card_y + 172,
            obtener_fuente("sans", 29),
            off_white,
            790,
            42,
        )
        btn_txt = "DEJÁ TU OPINIÓN EN 1 LÍNEA"

    f_btn = _fit_font_px(dl, btn_txt, "oswald_bold", 760, 28, 22)
    bb = dl.textbbox((0, 0), btn_txt, font=f_btn)
    bw = (bb[2] - bb[0]) + 72
    btn_y = card_bottom - 118
    dl.rounded_rectangle([(135, btn_y), (135 + bw, btn_y + 66)], radius=12, fill=accent)
    dl.text((135 + 36, btn_y + 16), btn_txt, font=f_btn, fill=bg)

    _draw_footer_cta(dl, "GUARDÁ ESTE POST  ·  @hablemosdeeco", muted, card_bg, border, show_arrow=False)

    ruta_last = f"{prefijo_archivo}_{total_slides}_cierre.jpg"
    img_last.save(ruta_last, quality=95)
    rutas_salida.append(ruta_last)

    return rutas_salida

def subir_imagen_temporal(ruta_imagen):
    with open(ruta_imagen, "rb") as file:
        res = requests.post(
            "https://api.imgbb.com/1/upload",
            params={"key": IMGBB_API_KEY, "expiration": 600},
            files={"image": file}
        ).json()
    
    if not res.get("success"):
        raise Exception(f"Error subiendo a ImgBB: {res}")
    return res["data"]["url"]

def esperar_procesamiento_meta(container_id, token, host, max_intentos=8, espera_segundos=3):
    """Consulta el estado del contenedor en Meta hasta que esté FINISHED o falle."""
    url = f"https://{host}/v21.0/{container_id}"
    params = {"fields": "status_code", "access_token": token}
    for intento in range(1, max_intentos + 1):
        try:
            res = requests.get(url, params=params).json()
            status = res.get("status_code", "")
            if status == "FINISHED":
                print(f"Contenedor {container_id} listo para publicar (FINISHED).")
                return True
            elif status == "ERROR":
                raise Exception(f"Meta reportó ERROR procesando contenedor {container_id}: {res}")
            print(f"Procesando en Meta... Intento {intento}/{max_intentos} (Estado: {status or 'EN PROCESO'})")
        except Exception as e:
            if "ERROR" in str(e):
                raise e
            print(f"Aviso en polling {intento}: {e}")
        time.sleep(espera_segundos)
    return True

def publicar_carrusel_en_instagram(rutas_imagenes, caption):
    token = IG_ACCESS_TOKEN.strip()
    user_id = IG_USER_ID.strip()

    host = "graph.instagram.com" if token.startswith("IG") else "graph.facebook.com"
    base_url = f"https://{host}/v21.0/{user_id}"

    # Validación previa de autenticación con Meta antes de procesar imágenes
    res_auth = requests.get(f"https://{host}/v21.0/me", params={"access_token": token}).json()
    if "error" in res_auth:
        err_msg = res_auth["error"].get("message", "")
        err_code = res_auth["error"].get("code", "")
        raise Exception(
            f"Meta Graph API rechazó el acceso (Código {err_code}): '{err_msg}'. "
            "El token IG_ACCESS_TOKEN caducó o tu aplicación en developers.facebook.com "
            "tiene una alerta de seguridad/revisión pendiente."
        )

    # 1. Subir cada imagen y crear cada item del carrusel
    item_ids = []
    print(f"Subiendo {len(rutas_imagenes)} placas para el carrusel...")
    for idx, ruta in enumerate(rutas_imagenes, 1):
        url_img = subir_imagen_temporal(ruta)
        res_item = requests.post(
            f"{base_url}/media",
            data={
                "image_url": url_img,
                "is_carousel_item": "true",
                "access_token": token
            }
        ).json()

        if "id" not in res_item:
            raise Exception(f"Error al crear item {idx} del carrusel en {host}: {res_item}")

        item_ids.append(res_item["id"])
        print(f"Item {idx}/{len(rutas_imagenes)} creado con ID: {res_item['id']}")

    time.sleep(4)

    # 2. Crear el contenedor padre de tipo CAROUSEL
    print("Creando contenedor padre de carrusel...")
    res_carousel = requests.post(
        f"{base_url}/media",
        data={
            "media_type": "CAROUSEL",
            "children": ",".join(item_ids),
            "caption": caption,
            "access_token": token
        }
    ).json()

    if "id" not in res_carousel:
        raise Exception(f"Error al crear contenedor de carrusel en {host}: {res_carousel}")

    carousel_id = res_carousel["id"]

    # Polling dinámico en Meta para verificar estado antes de publicar
    esperar_procesamiento_meta(carousel_id, token, host)

    # 3. Publicar el carrusel
    print("Publicando carrusel en el feed...")
    res_publish = requests.post(
        f"{base_url}/media_publish",
        data={
            "creation_id": carousel_id,
            "access_token": token
        }
    ).json()

    if "id" not in res_publish:
        raise Exception(f"Error al publicar carrusel en {host}: {res_publish}")

    return res_publish["id"]

def publicar_en_x(fecha, titular, dato_clave):
    if not (X_API_KEY and X_API_SECRET and X_ACCESS_TOKEN and X_ACCESS_SECRET):
        print("Credenciales de X no detectadas. Se saltea la publicación en X.")
        return None

    try:
        import tweepy
    except ImportError:
        print("Tweepy no está instalado. Se saltea la publicación en X.")
        return None

    try:
        print("Conectando con la API v2 de X para publicar tweet...")
        client_v2 = tweepy.Client(
            consumer_key=X_API_KEY,
            consumer_secret=X_API_SECRET,
            access_token=X_ACCESS_TOKEN,
            access_token_secret=X_ACCESS_SECRET
        )

        encabezado = f"🏛️ {fecha.upper()}\n\n📌 {titular}\n\n"
        cierre = "\n\n#HistoriaEconomica #Argentina"

        limite = 280
        espacio_dato = limite - len(encabezado) - len(cierre)
        if len(dato_clave) > espacio_dato:
            dato_texto = dato_clave[:max(0, espacio_dato - 3)] + "..."
        else:
            dato_texto = dato_clave

        texto_tweet = encabezado + dato_texto + cierre

        res = client_v2.create_tweet(text=texto_tweet)
        tweet_id = res.data["id"]
        print(f"¡Publicado exitosamente en X! Tweet ID: {tweet_id}")
        return tweet_id
    except Exception as e:
        print(f"Advertencia al publicar en X: {e}")
        return None

def parsear_dia_mes(fecha_str: str):
    """Extrae (dia, mes) numéricos de fechas en español como '14 de junio de 1985' o '4 de junio'."""
    if not fecha_str:
        return None, None
    meses_map = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
        "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
    }
    partes = fecha_str.lower().replace(",", "").split()
    dia, mes = None, None
    for p in partes:
        if p.isdigit() and dia is None:
            dia = int(p)
        if p in meses_map and mes is None:
            mes = meses_map[p]
    return dia, mes

def seleccionar_post_a_publicar(posts):
    """
    Cerrojo de Seguridad (Gatekeeper):
    Filtra estrictamente publicaciones NO publicadas Y VERIFICADAS.
    Prioriza coincidencia por efeméride del día (zona horaria Argentina); si no hay, usa fallback secuencial.
    Retorna una tupla: (post_seleccionado, es_efemeride_hoy)
    """
    tz_ar = obtener_zona_argentina()
    ahora_ar = datetime.now(tz_ar)
    dia_hoy = ahora_ar.day
    mes_hoy = ahora_ar.month

    # Cerrojo de Seguridad: solo posts pendientes que hayan sido auditados (verificado == True)
    posts_elegibles = [
        p for p in posts 
        if not p.get("publicado", False) 
        and p.get("verificado", False) is True
        and not REGEX_PATRONES_IDENTIDAD.search(" ".join(str(v) for v in p.values() if isinstance(v, str)))
        and not PATRON_PRIMERA_PERSONA.search(" ".join(str(v) for v in p.values() if isinstance(v, str)))
    ]

    # Alerta preventiva si el inventario de publicaciones verificadas es crítico
    if len(posts_elegibles) < 5:
        print(f"⚠️ ALERTA DE AUDITORÍA: Quedan menos de 5 posts verificados listos para salir. (Disponibles: {len(posts_elegibles)})")

    if not posts_elegibles:
        print("⚠️ ALERTA DE BLOQUEO: No hay ningún post verificado disponible para publicar. Se suspende la publicación.")
        return None, False

    # 1. Coincidencia por efeméride exacta de hoy (solo si es_efemeride es True)
    for p in posts_elegibles:
        if not p.get("es_efemeride"):
            continue
        fecha_post = p.get("fecha_historica", "")
        d, m = parsear_dia_mes(fecha_post)
        if d == dia_hoy and m == mes_hoy:
            print(f"¡Efeméride del día encontrada y verificada! Coincide con {dia_hoy}/{mes_hoy}: Post #{p.get('id')} - {p.get('titular')}")
            return p, True

    # 2. Fallback secuencial sobre el lote verificado
    siguiente = posts_elegibles[0]
    return siguiente, False

def actualizar_csv(posts, ruta_csv="control_publicaciones.csv"):
    """Regenera la planilla de control de auditoría para Excel tras cada ejecución con verificación de anonimato."""
    with open(ruta_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "ID", "ESTADO", "VERIFICADO", "CONTROL_ANONIMATO", "ORIGEN_GUION",
            "FECHA HISTÓRICA", "TITULAR", "CIFRA HERO", "DATO CLAVE", "FUENTE OFICIAL",
            "TIPO DE VALOR", "PALABRA CLAVE", "URL RESPALDO",
            "TEXTO FINAL INSTAGRAM", "TEXTO FINAL X (TWITTER)"
        ])
        for p in posts:
            fecha = p.get("fecha_historica", "")
            titular = p.get("titular", "")
            cifra_hero = p.get("cifra_hero", "")
            dato = p.get("dato_clave", "")
            caption_ig = p.get("caption", "")
            fuente = p.get("fuente_oficial", "")
            tipo_val = p.get("tipo_valor", "")
            origen = p.get("origen_guion", "Lote Fundacional HDE")
            kw = p.get("palabra_clave", "")
            url_resp = p.get("url_respaldo", "")

            texto_fila = " ".join(str(p.get(c, "")) for c in CAMPOS_TEXTO_POST)
            es_limpio = not (REGEX_PATRONES_IDENTIDAD.search(texto_fila) or PATRON_PRIMERA_PERSONA.search(texto_fila))
            control_anon = "LIMPIO" if es_limpio else "⚠️ ALERTA IDENTIDAD"

            texto_x = f"🏛️ {fecha.upper()}\n\n📌 {titular}\n\n{dato}\n\n#HistoriaEconomica #Argentina"
            estado = "PUBLICADO" if p.get("publicado") else "PENDIENTE"
            verificado = "SI" if p.get("verificado") else "NO"
            writer.writerow([
                p.get("id"), estado, verificado, control_anon, origen,
                fecha, titular, cifra_hero, dato, fuente, tipo_val, kw, url_resp, caption_ig, texto_x
            ])
    print(f"Planilla de control ({ruta_csv}) sincronizada automáticamente.")

# Alias para compatibilidad histórica
actualizar_csv_control = actualizar_csv

def main():
    with open("datos.json", "r", encoding="utf-8") as f:
        posts = json.load(f)

    post_pendiente, es_efemeride_hoy = seleccionar_post_a_publicar(posts)
    if not post_pendiente:
        print("No hay publicaciones verificadas pendientes en datos.json. Publicación detenida por seguridad.")
        return

    # Cortafuegos de Privacidad de Última Milla (Tolerancia Cero)
    validar_y_sanitizar_post(post_pendiente)

    print(f"Generando carrusel para el post #{post_pendiente.get('id')}: {post_pendiente.get('titular')}...")
    rutas_placas = crear_placas_carrusel(post_pendiente, es_efemeride_hoy=es_efemeride_hoy)

    try:
        ig_post_id = publicar_carrusel_en_instagram(rutas_placas, post_pendiente["caption"])
        print(f"¡Carrusel publicado exitosamente en Instagram! ID: {ig_post_id}")
    except Exception as e:
        print(f"Error publicando en Instagram: {e}")
        raise e

    # Publicación en X desactivada deliberadamente (el bot opera exclusivamente para Instagram sin advertencias)
    # x_tweet_id = publicar_en_x(post_pendiente["fecha_historica"], post_pendiente["titular"], post_pendiente["dato_clave"])

    post_pendiente["publicado"] = True
    with open("datos.json", "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    actualizar_csv(posts)

if __name__ == "__main__":
    main()
