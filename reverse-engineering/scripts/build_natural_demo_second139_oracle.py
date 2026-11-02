#!/usr/bin/env python3
"""Fresh current139 four-stage natural2123/925/2890/952 export-only oracle."""
from build_natural_demo139_oracle import build as source_build
from incoming139_tools import ROOT,SOURCE,SOURCE_SHA,sha,save,original,private_exports,function_proof

def build(out):
    m=source_build(out);raw,identity,ranges=original()
    ids={952,5719,1586,21552,8740,13563,20357,97426,97427,2801,1446,38882,66565,1886,66611,66558,20060,26521,50441,6440,31851,29912,11425,11499,81897,43076,32605,18062,66546,21553,4593,15556,1093,25511,1238,1173,2181,30022,27572,30628}
    proofs,texts=function_proof(raw,identity,ranges,ids,out/'static');m['functions'].update(proofs)
    assert all(x in texts[952]for x in('f32.load offset=2420','f32.const -0x1.8p+3 (;=-12;)','call 26521','f32.store offset=2420','f32.load offset=344','f32.load offset=2416'))
    text=(out/'static/884.wat').read_text();late=text[text.rfind('call 2123'):]
    assert late.index('call 2123')<late.index('call 925')<late.index('call 2890')<late.index('call 952')<late.index('call 49961')
    interval=late[late.index('call 2890'):late.index('call 952')]
    assert 'i32.load8_u offset=2579' in interval and 'offset=2587' not in interval
    additions=m['added_exports']
    filename='natural-demo-second139-original-exports.wasm';(out/filename).write_bytes(private_exports(raw,identity,additions))
    m.update(module_file=filename,module_sha256=sha(out/filename),added_exports=additions,
        scope='Actual singlecleaveXP0opening -> naturaldefaultDemo2 -> full2123/925/2890/952, persistent scheduler from first slice, UI1093 only after all four; other late884 systems absent, no full frame/game.',
        current884_no_phase_recheck_2890_to952=True)
    save(out/'manifest.json',m);return m
