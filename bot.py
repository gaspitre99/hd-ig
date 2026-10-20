import json
import os
import textwrap
import time
import requests
from PIL import Image, ImageDraw, ImageFont

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

def crear_placas_carrusel(fecha, titular, dato_clave):
    ancho, alto = 1080, 1350
    fondo_color = (18, 22, 28)
    acento_color = (212, 175, 55)
    texto_blanco = (245, 245, 245)
    gris_claro = (200, 205, 215)
    gris_tenue = (120, 125, 135)

    font_fecha = obtener_fuente("sans_bold", 34)
    font_titular = obtener_fuente("serif_bold", 62)
    font_dato = obtener_fuente("sans", 40)
    font_dato_grande = obtener_fuente("sans", 44)
    font_sub = obtener_fuente("sans_bold", 28)

    rutas_salida = []

    # ==========================
    # SLIDE 1: PORTADA
    # ==========================
    img1 = Image.new("RGB", (ancho, alto), color=fondo_color)
    draw1 = ImageDraw.Draw(img1)

    draw1.rectangle([(90, 120), (250, 128)], fill=acento_color)
    draw1.text((90, 155), fecha.upper(), font=font_fecha, fill=acento_color)

    y_text = 270
    for linea in textwrap.wrap(titular, width=21):
        draw1.text((90, y_text), linea, font=font_titular, fill=texto_blanco)
        y_text += 82

    y_text += 45
    draw1.line([(90, y_text), (990, y_text)], fill=(70, 75, 85), width=2)
    y_text += 55

    draw1.text((90, y_text), "ARCHIVO DE HISTORIA ECONÓMICA ARGENTINA", font=font_sub, fill=acento_color)

    draw1.rectangle([(90, 1190), (990, 1260)], fill=(24, 29, 37))
    draw1.text((120, 1212), "DESLIZÁ PARA CONOCER EL DATO CLAVE ➔", font=font_sub, fill=gris_claro)

    ruta_s1 = "slide_1_portada.jpg"
    img1.save(ruta_s1, quality=95)
    rutas_salida.append(ruta_s1)

    # ==========================
    # SLIDE 2: EL DATO CLAVE
    # ==========================
    img2 = Image.new("RGB", (ancho, alto), color=fondo_color)
    draw2 = ImageDraw.Draw(img2)

    draw2.rectangle([(90, 120), (250, 128)], fill=acento_color)
    draw2.text((90, 155), "EL DATO CLAVE", font=font_fecha, fill=acento_color)
    draw2.text((90, 215), fecha.upper(), font=font_sub, fill=gris_tenue)

    # Caja destacada para el dato clave
    box_y = 300
    box_h = 680
    draw2.rectangle([(90, box_y), (990, box_y + box_h)], fill=(26, 33, 42), outline=(60, 66, 78), width=2)
    draw2.rectangle([(90, box_y), (105, box_y + box_h)], fill=acento_color)

    y_dato = box_y + 80
    for linea in textwrap.wrap(dato_clave, width=28):
        draw2.text((140, y_dato), linea, font=font_dato_grande, fill=texto_blanco)
        y_dato += 68

    draw2.text((90, 1080), "HABLEMOS DE ECONOMÍA", font=font_sub, fill=gris_tenue)

    draw2.rectangle([(90, 1190), (990, 1260)], fill=(24, 29, 37))
    draw2.text((120, 1212), "DESLIZÁ PARA EL ANÁLISIS COMPLETO ➔", font=font_sub, fill=gris_claro)

    ruta_s2 = "slide_2_dato.jpg"
    img2.save(ruta_s2, quality=95)
    rutas_salida.append(ruta_s2)

    # ==========================
    # SLIDE 3: CIERRE / YOUTUBE CTA
    # ==========================
    img3 = Image.new("RGB", (ancho, alto), color=fondo_color)
    draw3 = ImageDraw.Draw(img3)

    draw3.rectangle([(90, 120), (250, 128)], fill=acento_color)
    draw3.text((90, 155), "¿CONOCÍAS ESTE CASO?", font=font_fecha, fill=acento_color)

    draw3.text((90, 240), "¿Qué opinás de esta medida?", font=font_titular, fill=texto_blanco)
    draw3.text((90, 340), "Dejá tu comentario abajo. Leemos y debatimos todos.", font=font_dato, fill=gris_claro)

    # Tarjeta de YouTube
    yt_y = 470
    yt_h = 560
    draw3.rectangle([(90, yt_y), (990, yt_y + yt_h)], fill=(26, 33, 42), outline=acento_color, width=2)

    draw3.text((140, yt_y + 60), "CANAL DE YOUTUBE", font=font_sub, fill=acento_color)
    draw3.text((140, yt_y + 120), "@hablemosdeeco", font=font_titular, fill=texto_blanco)

    y_desc = yt_y + 240
    desc_texto = "Documentales completos, gráficos interactivos y análisis semanal de historia económica argentina."
    for linea in textwrap.wrap(desc_texto, width=32):
        draw3.text((140, y_desc), linea, font=font_dato, fill=gris_claro)
        y_desc += 55

    # Botón simulación
    draw3.rectangle([(140, yt_y + 430), (620, yt_y + 495)], fill=acento_color)
    draw3.text((165, yt_y + 448), "ENLACE DIRECTO EN EL PERFIL", font=font_sub, fill=(18, 22, 28))

    draw3.text((90, 1212), "SEGUINOS EN INSTAGRAM: @hablemosdeeco", font=font_sub, fill=gris_tenue)

    ruta_s3 = "slide_3_cierre.jpg"
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

    # Esperar 6 segundos para que Meta termine de procesar las imágenes individuales
    time.sleep(6)

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

    # Esperar 8 segundos para que el carrusel esté listo para publicar
    time.sleep(8)

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

