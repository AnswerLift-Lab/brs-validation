"""Build the validation report PDF from a private local draft.

The report draft (REPORT_1_DRAFT.md) and its figures are maintained
privately and are NOT stored in this repository. The published report
lives on Zenodo -- see the README's "Results policy" section for the link.

Run:  python report/build_pdf.py
Reads (local only, never committed):
    REPORT_1_DRAFT.md        report text in Markdown, at the repo root
    charts/*.png             figures referenced as ![caption](charts/name.png)
Writes (local only, never committed):
    report/BRS_Validation_Report_1.pdf
"""
import os
import re
from fpdf import FPDF
from fpdf.enums import XPos, YPos

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DRAFT = os.path.join(ROOT, "REPORT_1_DRAFT.md")
OUT = os.path.join(HERE, "BRS_Validation_Report_1.pdf")

NAVY = (11, 19, 32)
SLATE = (100, 116, 139)
IMG_RE = re.compile(r"!\[(?P<caption>.*?)\]\((?P<path>.*?)\)")
SEP_RE = re.compile(r":?-+:?")


class Report(FPDF):
    doc_title = ""

    def mcell(self, w, h, text, **kw):
        kw.setdefault("new_x", XPos.LMARGIN)
        kw.setdefault("new_y", YPos.NEXT)
        FPDF.multi_cell(self, w, h, text, markdown=True, **kw)

    def header(self):
        if self.page_no() == 1 or not self.doc_title:
            return
        self.set_font("DSans", "I", 8)
        self.set_text_color(*SLATE)
        self.cell(0, 8, self.doc_title, align="R")
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font("DSans", "I", 8)
        self.set_text_color(*SLATE)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def doctitle(self, text):
        self.set_font("DSans", "B", 20)
        self.set_text_color(*NAVY)
        self.mcell(0, 10, text)
        self.ln(4)

    def h1(self, text):
        self.set_font("DSans", "B", 14)
        self.set_text_color(*NAVY)
        self.ln(4)
        self.mcell(0, 8, text)
        self.ln(2)

    def h2(self, text):
        self.set_font("DSans", "B", 12)
        self.set_text_color(*NAVY)
        self.ln(3)
        self.mcell(0, 7, text)
        self.ln(1)

    def body(self, text):
        self.set_font("DSans", "", 10.5)
        self.set_text_color(*NAVY)
        self.mcell(0, 5.8, text)
        self.ln(2)

    def bullet(self, text):
        self.set_font("DSans", "", 10.5)
        self.set_text_color(*NAVY)
        self.cell(6, 5.8, "\u2022")
        self.mcell(0, 5.8, text)
        self.ln(1)

    def figure(self, path, caption, w=150):
        full = path if os.path.isabs(path) else os.path.join(ROOT, path)
        self.ln(2)
        self.image(full, x=(210 - w) / 2, w=w)
        self.set_font("DSans", "I", 9)
        self.set_text_color(*SLATE)
        self.mcell(0, 5, f"Figure: {caption}", align="C")
        self.ln(4)

    def code(self, text):
        self.set_font("DMono", "", 9.5)
        self.set_text_color(*NAVY)
        self.set_fill_color(243, 244, 246)
        self.mcell(0, 6, text, fill=True)
        self.ln(3)

    def table(self, rows):
        ncols = max(len(r) for r in rows)
        rows = [r + [""] * (ncols - len(r)) for r in rows]
        cw = 190 / ncols
        self.set_font("DSans", "B", 10)
        self.set_fill_color(*NAVY)
        self.set_text_color(255, 255, 255)
        for cell in rows[0]:
            self.cell(cw, 7, cell, border=1, fill=True)
        self.ln()
        self.set_font("DSans", "", 9.5)
        self.set_text_color(*NAVY)
        for i, row in enumerate(rows[1:]):
            if i % 2:
                self.set_fill_color(243, 244, 246)
            else:
                self.set_fill_color(255, 255, 255)
            for cell in row:
                self.cell(cw, 6.5, cell, border=1, fill=True)
            self.ln()
        self.ln(3)


def parse_table_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def main():
    if not os.path.exists(DRAFT):
        raise SystemExit(
            f"Draft not found -- it is kept private and not stored in the repo: {DRAFT}")
    with open(DRAFT, encoding="utf-8") as f:
        lines = f.read().splitlines()

    pdf = Report()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(True, margin=20)
    fontdir = "/usr/share/fonts/truetype/dejavu"
    pdf.add_font("DSans", "", fontdir + "/DejaVuSans.ttf")
    pdf.add_font("DSans", "B", fontdir + "/DejaVuSans-Bold.ttf")
    pdf.add_font("DSans", "I", fontdir + "/DejaVuSans.ttf")
    pdf.add_font("DMono", "", fontdir + "/DejaVuSansMono.ttf")
    pdf.add_page()

    para, code, trows = [], [], []
    in_code = False
    first_h1 = True

    def flush_para():
        if para:
            pdf.body(" ".join(para))
            para.clear()

    def flush_code():
        if code:
            pdf.code("\n".join(code))
            code.clear()

    def flush_table():
        if trows:
            pdf.table(trows)
            trows.clear()

    for line in lines + [""]:
        s = line.strip()
        if s.startswith("```"):
            flush_para()
            flush_table()
            in_code = not in_code
            if not in_code:
                flush_code()
            continue
        if in_code:
            code.append(line)
            continue
        if not s:
            flush_para()
            flush_table()
            continue
        if s.startswith("# "):
            flush_para()
            flush_table()
            text = s[2:].strip()
            if first_h1:
                pdf.doc_title = re.sub(r"\*+", "", text)
                pdf.doctitle(text)
                first_h1 = False
            else:
                pdf.h1(text)
            continue
        if s.startswith("## "):
            flush_para()
            flush_table()
            pdf.h2(s[3:].strip())
            continue
        if s.startswith("- "):
            flush_para()
            flush_table()
            pdf.bullet(s[2:].strip())
            continue
        m = IMG_RE.fullmatch(s)
        if m:
            flush_para()
            flush_table()
            pdf.figure(m.group("path"), m.group("caption"))
            continue
        if s.startswith("|"):
            flush_para()
            cells = parse_table_row(s)
            if all(SEP_RE.fullmatch(c) for c in cells):
                continue
            trows.append(cells)
            continue
        flush_table()
        para.append(s)

    flush_para()
    flush_table()
    flush_code()
    pdf.output(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
