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
    1. Modo Efeméride (Prioridad 1): es_efemeride_hoy o post['es_efemeride'] == True -> Dorado / Ámbar (245, 158, 11)
    2. Modo Fin de Semana (Prioridad 2): Sábado (5) o Domingo (6) -> Verde Esmeralda (16, 185, 129)
    3. Modo Estándar Lunes a Viernes (Por defecto) -> Celeste Eléctrico HDE (14, 165, 233)
    """
    tz_ar = obtener_zona_argentina()
    ahora_ar = datetime.now(tz_ar)
    fecha_hist = post.get("fecha_historica", "") if isinstance(post, dict) else str(post)

    # 1. Modo Efeméride (Prioridad 1)
    if es_efemeride_hoy or (isinstance(post, dict) and post.get("es_efemeride")):
        return {
            "tipo": "efemeride",
            "color_acento": (245, 158, 11),       # Dorado / Ámbar
            "color_tarjeta": (28, 24, 18),        # Grafito cálido
            "borde_tarjeta": (70, 52, 28),        # Borde sutil cálido
            "etiqueta_portada": f"EFEMÉRIDE • TAL DÍA COMO HOY ({fecha_hist.upper()})"
        }

    # 2. Modo Edición Fin de Semana (Prioridad 2)
    if ahora_ar.weekday() in (5, 6):
        return {
            "tipo": "fin_de_semana",
            "color_acento": (16, 185, 129),       # Verde Esmeralda editorial
            "color_tarjeta": (18, 28, 24),        # Grafito verdoso sutil
            "borde_tarjeta": (36, 62, 50),        # Borde sutil esmeralda
            "etiqueta_portada": f"DEBATE • EDICIÓN DE FIN DE SEMANA • {fecha_hist.upper()}"
        }

    # 3. Modo Estándar Lunes a Viernes (Por defecto)
    categoria = post.get("categoria", "HISTORIA MONETARIA").upper() if isinstance(post, dict) else "HISTORIA MONETARIA"
    return {
        "tipo": "estandar",
        "color_acento": (14, 165, 233),           # Celeste Eléctrico HDE
        "color_tarjeta": (20, 24, 32),            # Grafito azulado
        "borde_tarjeta": (45, 55, 72),            # Borde sutil azulado
        "etiqueta_portada": f"{categoria} • {fecha_hist.upper()}"
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

def obtener_fuente(tipo="sans", tamano=40):
    rutas_linux = {
        "sans_bold": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "serif_bold": "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "sans": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    }
    rutas_windows = {
        "sans_bold": "C:/Windows/Fonts/arialbd.ttf",
        "serif_bold": "C:/Windows/Fonts/georgiab.ttf",
        "sans": "C:/Windows/Fonts/arial.ttf"
    }
    for ruta in [rutas_linux.get(tipo), rutas_windows.get(tipo)]:
        if ruta and os.path.exists(ruta):
            try:
                return ImageFont.truetype(ruta, tamano)
            except IOError:
                pass
    return ImageFont.load_default()

# ========================================================
# CORTAFUEGOS DE PRIVACIDAD DE ÚLTIMA MILLA (MODO LOW PROFILE)
# ========================================================
REGEX_PATRONES_IDENTIDAD = re.compile(
    r"(gaspar|trep[aá]|gaspitre|gaspi|gaspar's notion|\bmi\s+canal\b|\bmi\s+investigaci[oó]n\b)",
    re.IGNORECASE
)

PATRONES_REEMPLAZO_CALIENTE = [
    (re.compile(r"Gaspar'?s\s+Notion", re.IGNORECASE), "Archivo Editorial HDE"),
    (re.compile(r"Gaspar\s+Trep[aá]", re.IGNORECASE), "Equipo Editorial HDE"),
    (re.compile(r"@?gaspitre(99)?", re.IGNORECASE), "hablemosdeeco"),
    (re.compile(r"@?gaspi\b", re.IGNORECASE), "hde"),
    (re.compile(r"\bGaspar\b", re.IGNORECASE), "Equipo HDE"),
    (re.compile(r"\bTrep[aá]\b", re.IGNORECASE), "Equipo HDE"),
    (re.compile(r"\bmi\s+canal\b", re.IGNORECASE), "nuestro canal"),
    (re.compile(r"\bmi\s+investigaci[oó]n\b", re.IGNORECASE), "nuestra investigación"),
]

def validar_y_sanitizar_post(post: dict) -> dict:
    """
    Cortafuegos de Privacidad de Última Milla.
    Inspecciona y sanitiza todos los campos de texto del post para garantizar 0
    filtraciones de identidad personal antes de dibujar en Pillow o publicar en Instagram.
    Si se detecta un intento forzoso de filtración no sanitizable, aborta la ejecución.
    """
    if not isinstance(post, dict):
        return post

    campos = ["titular", "dato_clave", "caption", "fuente_oficial", "tipo_valor", "origen_guion", "fecha_historica"]
    for c in campos:
        val = post.get(c, "")
        if isinstance(val, str) and REGEX_PATRONES_IDENTIDAD.search(val):
            # Sanitización en caliente a identidad institucional
            val_limpio = val
            for pat, repl in PATRONES_REEMPLAZO_CALIENTE:
                val_limpio = pat.sub(repl, val_limpio)
            post[c] = val_limpio

            # Control de tolerancia cero: si persiste rastro, abortar
            if REGEX_PATRONES_IDENTIDAD.search(post[c]):
                raise ValueError(f"CRITICAL PRIVACY ALERT: Intento de publicar rastro de identidad personal en campo '{c}'. Publicación abortada.")
    return post

def crear_placas_carrusel(post_o_fecha, titular=None, dato_clave=None, es_efemeride_hoy=False, prefijo_archivo="slide"):
    if isinstance(post_o_fecha, dict):
        post = validar_y_sanitizar_post(post_o_fecha)
        fecha = post.get("fecha_historica", "")
        titular = post.get("titular", "")
        dato_clave = post.get("dato_clave", "")
    else:
        fecha = str(post_o_fecha)
        titular = str(titular or "")
        dato_clave = str(dato_clave or "")
        post = {"fecha_historica": fecha, "titular": titular, "dato_clave": dato_clave}
        post = validar_y_sanitizar_post(post)
        fecha = post.get("fecha_historica", "")
        titular = post.get("titular", "")
        dato_clave = post.get("dato_clave", "")

    paleta = obtener_paleta_editorial(post, es_efemeride_hoy=es_efemeride_hoy)
    color_acento = paleta["color_acento"]
    color_tarjeta = paleta["color_tarjeta"]
    borde_card = paleta["borde_tarjeta"]
    etiqueta_portada = paleta["etiqueta_portada"]

    ancho, alto = 1080, 1350
    fondo_color = (12, 14, 18)        # Negro grafito idéntico a la web
    blanco = (255, 255, 255)           # Blanco puro
    gris_sub = (203, 213, 225)         # Gris slate
    gris_tenue = (120, 130, 145)

    font_brand = obtener_fuente("sans_bold", 22)
    font_tag = obtener_fuente("sans_bold", 26)
    font_titular = obtener_fuente("serif_bold", 54)
    font_dato = obtener_fuente("sans", 36)
    font_dato_grande = obtener_fuente("sans", 42)
    font_sub = obtener_fuente("sans_bold", 24)

    rutas_salida = []

    # ==========================
    # SLIDE 1: PORTADA
    # ==========================
    img1 = Image.new("RGB", (ancho, alto), color=fondo_color)
    draw1 = ImageDraw.Draw(img1)

    # Identidad editorial armónica superior (✦ HABLEMOS DE ECONOMÍA)
    draw1.text((90, 85), "✦", font=font_tag, fill=color_acento)
    draw1.text((125, 88), "HABLEMOS DE ECONOMÍA", font=font_brand, fill=blanco)

    # Indicador de progreso (1/3)
    draw1.text((940, 88), "1/3", font=font_sub, fill=gris_tenue)

    # Tag de categoría y fecha
    draw1.text((90, 190), etiqueta_portada, font=font_tag, fill=color_acento)

    y_text = 270
    for linea in textwrap.wrap(titular, width=21):
        draw1.text((90, y_text), linea, font=font_titular, fill=blanco)
        y_text += 74

    y_text += 40
    draw1.line([(90, y_text), (990, y_text)], fill=borde_card, width=2)
    y_text += 50

    draw1.text((90, y_text), "ARCHIVO & ANÁLISIS MACROECONÓMICO", font=font_tag, fill=color_acento)

    # Footer
    draw1.rectangle([(90, 1200), (990, 1270)], fill=color_tarjeta, outline=borde_card, width=1)
    draw1.text((120, 1222), "DESLIZÁ PARA CONOCER EL DATO CLAVE ➔", font=font_sub, fill=color_acento)

    ruta_s1 = f"{prefijo_archivo}_1_portada.jpg"
    img1.save(ruta_s1, quality=95)
    rutas_salida.append(ruta_s1)

    # ==========================
    # SLIDE 2: EL DATO CLAVE
    # ==========================
    img2 = Image.new("RGB", (ancho, alto), color=fondo_color)
    draw2 = ImageDraw.Draw(img2)

    # Identidad editorial superior
    draw2.text((90, 85), "✦", font=font_tag, fill=color_acento)
    draw2.text((125, 88), "HABLEMOS DE ECONOMÍA", font=font_brand, fill=blanco)

    # Indicador de progreso (2/3)
    draw2.text((940, 88), "2/3", font=font_sub, fill=gris_tenue)

    draw2.text((90, 190), "HISTORIA ECONÓMICA  •  EL DATO CLAVE", font=font_tag, fill=color_acento)

    # Caja destacada para el dato clave
    box_y = 270
    box_h = 720
    draw2.rectangle([(90, box_y), (990, box_y + box_h)], fill=color_tarjeta, outline=borde_card, width=2)
    draw2.rectangle([(90, box_y), (105, box_y + box_h)], fill=color_acento)

    y_dato = box_y + 80
    for linea in textwrap.wrap(dato_clave, width=27):
        draw2.text((140, y_dato), linea, font=font_dato_grande, fill=blanco)
        y_dato += 66

    # Sello de Fuente Oficial en el margen inferior de la tarjeta elevada grafito
    fuente_oficial = post.get("fuente_oficial", "ARCHIVO HDE").upper()
    tipo_valor = post.get("tipo_valor", "SERIE HISTÓRICA").upper()
    texto_fuente = f"FUENTE: {fuente_oficial} • {tipo_valor}"
    color_fuente = (148, 163, 184)  # Gris tenue / slate
    font_fuente = obtener_fuente("sans", 22)

    # Línea divisoria sutil previa a la fuente
    y_fuente_sep = box_y + box_h - 90
    draw2.line([(140, y_fuente_sep), (940, y_fuente_sep)], fill=borde_card, width=1)

    y_fuente = y_fuente_sep + 20
    for linea_f in textwrap.wrap(texto_fuente, width=54):
        draw2.text((140, y_fuente), linea_f, font=font_fuente, fill=color_fuente)
        y_fuente += 28

    draw2.text((90, 1100), f"EFEMÉRIDE: {fecha.upper()}", font=font_sub, fill=gris_tenue)

    draw2.rectangle([(90, 1200), (990, 1270)], fill=color_tarjeta, outline=borde_card, width=1)
    draw2.text((120, 1222), "DESLIZÁ PARA EL ANÁLISIS COMPLETO ➔", font=font_sub, fill=color_acento)

    ruta_s2 = f"{prefijo_archivo}_2_dato.jpg"
    img2.save(ruta_s2, quality=95)
    rutas_salida.append(ruta_s2)

    # ==========================
    # SLIDE 3: CIERRE / YOUTUBE CTA
    # ==========================
    img3 = Image.new("RGB", (ancho, alto), color=fondo_color)
    draw3 = ImageDraw.Draw(img3)

    # Identidad editorial superior
    draw3.text((90, 85), "✦", font=font_tag, fill=color_acento)
    draw3.text((125, 88), "HABLEMOS DE ECONOMÍA", font=font_brand, fill=blanco)

    # Indicador de progreso (3/3)
    draw3.text((940, 88), "3/3", font=font_sub, fill=gris_tenue)

    draw3.text((90, 190), "DEBATE & COMUNIDAD", font=font_tag, fill=color_acento)

    y_preg = 260
    for linea in textwrap.wrap("¿Qué opinás de esta medida?", width=20):
        draw3.text((90, y_preg), linea, font=font_titular, fill=blanco)
        y_preg += 68

    y_coment = y_preg + 20
    for linea in textwrap.wrap("Dejá tu comentario abajo. Leemos y debatimos todos los puntos de vista.", width=32):
        draw3.text((90, y_coment), linea, font=font_dato, fill=gris_sub)
        y_coment += 50

    # Tarjeta de YouTube
    yt_y = y_coment + 40
    yt_h = 470
    draw3.rectangle([(90, yt_y), (990, yt_y + yt_h)], fill=color_tarjeta, outline=color_acento, width=2)

    draw3.text((130, yt_y + 45), "CANAL OFICIAL DE YOUTUBE", font=font_tag, fill=color_acento)
    draw3.text((130, yt_y + 105), "@hablemosdeeco", font=font_titular, fill=blanco)

    y_desc = yt_y + 195
    desc_texto = "Documentales completos, gráficos interactivos y análisis de historia económica argentina."
    for linea in textwrap.wrap(desc_texto, width=32):
        draw3.text((130, y_desc), linea, font=font_dato, fill=gris_sub)
        y_desc += 50

    # Botón simulación
    draw3.rectangle([(130, yt_y + 360), (620, yt_y + 425)], fill=color_acento)
    draw3.text((155, yt_y + 380), "ENLACE DIRECTO EN EL PERFIL", font=font_sub, fill=fondo_color)

    draw3.rectangle([(90, 1200), (990, 1270)], fill=color_tarjeta, outline=borde_card, width=1)
    draw3.text((120, 1222), "SEGUINOS EN INSTAGRAM: @hablemosdeeco", font=font_sub, fill=gris_tenue)

    ruta_s3 = f"{prefijo_archivo}_3_cierre.jpg"
    img3.save(ruta_s3, quality=95)
    rutas_salida.append(ruta_s3)

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
        if not p.get("publicado", False) and p.get("verificado", False) is True
    ]

    # Alerta preventiva si el inventario de publicaciones verificadas es crítico
    if len(posts_elegibles) < 5:
        print(f"⚠️ ALERTA DE AUDITORÍA: Quedan menos de 5 posts verificados listos para salir. (Disponibles: {len(posts_elegibles)})")

    if not posts_elegibles:
        print("⚠️ ALERTA DE BLOQUEO: No hay ningún post verificado disponible para publicar. Se suspende la publicación.")
        return None, False

    # 1. Coincidencia por efeméride exacta de hoy (Prioridad 1) sobre el lote verificado
    for p in posts_elegibles:
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
            "FECHA HISTÓRICA", "TITULAR", "DATO CLAVE", "FUENTE OFICIAL", "TIPO DE VALOR",
            "TEXTO FINAL INSTAGRAM", "TEXTO FINAL X (TWITTER)"
        ])
        for p in posts:
            fecha = p.get("fecha_historica", "")
            titular = p.get("titular", "")
            dato = p.get("dato_clave", "")
            caption_ig = p.get("caption", "")
            fuente = p.get("fuente_oficial", "")
            tipo_val = p.get("tipo_valor", "")
            origen = p.get("origen_guion", "Lote Fundacional HDE")

            # Verificación de privacidad institucional
            texto_fila = f"{titular} {dato} {caption_ig} {fuente} {tipo_val} {origen}"
            control_anon = "LIMPIO" if not REGEX_PATRONES_IDENTIDAD.search(texto_fila) else "⚠️ ALERTA IDENTIDAD"

            texto_x = f"🏛️ {fecha.upper()}\n\n📌 {titular}\n\n{dato}\n\n#HistoriaEconomica #Argentina"
            estado = "PUBLICADO" if p.get("publicado") else "PENDIENTE"
            verificado = "SI" if p.get("verificado") else "NO"
            writer.writerow([
                p.get("id"), estado, verificado, control_anon, origen,
                fecha, titular, dato, fuente, tipo_val, caption_ig, texto_x
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
