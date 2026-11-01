#!/usr/bin/env python3
"""Bounded WAT/snapshot contract extraction; no target instantiation."""
from datetime import datetime,timezone
import hashlib,json,sqlite3
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,parse_source,section_list
from build_upgrade134_oracle import sha

PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
INDICES=(29631,18670,46295,5795,23181,8751,13516,6730,91941)


def main():
    before=sha(__import__('pathlib').Path(__file__));original=SOURCE.read_bytes()
    assert hashlib.sha256(original).hexdigest()==SOURCE_SHA
    _,_,_,bodies,_=parse_source(original);sections=section_list(original);g=next(x for x in sections if x[0]==6)
    assert original[g[2]:g[3]].hex()=='017f01418080c0000b'and 8 not in[x[0]for x in sections]
    con=sqlite3.connect(f'file:{PROFILE}/index.sqlite?mode=ro',uri=True);con.row_factory=sqlite3.Row
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('world-query0135-static-%Y%m%dT%H%M%S.%fZ');out.mkdir();rows=[]
    with(PROFILE/'official-0.135.1-full.wat').open('rb')as stream:
        for i in INDICES:
            row=dict(con.execute('select * from functions where idx=?',(i,)).fetchone());assert(row['body_start'],row['body_end'])==bodies[i]
            stream.seek(row['wat_start']);wat=stream.read(row['wat_end']-row['wat_start']);assert wat.splitlines()[0].startswith(f'  (func (;{i};)'.encode())
            (out/f'{i}.wat').write_bytes(wat);lines=wat.decode().splitlines();returns=[dict(line=j+1,preceding=lines[max(0,j-12):j+1])for j,line in enumerate(lines)if line.strip()=='return']
            if i==6730:
                assert len(returns)==1
                assert '\n'.join(x.strip()for x in lines).startswith('(func (;6730;) (type 0) (param i32 i32)\n(local ')
                assert 'i32.const 3712\ni32.sub\nlocal.tee 18\nglobal.set 0' in '\n'.join(x.strip()for x in lines[:25])
                assert '\n'.join(x.strip()for x in returns[0]['preceding']).endswith('local.get 18\ni32.const 3712\ni32.add\nglobal.set 0\nreturn')
            rows.append(dict(index=i,**row,body_sha256=hashlib.sha256(original[row['body_start']:row['body_end']]).hexdigest(),wat_sha256=hashlib.sha256(wat).hexdigest(),
                explicit_return_windows=returns,direct_callees=[dict(x)for x in con.execute('select callee,count(*)sites from calls where caller=?group by callee',(i,))]))
    receipt=dict(version='0.135.1',build='0898d5e3',original_sha256=SOURCE_SHA,source_sha256=before,
        original_global_section_hex=original[g[2]:g[3]].hex(),mutable_global_count=1,initial_stack1048576=True,
        normal6730_only_return_restores_original_stack=True,functions=rows,
        contracts=['29631 world argument is Rc+8; nav inline8751/13516 uses Rc+32tag/+36ptr/+40len/+44originX/+48originY/+52width.',
            'Primary height grid Rc+56tag/+72ptr/+76len/+80originX/+84originY/+88width; secondary Rc+92tag/+96ptr/+100len/+104originX/+108originY/+112width.',
            '23181 is primary cached-raster ring search,not mesh collision; caller13516 passes Rc+56 and uses only returnedZ.',
            '5112 and5893 are hashmapreserve callees,notnavquery;8751/13516 do not call either.'],
        original_executed=False,complete_world_producer_reconstructed=False)
    target=out/'trace.json';target.write_text(json.dumps(receipt,indent=2)+'\n');assert sha(__import__('pathlib').Path(__file__))==before
    print(json.dumps(dict(directory=str(out),functions=len(rows),trace_sha256=sha(target),original_executed=False)))


if __name__=='__main__':main()
