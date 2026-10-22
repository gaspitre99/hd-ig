#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Módulo de Auditoría y Verificación de Datos - Hablemos de Economía (HDE)
Incorpora Escudo de Privacidad Institucional (Modo Low Profile).
Permite exportar e importar bidireccionalmente entre datos.json, control_publicaciones.csv
y auditoria_datos_hde.xlsx para auditorías asistidas por IA o revisión humana.
"""

import sys
import os
import json
import csv
import re
import argparse

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

JSON_PATH = "datos.json"
CSV_PATH = "control_publicaciones.csv"
EXCEL_PATH = "auditoria_datos_hde.xlsx"

# ========================================================
# ESCUDO DE PRIVACIDAD Y SANITIZACIÓN (MODO LOW PROFILE)
# ========================================================
PATRONES_IDENTIDAD_REEMPLAZO = [
    (re.compile(r"Gaspar'?s\s+Notion", re.IGNORECASE), "Archivo Editorial HDE"),
    (re.compile(r"Gaspar\s+Trep[aá]", re.IGNORECASE), "Equipo Editorial HDE"),
    (re.compile(r"@?gaspitre(99)?", re.IGNORECASE), "hablemosdeeco"),
    (re.compile(r"@?gaspi\b", re.IGNORECASE), "hde"),
    (re.compile(r"\bGaspar\b", re.IGNORECASE), "Equipo HDE"),
    (re.compile(r"\bTrep[aá]\b", re.IGNORECASE), "Equipo HDE"),
    (re.compile(r"\bmi\s+canal\b", re.IGNORECASE), "nuestro canal"),
    (re.compile(r"\bmi\s+investigaci[oó]n\b", re.IGNORECASE), "nuestra investigación"),
]

REGEX_DETECCION_IDENTIDAD = re.compile(
    r"(gaspar|trep[aá]|gaspitre|gaspi|gaspar's notion|\bmi\s+canal\b|\bmi\s+investigaci[oó]n\b)",
    re.IGNORECASE
)

def sanitizar_identidad(texto: str) -> str:
    """Limpia automáticamente cualquier rastro de nombres propios personales o referencias individuales."""
    if not isinstance(texto, str):
        return texto
    res = texto
    for pat, repl in PATRONES_IDENTIDAD_REEMPLAZO:
        res = pat.sub(repl, res)
    return res

def evaluar_anonimato_texto(texto: str) -> bool:
    """Retorna True si el texto está 100% LIMPIO, False si detecta alguna referencia personal."""
    if not isinstance(texto, str):
        return True
    return not bool(REGEX_DETECCION_IDENTIDAD.search(texto))

# ========================================================
# DEFINICIÓN DE COLUMNAS DE AUDITORÍA EXCEL
# ========================================================
COLUMNAS_EXCEL = [
    ("ID", 8, "center"),
    ("PUBLICADO", 12, "center"),
    ("VERIFICADO", 13, "center"),
    ("CONTROL_ANONIMATO", 22, "center"),
    ("ORIGEN_GUION", 28, "left"),
    ("FECHA_HISTORICA", 24, "left"),
    ("ES_EFEMERIDE", 14, "center"),
    ("CATEGORIA", 22, "left"),
    ("TITULAR_SLIDE_1", 45, "left"),
    ("LARGO_TITULAR", 16, "center"),
    ("DATO_CLAVE_SLIDE_2", 55, "left"),
    ("LARGO_DATO", 14, "center"),
    ("FUENTE_OFICIAL", 34, "left"),
    ("TIPO_VALOR_Y_MONEDA", 36, "left"),
    ("CAPTION_INSTAGRAM", 60, "left"),
    ("ESTADO_AUDITORIA_IA", 22, "center"),
    ("PROBLEMA_DETECTADO", 35, "left"),
    ("ARREGLO_SUGERIDO", 35, "left"),
]

def actualizar_csv_audit(posts, ruta_csv=CSV_PATH):
    """Sincroniza la planilla CSV de control con codificación utf-8-sig y delimitador ';'."""
    with open(ruta_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "ID", "ESTADO", "VERIFICADO", "CONTROL_ANONIMATO", "ORIGEN_GUION", "FECHA HISTÓRICA",
            "TITULAR", "DATO CLAVE", "FUENTE OFICIAL", "TIPO DE VALOR",
            "TEXTO FINAL INSTAGRAM", "TEXTO FINAL X (TWITTER)"
        ])
        for p in posts:
            fecha = sanitizar_identidad(p.get("fecha_historica", ""))
            titular = sanitizar_identidad(p.get("titular", ""))
            dato = sanitizar_identidad(p.get("dato_clave", ""))
            caption_ig = sanitizar_identidad(p.get("caption", ""))
            fuente = sanitizar_identidad(p.get("fuente_oficial", ""))
            tipo_val = sanitizar_identidad(p.get("tipo_valor", ""))
            origen = sanitizar_identidad(p.get("origen_guion", "Lote Fundacional HDE"))

            texto_total = f"{titular} {dato} {caption_ig} {fuente} {tipo_val} {origen}"
            control_anon = "LIMPIO" if evaluar_anonimato_texto(texto_total) else "⚠️ ALERTA IDENTIDAD"

            texto_x = f"🏛️ {fecha.upper()}\n\n📌 {titular}\n\n{dato}\n\n#HistoriaEconomica #Argentina"
            estado = "PUBLICADO" if p.get("publicado") else "PENDIENTE"
            verificado = "SI" if p.get("verificado") else "NO"
            writer.writerow([
                p.get("id"), estado, verificado, control_anon, origen, fecha,
                titular, dato, fuente, tipo_val, caption_ig, texto_x
            ])
    print(f"Planilla CSV de auditoría ({ruta_csv}) sincronizada.")

def exportar_excel():
    """Genera auditoria_datos_hde.xlsx y sincroniza control_publicaciones.csv desde datos.json."""
    if not os.path.exists(JSON_PATH):
        print(f"Error: No se encontró {JSON_PATH}")
        sys.exit(1)

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        posts = json.load(f)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Auditoría HDE"
    ws.views.sheetView[0].showGridLines = True

    # Estilos
    header_fill = PatternFill(start_color="0C0E12", end_color="0C0E12", fill_type="solid")
    header_font = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
    font_base = Font(name="Segoe UI", size=10)
    font_code = Font(name="Consolas", size=9)
    font_bold = Font(name="Segoe UI", size=10, bold=True)

    border_thin = Border(
        left=Side(style="thin", color="E2E8F0"),
        right=Side(style="thin", color="E2E8F0"),
        top=Side(style="thin", color="E2E8F0"),
        bottom=Side(style="thin", color="E2E8F0"),
    )

    fill_pub = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")     # Verde suave
    fill_verif = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")   # Amarillo suave
    fill_noverif = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid") # Rojo suave
    fill_limpio = PatternFill(start_color="ECFDF5", end_color="ECFDF5", fill_type="solid")  # Verde esmeralda suave
    fill_alerta = PatternFill(start_color="FEF2F2", end_color="FEF2F2", fill_type="solid")  # Rojo alerta
    font_limpio = Font(name="Segoe UI", size=10, bold=True, color="047857")
    font_alerta = Font(name="Segoe UI", size=10, bold=True, color="B91C1C")
    fill_zebra = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

    # 1. Escribir Encabezados
    for col_idx, (col_nombre, col_width, _) in enumerate(COLUMNAS_EXCEL, start=1):
        cell = ws.cell(row=1, column=col_idx, value=col_nombre)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=False)
        ws.column_dimensions[get_column_letter(col_idx)].width = col_width

    ws.row_dimensions[1].height = 28

    # 2. Poblar datos sanitizados
    for row_idx, p in enumerate(posts, start=2):
        es_pub = p.get("publicado", False)
        es_verif = p.get("verificado", False)

        val_pub = "SI" if es_pub else "NO"
        val_verif = "SI" if es_verif else "NO"

        origen = sanitizar_identidad(p.get("origen_guion", "Lote Fundacional HDE"))
        fecha = sanitizar_identidad(p.get("fecha_historica", ""))
        es_efe = "SI" if p.get("es_efemeride", False) else "NO"
        cat = sanitizar_identidad(p.get("categoria", "HISTORIA MONETARIA"))
        titular = sanitizar_identidad(p.get("titular", ""))
        dato = sanitizar_identidad(p.get("dato_clave", ""))
        fuente = sanitizar_identidad(p.get("fuente_oficial", ""))
        tipo_val = sanitizar_identidad(p.get("tipo_valor", ""))
        caption = sanitizar_identidad(p.get("caption", ""))
        estado_ia = p.get("estado_auditoria_ia", "")
        problema = sanitizar_identidad(p.get("problema_detectado", ""))
        arreglo = sanitizar_identidad(p.get("arreglo_sugerido", ""))

        # Evaluación de anonimato sobre toda la fila
        texto_fila = f"{titular} {dato} {caption} {fuente} {tipo_val} {origen} {fecha}"
        es_limpio = evaluar_anonimato_texto(texto_fila)
        val_anon = "LIMPIO" if es_limpio else "⚠️ ALERTA IDENTIDAD"

        valores_fila = [
            p.get("id"),
            val_pub,
            val_verif,
            val_anon,
            origen,
            fecha,
            es_efe,
            cat,
            titular,
            f"=LEN(I{row_idx})",
            dato,
            f"=LEN(K{row_idx})",
            fuente,
            tipo_val,
            caption,
            estado_ia,
            problema,
            arreglo
        ]

        ws.row_dimensions[row_idx].height = 22

        for col_idx, val in enumerate(valores_fila, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.border = border_thin
            _, _, align_h = COLUMNAS_EXCEL[col_idx - 1]

            # Formato y estilo por columna
            if col_idx == 1:
                cell.font = font_bold
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif col_idx == 2: # PUBLICADO
                cell.font = font_bold
                cell.alignment = Alignment(horizontal="center", vertical="center")
                if es_pub:
                    cell.fill = fill_pub
            elif col_idx == 3: # VERIFICADO
                cell.font = font_bold
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.fill = fill_verif if es_verif else fill_noverif
            elif col_idx == 4: # CONTROL_ANONIMATO
                cell.alignment = Alignment(horizontal="center", vertical="center")
                if es_limpio:
                    cell.font = font_limpio
                    cell.fill = fill_limpio
                else:
                    cell.font = font_alerta
                    cell.fill = fill_alerta
            elif col_idx in (10, 12): # Fórmulas de longitud
                cell.font = font_code
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif col_idx in (9, 11, 15): # Textos largos
                cell.font = font_base
                cell.alignment = Alignment(horizontal=align_h, vertical="center", wrap_text=False)
            else:
                cell.font = font_base
                cell.alignment = Alignment(horizontal=align_h, vertical="center")

            # Zebra para legibilidad en filas pares no coloreadas
            if col_idx not in (2, 3, 4) and row_idx % 2 == 0:
                cell.fill = fill_zebra

    # Congelar paneles: Encabezado fijo y columnas ID, PUBLICADO, VERIFICADO, CONTROL_ANONIMATO fijas
    ws.freeze_panes = "E2"

    # Activar autofiltro en toda la tabla
    ws.auto_filter.ref = ws.dimensions

    wb.save(EXCEL_PATH)
    print(f"✅ Excel de auditoría generado exitosamente: {EXCEL_PATH} ({len(posts)} registros)")

    # Sincronizar CSV complementario
    actualizar_csv_audit(posts)

def importar_excel():
    """Lee auditoria_datos_hde.xlsx y actualiza datos.json y control_publicaciones.csv con las correcciones."""
    if not os.path.exists(EXCEL_PATH):
        print(f"Error: No se encontró {EXCEL_PATH}")
        sys.exit(1)

    if not os.path.exists(JSON_PATH):
        print(f"Error: No se encontró {JSON_PATH}")
        sys.exit(1)

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        posts = json.load(f)

    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    ws = wb.active

    posts_map = {p["id"]: p for p in posts}
    actualizados = 0
    nuevos_verificados = 0
    bloqueados_seguridad = 0

    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or row[0] is None:
            continue

        try:
            post_id = int(row[0])
        except (ValueError, TypeError):
            continue

        if post_id not in posts_map:
            continue

        p = posts_map[post_id]

        # Mapeo de columnas desde Excel con sanitización obligatoria
        val_verif = str(row[2] or "").strip().upper()
        control_anon = str(row[3] or "").strip().upper()
        origen_guion = sanitizar_identidad(str(row[4] or "").strip())
        fecha_hist = sanitizar_identidad(str(row[5] or "").strip())
        es_efe_str = str(row[6] or "").strip().upper()
        categoria = sanitizar_identidad(str(row[7] or "").strip())
        titular = sanitizar_identidad(str(row[8] or "").strip())
        dato_clave = sanitizar_identidad(str(row[10] or "").strip())
        fuente_oficial = sanitizar_identidad(str(row[12] or "").strip())
        tipo_valor = sanitizar_identidad(str(row[13] or "").strip())
        caption = sanitizar_identidad(str(row[14] or "").strip())
        estado_ia = str(row[15] or "").strip().upper()
        problema = sanitizar_identidad(str(row[16] or "").strip())
        arreglo = sanitizar_identidad(str(row[17] or "").strip())

        # Evaluación de anonimato estricta sobre toda la fila
        texto_fila = f"{titular} {dato_clave} {caption} {fuente_oficial} {tipo_valor} {origen_guion} {fecha_hist}"
        fila_limpia = evaluar_anonimato_texto(texto_fila)

        # Actualizar campos editables
        if titular:
            p["titular"] = titular
        if dato_clave:
            p["dato_clave"] = dato_clave
        if fecha_hist:
            p["fecha_historica"] = fecha_hist
        if origen_guion:
            p["origen_guion"] = origen_guion
        if categoria:
            p["categoria"] = categoria
        if fuente_oficial:
            p["fuente_oficial"] = fuente_oficial
        if tipo_valor:
            p["tipo_valor"] = tipo_valor
        if caption:
            p["caption"] = caption

        p["es_efemeride"] = (es_efe_str == "SI")
        p["estado_auditoria_ia"] = estado_ia
        p["problema_detectado"] = problema
        p["arreglo_sugerido"] = arreglo

        # Regla de Seguridad y Anonimato:
        # Si la fila tiene alertas de identidad, QUEDA TERMINANTEMENTE BLOQUEADA (verificado = False)
        verif_previo = p.get("verificado", False)
        if not fila_limpia or "ALERTA" in control_anon:
            p["verificado"] = False
            p["control_anonimato"] = "⚠️ ALERTA IDENTIDAD"
            bloqueados_seguridad += 1
            print(f"⚠️ BLOQUEO DE SEGURIDAD: Post #{post_id} rechazado por rastro de identidad personal.")
        elif val_verif == "SI" or estado_ia in ("OK", "APROBADO", "CORREGIDO"):
            p["verificado"] = True
            p["control_anonimato"] = "LIMPIO"
            if not verif_previo:
                nuevos_verificados += 1
        elif val_verif == "NO":
            p["verificado"] = False
            p["control_anonimato"] = "LIMPIO"

        actualizados += 1

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    print(f"✅ Importación completada: {actualizados} registros sincronizados en {JSON_PATH}.")
    print(f"   Nuevos posts marcados como verificados: {nuevos_verificados}")
    if bloqueados_seguridad > 0:
        print(f"   ⚠️ Posts bloqueados por alerta de privacidad: {bloqueados_seguridad}")

    actualizar_csv_audit(posts)

def main():
    parser = argparse.ArgumentParser(description="Auditoría y Verificación de Datos HDE")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--exportar", action="store_true", help="Exportar datos.json a auditoria_datos_hde.xlsx y CSV")
    group.add_argument("--importar", action="store_true", help="Importar correcciones de auditoria_datos_hde.xlsx a datos.json y CSV")

    args = parser.parse_args()

    if args.exportar:
        exportar_excel()
    elif args.importar:
        importar_excel()

if __name__ == "__main__":
    main()
