#!/usr/bin/env python3
"""Bounded read-only135 kind12/1020 coexistence evidence and migration plan.
No target/module/model/builder/checker execution; no old source modifications.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sqlite3,stat
ROOT=Path(__file__).resolve().parents[1]
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
ORIGINAL=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
ORIGINAL_SHA='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'

def sha(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def main():
    assert sha(ORIGINAL)==ORIGINAL_SHA
    old_files=('reconstruction/core_spec/resource_consumer135.py','reconstruction/core_spec/resource_aura135.py','reconstruction/core_spec/mixed_resource135.py','reconstruction/core_spec/resource_player_update135.py')
    before={n:sha(ROOT/n)for n in old_files};out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('self-aura0135-static-plan-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    specs={1202:[(51,57,'active expiry strict greater'),(116,187,'inert default effective0 and8/9 magnitude dominance'),(199,313,'ordered positive aggregation'),(330,350,'negative live onlykind7'),(608,713,'separate owned definition12 source excluded')],2088:[(134,171,'any ordered expiry>=now dirty trigger'),(755,938,'stable strict retain and1512 then1202'),(940,1032,'poolmin and3s regen arithmetic')],4600:[(663,690,'selection protection1020 physical writes;12/16 not written'),(749,750,'selection calls full1202')],1072:[(7063,7067,'1512 then4600 continuation')],1512:[(614,788,'passive8B G1696/1700 tag13 to accumulator43'),(1525,1533,'accumulator43 storesG1620')]}
    queries=[];proofs=[]
    database_mode=oct(stat.S_IMODE((PROFILE/'index.sqlite').stat().st_mode))
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.135.1-full.wat').open('rb')as wat,ORIGINAL.open('rb')as original:
        db.row_factory=sqlite3.Row;db.execute('pragma query_only=on')
        for idx,ranges in specs.items():
            query='select * from functions where idx=?';row=dict(db.execute(query,(idx,)).fetchone());size=row['wat_end']-row['wat_start'];assert 0<size<524288
            wat.seek(row['wat_start']);text=wat.read(size);lines=text.decode().splitlines();(out/f'{idx}.wat').write_bytes(text)
            original.seek(row['body_start']);body=original.read(row['body_end']-row['body_start']);assert len(body)==row['body_bytes']
            queries.append(dict(sql=query,parameter=idx,result=row,body_sha256=hashlib.sha256(body).hexdigest(),wat_sha256=hashlib.sha256(text).hexdigest(),wat_bytes_read=size))
            for a,b,label in ranges:proofs.append(dict(function=idx,label=label,start_line=a,end_line=b,instructions=lines[a-1:b]))
    result=dict(schema='azeroth-ports-self-aura0135-static-plan-v1',status='static_rules_recovered_waiting_baseline_commit_before_minimal_expansion',version='0.135.1',actual_build='90898d5e3',historical_build_alias='0898d5e3',original_sha256=ORIGINAL_SHA,trace_sha256=sha(Path(__file__)),old_source_sha256_before=before,old_source_sha256_after={n:sha(ROOT/n)for n in old_files},queries=queries,windows=proofs,database_file_mode=database_mode,SQLite_connection='mode=ro,pragma query_only=on',full_WAT_read=False,total_WAT_bytes_read=sum(q['wat_bytes_read']for q in queries),original_functions_executed=0,models_executed=0,producer_calls_executed=0,new_cases=0,
        rules=['4600 removes all existing spell1020 then appends unique kind12/1020 expiringnow+1; writes0..11,20..31 but doesnotwrite12..19','1202 live positive aggregation covers active kind12; its default dominance effective value0 ignores loaded raw union values','1202 separate negative live pass accepts onlykind7; owned-definition-kind12 is another source and remains absent','2088 expiry has no special kind12 dispatch:>=dirty,<stable retain,1512 then1202,thenregen','passive13 G1696/1700 provides nonzero1620 via1512 accumulator43; App/profile grant producer remains untraced'],
        plan=dict(wait_for_root_baseline_commit=True,no_duplicate_self_production_modules=True,minimum_existing_changes=['resource_consumer135._semantics:kind12 onlyspell1020 with semantic value0, retain physicalkind andNone','resource_aura135._buffs:admit inert1020 positive aggregation without numeric magnitude reads','mixed_resource135 validator:use expanded checked semantic view; one canonicalHP/RNG owner','resource_player_update135:allow verified1020 family without double prefix/regen'],new_fresh_validation=['Replay original0/8 domains under new frozen source; old receipts remain historical snapshot identities','Fresh full1202 and2088 coexistence:all orders of0speed/0berserker/8Battle/12protection,strict1s/10s/15s expiry and simultaneous expiry,full32backing/48Aura/None','Nonzero1620 typedpassive13 input:actual1512 computes derived;elapsed<3/=3/>3 withgate0/5 andHPclamp; do notinject arbitraryderived','Otherkind12 andunsupportedsource families remain explicitPending'],api='Keep existing canonical LevelCycleState+MixedResourceContext135+resource prefix; no headless/racial/registry change by this task',passive13_scope='Controlled valid typed vector consumer input only. Not proof of the profile/talent/App grant producer or natural trajectory.'),artifacts={str(p.name):dict(bytes=p.stat().st_size,sha256=sha(p))for p in out.glob('*.wat')})
    assert result['old_source_sha256_before']==result['old_source_sha256_after']
    (out/'trace.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(directory=str(out),sha256=sha(out/'trace.json'),new_original_cases=0,WAT_bytes_read=result['total_WAT_bytes_read'])))
if __name__=='__main__':main()
