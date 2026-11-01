#!/usr/bin/env python3
"""Actual135 event/source identities; no original application/function calls."""
import hashlib,json,sqlite3
from datetime import datetime,timezone
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,parse_source

PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
WAT_SHA='15bccec81235752573d903d098911612d8add22cc51956d03afb8fb17382a7f2'


def main():
    raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA
    *_,bodies,segments=parse_source(raw)
    con=sqlite3.connect(f'file:{PROFILE/"index.sqlite"}?mode=ro',uri=True)
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('proc0135-static-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    functions=[];texts={}
    with(PROFILE/'official-0.135.1-full.wat').open('rb')as stream:
        assert hashlib.file_digest(stream,'sha256').hexdigest()==WAT_SHA
        for index in(914,984,8157,1512,18353):
            a,b=con.execute('select wat_start,wat_end from functions where idx=?',(index,)).fetchone();stream.seek(a);data=stream.read(b-a);texts[index]=data.decode()
            (out/f'function-{index}.wat').write_bytes(data);begin,end=bodies[index]
            functions.append(dict(index=index,body_bytes=end-begin,body_sha256=hashlib.sha256(raw[begin:end]).hexdigest(),
                signature=texts[index].splitlines()[0].strip(),direct_callees=[x[0]for x in con.execute('select distinct callee from calls where caller=? order by callee',(index,))]))
    byindex={x['index']:x for x in functions};assert 984 in byindex[914]['direct_callees'] and 1512 in byindex[984]['direct_callees'] and 8157 in byindex[984]['direct_callees']
    assert texts[914].index('call 18353')<texts[914].index('call 984')
    report=dict(original_sha256=SOURCE_SHA,wat_sha256=WAT_SHA,functions=functions,
        restored_branch=dict(producer_kind=27,definition_stride=36,gate_words_offsets=[4,8,12,16],value_offset=20,max_stack_offset=24,duration_offset=28,modifier_tag_byte=32,
         source_vector=dict(capacity=596,pointer=600,length=604,stride=12),record_fields=['definition_index','stack_count','expires_bits'],
         mutation='First matching definition_index only. Existing: stack=(!oldExpiry<=now ? wrapping(oldStack+1):1); then unsignedmin(stack,maxStack);expiry=f32(now+duration). Missing:append(index,1,expiry)withoutcap.',
         dirty_recalculation='After the whole ordered declaration loop,1512 executes once if anykind27 matched8157.',
         zero_gate='For exact zero16B gate, event29==0 OR(event34&1) matches; all othergate families remain unresolved.',
         hit_order='91418353 selfheal occurs before primary984 then optionalsecondary984;context774=0 primary category0,secondary category2(flag34=0).'),
        pending=['Nonzero8157 gate families and other984 producer kinds.','Physical Vec allocation/capacity and full message/account/presentation metadata.','Other modifier types changing cast coefficients mid-target loop.'])
    (out/'proc135-static.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(directory=str(out),functions=len(functions))))


if __name__=='__main__':main()
