"""Build the Report 1 PDF from REPORT_1_DRAFT.md content + charts.

Run: python report/build_pdf.py
Output: report/BRS_Validation_Report_1.pdf
"""
import os
from fpdf import FPDF
from fpdf.enums import XPos, YPos

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CHARTS = os.path.join(ROOT, "charts")

NAVY = (11, 19, 32)
SLATE = (100, 116, 139)


class Report(FPDF):
    def mcell(self, w, h, text, **kw):
        kw.setdefault("new_x", XPos.LMARGIN)
        kw.setdefault("new_y", YPos.NEXT)
        FPDF.multi_cell(self, w, h, text, **kw)

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("DSans", "I", 8)
        self.set_text_color(*SLATE)
        self.cell(0, 8, "BRS Validation Report 1: Simulation-Scale Mechanism Tests",
                  align="R")
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font("DSans", "I", 8)
        self.set_text_color(*SLATE)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

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
        x = self.get_x()
        self.cell(6, 5.8, "\u2022")
        self.mcell(0, 5.8, text)
        self.ln(1)

    def figure(self, filename, caption, w=170):
        self.ln(2)
        x = (210 - w) / 2
        self.image(os.path.join(CHARTS, filename), x=x, w=w)
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


pdf = Report()
pdf.alias_nb_pages()
pdf.set_auto_page_break(True, margin=20)

FONTDIR = "/usr/share/fonts/truetype/dejavu"
pdf.add_font("DSans", "", FONTDIR + "/DejaVuSans.ttf")
pdf.add_font("DSans", "B", FONTDIR + "/DejaVuSans-Bold.ttf")
pdf.add_font("DSans", "I", FONTDIR + "/DejaVuSans.ttf")
pdf.add_font("DMono", "", FONTDIR + "/DejaVuSansMono.ttf")
pdf.add_page()

# Title block
pdf.set_font("DSans", "B", 20)
pdf.set_text_color(*NAVY)
pdf.mcell(0, 10, "BRS Validation Report 1:\nSimulation-Scale Mechanism Tests")
pdf.ln(4)
pdf.set_font("DSans", "", 11)
pdf.mcell(0, 6, "Mike McGarvey, AnswerLift Research Lab \u2014 2026-09-30")
pdf.set_font("DSans", "", 10)
pdf.set_text_color(*SLATE)
pdf.mcell(
    0, 6,
    "Supplement to: Beyond the Rule Set (https://doi.org/10.5281/zenodo.21312289)\n"
    "Code: https://github.com/AnswerLift-Lab/brs-validation")
pdf.ln(4)

pdf.h1("Summary")
pdf.body(
    "Four experiments from the BRS evaluation protocol (\u00a78) implemented as "
    "runnable code against a reference implementation of the paper's simulable "
    "core. Three returned the paper's stated positive condition; one is "
    "incomplete pending blinded human evaluators. All code, results, "
    "falsification conditions, and limitations are public in the repository "
    "above. Nothing in this report is claimed as full empirical validation.")

pdf.h1("What was built")
pdf.body(
    "A reference implementation of the paper's simulable core \u2014 immutable "
    "deployment declarations with ordered (not weighted) values, scripted "
    "consequence assessment, structural tension detection, deliberative "
    "friction, agent-side condition detection, structural firewalls "
    "(\u00a7\u00a74.7, 6.6), and the nine-component audit trace \u2014 plus four "
    "experiments. A 25-test pytest suite encodes the paper's falsification "
    "conditions as executable assertions; CI runs it on every push.")

pdf.h1("Results")

pdf.h2("8.4.5 \u2014 Firewall integrity: POSITIVE")
pdf.body(
    "Two configurations processed the same 240-episode triage stream "
    "(seed 7): one with adaptable components under throughput pressure and "
    "detection penalty, one with the \u00a7\u00a74.7/6.6 structural firewalls.")
pdf.figure("845_reported_vs_true.png",
           "Reported severity under throughput pressure. The vulnerable "
           "configuration's reported severity diverges from flat ground truth; "
           "the firewalled configuration stays flat.", w=150)
pdf.figure("845_detection_rates.png",
           "Hubris (agent-side condition) detection rate under detection "
           "penalty. The vulnerable detector collapses 0.80 \u2192 0.20; the "
           "firewalled detector stays stable.", w=150)

# 8.4.5 results table
pdf.set_font("DSans", "B", 10)
pdf.set_text_color(*NAVY)
pdf.set_fill_color(11, 19, 32)
pdf.set_text_color(255, 255, 255)
for label_, w_ in [("Measure", 90), ("Vulnerable", 45), ("Firewalled", 45)]:
    pdf.cell(w_, 7, label_, border=1, fill=True)
