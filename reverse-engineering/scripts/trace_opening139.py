#!/usr/bin/env python3
"""Whole1391108 static selectors and default no-effect call conditions."""
import hashlib,struct
from incoming139_tools import original,static_reader,function_proof,save,SOURCE_SHA

def trace_opening139(out):
    out.mkdir();raw,identity,ranges=original();read=static_reader(raw,identity)
    proof,texts=function_proof(raw,identity,ranges,(1108,1795,10099,11425,11499),out)
    normal=read(5830904,12*72);eligible=[]
    for i in range(12):
        row=normal[i*72:(i+1)*72];duration=struct.unpack_from('<I',row,64)[0]
        if row[68]==1 and duration&0x7fffffff<0x7f800000:eligible.append(dict(index=i,identifier=struct.unpack_from('<I',row,24)[0],duration_bits=duration,flag68=row[68]))
    assert [r['index']for r in eligible]==[9,10,11]
    lines=texts[1108].splitlines();selector='\n'.join(lines[3024:3207]);append='\n'.join(lines[4239:4310])
    assert 'local.get 9\n                                        local.get 1\n                                        i32.store'in selector
    assert 'i32.store offset=28'in append
    #10099 scans item8 for category32 and modifier36 for42; the constructor
    #default has count2032=count2056=0, hence no1744/5748 callback executes.
    assert 'i32.load offset=2032'in texts[10099]and'i32.load offset=2056'in texts[10099]and'call 1744'in texts[10099]and'call 5748'in texts[10099]
    assert all(s in texts[1795]for s in('i32.const 240\n      i32.add','i32.const 256\n      i32.add','i32.const 8\n                i32.add','local.tee 7\n                i32.const 255\n                i32.eq'))
    result=dict(source_sha256=SOURCE_SHA,functions=proof,normal72_pointer=5830904,normal72_sha256=hashlib.sha256(normal).hexdigest(),eligible=eligible,special28_semantics='zero-based enumeration index,not normal72 identifier24',selector_source_window=dict(first_line=3025,last_line=3207,sha256=hashlib.sha256(selector.encode()).hexdigest()),append_source_window=dict(first_line=4240,last_line=4310,sha256=hashlib.sha256(append.encode()).hexdigest()),default_call_domains=dict(companion1795='tags244/252 both255;absent branches',callback10099='item2032=0/modifier2056=0;no callbacks',debug='protection2576=0/rank387=0/optional2577=0/activeevent2140=0'),original_executed=False,read_proof=read.proof)
    save(out/'trace.json',result);return result
