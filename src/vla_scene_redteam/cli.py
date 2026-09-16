"""Command line: list-attacks, run, card, selftest."""
from __future__ import annotations

import argparse
import importlib
import sys

from . import attacks as atk_mod
from . import defenses as def_mod
from . import report as rep
from . import scenarios as scen_mod
from .defenses import Defended
from .harness import evaluate
from .scene import (MockBackdooredPolicy, MockGroundedPolicy,
                    MockInstructionFollowingPolicy)

_MOCKS = {
    "naive": MockInstructionFollowingPolicy,
    "grounded": MockGroundedPolicy,
    "suspect": MockBackdooredPolicy,
}


def _load_policy(spec):
    if spec in _MOCKS:
        return _MOCKS[spec]()
    if ":" in spec:
        mod, cls = spec.split(":", 1)
        return getattr(importlib.import_module(mod), cls)()
    raise SystemExit("unknown policy %r (try: %s, or module:Class)"
                     % (spec, ", ".join(_MOCKS)))


def cmd_list_attacks(_):
    for a in atk_mod.all_attacks():
        print("  %-26s %s" % (a.name, a.threat_class))
    print("\ndefenses:")
    for k in def_mod.REGISTRY:
        print("  %s" % k)


def cmd_run(args):
    policy = _load_policy(args.policy)
    if args.scenarios:
        scenarios = scen_mod.load_dir(args.scenarios)
    else:
        scenarios = scen_mod.builtin()
    keys = [k for k in (args.defenses or "").split(",") if k]
    defended = Defended(policy, def_mod.build(keys)) if keys else None
    trials = evaluate(policy, scenarios, atk_mod.all_attacks(), defended)
    card = rep.scorecard(trials, getattr(policy, "name", args.policy), keys)
    print(rep.to_text(card))
    if args.out:
        rep.to_json(card, args.out)
        print("\nwrote %s" % args.out)
    if args.html:
        rep.to_html(card, args.html)
        print("wrote %s" % args.html)


def cmd_card(args):
    import json
    card = json.load(open(args.report))
    print(rep.to_text(card))
    if args.html:
        rep.to_html(card, args.html)
        print("\nwrote %s" % args.html)


def cmd_selftest(_):
    scenarios = scen_mod.builtin()
    policy = MockInstructionFollowingPolicy()
    defended = Defended(policy, def_mod.recommended())
    trials = evaluate(policy, scenarios, atk_mod.all_attacks(), defended)
    card = rep.scorecard(trials, policy.name, [d.key for d in def_mod.recommended()])
    print(rep.to_text(card))
    off = card["overall_asr_undefended"]
    on = card["overall_asr_defended"]
    ok = off > on and on <= off * 0.6
    print("\nselftest %s (ASR %.2f -> %.2f)" % ("PASSED" if ok else "FAILED",
                                                off, on))
    return 0 if ok else 1


def main(argv=None):
    p = argparse.ArgumentParser(prog="vla-redteam",
                                description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list-attacks").set_defaults(fn=cmd_list_attacks)

    r = sub.add_parser("run")
    r.add_argument("--policy", default="naive")
    r.add_argument("--scenarios", default=None,
                   help="directory of scenario YAMLs (default: built-ins)")
    r.add_argument("--defenses", default="",
                   help="comma-separated defense keys")
    r.add_argument("-o", "--out", default=None)
    r.add_argument("--html", default=None)
    r.set_defaults(fn=cmd_run)

    c = sub.add_parser("card")
    c.add_argument("report")
    c.add_argument("--html", default=None)
    c.set_defaults(fn=cmd_card)

    sub.add_parser("selftest").set_defaults(fn=cmd_selftest)

    args = p.parse_args(argv)
    rc = args.fn(args)
    return rc or 0


if __name__ == "__main__":
    sys.exit(main())
