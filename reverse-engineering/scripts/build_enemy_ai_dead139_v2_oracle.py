#!/usr/bin/env python3
"""Current925 queued170 phase before deferred motion and attack."""
from build_enemy_ai_dead139_oracle import build as old_build
from incoming139_tools import ROOT,SOURCE,SOURCE_SHA,sha,save


def build(out):
    m=old_build(out);text=(out/'static/925.wat').read_text()
    assert text.index('call 40215')<text.index('i32.const 170')<text.index('i32.const 221')<text.index('call 1076')
    m['packet_phase_order']=[dict(label=label,first_WAT_line=next(i for i,line in enumerate(text.splitlines(),1)if token in line))for label,token in[('queued_remove40215','call 40215'),('queued_despawn170','i32.const 170'),('deferred_motion221','i32.const 221'),('deferred_incoming1076','call 1076')]]
    m['module_file']='enemy-ai-dead139-v2-original-exports.wasm'
    (out/'enemy-ai-dead139-original-exports.wasm').rename(out/m['module_file'])
    m['module_sha256']=sha(out/m['module_file']);m['scope']='Current925 numericphysical corpse domain plus queued170 before deferred221/330, real continuous sameframe probes'
    save(out/'manifest.json',m);return m
