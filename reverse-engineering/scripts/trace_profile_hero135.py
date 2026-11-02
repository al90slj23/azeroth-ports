#!/usr/bin/env python3
"""Static name producer trace; read input App name header only,never output text."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sqlite3,struct
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
SHA='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
PRESTATE=ROOT/'evidence/entry-world0135-probe-20261101T092959.623703Z'
SNAPSHOT_SHA='23af074eaebd5c1ac915ee8f8a35430b94c4276c822bc15aaf505e9c29911aaf'
def sha(p):
    with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def main():
    source=SOURCE.read_bytes();assert hashlib.sha256(source).hexdigest()==SHA
    names=('scripts/browser_entry_world135.mjs','scripts/run_opening_combat135_oracle.mjs','scripts/run_opening_combat135_cas_oracle.mjs','reconstruction/core_spec/profile_hero135.py',str(Path(__file__).relative_to(ROOT)))
    frozen={n:sha(ROOT/n)for n in names};config=json.loads((PRESTATE/'entry-world135-config.json').read_text());receipt=json.loads((PRESTATE/'entry-world135-probe-receipt.json').read_text())
    assert config['source_before']==receipt['source_before']==receipt['source_after']
    assert frozen[names[0]]==config['source_before'][names[0]]==sha(PRESTATE/'source-snapshot'/names[0])
    snapshot=PRESTATE/'after_real_begin1089.memory';assert sha(snapshot)==SNAPSHOT_SHA
    app=14549000
    with snapshot.open('rb')as f:
        f.seek(app+3376);tag=f.read(4);f.seek(app+3376+200);header=f.read(12)
    assert tag==bytes(4)and header==bytes(12)
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('profile-hero135-static-%Y%m%dT%H%M%S.%fZ');out.mkdir();texts={};functions={}
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.135.1-full.wat').open('rb')as stream:
        db.row_factory=sqlite3.Row;db.execute('pragma query_only=on')
        for index in(6730,75442,1560,1938):
            row=dict(db.execute('select *from functions where idx=?',(index,)).fetchone());stream.seek(row['wat_start']);text=stream.read(row['wat_end']-row['wat_start']);assert len(text)<1048576
            body=source[row['body_start']:row['body_end']];functions[index]=dict(body_start=row['body_start'],body_end=row['body_end'],body_bytes=len(body),body_sha256=hashlib.sha256(body).hexdigest(),wat_bytes=len(text),wat_sha256=hashlib.sha256(text).hexdigest());texts[index]=text.decode();(out/f'{index}.wat').write_bytes(text)
    windows={}
    for name,index,a,b,terms in(
        ('selected_profile_present',6730,14,20,('i32.load offset=3376','i32.const 2','i32.ne')),
        ('profile_name_string_clone',6730,39,46,('i32.const 3520','i32.const 3576','call 75442')),
        ('first_profile152',6730,247,256,('i32.const 3320','i32.const 152','memory.copy')),
        ('profile_tail_and_name_reorder',6730,282,309,('i32.const 3512','i32.const 152','i32.const 184','i32.const 168','i32.const 32','memory.copy')),
        ('final_selected376_into1560',6730,10640,10697,('i32.const 2944','i32.const 184','i32.const 168','i32.const 3136','i32.const 32','i32.const 152','call 1560')),
        ('profile376_copy_to_scratch104',1560,682,688,('i32.const 104','local.get 1','i32.const 376','memory.copy')),
        ('scratch88_copy_to_Game',1560,2740,2754,('i32.const 88','call 1512','local.get 0','i32.const 2592','memory.copy')),
        ('Game_hero_to_quote11735',1938,1074,1095,('i32.load offset=224','i32.load offset=220','i32.const 1583604','call 11735')),
        ('clone_empty_skips_payload',75442,4,15,('i32.load offset=8','i32.eqz','i32.const 1','br 1')),
        ('clone_header_is_len_ptr_len',75442,32,44,('i32.store offset=8','i32.store offset=4','i32.store','return'))):
        text='\n'.join(texts[index].splitlines()[a-1:b]);assert all(x in text for x in terms),name;windows[name]=dict(function=index,first_line=a,last_line=b,text=text,sha256=hashlib.sha256(text.encode()).hexdigest())
    browser=(ROOT/names[0]).read_text();assert 'const P=App+3376;b().fill(0,P,P+376);'in browser
    runner_windows={}
    for name in names[1:3]:
        text=(ROOT/name).read_text();a=text.index('const appBefore=hex(App,5168)');b=text.index('const answer=',a);fragment=text[a:b]
        assert all(x in fragment for x in('App+4928','App+3720','App+3721','App+3552','App+3604','App+3612'))and all(x not in fragment for x in('App+3576','App+3580','App+3584'))
        runner_windows[name]=dict(text=fragment,sha256=hashlib.sha256(fragment.encode()).hexdigest())
    result=dict(status='static_source_chain_complete_for_explicit_empty_research_profile',original_sha256=SHA,source_before=frozen,source_after={n:sha(ROOT/n)for n in names},original_calls=0,production_imports=0,production_executions=0,functions=functions,windows=windows,runner_windows=runner_windows,input_prestate=dict(snapshot=str(snapshot.relative_to(ROOT)),sha256=SNAPSHOT_SHA,App=app,selected_profile_offset=3376,profile_tag_hex=tag.hex(),name_header_profile200_204_208_hex=header.hex(),input_name_bytes_read=0,post_target_results_read=False,browser_input_source_sha256=frozen[names[0]]),mapping=dict(input='App3376+200/204/208',clone='75442→temporary3520',profile='selected376+200/204/208',Game='216/220/224',notification='1938 Game220/224→11735'),conclusion=dict(hero='',empty_clone_header=[0,1,0],basis='Explicit zero376 research input plus75442 length-zero branch;not absence of EmptyOpeningInput field',natural_menu_profile_producer_recovered=False),api='core_spec.profile_hero135.empty_research_selected_profile_hero135()',limitations=['Only declared browser research empty selected376 and name-preserving opening wrappers.','EmptyOpeningInput135 alone cannot imply hero empty.','Input nameheader only;no post-target string bytes or expected-output feedback read.','Positive UTF8 input permitted by pure clone semantics,new pointer remainsNone;no differential acceptance added.'])
    assert result['source_before']==result['source_after'];save(out/'trace.json',result);print(json.dumps(dict(output=str(out/'trace.json'),sha256=sha(out/'trace.json'),sources=frozen)))
if __name__=='__main__':main()
