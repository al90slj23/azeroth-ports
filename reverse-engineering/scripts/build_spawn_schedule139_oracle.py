#!/usr/bin/env python3
"""Export-only current139 full952, current declarations and normal dependencies."""
import ast,hashlib,struct
from incoming139_tools import original,private_exports,function_proof,static_reader,sha,save,SOURCE_SHA,ROOT

def build(out):
    raw,identity,ranges=original();static=out/'static';static.mkdir()
    ids={952,5719,1586,21552,8740,13563,20357,97426,97427,2801,1446,1600,1108,38882,66565,26521,50441,6440,2945}
    proof,texts=function_proof(raw,identity,ranges,ids,static)
    assert proof[952]['signature']==('7f7d','') and proof[5719]['signature']==('7f7f7f7f','')
    assert 'i32.const 432' in texts[5719]and'f32.load offset=2416'in texts[952]
    read=static_reader(raw,identity);zone=read(5871348,152);ptr,count=struct.unpack_from('<II',zone,64)
    tables=tuple(read(ptr+72*j,72).hex()for j in range(count))
    values={n.targets[0].id:ast.literal_eval(n.value)for n in ast.parse((ROOT/'reconstruction/core_spec/spawn_schedule139_data.py').read_text()).body if isinstance(n,ast.Assign)}
    assert values['ELWYNN152_HEX']==zone.hex()and values['NORMAL_BASE']==ptr and values['NORMALS72_HEX']==tables
    # New constructor facts: actual T+88..+2680 is copied into Game.
    t=texts[1600];normal=[' '.join(s.split())for s in t.splitlines()]
    for fragment in ['i64.const 0\n                  i64.store offset=1824','i64.const 1077936128\n                  i64.store offset=2504','i64.const 0\n                  i64.store offset=2456','local.get 13\n                  i32.store offset=2072','i32.const 2592\n                  memory.copy']:assert fragment in t
    assert 'i32.load8_u offset=371'in t and 'i32.const 3\n                  i32.lt_u'in t
    # Original22-line functions restore actual f32 parenthesization, no old
    # version runtime receipt is used by the production module.
    for idx,cubic in[(97426,'0x1.8548aap-8'),(97427,'0x1.cd5f9ap-8')]:
        assert 'f32.const '+cubic in texts[idx]and'f32.const 0x1.26e978p-5'in texts[idx]
    assert 'i32.load8_u offset=68'in texts[20357]or'f32.load offset=64'in texts[20357]
    added=[('research139_spawn_companion',0,2945),('research139_spawn_initial',0,1600),('research139_spawn_opening',0,1108),('research139_spawn_tick952',0,952),('research139_spawn_stack',3,0)]
    name='spawn-schedule139-original-exports.wasm';(out/name).write_bytes(private_exports(raw,identity,added))
    manifest=dict(source_sha256=SOURCE_SHA,module_file=name,module_sha256=sha(out/name),original_imports=identity['imports'],added_exports=added,functions=proof,only_export_section_changed=True,original_executions=0,static_reads=read.proof,static_data_source_sha256=sha(ROOT/'reconstruction/core_spec/spawn_schedule139_data.py'),initial_current1600_producers=dict(velocity1736_1740='T1824i64zero',budget2416_killcost2420='T2504i64_0x40400000',path2368='T2456i64zero',events1984='profile371less3→defaultlocal13zero→T2072',Game_copy='T+88,2592bytes'),scope='Actualfull952 defaultstationary opening normalbudget/density before40s; futurepickup/elite/wave/BossPending')
    save(out/'manifest.json',manifest);return manifest
