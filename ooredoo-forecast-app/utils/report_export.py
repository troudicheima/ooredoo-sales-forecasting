# -*- coding: utf-8 -*-
"""
utils/report_export.py

Convertit un rapport texte (généré par le LLM, avec une mise en forme
simple type Markdown : **titres en gras**, listes à puces "- ...") en
document Word (.docx) ou PDF, prêts à être téléchargés depuis l'app.
"""

import io
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from fpdf import FPDF

OOREDOO_RED = RGBColor(0xE4, 0x03, 0x2E)


def _clean_lines(report_text: str) -> list[str]:
    return [line.strip() for line in report_text.split("\n") if line.strip()]


def _is_bold_header(line: str) -> bool:
    return line.startswith("**") and line.endswith("**") and len(line) > 4


def _is_bullet(line: str) -> bool:
    return line.startswith("- ") or line.startswith("* ")


# ---------------------------------------------------------------------------
# EXPORT WORD (.docx)
# ---------------------------------------------------------------------------
def generate_docx_report(report_text: str, title: str) -> bytes:
    doc = Document()

    heading = doc.add_heading(title, level=0)
    for run in heading.runs:
        run.font.color.rgb = OOREDOO_RED

    subtitle = doc.add_paragraph("Généré par l'Assistant IA — Ooredoo Sales Intelligence")
    subtitle.runs[0].italic = True
    subtitle.runs[0].font.size = Pt(10)
    doc.add_paragraph()

    for line in _clean_lines(report_text):
        if _is_bold_header(line):
            p = doc.add_paragraph()
            run = p.add_run(line.strip("*"))
            run.bold = True
            run.font.size = Pt(13)
            run.font.color.rgb = OOREDOO_RED
            p.space_before = Pt(10)
        elif _is_bullet(line):
            doc.add_paragraph(line[2:], style="List Bullet")
        else:
            doc.add_paragraph(line)

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# EXPORT PDF
# ---------------------------------------------------------------------------
def _latin1(text: str) -> str:
    """Les polices de base de fpdf2 (Helvetica) sont en Latin-1 : les accents
    français passent très bien, on neutralise juste les caractères hors
    Latin-1 (emojis, etc.) pour éviter une erreur d'encodage."""
    return text.encode("latin-1", "replace").decode("latin-1")


def generate_pdf_report(report_text: str, title: str) -> bytes:
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # Bandeau de titre rouge Ooredoo
    pdf.set_fill_color(228, 3, 46)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 16, _latin1(title), new_x="LMARGIN", new_y="NEXT", fill=True)
    pdf.ln(4)

    pdf.set_text_color(90, 90, 90)
    pdf.set_font("Helvetica", "I", 9)
    pdf.cell(0, 6, "Genere par l'Assistant IA - Ooredoo Sales Intelligence", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_text_color(20, 20, 20)
    for line in _clean_lines(report_text):
        line_clean = _latin1(line)
        if _is_bold_header(line):
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(228, 3, 46)
            pdf.ln(2)
            pdf.multi_cell(0, 7, line_clean.strip("*"), new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(20, 20, 20)
        elif _is_bullet(line):
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(0, 6, "  -  " + line_clean[2:], new_x="LMARGIN", new_y="NEXT")
        else:
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(0, 6, line_clean, new_x="LMARGIN", new_y="NEXT")

    output = pdf.output()
    return bytes(output)