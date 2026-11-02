#!/usr/bin/env python3
"""Current139 fullopening/select/2123 export-only component module."""
from incoming139_tools import ROOT,SOURCE,SOURCE_SHA,original,private_exports,function_proof,static_reader,sha,save


def build(out):
    raw,identity,ranges=original();static=out/'static';static.mkdir()
    ids={2945,1600,1108,4677,2181,1093,4603,2123,1238,23328,8673,27754,922,1542,1173,1466,28155,52397,42159,46690,66535,66547}
    functions,texts=function_proof(raw,identity,ranges,ids,static);read=static_reader(raw,identity)
    assert functions[2123]['signature']==functions[1238]['signature']==('7f7d','')
    assert texts[2123].index('call 1542')<texts[2123].index('call 1173')<texts[2123].index('call 1238')
    assert 'i32.load offset=1712'in texts[2123]and'i32.const 28'in texts[2123]and'i32.const 24'in texts[2123]
    cls=read(5877920,108);perception=read(5891892,88);assert int.from_bytes(cls[:4],'little')==1 and perception[84]==9 and int.from_bytes(perception[:4],'little')==8
    additions=[('research139_gw_companion',0,2945),('research139_gw_initial',0,1600),('research139_gw_opening',0,1108),('research139_gw_gain',0,4677),('research139_gw_select',0,1093),('research139_gw_stack',3,0),('research139_pu_update2123',0,2123)]
    filename='player-update139-original-exports.wasm';(out/filename).write_bytes(private_exports(raw,identity,additions))
    manifest=dict(version='0.139.0',build='f79c5e2b4',source_sha256=SOURCE_SHA,module_file=filename,module_sha256=sha(out/filename),original_imports=identity['imports'],added_exports=additions,functions=functions,only_export_section_changed=True,implicit_start=False,builder_original_executions=0,warrior_class108_hex=cls.hex(),perception88_hex=perception.hex(),cleave88_hex=read(5882740,88).hex(),thunder_clap88_hex=read(5882916,88).hex(),static_reads=read.proof,scope='Full2123onnewfull1108/firstselecteddefaultHumanWarrior;clockexternal,NPCcenterquietsourcesretained;notmain884')
    save(out/'manifest.json',manifest);return manifest
