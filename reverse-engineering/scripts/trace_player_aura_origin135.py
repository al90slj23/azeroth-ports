#!/usr/bin/env python3
"""Read-only1560/default1089 Aura owner and App-notification path evidence.
Bounded indexed WAT reads only; never execute a target, model or checker.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sqlite3
ROOT=Path(__file__).resolve().parents[1]
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
ORIGINAL=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
SOURCE_SHA='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'

def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    assert sha(ORIGINAL)==SOURCE_SHA
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('player-aura-origin0135-static-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    specs={1560:[(1193,1205,'raw2657=Game2569 zero andraw2088=Game2000 emptyAura header'),(2736,2745,'Game base istemporaryframe+88 for1512')],1089:[(8,16,'firstdebugguard'),(1177,1214,'allfiveboss2785 calls insidefirstdebugguard'),(1885,1911,'secondG2576 debugguard excludeslate5745'),(2462,2502,'debug5745 via temporarydefinition list')],10146:[(148,170,'G2052/2056 iterator source'),(579,617,'emptydefinition source produceszero followup rows'),(707,723,'5745 onlythroughdefinition traversal')]}
    windows=[];identities=[]
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,ORIGINAL.open('rb')as raw,(PROFILE/'official-0.135.1-full.wat').open('rb')as wat:
        db.row_factory=sqlite3.Row;db.execute('pragma query_only=on')
        for idx,ranges in specs.items():
            row=dict(db.execute('select * from functions where idx=?',(idx,)).fetchone());size=row['wat_end']-row['wat_start'];assert 0<size<524288
            wat.seek(row['wat_start']);text=wat.read(size);(out/f'{idx}.wat').write_bytes(text);lines=text.decode().splitlines()
            raw.seek(row['body_start']);body=raw.read(row['body_bytes']);assert len(body)==row['body_bytes']
            identities.append(dict(index=idx,query='select * from functions where idx=?',row=row,body_sha256=hashlib.sha256(body).hexdigest(),WAT_sha256=hashlib.sha256(text).hexdigest()))
            for a,b,label in ranges:windows.append(dict(index=idx,lines=[a,b],label=label,instructions=lines[a-1:b]))
        targets={1202,42920,23581,44447};skipped={(1089,2785):'G2576=0 firstdebugguard',(1089,5745):'G2576=0 seconddebugguard',(10146,5745):'G2056=0 definition traversal'}
        closure=[]
        for entry in(1560,1089):
            seen=set();todo=[entry];edges=[];excluded=[]
            while todo:
                idx=todo.pop()
                if idx<878 or idx in seen:continue
                seen.add(idx);assert len(seen)<=1024
                for row in db.execute('select distinct callee from calls where caller=? order by callee',(idx,)):
                    callee=row['callee'];edge=(idx,callee)
                    if edge in skipped:excluded.append(dict(caller=idx,callee=callee,reason=skipped[edge]));continue
                    edges.append(edge)
                    if callee not in seen:todo.append(callee)
            assert not seen&targets
            closure.append(dict(entry=entry,function_count=len(seen),functions=sorted(seen),direct_edges=sorted(edges),excluded_edges=excluded,targets=sorted(targets),no_target_reachable=True,scope='Conservative direct-call index with explicit proven gates; not a generic full indirect-call/type analysis'))
    result=dict(schema='azeroth-ports-player-aura-origin0135-static-v1',version='0.135.1',actual_build='90898d5e3',original_sha256=SOURCE_SHA,producer_sha256=sha(Path(__file__)),status='bounded_static_constructor_and_default_opening_rules',functions=identities,windows=windows,direct_call_closures=closure,
        constructor_rules=dict(actual_Game_base='1560temporaryframe+88',aura_header=dict(capacity_offset=2000,pointer_offset=2004,count_offset=2008,capacity=0,pointer=4,count=0),initialized2569=0,full48_allocated_by_constructor=False,called1512=True,called1202=False),
        default_opening_requirements=dict(flags2576=0,definitions2056=0,empty_selected_profile=True),default_opening_rules=dict(final_Aura_state_not_proven_by_direct_graph=True,App14340336_history_not_proven_by_direct_graph=True,controller_notification_input_remains_explicit=True,indirect_call_edges_not_resolved=True,not_claimed_for_nonempty_definition_or_debug_inputs=True),
        implementation_input='Constructor explicit header writes support ResourceAuraState135(storage=(),initialized2569=0). Opening final state additionally requires controlled raw corroboration; direct graph alone is insufficient. Verified1202 rebuild can generate48 rows with marker0 known and12inactive bytes None',root_correction='G1976 is not this fixed135 Aura header; do not confuse constructor temporaryframe offsets with Game offsets',prior_trace_diagnostic='220416 origin receipt overstates default AppID/Aura conclusions; retained as historical diagnostic, superseded by this explicit indirect-edge limitation',original_executed=False,models_executed=False,new_original_cases=0,new_mainloop_frames=0,full_WAT_read=False,total_WAT_bytes_read=sum(i['row']['wat_end']-i['row']['wat_start']for i in identities))
    (out/'trace.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(directory=str(out),trace_sha256=sha(out/'trace.json'),functions=[(x['entry'],x['function_count'])for x in closure],WAT_bytes_read=result['total_WAT_bytes_read'],new_original_cases=0)))
if __name__=='__main__':main()
