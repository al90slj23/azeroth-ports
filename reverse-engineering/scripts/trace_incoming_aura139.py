#!/usr/bin/env python3
"""Current1391173 and full1076 shield-retain→Aura producer declarations."""
import hashlib,re,struct
from incoming139_tools import original,static_reader,function_proof,save,sha
def trace(out):
    raw,identity,ranges=original();read=static_reader(raw,identity)
    proof,text=function_proof(raw,identity,ranges,{1173,1076,1600,83304,29910,31155,52397,66545,66553,73034,108362},out)
    aura=text[1173];calls=sorted(set(map(int,re.findall(r'call (\d+)',aura))))
    assert calls==[23732,29910,31155,52397,66545,66553,73034,81897,108362,109316]and 1542 not in calls
    assert all('i32.store offset='+str(o)in aura for o in(2000,2004,2008))and'i32.store8 offset=2569'in aura
    assert re.findall(r'i32.const (\d+)\n\s+i32.lt_u',aura)==['95','96','97','98','99','100']
    for term in('i32.const 47','i32.const 113','i32.load16_u offset=50','i32.const 52','i32.load offset=76','i32.const 48','i32.const 768','i32.const 12'):
        assert term in aura,term
    kinds={str(p):struct.unpack('<I',read(p,4))[0]for p in(5882740,5891892)}
    assert all(k!=12 for k in kinds.values())
    lines=text[1600].splitlines();windows={}
    for name,lo,hi,terms in(
        ('constructor_f64_zero_temporary',614,625,('i64.const 0','i64.store offset=2872')),
        ('constructor_f64_Game992',985,1000,('i64.load offset=2872','i64.store offset=1080','i64.store offset=1056','i64.store offset=1064')),
        ('constructor_shield_source_zero',713,722,('i64.const 0','i64.store offset=1432')),
        ('constructor_Aura_empty_ready0',1183,1202,('i32.store16 offset=2657','i64.store offset=2096','i64.const 17179869184','i64.store offset=2088')),
        ('constructor_frame88_Game2592',2695,2710,('i32.const 88','call 1542','i32.const 2592','memory.copy'))):
        chunk='\n'.join(lines[lo-1:hi]);assert all(t in chunk for t in terms),name;windows[name]=dict(first_line=lo,last_line=hi,text=chunk,sha256=hashlib.sha256(chunk.encode()).hexdigest())
    result=dict(version='0.139.0',functions=proof,direct1173_callees=calls,default_humanwarrior_definition_kinds=kinds,constructor_frame88_source_windows=windows,empty_source_policy='post-retain live32empty/mod36empty; every owned/racial definition kind!=12; prior Aura empty0 or tag0×48',Aura_layout=dict(header=[2000,2004,2008],stride=16,count=48,allocation_bytes=768,tag=0,tag_initialized_bytes=4,inactive_payload_bytes=12,flag=2569),keyed_layout=dict(header=[2476,2480,2484],count_u16=50,keys_u16=52,values_u32=4,children_u32=76,leaf_bytes=76,internal_bytes=124),keyed_zero_groups=[list(range(47,95)),list(range(95,101)),list(range(113,125))],shield_cleanup='1076 retains away kind7 on exhaustion or previous sourceID on depletion, then calls actual1173 before HP/history; no1542call',read_proofs=read.proof,trace_source_sha256=sha(__file__),original_calls=0)
    save(out/'trace.json',result);return result
