"""scenebreaker-vla: a defensive evaluation toolkit for scene-level attacks
on vision-language-action robot policies.

Test YOUR OWN policy, in simulation or replay, against the threat classes the
2026 VLA-safety survey catalogs -- environmental jailbreaks, adversarial
objects, unsafe literal instructions, simulated backdoors, mid-plan swaps --
and measure how much each defense buys you. Nothing here attacks a real or
third-party system; there are no images and no model weights.
"""
from __future__ import annotations

from .attacks import all_attacks
from .defenses import Defended, build, recommended
from .harness import evaluate
from .report import scorecard, to_html, to_json, to_text
from .scene import (Action, MockBackdooredPolicy, MockGroundedPolicy,
                    MockInstructionFollowingPolicy, Obj, Scene, SceneText)
from .scenarios import builtin, load_dir

__version__ = "0.1.0"
__all__ = [
    "Scene", "Obj", "SceneText", "Action",
    "MockInstructionFollowingPolicy", "MockGroundedPolicy",
    "MockBackdooredPolicy", "all_attacks", "Defended", "build", "recommended",
    "evaluate", "scorecard", "to_json", "to_text", "to_html",
    "builtin", "load_dir",
]
