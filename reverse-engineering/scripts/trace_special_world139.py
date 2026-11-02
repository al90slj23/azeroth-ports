#!/usr/bin/env python3
"""Current2372 due20/notify/scalar/Guardian declarations: no runtime calls."""
import json,struct,sqlite3
from incoming139_tools import ROOT,PROFILE,SOURCE_SHA,original,function_proof,static_reader,save,sha


def trace(out):
    raw,identity,ranges=original();read=static_reader(raw,identity)
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db:
        calls={str(i):[dict(callee=r[0],sites=r[1])for r in db.execute('select callee,count(*) from calls where caller=? group by callee',(i,))]for i in(2372,16381,42922,1586,33347)}
    indices={2372,16381,42922,1586,33347,1600,1108,2945,20060,32605,38882,66565,66546,55846,108362,73034,81897,109316}
    indices.update(r['callee']for group in calls.values()for r in group if r['callee']>=882)
    proof,texts=function_proof(raw,identity,ranges,indices,out)
    assert proof[2372]['signature']==('7f','')and proof[16381]['signature']==proof[42922]['signature']==('7f7f','7d')
    assert proof[1586]['signature']==('7f7e7f7f7d7d7f7f','')
    assert all(x in texts[2372]for x in('call 16381','call 42922','call 1586','i32.const 432','i32.store offset=392','i32.store offset=396','i32.store8 offset=2565','i32.const 548'))
    assert 'i32.const 1\n                  i32.store16 offset=2652'in texts[1600]and'i32.const 0\n                  i32.store offset=480'in texts[1600]and'i64.const 0\n                  i64.store offset=2480'in texts[1600]
    #T+88is copied to the finalGame. G387=T475 is profile371: the
    #actual caller's zero-filled376Bprofile is copied toT+104. G1092=T1180
    #is bytes3..6ofstore1177 fromscratch2812;store2811zero covers these.
    assert 'i64.const 0\n                  i64.store offset=2811 align=1'in texts[1600]
    assert 'i64.load offset=2812 align=1\n                  i64.store offset=1177 align=1'in texts[1600]
    assert 'i32.const 104\n                  i32.add\n                  local.get 1\n                  i32.const 376\n                  memory.copy'in texts[1600]
    defs=[];locale_p,locale_n=struct.unpack('<2I',read(5401532,8));english=json.loads(read(locale_p,locale_n))
    for index,h in((9,5899360),(10,5899388),(11,5899416)):
        ptr=5830904+72*index;data=read(ptr,72);p,n,entry=struct.unpack_from('<3I',data,16);header=read(h,28);ability,count=struct.unpack_from('<2I',header)
        assert count==3 and struct.unpack_from('<I',header,12)[0]==0
        defs.append((index,ptr,data.hex(),english.get('enemy.'+str(entry),read(p,n).decode()),h,header.hex(),ability,tuple(read(ability+44*j,44).hex()for j in range(count))))
    milestone=read(5833692,72);assert struct.unpack_from('<2I',milestone,48)==(0x40400000,0x45610000)and milestone[68]!=1
    result=dict(source_sha256=SOURCE_SHA,functions=proof,direct_callees=calls,declarations=defs,zone136_bits=struct.unpack('<I',read(5871348+136,4))[0],first_milestone=[0x40400000,0x45610000],static_reads=read.proof,original_calls=0,trace_source_sha256=sha(__file__),constructor_initial_special_flags=dict(selected392=0,target396=None,navigation2564=1,announced2565=0,stamp2392=0),constructor_scaling_producers=dict(difficulty387='T475←profile371 within376Bcopy, caller zero supplies0',field1092='T1180←scratch2815..2818, covered byi64zero2811 theni64copy2812→1177'),scope='Current defaultfirstexpiry20; activecontinuation belowfirstboss; due>21localized150respawn/newAIremainPending.')
    save(out/'special-trace.json',result);return result
