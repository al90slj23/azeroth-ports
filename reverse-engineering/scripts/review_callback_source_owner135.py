#!/usr/bin/env python3
"""Second-author readonly empty-source owner/selection64 audit.

No production/model/checker/builder/original executes. In particular the
incoming_callbacks135 dependency was authored by this reviewer and receives no
second-author predicate credit here;only source-owner output tuples are read.
"""
from pathlib import Path
from collections import Counter
import argparse,ast,hashlib,json,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
import review_player_motion135 as M  # Binary/AST readers only;not reference().
ROOT=M.ROOT;RUN=ROOT/'evidence/full0135-oracle-20261102T003504.117627Z'
SHA='d4d48ab268e42a5b6abb9bb826cdd3238c2832736ba0d22536d112a9f27ba354'
STATIC=ROOT/'evidence/callback-source-owner135-static-20261102T003650.844444Z'
STATIC_SHA='3505a7d7a0245326575d1ad4350d8e626a4958b697e70e9f4b6d9fa22d576833'
sha=M.sha;load=M.load
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();out=args.output.resolve();assert out.is_relative_to((ROOT/'evidence').resolve());out.mkdir();began=time.monotonic()
    reviewers={str(p.relative_to(ROOT)):sha(p)for p in(Path(__file__),Path(M.__file__))}
    for n,h in reviewers.items():p=out/'reviewer-source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==h
    assert sha(RUN/'comparison.json')==SHA;report=load(RUN/'comparison.json');prepared=load(RUN/'prepared.json');manifest=load(RUN/'manifest.json');author=load(ROOT/'reports/2026-11-02-callback-source-owner0135.json')
    assert(report['cases'],report['full1560'],report['full1072'],report['differences'])==(9,9,64,0)
    files=report['source_sha256_before'];assert len(files)==17 and files==report['source_sha256_after']==prepared['source_sha256']
    for n,h in files.items():assert sha(ROOT/n)==sha(RUN/'source-snapshot'/n)==h,n
    edges=M.source_edges(RUN/'source-snapshot',files);assert edges==[tuple(x)for x in report['local_source_import_edges']]and len(edges)==32
    prod={n for n in files if n.startswith('reconstruction/')};todo=['reconstruction/core_spec/callback_source_owner135.py','reconstruction/core_spec/ability_state135.py'];seen=set()
    while todo:
        n=todo.pop()
        if n in seen:continue
        seen.add(n);todo.extend(b for a,b in edges if a==n)
    assert seen==prod and len(prod)==10
    assert report['expected_before_original']and prepared['expected_before_original']
    checker=(RUN/'source-snapshot/scripts/check_callback_source_owner135.py').read_text();assert checker.index("('expected.json',expected)")<checker.index('subprocess.Popen(')
    for n,h in report['frozen_artifacts'].items():assert sha(RUN/n)==h
    assert prepared['artifacts']==report['frozen_artifacts']and not load(RUN/'differences.json')
    original=M.ORIGINAL.read_bytes();assert hashlib.sha256(original).hexdigest()==M.ORIGINAL_SHA==report['original_sha256']
    changed=(RUN/manifest['module_file']).read_bytes();assert hashlib.sha256(changed).hexdigest()==manifest['module_sha256']
    old,new=M.sections(original),M.sections(changed);assert[k for k,*_ in old]==[k for k,*_ in new]and not any(k==8 for k,*_ in old)
    assert all(original[a:z]==changed[b:y]for(k,a,_,z),(_,b,_,y)in zip(old,new)if k!=7)
    ex=lambda raw,sects:M.exports(raw,next(x for x in sects if x[0]==7))
    assert ex(changed,new)==ex(original,old)+[(r['export'],0,r['index'])for r in manifest['roles']]and not any('stack'in name for name,_,_ in ex(changed,new))
    at=next(x for x in old if x[0]==1)[2];n,at=M.leb(original,at);types=[]
    for _ in range(n):
        assert original[at]==0x60;n,at=M.leb(original,at+1);a=original[at:at+n].hex();at+=n;n,at=M.leb(original,at);b=original[at:at+n].hex();at+=n;types.append([a,b])
    at=next(x for x in old if x[0]==3)[2];n,at=M.leb(original,at);decl=[]
    for _ in range(n):x,at=M.leb(original,at);decl.append(x)
    at=next(x for x in old if x[0]==10)[2];n,at=M.leb(original,at);bodies=[]
    for _ in range(n):size,start=M.leb(original,at);at=start+size;bodies.append((start,at))
    assert sha(STATIC/'proof.json')==STATIC_SHA==author['static_proof_sha256'];proof=load(STATIC/'proof.json');functions={};texts={}
    with sqlite3.connect((M.PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(M.PROFILE/'official-0.135.1-full.wat').open('rb')as stream:
        db.row_factory=sqlite3.Row;db.execute('pragma query_only=on')
        for idx in(9868,25765,20363,1976,1560,1072,1512,24129,4600,26967,25368,28796):
            row=dict(db.execute('select *from functions where idx=?',(idx,)).fetchone());a,b=bodies[idx-878];assert(a,b)==(row['body_start'],row['body_end']);stream.seek(row['wat_start']);data=stream.read(row['wat_end']-row['wat_start']);assert len(data)<1048576
            functions[idx]=dict(body_start=a,body_end=b,body_sha256=hashlib.sha256(original[a:b]).hexdigest(),signature=types[decl[idx-878]],wat_bytes=len(data),wat_sha256=hashlib.sha256(data).hexdigest());texts[idx]=data.decode();(out/f'{idx}.wat').write_bytes(data)
            if str(idx)in proof['functions']:assert data==(STATIC/f'{idx}.wat').read_bytes()and functions[idx]['body_sha256']==proof['functions'][str(idx)]['body_sha256']
    for role in manifest['roles']:
        f=functions[role['index']];assert f['signature']==[role['parameters_hex'],role['results_hex']]and all(f[k]==role[k]for k in('body_start','body_end','body_sha256'))
    windows={}
    for name,index,a,b,terms in(
        ('9868_zero_store_and_rank_count',9868,8,52,('i32.store offset=68','i64.const 17179869184','i64.store offset=12','i32.load offset=8','if')),
        ('9868_derived_queue_empty',9868,996,1030,('i32.load offset=100','i32.eqz','br_if 0')),
        ('9868_flag164',9868,1166,1179,('i32.load8_u offset=12','i32.eqz','br_if 0')),
        ('9868_header_return',9868,1509,1540,('i32.store offset=56','i64.load offset=12','i64.store align=4')),
        ('25765_profile152_and_gear260',25765,8,42,('i32.const 152','call 9868','i32.const 260','call 20363')),
        ('20363_each_equipped_ID',20363,25,72,('i32.load','call 1976','i32.const -1')),
        ('1976_zero_unsigned_range',1976,450,460,('i32.const 1','i32.sub','i32.const 99999','i32.lt_u','i32.const 100000')),
        ('1976_not_found',1976,1338,1347,('i32.const -1','i32.store')),
        ('20363_19_slots',20363,154,176,('i32.const 4','i32.const 76','i32.eq')),
        ('20363_tag2_no_set',20363,245,292,('i32.const 2','i32.store8 offset=4')),
        ('25765_no_extra_gear',25765,163,176,('i32.load offset=80','i32.const -1','i32.eq','br_if 0')),
        ('1560_profile_source_call',1560,194,206,('i32.const 24','call 25765')),
        ('1560_source60_copy',1560,1246,1278,('i32.store offset=2168','i64.store offset=2136','i64.store offset=2112')),
        ('1560_lives0',1560,809,821,('i32.const 0','i32.store offset=1720')),
        ('1560_left0',1560,1166,1176,('i32.const 0','i32.store8 offset=2655')),
        ('1560_ring_empty',1560,986,1002,('i64.const 17179869184','i64.store offset=1056','i64.store offset=1064')),
        ('1072_new_reads_item_source',1072,486,515,('i32.const 2024','call 26967','call 26591')),
        ('1072_new_owned_reorder',1072,597,617,('call 24129',)),
        ('1072_upgrade_owned',1072,810,878,('i32.load offset=1664','i32.load offset=1660','call 25368')),
        ('1072_common1512_4600',1072,7060,7072,('call 1512','call 4600'))):
        text='\n'.join(texts[index].splitlines()[a-1:b]);assert all(t in text for t in terms),name;windows[name]=dict(function=index,first_line=a,last_line=b,text=text,sha256=hashlib.sha256(text.encode()).hexdigest())
    #Independent overlapping-store execution of9868's initial60B,then its
    #return/copy offsets. This is not the author's owner or callback model.
    scratch=bytearray(80)
    for offset,width,value in((68,4,0),(60,8,4<<32),(52,8,4),(44,8,0),(36,8,4<<32),(28,8,4),(20,8,0),(12,8,4<<32)):scratch[offset:offset+width]=value.to_bytes(width,'little')
    headers60=scratch[12:72];assert list(struct.iter_unpack('<3I',headers60))==[(0,4,0)]*5
    selected=bytearray(2976);selected[2112:2172]=headers60;struct.pack_into('<I',selected,1720,0);selected[2655]=0
    struct.pack_into('<QQ',selected,1056,4<<32,0);game=selected[88:2680];header={str(o):struct.unpack_from('<I',game,o)[0]for o in(2024,2028,2032,2048,2052,2056)};assert header=={'2024':0,'2028':4,'2032':0,'2048':0,'2052':4,'2056':0}
    ring=list(struct.unpack_from('<4I',game,968));assert ring==[0,4,0,0]and struct.unpack_from('<I',game,1632)[0]==0 and game[2567]==0
    inputs=load(RUN/'input.json');expected=load(RUN/'expected.json');actual=[json.loads(x)for x in(RUN/'actual.jsonl').read_text().splitlines()];assert len(inputs)==len(expected)==len(actual)==9
    counts=Counter();cases=[]
    for inp,want,got in zip(inputs,expected,actual):
        assert inp['id']==want['id']==got['id']and set(inp)=={'id','class_byte','race_byte','region_id','seed','object_id','flat_height_bits','selections'}
        profile=dict(ranked_count160=0,ranked_flag164=0,equipped19=[0]*19);predicted=dict(id=inp['id'],stages=[dict(role=1560,headers=header,ring968=ring)],profileBefore=profile,profileAfter=profile)
        for card in inp['selections']:
            assert card['variant']in('upgrade','new','gold')
            if card['variant']=='upgrade':assert card['owned_index']==0 and card['kinds']in([0],[1],[2],[3],[4],[])
            if card['variant']=='new':assert card['ability_id']=='cleave'and card['tier']==0
            if card['variant']=='gold':assert card['gold']==17
            predicted['stages'].append(dict(role=1072,headers=header,phase2587=1));counts[card['variant']]+=1
        assert predicted==want==got,(inp['id'],'independent header/profile/stages')
        counts['header_projection_bytes']+=len(predicted['stages'])*24;counts['profile_slice_readonly_bytes']+=81*2;counts['constructor_ring_bytes']+=16;counts['selection_phase_bytes']+=len(inp['selections']);cases.append(dict(id=inp['id'],class_byte=inp['class_byte'],selections=len(inp['selections'])))
    assert(counts['upgrade'],counts['new'],counts['gold'])==(54,1,9)and{row['class_byte']for row in inputs}=={1,2,3,4,5,7,8,9,11}
    runtime=load(RUN/'callback-source-owner-runtime.json');terminal=load(RUN/'process-terminal.json');assert runtime==report['runtime']and terminal==report['process']and terminal['exit_code']==0 and terminal['seconds']<prepared['deadline_seconds']==60 and terminal['pid_missing']and terminal['pgid_missing']and M.missing(terminal['pid'])and M.missing(terminal['pgid'],True)
    assert(runtime['fresh_instances'],runtime['full1560'],runtime['full1072'],runtime['actual_host_calls'],runtime['denied_imports'])==(9,9,64,0,878)and runtime['max_memory_bytes']<=33554432 and not runtime['stack_guard_export']
    assert not any(runtime[k]for k in('original_snapshot_loaded','application_start_called','externref_fabricated'))
    owned=load(RUN/'owned-process.json');assert owned['deadline_seconds']==60 and'--max-old-space-size=256'in owned['command']and'--wasm-max-mem-pages=512'in owned['command']
    artifacts={n:sha(RUN/n)for n in('comparison.json','actual.jsonl','callback-source-owner-runtime.json','process-terminal.json','owned-process.json','prepared.json','input.json','expected.json','model-refusals.json','differences.json','manifest.json','validation.stdout.txt','validation.stderr.txt')}
    for n,h in files.items():assert sha(ROOT/n)==sha(RUN/'source-snapshot'/n)==h
    for n,h in reviewers.items():assert sha(ROOT/n)==h
    assert sha(RUN/'comparison.json')==SHA
    result=dict(status='passed-within-declared-source-owner-domain',author_receipt_sha256=SHA,static_receipt_sha256=STATIC_SHA,reviewer_sources=reviewers,source_count=17,production_sources=10,local_import_edges=32,sources_verified=files,static_functions=functions,static_windows=windows,constructor_source60_hex=headers60.hex(),constructor_headers=header,ring968=ring,lives1632=dict(value=0,evidence='static1560scratch1720,notcapturedbythiscomponent'),left2567=dict(value=0,evidence='static1560scratch2655,notcapturedbythiscomponent'),cases=cases,counts=dict(counts),full1560_calls=9,full1072_calls=64,new_original_calls=0,production_imports=0,production_executions=0,own_callback_predicate_independent_credit=0,runtime=runtime,process=terminal,artifacts_as_read_sha256=artifacts,seconds=time.monotonic()-began,limits=['Explicitzero376 researchprofile,not naturalApp/account/menu selection.','Sourceheaders/profile81B/ring/phase only;no completeGame1072 semantics orall source producer closure throughactual casts/events.','Onlynewcleave executed inthiscomponent;newskill source preservationelsewhere is staticbranch support,not additionaldynamiccases.','LIVES1632 andleft2567 arestatic constructor claims;actual readerdidnot capture them in9/64batch.','No stackglobal export/percall stack receipt;normalreturn/0host/outerprocess only.','Authorcomparison freezesinput/expected/module,butdoesnot hashactual/runtime/postprocess artifacts.Thisreviewbindstheir currentbytes asread,not retroactivepre-runfreeze.','Thisreviewer authoredincoming_callbacks135;no second-author callback-predicate recovery credit here.','8 model refusals notrun bythisreviewer andnotextraoriginalcases.'])
    save(out/'review.json',result);print(json.dumps(dict(output=str(out/'review.json'),sha256=sha(out/'review.json'),counts=dict(counts),seconds=result['seconds'])))
if __name__=='__main__':main()