def publicar_en_x(rutas_imagenes, fecha, titular, dato_clave):
    if not (X_API_KEY and X_API_SECRET and X_ACCESS_TOKEN and X_ACCESS_SECRET):
        print("Credenciales de X no detectadas. Se saltea la publicación en X.")
        return None

    try:
        import tweepy
    except ImportError:
        print("Tweepy no está instalado. Se saltea la publicación en X.")
        return None

    try:
        print("Intentando autenticar y subir imágenes a X (Twitter)...")
        media_ids = []
        try:
            auth = tweepy.OAuth1UserHandler(
                X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET
            )
            api_v1 = tweepy.API(auth)
            for ruta in rutas_imagenes:
                media = api_v1.media_upload(ruta)
                media_ids.append(media.media_id)
        except Exception as e_media:
            print(f"Aviso: La subida de imágenes en X no está habilitada en tu nivel de cuenta ({e_media}).")
            print("Se procederá a publicar el tweet en formato texto con enlace a YouTube.")
            media_ids = None

        client_v2 = tweepy.Client(
            consumer_key=X_API_KEY,
            consumer_secret=X_API_SECRET,
            access_token=X_ACCESS_TOKEN,
            access_token_secret=X_ACCESS_SECRET
        )

        encabezado = f"🏛️ {fecha.upper()}\n\n📌 {titular}\n\n"
        cierre = f"\n\n📺 Más archivo en YouTube:\nhttps://youtube.com/@hablemosdeeco\n\n#HistoriaEconomica #Argentina"

        limite = 280
        espacio_dato = limite - len(encabezado) - len(cierre)
        if len(dato_clave) > espacio_dato:
            dato_texto = dato_clave[:max(0, espacio_dato - 3)] + "..."
        else:
            dato_texto = dato_clave

        texto_tweet = encabezado + dato_texto + cierre

        if media_ids:
            res = client_v2.create_tweet(text=texto_tweet, media_ids=media_ids)
        else:
            res = client_v2.create_tweet(text=texto_tweet)

        tweet_id = res.data["id"]
        print(f"¡Publicado exitosamente en X! Tweet ID: {tweet_id}")
        return tweet_id
    except Exception as e:
        print(f"Advertencia al publicar en X (no detiene el proceso): {e}")
        return None

def main():
    with open("datos.json", "r", encoding="utf-8") as f:
        posts = json.load(f)

    post_pendiente = next((p for p in posts if not p.get("publicado")), None)
    if not post_pendiente:
        print("No hay publicaciones pendientes en datos.json.")
        return

    print(f"Generando carrusel para el post #{post_pendiente.get('id')}: {post_pendiente.get('titular')}...")
    rutas_placas = crear_placas_carrusel(
        post_pendiente["fecha_historica"],
        post_pendiente["titular"],
        post_pendiente["dato_clave"]
    )

    try:
        ig_post_id = publicar_carrusel_en_instagram(rutas_placas, post_pendiente["caption"])
        print(f"¡Carrusel publicado exitosamente en Instagram! ID: {ig_post_id}")
    except Exception as e:
        print(f"Error publicando en Instagram: {e}")
        raise e

    try:
        x_tweet_id = publicar_en_x(
            rutas_placas,
            post_pendiente["fecha_historica"],
            post_pendiente["titular"],
            post_pendiente["dato_clave"]
        )
    except Exception as e:
        print(f"Error secundario en X: {e}")

    post_pendiente["publicado"] = True
    with open("datos.json", "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
