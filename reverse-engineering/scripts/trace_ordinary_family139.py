#!/usr/bin/env python3
"""Fresh current139 two ordinary definitions/English/925/913 source binding."""
import json,sqlite3,struct
from collections import Counter
from incoming139_tools import (ROOT,PROFILE,SOURCE_SHA,original,
    function_proof,static_reader,save,sha)


def trace(out):
    raw,identity,ranges=original();read=static_reader(raw,identity)
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db:
        db.execute('pragma query_only=on')
        calls={str(index):[dict(callee=row[0],sites=row[1])for row in db.execute('select callee,count(*) from calls where caller=? group by callee',(index,))]for index in(925,913,952)}
    direct={r['callee']for group in calls.values()for r in group}
    ids={925,913,952,1076,59230,20060,40215,36520,8569,30861,26202,18421,1466,2077,19598,5719,1586}|{i for i in direct if i>=882}
    proof,texts=function_proof(raw,identity,ranges,ids,out)
    assert proof[925]['signature']==('7f7d','')and proof[913]['signature']==('7f7e7d7f7f7f7f','')
    assert texts[925].index('call 40215')<texts[925].index('i32.const 170')<texts[925].index('i32.const 221')<texts[925].index('call 1076')
    assert all(s in texts[913]for s in('i32.const 56','f32.load offset=60','call 1466','call 2077'))
    p,n=struct.unpack('<2I',read(5401532,8));english=json.loads(read(p,n));definitions=[]
    for pointer in(5830904,5830976):
        data=read(pointer,72);p,n,entry=struct.unpack_from('<3I',data,16);fallback=read(p,n).decode();key='enemy.'+str(entry)
        definitions.append(dict(pointer=pointer,raw72_hex=data.hex(),raw72_sha256=__import__('hashlib').sha256(data).hexdigest(),fallback=fallback,english_key=key,english_name=english.get(key,fallback),XP56=struct.unpack_from('<I',data,56)[0],cost60_bits=struct.unpack_from('<I',data,60)[0],classification68=data[68]))
    result=dict(source_sha256=SOURCE_SHA,definitions=definitions,functions=proof,direct_callees=calls,import_callees=[i for i in direct if i<882],static_reads=read.proof,original_calls=0,trace_source_sha256=sha(__file__),pending=['Only observed ordinary two-definition branches are dynamically admitted.','Demo1160 and other owned abilities are not accepted by this experiment.'])
    save(out/'family-trace.json',result);return result
