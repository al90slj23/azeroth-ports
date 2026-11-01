#!/usr/bin/env python3
"""Read-only fixed135 App constructor/owner/interval static evidence."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sqlite3,struct,sys
sys.dont_write_bytecode=True
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,parse_source,section_list
from build_upgrade134_oracle import Reader,sha,source_memory

PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
GLUE=ROOT/'originals/official-acquisition-20261101T030310.926207Z/official-wenilla.js'


def extract_static():
    raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA
    types,imports,decl,bodies,segments=parse_source(raw)
    section=next(x for x in section_list(raw)if x[0]==9);reader=Reader(raw,section[2],section[3])
    assert reader.uint()==1 and reader.uint()==0 and reader.byte()==0x41
    base=reader.sint();assert reader.byte()==0x0b;count=reader.uint();table=[reader.uint()for _ in range(count)];reader.finished()
    assert table[4472-base]==58521 and table[4473-base]==83825
    vt,offset,segment=source_memory(raw,segments,5305816,20)
    assert struct.unpack('<5I',vt)[1:]==(12,4,4472,4473)
    text,server_offset,server_segment=source_memory(raw,segments,5221378,13);assert text==b'azeroth.local'
    assert sha(PROFILE/'index.sqlite')=='b1032d016b6ef43da115eb373a10f03ee2ddfae428cee7d988057d2caac773a0'
    con=sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);functions={}
    with(PROFILE/'official-0.135.1-full.wat').open('rb')as wat:
        for idx in(4253,880,1371,58521,83825,122123,104471,105393,135253,101072):
            lo,hi=con.execute('SELECT wat_start,wat_end FROM functions WHERE idx=?',(idx,)).fetchone()
            wat.seek(lo);value=wat.read(hi-lo);start,end=bodies[idx]
            assert value.splitlines()[0].startswith(f'  (func (;{idx};)'.encode())
            functions[idx]=dict(index=idx,body_sha256=hashlib.sha256(raw[start:end]).hexdigest(),wat_sha256=hashlib.sha256(value).hexdigest(),wat_start=lo,wat_end=hi,text=value.decode())
    con.close()
    return raw,functions,dict(vtable_address=5305816,vtable_words=struct.unpack('<5I',vt),vtable_file_offset=offset,vtable_segment=segment,
        function_table_base=base,function_table_entries=count,once_slot4472=58521,mut_slot4473=83825,
        server_address=5221378,server_bytes_hex=text.hex(),server_file_offset=server_offset,server_segment=server_segment,
        closure_cast_import867=imports[867],interval_import517=imports[517])


def main():
    original,functions,bindings=extract_static()
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('app-state0135-static-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    windows=[]
    for name,index,lo,hi in(('constructor',4253,8602,8894),('owner_move',4253,8938,8987),('tick_closure',4253,9293,9373),
            ('game_move_880',880,15850,15864),('game_move_1371',1371,11306,11326)):
        lines=functions[index]['text'].splitlines();text='\n'.join(lines[lo-1:hi])+'\n';path=out/(name+'.wat.txt');path.write_text(text)
        windows.append(dict(name=name,index=index,first_line=lo,last_line=hi,sha256=sha(path)))
    for idx in(58521,83825,122123,104471,105393,135253,101072):(out/f'{idx}.wat').write_text(functions[idx]['text'])
    glue=GLUE.read_text();assert 'function makeMutClosure(arg0, arg1, f)'in glue
    closure=glue.split('function makeMutClosure(arg0, arg1, f)',1)[1].split('function passArrayF32ToWasm0',1)[0]
    assert '.original'not in closure
    result=dict(version='0.135.1',build='0898d5e3',kind='partialAppconstructor_owner_and_tickclosure_static_identity',original_sha256=SOURCE_SHA,
        production_source_sha256=sha(ROOT/'reconstruction/core_spec/app_state135.py'),trace_source_sha256=sha(Path(__file__)),
        functions=[{k:v for k,v in x.items()if k!='text'}for x in functions.values()],windows=windows,bindings=bindings,
        official_glue_sha256=sha(GLUE),official_makeMutClosure_exposes_original=False,
        pointer_contract='Only__wbindgen_cast_0010 withb5305816:Rc=u32(a+8);App=Rc+16;borrowbyteRc+8;actualsetInterval25ms',
        app_known_bytes_no_livecopies=730,app_unrestored_or_inactive_bytes_no_livecopies=4438,
        app_complete_or_legal=False,new_original_calls=0,original_program_executed=False,snapshot_read=False,
        limitations=['Constructor inlinewindow isnotcomplete4253;noUI/storage/renderer/account/profile execution.',
          'Opaque entropy/pointers/copies declared as typed inputs;Rcfinalholdercount andGame24129 ownershipremain separate.'])
    path=out/'trace.json';path.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(directory=str(out),sha256=sha(path),new_original_calls=0)))


if __name__=='__main__':main()
