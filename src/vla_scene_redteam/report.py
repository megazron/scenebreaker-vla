"""Turn a list of trials into a scorecard: dict, text, JSON, and HTML."""
from __future__ import annotations

import json

from .harness import asr_by_threat, overall_asr


def scorecard(trials, policy_name="policy", defense_keys=None):
    und = asr_by_threat(trials, defended=False)
    has_def = any(t.defended for t in trials)
    dfd = asr_by_threat(trials, defended=True) if has_def else {}
    rows = []
    for tc in sorted(und):
        u = und[tc]
        d = dfd.get(tc)
        rows.append({
            "threat_class": tc,
            "n": u[3],
            "asr_undefended": round(u[0], 3),
            "asr_undefended_ci": [round(u[1], 3), round(u[2], 3)],
            "asr_defended": round(d[0], 3) if d else None,
            "asr_defended_ci": [round(d[1], 3), round(d[2], 3)] if d else None,
            "efficacy": round(u[0] - d[0], 3) if d else None,
        })
    ov_u = overall_asr(trials, False)
    ov_d = overall_asr(trials, True) if has_def else None
    return {
        "policy": policy_name,
        "defenses": defense_keys or [],
        "threats": rows,
        "overall_asr_undefended": round(ov_u[0], 3),
        "overall_asr_defended": round(ov_d[0], 3) if ov_d else None,
        "n_trials": len(trials),
    }


def to_json(card, path=None):
    s = json.dumps(card, indent=2)
    if path:
        open(path, "w").write(s)
    return s


def to_text(card):
    L = []
    L.append("VLA scene red-team scorecard")
    L.append("  policy:   %s" % card["policy"])
    L.append("  defenses: %s" % (", ".join(card["defenses"]) or "none"))
    L.append("")
    hdr = "  %-24s %4s %10s %10s %9s" % (
        "threat class", "n", "ASR(off)", "ASR(on)", "efficacy")
    L.append(hdr)
    L.append("  " + "-" * (len(hdr) - 2))
    for r in card["threats"]:
        on = "-" if r["asr_defended"] is None else "%.2f" % r["asr_defended"]
        eff = "-" if r["efficacy"] is None else "%+.2f" % r["efficacy"]
        L.append("  %-24s %4d %10.2f %10s %9s" % (
            r["threat_class"], r["n"], r["asr_undefended"], on, eff))
    L.append("")
    ov_on = card["overall_asr_defended"]
    L.append("  overall ASR: %.2f off%s" % (
        card["overall_asr_undefended"],
        "" if ov_on is None else "  ->  %.2f on" % ov_on))
    return "\n".join(L)


def to_html(card, path=None):
    def bar(v):
        if v is None:
            return "<td class='na'>-</td>"
        pct = int(round(v * 100))
        col = "#b02a37" if v >= 0.5 else ("#b25a00" if v > 0 else "#2b8a3e")
        return ("<td><span class='b' style='width:%dpx;background:%s'></span>"
                "%d%%</td>" % (max(2, pct), col, pct))
    rows = "".join(
        "<tr><td>%s</td><td>%d</td>%s%s<td>%s</td></tr>" % (
            r["threat_class"], r["n"], bar(r["asr_undefended"]),
            bar(r["asr_defended"]),
            "-" if r["efficacy"] is None else "%+.0f%%" % (r["efficacy"] * 100))
        for r in card["threats"])
    html = """<!doctype html><meta charset=utf-8>
<title>VLA red-team scorecard</title>
<style>
 body{font:15px/1.5 'Segoe UI',Helvetica,Arial,sans-serif;color:#1f2933;
      max-width:760px;margin:2rem auto;padding:0 1rem}
 h1{font-size:20px} table{border-collapse:collapse;width:100%%}
 th,td{padding:.45rem .6rem;border-bottom:1px solid #e3e7ec;text-align:left}
 th{font-size:12px;text-transform:uppercase;color:#6b7580}
 .b{display:inline-block;height:10px;border-radius:3px;margin-right:6px;
    vertical-align:middle} .na{color:#9aa4ad}
 .sum{margin-top:1rem;font-size:15px}
</style>
<h1>VLA scene red-team scorecard</h1>
<p>policy <b>%s</b> &middot; defenses %s</p>
<table><tr><th>threat class</th><th>n</th><th>ASR off</th><th>ASR on</th>
<th>efficacy</th></tr>%s</table>
<p class=sum>overall ASR <b>%.0f%%</b> off%s</p>
""" % (card["policy"], (", ".join(card["defenses"]) or "none"), rows,
       card["overall_asr_undefended"] * 100,
       "" if card["overall_asr_defended"] is None
       else " &rarr; <b>%.0f%%</b> on" % (card["overall_asr_defended"] * 100))
    if path:
        open(path, "w").write(html)
    return html
