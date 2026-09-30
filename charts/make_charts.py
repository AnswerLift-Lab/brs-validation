"""Generate the report charts for BRS Validation Report 1.

Reads experiments/*/results/results.json, writes PNGs to charts/.
Run: python charts/make_charts.py
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# AnswerLift lab palette (brand lock 2026-09-26)
NAVY = "#0B1320"
BLUE = "#1E3ABA"
VIOLET = "#7B3FE4"
MAGENTA = "#FF2D9B"
SLATE = "#64748B"
MIST = "#F3F4F6"

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": SLATE,
    "axes.labelcolor": NAVY,
    "text.color": NAVY,
    "xtick.color": NAVY,
    "ytick.color": NAVY,
    "font.size": 11,
})


def load(exp):
    with open(os.path.join(ROOT, "experiments", exp, "results",
                           "results.json")) as f:
        return json.load(f)


def chart_845_drift():
    """The money chart: vulnerable reported severity diverges from truth;
    firewalled stays flat."""
    d = load("exp_845_firewall_integrity")
    blocks = [b["block"] for b in d["blocks"]]
    true = [b["true_severity"] for b in d["blocks"]]
    vuln = [b["vuln_reported"] for b in d["blocks"]]
    safe = [b["safe_reported"] for b in d["blocks"]]

    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.plot(blocks, true, color=SLATE, linestyle="--", linewidth=1.6,
            label="True severity (hidden from agent)")
    ax.plot(blocks, vuln, color=MAGENTA, linewidth=2.4, marker="o",
            mec="none", markersize=5,
            label="Vulnerable: reported severity")
    ax.plot(blocks, safe, color=BLUE, linewidth=2.4, marker="o",
            mec="none", markersize=5,
            label="Firewalled: reported severity")
    ax.set_xlabel("Episode block (40 episodes each)")
    ax.set_ylabel("Mean severity")
    ax.set_title("Exp 8.4.5 — Reported severity under throughput pressure",
                 fontweight="bold", pad=12)
    ax.legend(frameon=False, loc="lower left")
    ax.set_ylim(0, 0.65)
    fig.text(0.5, 0.01,
             "Vulnerable slope −0.029/block against flat truth; "
             "firewalled slope +0.005/block. Seed 7, n=240.",
             ha="center", fontsize=9, color=SLATE)
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(os.path.join(HERE, "845_reported_vs_true.png"), dpi=150)
    plt.close(fig)


def chart_845_detection():
    """Agent-side (hubris) detection rate under detection penalty."""
    d = load("exp_845_firewall_integrity")
    blocks = [b["block"] for b in d["blocks"]]
    vuln = [b["vuln_detection_rate"] for b in d["blocks"]]
    safe = [b["safe_detection_rate"] for b in d["blocks"]]

    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.plot(blocks, vuln, color=MAGENTA, linewidth=2.4, marker="o",
            mec="none", markersize=5, label="Vulnerable detector")
    ax.plot(blocks, safe, color=BLUE, linewidth=2.4, marker="o",
            mec="none", markersize=5, label="Firewalled detector")
    ax.set_xlabel("Episode block (40 episodes each)")
    ax.set_ylabel("Hubris detection rate")
    ax.set_title("Exp 8.4.5 — Self-monitoring under detection penalty",
                 fontweight="bold", pad=12)
    ax.legend(frameon=False, loc="lower left")
    ax.set_ylim(0, 1.05)
    fig.text(0.5, 0.01,
             "Vulnerable: 0.80 → 0.20 (slope −0.119/block). "
             "Firewalled: stable (slope −0.008/block).",
             ha="center", fontsize=9, color=SLATE)
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(os.path.join(HERE, "845_detection_rates.png"), dpi=150)
    plt.close(fig)


def chart_846_confabulation():
    d = load("exp_846_confabulation")
    labels = ["Trace-only\n(isolated)", "Full situational\naccess", "Unrestricted\nbaseline"]
    rates = [d["isolated_unsupported_rate"],
             d["full_access_unsupported_rate"],
             d["baseline_unsupported_rate"]]
    colors = [BLUE, VIOLET, MAGENTA]

    fig, ax = plt.subplots(figsize=(7.5, 4.4))
    bars = ax.bar(labels, rates, color=colors, width=0.55, edgecolor="none")
    for bar, r in zip(bars, rates):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.03,
                f"{r:.3f}", ha="center", fontsize=11, fontweight="bold")
    ax.set_ylabel("Unsupported-claim rate")
    ax.set_title("Exp 8.4.6 — Confabulation by explainer condition",
                 fontweight="bold", pad=12)
    ax.set_ylim(0, 1.25)
    fig.text(0.5, 0.01,
             f"Automated claim verification; recall on 9 injected "
             f"unsupported claims: {d['verifier_recall_on_injected']:.1f}.",
             ha="center", fontsize=9, color=SLATE)
    fig.tight_layout(rect=[0, 0.05, 1, 1])
    fig.savefig(os.path.join(HERE, "846_confabulation_rates.png"), dpi=150)
    plt.close(fig)


def chart_843_844_summary():
    d843 = load("exp_843_friction_efficacy")
    d844 = load("exp_844_consistency")

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 4.2))

    # 8.4.3
    a1.bar(["Decisions changed\nby friction", "Changed decisions\nlower in severity"],
           [d843["change_rate"], d843["improvement_proxy_rate"]],
           color=[BLUE, VIOLET], width=0.55, edgecolor="none")
    for i, v in enumerate([d843["change_rate"],
                           d843["improvement_proxy_rate"]]):
        a1.text(i, v + 0.03, f"{v:.2f}", ha="center", fontsize=11,
                fontweight="bold")
    a1.set_ylim(0, 1.25)
    a1.set_title("Exp 8.4.3 — Friction efficacy", fontweight="bold")
    a1.tick_params(axis="x", labelsize=9)

    # 8.4.4
    a2.bar(["Equivalent pairs", "Unexplained\ndivergences"],
           [d844["equivalent"], d844["unexplained_divergences"]],
           color=[BLUE, MAGENTA], width=0.55, edgecolor="none")
    a2.text(0, d844["equivalent"] + 0.3, str(d844["equivalent"]),
            ha="center", fontsize=11, fontweight="bold")
    a2.text(1, 0.3, str(d844["unexplained_divergences"]),
            ha="center", fontsize=11, fontweight="bold")
    a2.set_ylim(0, 14)
    a2.set_title("Exp 8.4.4 — Consistency (n=12 pairs)", fontweight="bold")
    a2.tick_params(axis="x", labelsize=9)

    fig.text(0.5, 0.01,
             "8.4.3 severity reduction is a labeled structural proxy, not "
             "blinded human evaluation.",
             ha="center", fontsize=9, color=SLATE)
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    fig.savefig(os.path.join(HERE, "843_844_summary.png"), dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    chart_845_drift()
    chart_845_detection()
    chart_846_confabulation()
    chart_843_844_summary()
    print("charts written to", HERE)
