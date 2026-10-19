import json
import os
import textwrap
import requests
from PIL import Image, ImageDraw, ImageFont

def limpiar_secreto(val: str) -> str:
    s = val.strip().strip("\"'").strip()
    if s.lower().startswith("bearer "):
        s = s[7:].strip()
    return s

IG_USER_ID = limpiar_secreto(os.environ["IG_USER_ID"])
IG_ACCESS_TOKEN = limpiar_secreto(os.environ["IG_ACCESS_TOKEN"])
IMGBB_API_KEY = limpiar_secreto(os.environ["IMGBB_API_KEY"])

def crear_placa_grafica(fecha, titular, dato_clave, output_path="post_actual.jpg"):
    ancho, alto = 1080, 1350
    fondo_color = (18, 22, 28)
    acento_color = (212, 175, 55)
    texto_blanco = (245, 245, 245)

    img = Image.new("RGB", (ancho, alto), color=fondo_color)
    draw = ImageDraw.Draw(img)

    try:
        font_fecha = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34)
        font_titular = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 64)
        font_dato = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
    except IOError:
        font_fecha = font_titular = font_dato = ImageFont.load_default()

    draw.rectangle([(90, 120), (240, 128)], fill=acento_color)
    draw.text((90, 155), fecha.upper(), font=font_fecha, fill=acento_color)

    y_text = 260
    for linea in textwrap.wrap(titular, width=22):
        draw.text((90, y_text), linea, font=font_titular, fill=texto_blanco)
        y_text += 82

    y_text += 50
    draw.line([(90, y_text), (990, y_text)], fill=(70, 75, 85), width=2)
    y_text += 60

    for linea in textwrap.wrap(dato_clave, width=36):
        draw.text((90, y_text), linea, font=font_dato, fill=(200, 205, 215))
        y_text += 58

    draw.text((90, 1230), "ARCHIVO DE HISTORIA ECONÓMICA ARGENTINA", font=font_fecha, fill=(120, 125, 135))

    img.save(output_path, quality=95)
    return output_path

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

def publicar_en_instagram(image_url, caption):
    base_url = f"https://graph.facebook.com/v21.0/{IG_USER_ID}"
    
    res_container = requests.post(
        f"{base_url}/media",
        data={
            "image_url": image_url,
            "caption": caption,
            "access_token": IG_ACCESS_TOKEN
        }
    ).json()

    if "id" not in res_container:
        raise Exception(f"Error al crear contenedor: {res_container}")

    creation_id = res_container["id"]

    res_publish = requests.post(
        f"{base_url}/media_publish",
        data={
            "creation_id": creation_id,
            "access_token": IG_ACCESS_TOKEN
        }
    ).json()

    if "id" not in res_publish:
        raise Exception(f"Error al publicar: {res_publish}")

    return res_publish["id"]

def main():
    with open("datos.json", "r", encoding="utf-8") as f:
        posts = json.load(f)

    post_pendiente = next((p for p in posts if not p.get("publicado")), None)
    if not post_pendiente:
        print("No hay publicaciones pendientes en datos.json.")
        return

    ruta_img = crear_placa_grafica(
        post_pendiente["fecha_historica"],
        post_pendiente["titular"],
        post_pendiente["dato_clave"]
    )

    url_publica = subir_imagen_temporal(ruta_img)
    ig_post_id = publicar_en_instagram(url_publica, post_pendiente["caption"])
    print(f"¡Publicado exitosamente en Instagram! ID: {ig_post_id}")

    post_pendiente["publicado"] = True
    with open("datos.json", "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
