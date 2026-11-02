#!/usr/bin/env python3
"""Current full952 appended to unchanged real2123/922 death-prefix exports."""
from build_enemy_ai_dead139_v2_oracle import build as source_build
from incoming139_tools import ROOT,SOURCE,SOURCE_SHA,sha,save,original,private_exports,function_proof

def build(out):
 m=source_build(out);raw,identity,ranges=original()
 ids={952,5719,1586,21552,8740,13563,20357,97426,97427,2801,1446,1600,1108,38882,66565,1886,66611,66558,20060,26521,50441,6440,2945,31851,29912,11425,11499,81897,43076,32605,18062,66546}
 proof,texts=function_proof(raw,identity,ranges,ids,out/'static');m['functions'].update(proof)
 assert all(x in texts[952]for x in['f32.load offset=2420','f32.const -0x1.8p+3 (;=-12;)','call 26521','f32.store offset=2420','f32.load offset=344','f32.load offset=2416'])
 assert 'i32.const 1\n          i32.xor'in texts[5719]and 'i32.load offset=1432'in texts[1586]
 added=m['added_exports']+[('research139_spawncombat_tick952',0,952)];name='spawn-combat139-original-exports.wasm';(out/name).write_bytes(private_exports(raw,identity,added));m.update(module_file=name,module_sha256=sha(out/name),added_exports=added,scope='Real6full2123 andoptional922 deathproducers tocomplete952 withretainedfullopeningNPC/path/pickup/background owners;noinputNPC/HP/killcost/RNG/timerwrites')
 save(out/'manifest.json',m);return m
