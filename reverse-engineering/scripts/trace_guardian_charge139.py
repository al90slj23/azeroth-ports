#!/usr/bin/env python3
"""Static current925 genuine3timer→916 tag7→120/32 producer/source binding."""
import json,sqlite3,struct,re
from incoming139_tools import ROOT,PROFILE,SOURCE_SHA,original,function_proof,static_reader,save,sha
from trace_special_world139 import trace as trace_special
from trace_ordinary_family139 import trace as trace_family


def trace(out):
    special=trace_special(out);family=trace_family(out)
    raw,identity,ranges=original();read=static_reader(raw,identity)
    roots=(925,916,4860,21112,62654,35067,68224,20693,32071,81682,51773,16627,36367,38553,10490,66567,66546,15962,6619,58587,64899,47161,66558,30179)
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db:
        db.execute('pragma query_only=on')
        calls={str(i):[dict(callee=r[0],sites=r[1])for r in db.execute('select callee,count(*)from calls where caller=? group by callee',(i,))]for i in roots}
    indices=set(roots)|{r['callee']for group in calls.values()for r in group if r['callee']>=882}
    proof,texts=function_proof(raw,identity,ranges,indices,out)
    assert proof[925]['signature']==('7f7d','')and proof[916]['signature']==('7f7f7f','')and proof[38553]['signature']==('7f','')
    assert all(x in texts[925]for x in('call 916','call 16381','call 42922','call 51773','call 16627'))
    assert texts[925].index('call 1076')<texts[925].index('call 916')<texts[925].index('call 51773')
    assert 'i32.const 120'in texts[35067]and'i32.store offset=1816'in texts[35067]and'i64.store offset=111 align=1'in texts[35067]
    assert all(x in texts[68224]for x in('i32.store offset=1840','i32.const 5','i32.shl'))
    constructor=(out/'1600.wat').read_text()
    assert all(x in constructor for x in('i32.store offset=1904','i64.store offset=1896','i64.store offset=2444 align=4','i64.store offset=1916 align=4','i64.store offset=1924 align=4'))
    #Recover the structured target, including selector's subtract1. The
    #rejected firstpilot used index4 rather than actualraw7→norm4→index3.
    lines=texts[916].splitlines();stack=[];matched={};switch=None
    for number,line in enumerate(lines,1):
        t=line.strip()
        if re.match(r'^(block|loop|if)\b',t):stack.append(number)
        elif t=='end':matched[stack.pop()]=number
        if 'br_table 1 (;@39;) 25 (;@15;)'in t:switch=(number,tuple(stack))
    number,scopes=switch;target_open=scopes[-24];target_close=matched[target_open]
    assert lines[number-3].strip()=='i32.const 1'and lines[number-2].strip()=='i32.sub'
    assert lines[target_close].strip()=='local.get 2'and any('call 64899'in x for x in lines[target_close:target_close+225])
    assert any('f32.const 0x1p+0'in x for x in lines[target_close:target_close+225])
    dispatch=dict(rawtag=7,normalized=4,selector=3,br_depth=23,target_block_open_line=target_open,target_block_end_line=target_close,branch_start_line=target_close+1,branch_end_line=target_close+222,record_param_words_not_read=True,cast_duration_bits=0x3f800000,effect_shape=2,effect_damage='f32(attack+attack)',deferred_function=64899,deferred_stride=56,not_called_in_rawtag7=[68224])
    save(out/'charge-dispatch-proof.json',dispatch)
    phases={}
    for d in special['declarations']:
        p,n=struct.unpack_from('<2I',bytes.fromhex(d[5]),16)
        phases[d[4]]=tuple(read(p+52*j,52).hex()for j in range(n))
    english_p,english_n=struct.unpack('<2I',read(5401532,8));english=json.loads(read(english_p,english_n))
    key=read(1594130,24).decode()
    result=dict(source_sha256=SOURCE_SHA,functions={**family['functions'],**special['functions'],**proof},direct_callees=calls,special=special,family=family,phases=phases,engage_key=key,engage_english=english.get(key,key),static_reads=read.proof,ABI=dict(full925=['Game_i32','dt_f32'],full916=['Game_i32','unit_index_i32','skill40ptr_i32'],full38553=['Game_i32']),constructor_queue_producers=dict(effects='G1808/1812/1816=[0,8,0] from T1896i64(8<<32)/T1904zero',scheduled='G1832/1836/1840=[0,8,0] from T1916i64zero/T1924i64eight',deferred='G1820/1824/1828=[0,8,0] from T1908i64(8<<32)/T1916zero',counter2356='G2356=T2444 lower word i64zero'),dispatch=dispatch,original_executions=0,pending=['Only real default100/rawtag7 source dynamically admitted; former index4 guess rejected.','Effect120 remains for later920; the full920 consumer is not this experiment.'])
    save(out/'guardian-trace.json',result);return result
