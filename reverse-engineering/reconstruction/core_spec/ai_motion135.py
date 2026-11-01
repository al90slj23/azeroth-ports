"""Ordinary135 AI with independently restored medium-angle trigonometry.

All original ordinary-AI source/owner/terrain/death restrictions are preserved.
The accumulated orbit word is never wrapped or reset to fit a smaller model.
"""
from .ai135 import AiFrame135, AiResult135, update_ordinary_units as _update
from .ai_trig135 import sin_bits, cos_bits


def update_ordinary_units(state: AiFrame135):
    return _update(state, trig_sin_bits=sin_bits, trig_cos_bits=cos_bits)
