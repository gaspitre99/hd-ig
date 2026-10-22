#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Módulo de Auditoría y Verificación de Datos - Hablemos de Economía (HDE)
Permite exportar e importar bidireccionalmente entre datos.json, control_publicaciones.csv
y auditoria_datos_hde.xlsx para auditorías asistidas por IA (Claude / Gemini) o revisión humana.
"""

import sys
import os
import json
import csv
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

COLUMNAS_EXCEL = [
    ("ID", 8, "center"),
    ("PUBLICADO", 12, "center"),
    ("VERIFICADO", 13, "center"),
    ("ORIGEN_GUION", 24, "left"),
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
            "ID", "ESTADO", "VERIFICADO", "ORIGEN_GUION", "FECHA HISTÓRICA",
            "TITULAR", "DATO CLAVE", "FUENTE OFICIAL", "TIPO DE VALOR",
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
            texto_x = f"🏛️ {fecha.upper()}\n\n📌 {titular}\n\n{dato}\n\n#HistoriaEconomica #Argentina"
            estado = "PUBLICADO" if p.get("publicado") else "PENDIENTE"
            verificado = "SI" if p.get("verificado") else "NO"
            writer.writerow([
                p.get("id"), estado, verificado, origen, fecha,
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
    fill_zebra = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

    # 1. Escribir Encabezados
    for col_idx, (col_nombre, col_width, _) in enumerate(COLUMNAS_EXCEL, start=1):
        cell = ws.cell(row=1, column=col_idx, value=col_nombre)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=False)
        ws.column_dimensions[get_column_letter(col_idx)].width = col_width

    ws.row_dimensions[1].height = 28

    # 2. Poblar datos
    for row_idx, p in enumerate(posts, start=2):
        es_pub = p.get("publicado", False)
        es_verif = p.get("verificado", False)

        val_pub = "SI" if es_pub else "NO"
        val_verif = "SI" if es_verif else "NO"
        origen = p.get("origen_guion", "Lote Fundacional HDE")
        fecha = p.get("fecha_historica", "")
        es_efe = "SI" if p.get("es_efemeride", False) else "NO"
        cat = p.get("categoria", "HISTORIA MONETARIA")
        titular = p.get("titular", "")
        dato = p.get("dato_clave", "")
        fuente = p.get("fuente_oficial", "")
        tipo_val = p.get("tipo_valor", "")
        caption = p.get("caption", "")
        estado_ia = p.get("estado_auditoria_ia", "")
        problema = p.get("problema_detectado", "")
        arreglo = p.get("arreglo_sugerido", "")

        valores_fila = [
            p.get("id"),
            val_pub,
            val_verif,
            origen,
            fecha,
            es_efe,
            cat,
            titular,
            f"=LEN(H{row_idx})",
            dato,
            f"=LEN(J{row_idx})",
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
            elif col_idx in (9, 11): # Fórmulas de longitud
                cell.font = font_code
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif col_idx in (8, 10, 14): # Textos largos
                cell.font = font_base
                cell.alignment = Alignment(horizontal=align_h, vertical="center", wrap_text=False)
            else:
                cell.font = font_base
                cell.alignment = Alignment(horizontal=align_h, vertical="center")

            # Zebra para legibilidad en filas pares no coloreadas
            if col_idx not in (2, 3) and row_idx % 2 == 0:
                cell.fill = fill_zebra

    # Congelar paneles: Encabezado fijo y columnas ID, PUBLICADO, VERIFICADO fijas a la izquierda
    ws.freeze_panes = "D2"

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

        # Mapeo de columnas desde Excel
        val_verif = str(row[2] or "").strip().upper()
        origen_guion = str(row[3] or "").strip()
        fecha_hist = str(row[4] or "").strip()
        es_efe_str = str(row[5] or "").strip().upper()
        categoria = str(row[6] or "").strip()
        titular = str(row[7] or "").strip()
        dato_clave = str(row[9] or "").strip()
        fuente_oficial = str(row[11] or "").strip()
        tipo_valor = str(row[12] or "").strip()
        caption = str(row[13] or "").strip()
        estado_ia = str(row[14] or "").strip().upper()
        problema = str(row[15] or "").strip()
        arreglo = str(row[16] or "").strip()

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

        # Regla de Verificación: Se valida si el usuario puso "SI" o si la IA puso "OK"
        verif_previo = p.get("verificado", False)
        if val_verif == "SI" or estado_ia == "OK":
            p["verificado"] = True
            if not verif_previo:
                nuevos_verificados += 1
        elif val_verif == "NO":
            p["verificado"] = False

        actualizados += 1

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    print(f"✅ Importación completada: {actualizados} registros sincronizados en {JSON_PATH}.")
    print(f"   Nuevos posts marcados como verificados: {nuevos_verificados}")

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