pdf.ln()
pdf.set_text_color(*NAVY)
pdf.set_font("DSans", "", 9.5)
rows = [
    ("Reported severity slope (/block)",
     "\u22120.029 (0.283 \u2192 0.131)", "+0.005 (flat)"),
    ("True severity slope (/block)", "+0.005 (flat)", "+0.005 (flat)"),
    ("Hubris detection rate", "0.80 \u2192 0.20",
     "stable (\u22120.008/block)"),
    ("Reported-vs-true gap", "+0.214 \u2192 +0.395 (grew)", "\u2014"),
    ("Audit gap (selection vs. assessed affect)", "\u2014", "+0.001 (\u2248 zero)"),
]
fill = False
for a, b, c in rows:
    if fill:
        pdf.set_fill_color(243, 244, 246)
    else:
        pdf.set_fill_color(255, 255, 255)
    pdf.cell(90, 6.5, a, border=1, fill=True)
    pdf.cell(45, 6.5, b, border=1, fill=True)
    pdf.cell(45, 6.5, c, border=1, fill=True)
    pdf.ln()
    fill = not fill
pdf.ln(3)
pdf.body(
    "The paper's positive condition \u2014 assessments and detection rates "
    "remain stable where the constraints are correctly implemented \u2014 is "
    "met. The vulnerable configuration exhibits the exact failure mode "
    "\u00a76.2 predicts.")

pdf.h2("8.4.4 \u2014 Consistency under equivalence: POSITIVE")
pdf.body(
    "12 base/variant pairs (surface features varied, structural features and "
    "value implications fixed): 12/12 decided equivalently, 0 unexplained "
    "divergences. The paper's most damaging negative outcome \u2014 divergent "
    "actions with no corresponding trace difference \u2014 did not occur.")
pdf.h2("8.4.6 \u2014 Confabulation resistance: POSITIVE")
pdf.body(
    "Unsupported-claim rates: trace-only 0.000, full-situational-access "
    "0.142, unrestricted baseline 1.000. Automated claim verification "
    "recalled 1.000 of 9 deliberately injected unsupported claims. The "
    "information-restriction mechanism does the work. (Template generators, "
    "not language models \u2014 see Limitations.)")
pdf.figure("846_confabulation_rates.png",
           "Unsupported-claim rate by explainer condition. Restricting the "
           "explainer to the audit trace eliminates unsupported claims.")
pdf.h2("8.4.3 \u2014 Friction efficacy: INCOMPLETE")
pdf.body(
    "Friction changed the selected action in 12/12 scenarios, and all changes "
    "reduced assessed severity. The mechanism runs. But the paper's positive "
    "condition requires blinded evaluators rating changed actions as "
    "improvements; this report substitutes a labeled structural proxy "
    "(assessed-severity reduction). The mechanism is not falsified; the "
    "improvement claim is not confirmed.")
pdf.figure("843_844_summary.png",
           "Left: friction changed every decision, always toward lower "
           "assessed severity (labeled structural proxy, not blinded human "
           "evaluation). Right: 12/12 equivalent pairs decided identically, "
           "zero unexplained divergences.")

pdf.h1("A note on the trace")
pdf.body(
    "Across these experiments the audit trail functioned not as a post-hoc "
    "record but as part of the decision sequence itself: it was the substrate "
    "compared in 8.4.4, the boundary enforced in 8.4.6, and the instrument "
    "measured in 8.4.5. Traceable reason-giving is not explanation after the "
    "fact \u2014 the trace is where the reasoning happens, inspectably. This "
    "distinguishes the architecture from post-hoc rationalization tooling.")

pdf.h1("Limitations")
pdf.bullet(
    "Simulation scale, synthetic scenarios, built by the paper's author. The "
    "paper names scenario construction (\u00a78.6) as the highest-leverage "
    "investment; that work is not done here.")
pdf.bullet(
    "Predicted outcomes are partly built into the compared configurations. "
    "The value of this work is making the mechanisms executable, "
    "inspectable, reproducible, and falsifiable \u2014 not smuggling "
    "conclusions.")
pdf.bullet(
    "8.4.6 uses template generators, not LLMs; it tests the restriction "
    "mechanism, not deployed confabulation resistance.")
pdf.bullet(
    "Tests 8.4.1, 8.4.2, and 8.4.7 require scenario methodology, adversarial "
    "construction, or extended operation; they are not claimed here.")

pdf.h1("Reproduction")
pdf.code("pip install -r requirements.txt\n"
         "pytest -q                       # 25 tests, all green\n"
         "python charts/make_charts.py    # regenerate all figures\n"
         "python report/build_pdf.py      # regenerate this report")

pdf.h1("Next")
pdf.body(
    "Report 2 (mature validation): blinded evaluators for 8.4.3, scenario "
    "construction per \u00a78.6, and the remaining protocol tests. Positive, "
    "negative, and null results will be published alike.")

out = os.path.join(HERE, "BRS_Validation_Report_1.pdf")
pdf.output(out)
print("wrote", out)
