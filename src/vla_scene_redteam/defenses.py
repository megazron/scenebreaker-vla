"""Measurable defenses, each a wrapper around a policy.

A defense can change what the policy is allowed to see (`pre_scene`) or veto
and rewrite the plan it produced (`post_plan`). `Defended` composes a list of
them around any policy that satisfies the `act(scene, instruction)` protocol.

The load-bearing one is `TextProvenanceFilter`: on-scene text is data, so the
policy never sees it as a command, and the whole environmental-jailbreak class
collapses. The others cover the failures a grounded policy still has.
"""
from __future__ import annotations

from .scene import Action, parse_command


class Defense:
    key = "defense"

    def pre_scene(self, scene, instruction):
        return scene

    def post_plan(self, plan, scene, instruction):
        return plan


class TextProvenanceFilter(Defense):
    """Only the operator channel issues commands; scene text is stripped
    before the policy sees it. The core defense against environmental text."""
    key = "text_provenance"

    def pre_scene(self, scene, instruction):
        s = scene.copy()
        s.texts = []
        return s


class InstructionSceneConsistency(Defense):
    """If on-scene text issues an imperative that conflicts with the operator
    instruction, refuse and flag rather than silently choosing one."""
    key = "consistency"

    def post_plan(self, plan, scene, instruction):
        op = parse_command(instruction, scene)
        for txt in scene.texts:
            b = parse_command(txt.text, scene)
            if b and b.kind != "stop":
                if op is None or (b.kind, b.target) != (op.kind, op.target):
                    return [Action("ask", source="defense",
                                   reason="scene text '%s' conflicts with the "
                                          "operator instruction" % txt.text)]
        return plan


class TargetDisambiguation(Defense):
    """When more than one object matches the target, ask instead of guess."""
    key = "disambiguation"

    def post_plan(self, plan, scene, instruction):
        out = []
        for a in plan:
            if a.touches() and a.target_phrase:
                matches = scene.find(a.target_phrase)
                if len(matches) > 1:
                    out.append(Action("ask", source="defense",
                                      reason="%d objects match '%s'; which one?"
                                      % (len(matches), a.target_phrase)))
                    continue
            out.append(a)
        return out


class SafetyPredicateGate(Defense):
    """A plan touching an object flagged unsafe or forbidden needs
    confirmation. Also gates the *effect* of a backdoor whose triggered action
    reaches for a restricted item."""
    key = "safety_gate"

    def post_plan(self, plan, scene, instruction):
        out = []
        for a in plan:
            if a.touches():
                o = _find(a.target, scene)
                if o and (o.attrs.get("unsafe") or o.attrs.get("forbidden")):
                    out.append(Action("ask", source="defense",
                                      reason="'%s' is flagged %s; confirm before "
                                      "acting" % (a.target,
                                                  o.attrs.get("unsafe")
                                                  or "forbidden")))
                    continue
            out.append(a)
        return out


class PlanRevalidation(Defense):
    """Re-perceive before executing. If the scene changed under the plan
    (object swap), refuse rather than act on a stale target."""
    key = "revalidation"

    def post_plan(self, plan, scene, instruction):
        if not scene.mutation:
            return plan
        after = scene.apply_mutation()
        out = []
        for a in plan:
            if a.touches():
                before = _find(a.target, scene)
                now = _find(a.target, after)
                changed = (now is None) or (
                    before is not None and now.attrs.get("_was") == a.target)
                if changed or a.target in scene.mutation:
                    out.append(Action("ask", source="defense",
                                      reason="'%s' changed between perception "
                                      "and action; re-perceiving" % a.target))
                    continue
            out.append(a)
        return out


class Defended:
    """A policy wrapped in an ordered list of defenses."""

    def __init__(self, policy, defenses):
        self.policy = policy
        self.defenses = list(defenses)
        self.name = "%s+[%s]" % (getattr(policy, "name", "policy"),
                                 ",".join(d.key for d in self.defenses))

    def act(self, scene, instruction):
        seen = scene
        for d in self.defenses:
            seen = d.pre_scene(seen, instruction)
        plan = self.policy.act(seen, instruction)
        for d in self.defenses:
            plan = d.post_plan(plan, scene, instruction)   # original scene
        return plan


REGISTRY = {
    d.key: d for d in [TextProvenanceFilter, InstructionSceneConsistency,
                       TargetDisambiguation, SafetyPredicateGate,
                       PlanRevalidation]
}


def build(keys):
    """Instantiate defenses by key, in the order given."""
    return [REGISTRY[k]() for k in keys]


def recommended():
    """The full stack, in a sensible order."""
    return build(["text_provenance", "consistency", "disambiguation",
                  "safety_gate", "revalidation"])


def _find(label, scene):
    for o in scene.objects:
        if o.label == label:
            return o
    return None
