#!/usr/bin/env python3
"""Current1391 stats1542/table/seven-source binding, no original execution."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,sqlite3,sys
sys.dont_write_bytecode=True
import map_engine1391_incremental as base
ROOT=base.ROOT
PROFILE=ROOT/'evidence/wasm01391-profile-20261102T133454.115329Z'
MAPPING=ROOT/'evidence/engine1391-refined-static-20261102T134726.927557Z/mapping.json'
MAP_SHA='bc7d702aedfb762bec50929d277f0374fdc74c5121d19dfc25b9328768117e42'


def main():
    assert base.sha(MAPPING)==MAP_SHA
    role=next(e for e in json.loads(MAPPING.read_text())['entries']if e['role']=='stats')
    old=base.catalog(base.OLD,base.OLD_SHA,base.identity139old)
    new=base.catalog(base.SOURCE,base.SOURCE_SHA,base.identity139new)
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('stats1391-static-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    memory=bytearray(new['static_bounds'][1])
    for seg in new['identity']['data_segments']:
        if seg['address']is not None:memory[seg['address']:seg['address']+seg['bytes']]=new['raw'][seg['file_offset']:seg['file_offset']+seg['bytes']]
    def u(p):
        assert 0<=p<=p+4<=len(memory)
        return int.from_bytes(memory[p:p+4],'little')
    classes={};races={};declarations=[]
    for cls in(1,2,3,4,5,7,8,9,11):
        pointer=u(1601176+4*(cls-2))if cls>=2 else 5874384
        classes[cls]=(u(pointer+72),u(pointer+76));declarations.append(dict(domain='class',selector=cls,pointer=pointer,hp_bits=u(pointer+72),armor_bits=u(pointer+76),scalar8_hex=memory[pointer+72:pointer+80].hex()))
    for race in range(1,9):
        pointer=u(1601016+4*(race-2))if race>=2 else 5871100
        p,n=u(pointer+16),u(pointer+20);assert 1<=n<=8 and p+n*8<=len(memory)
        mods=[(memory[p+8*j],u(p+8*j+4))for j in range(n)];races[race]=mods
        declarations.append(dict(domain='race',selector=race,pointer=pointer,modifier_pointer=p,modifier_count=n,raw_modifiers8_hex=memory[p:p+n*8].hex(),modifiers=mods))
    functions=[];texts={}
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.139.1-full.wat').open('rb')as stream:
        db.row_factory=sqlite3.Row;db.execute('pragma query_only=on')
        callees=[dict(row)for row in db.execute('select callee,count(*) sites from calls where caller=1542 group by callee')]
        for idx in[1542]+[row['callee']for row in callees]:
            row=dict(db.execute('select *from functions where idx=?',(idx,)).fetchone())
            assert(row['body_start'],row['body_end'],row['body_bytes'])==new['ranges'][idx]
            size=row['wat_end']-row['wat_start'];assert size<500000
            stream.seek(row['wat_start']);raw=stream.read(size);assert raw.startswith(f'  (func (;{idx};)'.encode())
            (out/f'{idx}.wat').write_bytes(raw);texts[idx]=raw.decode()
            functions.append(dict(index=idx,params_hex=new['sig'][idx][0],results_hex=new['sig'][idx][1],body_sha256=new['hashes'][idx],wat_sha256=hashlib.sha256(raw).hexdigest(),**row))
    assert new['sig'][1542]==('7f','')and new['hashes'][1542]==role['new']['body_sha256']
    assert hashlib.sha256(texts[1542].encode()).hexdigest()==role['new']['wat_sha256']
    oldwat=(MAPPING.parent/'1390-stats-1542.wat').read_text()
    assert hashlib.sha256(oldwat.encode()).hexdigest()==role['old']['wat_sha256']
    assert base.normalized(oldwat,old,True)==base.normalized(texts[1542],new,True)
    lines=[line.strip()for line in texts[1542].splitlines()];guards=[]
    for label,sequence in[
        ('classdefault',['i32.const 5874384','local.set 3']),('classtable',['i32.load offset=1601176','local.set 3']),
        ('racedefault',['i32.const 5871100','local.set 9']),('racetable',['i32.load offset=1601016','local.set 9']),
        ('racecount',['local.get 9','i32.load offset=20']),('raceptr',['local.get 9','i32.load offset=16']),
        ('frame32',['global.get 0','i32.const 32','i32.sub','local.tee 4','global.set 0'])]:
        sites=[j+1 for j in range(len(lines)-len(sequence)+1)if lines[j:j+len(sequence)]==sequence]
        assert sites,label;guards.append(dict(label=label,sites=sites,instructions=sequence))
    headers=dict(passives=[1692,1696,1700,8],adjustments=[1668,1672,1676,16],items=[2024,2028,2032,8],owned=[168,172,176,8],timed_definitions=[2048,2052,2056,36],timed_records=[592,596,600,12],live=[1704,1708,1712,32])
    for label,(cap,ptr,count,stride)in headers.items():assert f'i32.load offset={ptr}'in lines and f'i32.load offset={count}'in lines,label
    sources={name:base.sha(ROOT/name)for name in('scripts/trace_stats1391.py','scripts/map_engine1391_incremental.py','scripts/wasm139_profile.py','scripts/wasm1391_profile.py','scripts/wasm134_profile.py','scripts/wasm_index.py')}
    for name,h in sources.items():p=out/'source-snapshot'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes());assert base.sha(p)==h
    result=dict(version='0.139.1',build='b89633f9b',source_sha256=base.SOURCE_SHA,old_source_sha256=base.OLD_SHA,entry_map_sha256=MAP_SHA,script_sha256=base.sha(Path(__file__)),classes=classes,races=races,declarations=declarations,functions=functions,direct_callees=callees,full_normalized_body_after_explicit_codegen_rewrites_equal=True,explicit_codegen_rewrites=[],full_normalized_body_equal_without_codegen_rewrite=True,guards=guards,seven_source_headers=headers,source_files=sources,
        output_fields=dict(derived=list(range(1536,1625,4)),currentHP=1440,auxiliary=[1444,1448,1348,764],speed=1648,speed_sequence=1644,movement_queue=[1880,1884,1888],BTree=[2476,2480],BTree_keys=[22,28,1109]),original_executions=0,old_acceptance_transferred=False,
        limitations=['Staticfullnormalizedbody/tableidentityonly;alloriginalcalleesremainnew1391andrequirefreshbehaviorvalidation.','Sevenexplicitcaller-ownedorderedsourcevectors,notnaturalproducerorcompleteGame.','NoWindowsapplicationorwholegameexecution.'])
    base.save(out/'trace.json',result)
    print(json.dumps(dict(directory=str(out),trace_sha256=base.sha(out/'trace.json'),body_sha256=new['hashes'][1542],functions=len(functions),callees=callees)),flush=True)


if __name__=='__main__':main()
