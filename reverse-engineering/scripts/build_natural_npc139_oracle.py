#!/usr/bin/env python3
"""Unchanged original5719 export, naturalNone input, healthyv2 realworld."""
from build_npc_spawn139_oracle import ROOT,SOURCE,SOURCE_SHA,build as build_base,sha,save,missing

def build(out):
 m=build_base(out);m.update(kind='original1395719naturalNone_over_healthyv2world',memory_page_cap=4096,position_argument_tag=0,context_world_Rc_pointer=20544696,original_full_callees_preserved=True)
 save(out/'manifest.json',m);return m
