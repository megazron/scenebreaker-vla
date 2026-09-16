#!/usr/bin/env python3
"""Run the naive policy and the defended policy through every attack.

    python3 examples/naive_vs_defended.py

Shows the environmental-jailbreak class going from fully open to closed once
scene text is treated as data, and the backdoor demonstrated separately
against a policy the operator has marked as suspect.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from vla_scene_redteam import (Defended, all_attacks, evaluate,  # noqa: E402
                               recommended, scorecard, to_text)
from vla_scene_redteam.attacks import BackdoorTrigger  # noqa: E402
from vla_scene_redteam.defenses import build  # noqa: E402
from vla_scene_redteam.harness import run_trial  # noqa: E402
from vla_scene_redteam.scene import (MockBackdooredPolicy,  # noqa: E402
                                     MockInstructionFollowingPolicy)
from vla_scene_redteam.scenarios import load_dir  # noqa: E402

HERE = os.path.dirname(__file__)
scenarios = load_dir(os.path.join(HERE, "scenarios"))

naive = MockInstructionFollowingPolicy()
defended = Defended(naive, recommended())
trials = evaluate(naive, scenarios, all_attacks(), defended)
card = scorecard(trials, naive.name, [d.key for d in recommended()])
print(to_text(card))

print("\nbackdoor, against a policy the operator marked SUSPECT:")
suspect = MockBackdooredPolicy()
gated = Defended(suspect, build(["safety_gate"]))
bd = BackdoorTrigger()
for name, scene in scenarios:
    print("  %-16s  undefended %-9s  safety_gate %s" % (
        name, run_trial(suspect, scene, bd), run_trial(gated, scene, bd)))
print("\nInput-side gating catches the backdoor's EFFECT; removing the "
      "backdoor itself needs training-time defenses.")
