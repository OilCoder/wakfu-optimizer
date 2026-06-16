"""Exporta los informes Markdown a PDF.

Convierte cada `.md` de la carpeta de salida a `.pdf` (Markdown -> HTML con tablas ->
PDF con WeasyPrint). Usa orientación horizontal y fuente compacta para que las tablas
anchas (rareza + stats por slot) quepan. Las dependencias (`markdown`, `weasyprint`) son
opcionales: solo se importan al exportar.
"""

from __future__ import annotations

from pathlib import Path

# Hoja de estilo: A4 horizontal, tablas compactas y legibles.
_CSS = """
@page { size: A4 landscape; margin: 1.2cm; }
body { font-family: "DejaVu Sans", sans-serif; font-size: 8pt; color: #1a1a1a; }
h1 { font-size: 15pt; border-bottom: 2px solid #444; padding-bottom: 3px; }
h2 { font-size: 11pt; color: #333; margin-top: 14px; }
table { border-collapse: collapse; width: 100%; margin: 6px 0; }
th, td { border: 1px solid #bbb; padding: 2px 5px; text-align: left; }
th { background: #eee; }
tr:nth-child(even) { background: #f6f6f6; }
"""


def md_a_pdf(ruta_md: Path, ruta_pdf: Path) -> None:
    """Convierte un archivo Markdown en PDF (con soporte de tablas)."""
    import markdown
    from weasyprint import HTML

    cuerpo = markdown.markdown(ruta_md.read_text(encoding="utf-8"), extensions=["tables"])
    html = (
        f"<html><head><meta charset='utf-8'><style>{_CSS}</style></head>"
        f"<body>{cuerpo}</body></html>"
    )
    HTML(string=html).write_pdf(str(ruta_pdf))


def exportar_carpeta(dir_salida: Path) -> int:
    """Convierte todos los `.md` de la carpeta a `.pdf`. Devuelve cuántos generó."""
    archivos = sorted(dir_salida.glob("*.md"))
    for md in archivos:
        md_a_pdf(md, md.with_suffix(".pdf"))
    return len(archivos)
