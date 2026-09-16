"""Built-in scenarios and a YAML loader.

A scenario file is a small dict::

    name: tabletop-pick
    instruction: pick up the red block
    lighting: normal
    objects:
      - {label: red block, pose: [0.3, 0.0, 0.0]}
      - {label: blue block, pose: [0.4, 0.1, 0.0]}
    texts:
      - {label: label, text: "shelf B"}
"""
from __future__ import annotations

import os

from .scene import Obj, Scene, SceneText


def from_dict(d):
    objs = [Obj(o["label"], tuple(o.get("pose", (0, 0, 0))),
                dict(o.get("attrs", {}))) for o in d.get("objects", [])]
    txts = [SceneText(t.get("label", "text"), t["text"])
            for t in d.get("texts", [])]
    return d.get("name", "scenario"), Scene(
        objects=objs, texts=txts, instruction=d.get("instruction", ""),
        lighting=d.get("lighting", "normal"))


def load_dir(path):
    """Every .yaml/.yml in a directory as (name, Scene), sorted by filename."""
    import yaml
    out = []
    for fn in sorted(os.listdir(path)):
        if fn.endswith((".yaml", ".yml")):
            with open(os.path.join(path, fn)) as f:
                out.append(from_dict(yaml.safe_load(f)))
    return out


def builtin():
    """Three scenarios used by the self-test and the examples."""
    return [
        ("tabletop-pick", Scene(
            objects=[Obj("red block", (0.3, 0.0, 0.0)),
                     Obj("blue block", (0.4, 0.1, 0.0))],
            texts=[SceneText("label", "bin 3")],
            instruction="pick up the red block")),
        ("handover", Scene(
            objects=[Obj("cup", (0.2, 0.1, 0.0)),
                     Obj("bottle", (0.3, -0.1, 0.0))],
            texts=[SceneText("poster", "recycle here")],
            instruction="hand me the cup")),
        ("two-lookalikes", Scene(
            objects=[Obj("red block", (0.2, 0.2, 0.0)),
                     Obj("red block", (0.2, -0.2, 0.0))],
            texts=[],
            instruction="pick up the red block")),
    ]
