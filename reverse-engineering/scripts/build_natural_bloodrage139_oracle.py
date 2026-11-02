#!/usr/bin/env python3
"""Fresh current139 four-stage natural2123/925/2890/952 export-only oracle."""
from build_natural_demo_second139_oracle import build as source_build
from incoming139_tools import ROOT,SOURCE,SOURCE_SHA,sha,save,original,private_exports,function_proof,static_reader

def build(out):
    m=source_build(out);raw,identity,ranges=original()
    ids={952,5719,1586,21552,8740,13563,20357,97426,97427,2801,1446,38882,66565,1886,66611,66558,20060,26521,50441,6440,31851,29912,11425,11499,81897,43076,32605,18062,66546,21553,4593,15556,1093,25511,1238,1173,2181,30022,27572,30628,983,10285,33222,50267,12774,22428,27754,36518,20123,913}
    proofs,texts=function_proof(raw,identity,ranges,ids,out/'static');m['functions'].update(proofs)
    assert all(x in texts[952]for x in('f32.load offset=2420','f32.const -0x1.8p+3 (;=-12;)','call 26521','f32.store offset=2420','f32.load offset=344','f32.load offset=2416'))
    text=(out/'static/884.wat').read_text();late=text[text.rfind('call 2123'):]
    assert late.index('call 2123')<late.index('call 925')<late.index('call 2890')<late.index('call 952')<late.index('call 49961')
    interval=late[late.index('call 2890'):late.index('call 952')]
    assert 'i32.load8_u offset=2579' in interval and 'offset=2587' not in interval
    from core_spec.candidates139_data import DEFINITIONS139
    read=static_reader(raw,identity);bloodrage=read(5883620,88)
    assert bloodrage==bytes.fromhex(DEFINITIONS139['bloodrage'][1])and bloodrage[84]==11
    name=read(int.from_bytes(bloodrage[12:16],'little'),int.from_bytes(bloodrage[16:20],'little'));kinds=read(int.from_bytes(bloodrage[36:40],'little'),int.from_bytes(bloodrage[40:44],'little'))
    assert name==b'bloodrage'and tuple(kinds)==DEFINITIONS139['bloodrage'][2]
    m.update(bloodrage88_hex=bloodrage.hex(),bloodrage_kinds=list(kinds),bloodrage_name=name.decode());m['static_reads'].update(read.proof)
    additions=list(m['added_exports'])+[['research139_bloodrage_owned983',0,983],['research139_bloodrage_damage913',0,913]]
    additions=[tuple(x)for x in additions]
    filename='natural-bloodrage139-original-exports.wasm';(out/filename).write_bytes(private_exports(raw,identity,additions))
    m.update(module_file=filename,module_sha256=sha(out/filename),added_exports=additions,
        scope='Actual singlecleaveXP0opening -> naturaldefaultDemo2 -> naturaldefaultBloodrage0 -> full2123/983/925/2890/952, persistent scheduler from first slice, UI1093 only after five; other late884 systems absent, no full frame/game.',
        current884_no_phase_recheck_2890_to952=True)
    assert late.index('call 2123')<late.index('call 983')<late.index('call 925')
    save(out/'manifest.json',m);return m
