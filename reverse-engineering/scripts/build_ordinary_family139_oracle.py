#!/usr/bin/env python3
"""Private unmodified139 functions with added export entries only."""
from build_natural_spawn139_oracle import build as source_build
from incoming139_tools import ROOT,SOURCE,SOURCE_SHA,sha,save
from trace_ordinary_family139 import trace


def build(out):
    m=source_build(out);proof=trace(out/'static');m['functions'].update(proof['functions'])
    m['ordinary_family_trace']=proof
    m['direct913_ABI']=['Game_i32','target_GUID_i64','amount_f32','spellID_i32','school_i32','critical_i32','suppress_spell_packet_i32']
    m['scope']='Actual2945/1600/1108→controlledclock30.1 complete952→retainedKobold/Wolf full925, controlled913 nonlethal/lethal/dead and full925 corpse removal. Not natural30seconds or main884.'
    save(out/'manifest.json',m);return m
