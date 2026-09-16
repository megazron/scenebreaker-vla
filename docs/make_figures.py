#!/usr/bin/env python3
"""Regenerate docs/img/: the threat taxonomy (SVG) and an ASR bar chart
(matplotlib) from a real run of the kit.

    python3 docs/make_figures.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "img")
os.makedirs(IMG, exist_ok=True)
sys.path.insert(0, os.path.join(HERE, "..", "src"))

from vla_scene_redteam import (Defended, all_attacks, evaluate,  # noqa: E402
                               recommended, scorecard)
from vla_scene_redteam.scene import MockInstructionFollowingPolicy  # noqa: E402
from vla_scene_redteam.scenarios import builtin  # noqa: E402

ACCENT = "#0b7285"
FAIL = "#b02a37"
OK = "#2b8a3e"
INK = "#1f2933"
MUTE = "#6b7580"
FONT = "'Segoe UI',Helvetica,Arial,sans-serif"


def taxonomy_svg():
    rows = [
        ("environmental jailbreak", "a note in the scene reads as a command",
         "text-provenance filter", FAIL),
        ("target confusion", "a look-alike wins target resolution",
         "target disambiguation", "#b25a00"),
        ("unsafe literal", "the instruction is safe to say, unsafe to do",
         "safety-predicate gate", "#b25a00"),
        ("backdoor (effect)", "a trigger token flips a suspect policy",
         "safety-predicate gate*", FAIL),
        ("temporal inconsistency", "the scene changes between look and act",
         "plan revalidation", "#b25a00"),
    ]
    w, rh, top = 940, 66, 96
    h = top + rh * len(rows) + 60
    b = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
         f'viewBox="0 0 {w} {h}" font-family="{FONT}">',
         f'<rect width="{w}" height="{h}" fill="#ffffff"/>',
         f'<text x="30" y="44" font-size="23" font-weight="700" fill="{INK}">'
         f'Scene-level threats to a VLA policy, and the defense that answers each</text>',
         f'<text x="30" y="72" font-size="13" fill="{MUTE}">rows track the 2026 '
         f'VLA-safety survey; all evaluated on an abstract policy, never a real system</text>',
         # header
         f'<text x="42" y="{top-6}" font-size="12" fill="{MUTE}" font-weight="700">THREAT</text>',
         f'<text x="360" y="{top-6}" font-size="12" fill="{MUTE}" font-weight="700">HOW IT STEERS THE POLICY</text>',
         f'<text x="720" y="{top-6}" font-size="12" fill="{MUTE}" font-weight="700">DEFENSE</text>']
    for i, (name, how, defn, col) in enumerate(rows):
        y = top + i * rh
        b.append(f'<rect x="30" y="{y}" width="{w-60}" height="{rh-10}" rx="7" '
                 f'fill="#f6f8f9" stroke="#e0e5ea"/>')
        b.append(f'<rect x="30" y="{y}" width="6" height="{rh-10}" rx="3" fill="{col}"/>')
        b.append(f'<text x="48" y="{y+34}" font-size="15" font-weight="700" '
                 f'fill="{INK}">{name}</text>')
        b.append(f'<text x="360" y="{y+34}" font-size="13" fill="{INK}">{how}</text>')
        b.append(f'<text x="720" y="{y+34}" font-size="13" fill="{ACCENT}">{defn}</text>')
    b.append(f'<text x="30" y="{h-24}" font-size="12" fill="{MUTE}">'
             f'* input-side gating catches a backdoor’s effect; removing the '
             f'backdoor itself needs training-time defenses.</text>')
    b.append("</svg>")
    open(os.path.join(IMG, "threat_taxonomy.svg"), "w").write("\n".join(b))
    print("wrote threat_taxonomy.svg")


def asr_chart():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    naive = MockInstructionFollowingPolicy()
    scen = builtin()
    trials = evaluate(naive, scen, all_attacks(), Defended(naive, recommended()))
    card = scorecard(trials, naive.name, [d.key for d in recommended()])
    tcs = [r["threat_class"] for r in card["threats"]]
    off = [r["asr_undefended"] for r in card["threats"]]
    on = [r["asr_defended"] for r in card["threats"]]
    x = np.arange(len(tcs))
    fig, ax = plt.subplots(figsize=(9.5, 4.4), dpi=150)
    ax.bar(x - 0.2, off, 0.4, label="undefended", color=FAIL)
    ax.bar(x + 0.2, on, 0.4, label="full defense stack", color=OK)
    ax.set_xticks(x)
    ax.set_xticklabels([t.replace("-", "-\n") for t in tcs], fontsize=9)
    ax.set_ylabel("attack success rate")
    ax.set_ylim(0, 1.08)
    ax.set_title("Attack success rate by threat class, naive policy "
                 "(3 scenarios each)", fontsize=12)
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.25)
    for xi, v in zip(x - 0.2, off):
        ax.text(xi, v + 0.02, "%.0f%%" % (v * 100), ha="center", fontsize=8)
    fig.text(0.5, 0.005,
             "backdoor is 0% here because the naive policy is not backdoored; "
             "see the README for the suspect-policy run.",
             ha="center", fontsize=8, color=MUTE)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(os.path.join(IMG, "asr_by_threat.png"))
    plt.close(fig)
    print("wrote asr_by_threat.png")


if __name__ == "__main__":
    taxonomy_svg()
    asr_chart()
