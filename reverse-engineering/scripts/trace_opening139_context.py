#!/usr/bin/env python3
"""Bounded139 opening/context dependency discovery; no original execution."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sqlite3
from wasm139_profile import ROOT,SOURCE,SOURCE_SHA,binary_identity

PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
FUNCTIONS=(1108,6786,4562,1795,5719,13563,1446,66941,26623,36521,48446,2917,1139,1586,8740,6440,97553,2945,177894)
def sha(p):
    with p.open('rb')as s:return hashlib.file_digest(s,'sha256').hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')

def main():
    before=sha(Path(__file__));raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA
    identity,ranges=binary_identity(raw);out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('opening139-context-static-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    keys=[]
    for s in identity['data_segments']:
        if s['address']is None:continue
        body=raw[s['file_offset']:s['file_offset']+s['bytes']];pos=0
        while True:
            pos=body.find(b'rogue.characters',pos)
            if pos<0:break
            keys.append(s['address']+pos);pos+=1
    assert len(keys)==1
    funcs={};links={};total=0
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.139.0-full.wat').open('rb')as w:
        db.row_factory=sqlite3.Row;db.execute('pragma query_only=on')
        key_consumers=[dict(x)for x in db.execute('select *from iconsts where value=?',(keys[0],))]
        pending=list(FUNCTIONS)+[x['function_idx']for x in key_consumers]
        while pending:
            i=pending.pop(0)
            if str(i)in funcs:continue
            row=dict(db.execute('select *from functions where idx=?',(i,)).fetchone());n=row['wat_end']-row['wat_start'];assert n<=1048576 and total+n<=4194304
            w.seek(row['wat_start']);wat=w.read(n);(out/f'{i}.wat').write_bytes(wat);a,b,_=ranges[i];assert(a,b)==(row['body_start'],row['body_end']);total+=n
            calls=[dict(x)for x in db.execute('select *from calls where caller=?order by wat_offset',(i,))]
            funcs[str(i)]={**row,'body_sha256':hashlib.sha256(raw[a:b]).hexdigest(),'wat_sha256':hashlib.sha256(wat).hexdigest(),'signature':wat.decode().splitlines()[0].strip(),'direct_calls':calls,
                'memory_ops':[dict(x)for x in db.execute('select *from memops where function_idx=?order by wat_offset',(i,))]}
            links[str(i)]=[dict(x)for x in db.execute('select caller,count(*)as sites from calls where callee=?group by caller',(i,))]
    proof=dict(version='0.139.0',build='f79c5e2b4',source_wasm_sha256=SOURCE_SHA,script_sha256=before,
        selected_functions=funcs,callers=links,account_storage_key='rogue.characters',account_storage_key_pointer=keys[0],key_consumers=key_consumers,
        read_WAT_bytes=total,target_executions=0,old_acceptance_transferred=False,old_snapshot_loaded=False,
        context_status='Real139 world/locale/cache context not yet acquired; direct1600 flatview is not full1108 context',
        scope='Actual1391108 and dependency graph discovery; candidate key consumers are not yet account-loader identity acceptance')
    save(out/'proof.json',proof);assert before==sha(Path(__file__))
    print(json.dumps(dict(directory=str(out),proof_sha256=sha(out/'proof.json'),key_pointer=keys[0],key_consumers=key_consumers,functions=len(funcs),read_WAT_bytes=total)),flush=True)

if __name__=='__main__':main()
