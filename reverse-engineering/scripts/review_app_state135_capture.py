#!/usr/bin/env python3
"""Read-only independent697B prediction audit against one prior original cast.

Reuses only independent reviewer byte/WAT utilities; never imports production.
No WASM/browser/network starts, no memory restore or original-state writes.
The33 directly observed bytes remain explicit inputs, not predictions.
"""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,os,sqlite3,struct,sys
sys.dont_write_bytecode=True
from review_app_state135 import execute_window
from review_app_history135 import static_data,interpret53845

ROOT=Path(__file__).resolve().parents[1]
DIRECTORY=ROOT/'evidence/app-state0135-capture-check-20261101T121246.633972Z'
COMPARISON_SHA='0850bf419fe3b430117255ddd445501721c0c3c6ffb343d99fdd7c3e0b09c03a'
ORIGIN=ROOT/'evidence/full-app0135-probe-20261101T120144.289175Z'
ORIGIN_SHA='fd5dba35d0aeacffe822ce070fd5bc218da8352a5b725e48c166df289b91c726'
SOURCE=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
SOURCE_SHA='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
INDEX_SHA='b1032d016b6ef43da115eb373a10f03ee2ddfae428cee7d988057d2caac773a0'
INPUT_RANGES=((4008,16),(4768,4),(4928,8),(5056,4),(5161,1))


def sha(path):
    with Path(path).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()


def author_sources():
    pending=[ROOT/'scripts/check_app_state135_capture.py'];seen=set()
    while pending:
        p=pending.pop()
        if p in seen:continue
        seen.add(p)
        for node in ast.walk(ast.parse(p.read_text())):
            if not isinstance(node,ast.ImportFrom):continue
            if node.level:
                assert node.level==1
                pending.extend(p.parent/(name.replace('.','/')+'.py')for name in([node.module]if node.module else[a.name for a in node.names]))
            elif node.module and node.module.startswith('core_spec'):
                pending.append(ROOT/'reconstruction/core_spec/__init__.py')
                if node.module!='core_spec':pending.append(ROOT/'reconstruction'/(node.module.replace('.','/')+'.py'))
                else:pending.extend(ROOT/'reconstruction/core_spec'/(a.name+'.py')for a in node.names if(ROOT/'reconstruction/core_spec'/(a.name+'.py')).exists())
            elif node.module and(ROOT/'scripts'/(node.module+'.py')).exists():pending.append(ROOT/'scripts'/(node.module+'.py'))
    return set(str(p.relative_to(ROOT))for p in seen)


def missing(pid,group=False):
    try:(os.killpg if group else os.kill)(pid,0)
    except ProcessLookupError:return True
    return False


def ranges_of_none(values):
    result=[];start=None
    for i,value in enumerate((*values,0)):
        if value is None and start is None:start=i
        elif value is not None and start is not None:result.append([start,i-start]);start=None
    return result


def main():
    comparison_path=DIRECTORY/'comparison.json';assert sha(comparison_path)==COMPARISON_SHA
    r=json.loads(comparison_path.read_text());assert(r['known_bytes_compared'],r['declared_input_bytes'],r['independently_predicted_bytes_compared'],r['unknown_or_inactive_bytes_uncompared'])==(730,33,697,4438)
    assert r['status']=='passed_known_projection'and not r['differences']and r['new_original_calls']==r['new_original_cases']==0
    assert r['full_legal_app_produced']is False and r['original_module_instantiated_by_this_checker']is False
    before=dict(r['source_sha256_before']);assert before==r['source_sha256_after']and set(before)==author_sources()and len(before)==7
    for name,h in before.items():assert sha(ROOT/name)==h==sha(DIRECTORY/'source-snapshot'/name)
    for name,record in r['artifacts'].items():assert(DIRECTORY/name).stat().st_size==record['bytes']and sha(DIRECTORY/name)==record['sha256']
    for p in(Path(__file__),ROOT/'scripts/review_app_state135.py',ROOT/'scripts/review_app_history135.py'):before[str(p.relative_to(ROOT))]=sha(p)
    origin_path=ORIGIN/'receipt.json';assert sha(origin_path)==ORIGIN_SHA
    origin=json.loads(origin_path.read_text());assert origin['original_sha256']==SOURCE_SHA and origin['source_sha256_before']==origin['source_sha256_after']
    assert origin['process']['exit_code']==0 and origin['process']['terminal']['all_owned_terminal']is True
    terminal=origin['process']['terminal'];assert all(missing(int(p))for p in terminal['owned_pids'])and all(missing(int(g),True)for g in terminal['owned_pgids'])
    frozen_origin_sources={}
    for name,h in origin['source_sha256_before'].items():assert sha(ORIGIN/'source-snapshot'/name)==h;frozen_origin_sources[name]=h
    assert sha(ORIGIN/'config.json')==origin['config_sha256']and sha(ORIGIN/'bridge.mjs')==origin['bridge_sha256']
    config=json.loads((ORIGIN/'config.json').read_text());glue=ROOT/'originals/official-acquisition-20261101T030310.926207Z/official-wenilla.js'
    assert config['original_sha256']==SOURCE_SHA and sha(glue)==config['official_glue_sha256']
    probe=ast.parse((ORIGIN/'source-snapshot/scripts/probe_full_app135.py').read_text())
    append=next(ast.literal_eval(n.value)for n in probe.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='APPEND'for t in n.targets))
    assert(ORIGIN/'bridge.mjs').read_bytes()==glue.read_bytes()+append.encode()
    browser=(ORIGIN/'source-snapshot/scripts/browser_full_app135.mjs').read_text()
    assert 'crypto.subtle.digest'in browser and 'if(digest!==config.original_sha256)'in browser
    assert "phase==='after'&&id===867&&args[1]===5305816"in browser
    assert 'const env=args[0]>>>0,Rc=u(env+8),App=Rc+16'in browser
    assert 'app5168_hex_at_cast:Array.from(new Uint8Array(memory().buffer,App,5168)'in browser
    runtime=origin['runtime'];result=runtime['result'];assert len(result['contexts'])==1
    context=result['contexts'][0];actual=bytes.fromhex(context['app5168_hex_at_cast']);assert len(actual)==5168 and actual==(DIRECTORY/'observed-app5168.bin').read_bytes()
    assert context['source']=='actual_original_cast867_env12_plus8_AppRc'and result['original_function_bodies_changed']is False and result['wasm_memory_written_by_research']is False
    assert result['user_profile_used']is False and origin['user_profile_used']is False
    assert any(row.get('phase')=='after' and row.get('id')==867 and row.get('args',[])[:2]==[context['env'],5305816] and row.get('returned')=='function'for row in result['imports'])
    env=bytes.fromhex(context['closure_env12_hex']);assert len(env)==12
    rc=struct.unpack_from('<I',env,8)[0];assert rc==context['Rc']and rc+16==context['App']
    header=context['header'];assert header['App']==context['App'] and header['Rc']==rc and header['memory_bytes']==27787264
    timer=[t for t in result['timers']if t['env']==context['env']];assert len(timer)==1 and timer[0]['vtable']==5305816 and timer[0]['interval_ms']==25
    assert int.from_bytes(actual[:8],'little')==0 and context['final']['marker_u64']=='1'
    assert context['final']['memory_bytes']!=header['memory_bytes']
    raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA and sha(PROFILE/'index.sqlite')==INDEX_SHA
    con=sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);con.row_factory=sqlite3.Row;texts={};functions=[]
    with(PROFILE/'official-0.135.1-full.wat').open('rb')as stream:
        for idx in(4253,53845,83825,122123):
            row=dict(con.execute('SELECT * FROM functions WHERE idx=?',(idx,)).fetchone());stream.seek(row['wat_start']);text=stream.read(row['wat_end']-row['wat_start']);texts[idx]=text
            assert text.startswith(f'  (func (;{idx};)'.encode());functions.append(dict(**row,wat_sha256=hashlib.sha256(text).hexdigest(),body_sha256=hashlib.sha256(raw[row['body_start']:row['body_end']]).hexdigest()))
    con.close();history,stores=interpret53845(texts[53845]);table,tableproof=static_data(raw,5222424,16);server,serverproof=static_data(raw,5221378,13)
    assert history==(DIRECTORY/'independent-history240.bin').read_bytes()and struct.unpack('<4I',table)==(5222416,0,0,0)and server==b'azeroth.local'
    first,second=struct.unpack_from('<2Q',actual,4008);maps=b''.join(table+struct.pack('<2Q',(first+j)&((1<<64)-1),second)for j in range(4))
    assert maps==(DIRECTORY/'independent-maps128.bin').read_bytes()
    scalar=dict(lcg_input=struct.unpack_from('<Q',actual,4928)[0],transport_pointer=struct.unpack_from('<I',actual,4768)[0],
        server_pointer=struct.unpack_from('<I',actual,5056)[0],startup_flag5161=actual[5161])
    declared=json.loads((DIRECTORY/'inputs.json').read_text());assert declared['first_map_seed_pair_u64']==[str(first),str(second)]and declared['directly_observed_input_bytes']==33
    assert declared['lcg_seed_u64']==scalar['lcg_input']and declared['transport_pointer']==scalar['transport_pointer']and declared['server_string_pointer']==scalar['server_pointer']and declared['startup_flag5161']==scalar['startup_flag5161']
    case=dict(**scalar,history240_hex=history.hex(),hash_maps128_hex=maps.hex(),live_blocks=[])
    window='\n'.join(texts[4253].decode().splitlines()[8601:8894])+'\n';expected,write_trace=execute_window(window,case,{5222424:table,5221378:server})
    assert list(expected)==json.loads((DIRECTORY/'independent-expected.json').read_text())
    known={i for i,v in enumerate(expected)if v is not None};supplied={i for start,count in INPUT_RANGES for i in range(start,start+count)};predicted=known-supplied
    assert(len(known),len(supplied),len(predicted))==(730,33,697)and supplied<=known
    masks=json.loads((DIRECTORY/'masks.json').read_text());assert masks==dict(known_offsets=sorted(known),direct_input_offsets=sorted(supplied),independently_predicted_offsets=sorted(predicted),unknown_ranges=ranges_of_none(expected))
    assert all(expected[i]==actual[i]for i in known)
    predicted_expected=bytes(expected[i]for i in sorted(predicted));predicted_actual=bytes(actual[i]for i in sorted(predicted));assert predicted_expected==predicted_actual
    assert hashlib.sha256(predicted_expected).hexdigest()==r['expected_predicted697_sha256']==r['observed_predicted697_sha256']
    assert all(expected[i]is None for start,count in((4160,368),(4528,48),(4980,36))for i in range(start,start+count))
    assert r['history240_independently_generated']is True and r['maps_next_three_seed_pairs_independently_generated']is True and r['input_maps128_wholecopy']is False
    assert r['prior_run_scope']['healthy_renderer_or_boot_proved']is False and r['prior_run_scope']['gameplay_proved']is False
    for region in r['regions']:
        start,count=region['offset'],region['length'];assert all(expected[i]is not None for i in range(start,start+count))
        assert region['expected_sha256']==hashlib.sha256(bytes(expected[start:start+count])).hexdigest()==region['observed_sha256']
        assert region['direct_input_bytes']==sum(i in supplied for i in range(start,start+count))and region['independently_predicted_bytes']==sum(i in predicted for i in range(start,start+count))
    after={n:sha(ROOT/n)for n in before};assert before==after
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('app-state0135-capture-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    for n,h in before.items():p=out/'source-snapshot'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==h
    (out/'independent-wat-byte-write-trace.json').write_text(json.dumps(write_trace,indent=2)+'\n');(out/'predicted697.bin').write_bytes(predicted_expected)
    (out/'decoded-history240.bin').write_bytes(history);(out/'decoded-maps128.bin').write_bytes(maps)
    record=dict(status='passed_scoped_read_only_projection_review',version='0.135.1',build='0898d5e3',comparison=str(comparison_path.relative_to(ROOT)),comparison_sha256=COMPARISON_SHA,
        original_observation=str((ORIGIN/'receipt.json').relative_to(ROOT)),original_observation_sha256=ORIGIN_SHA,
        source_count=7,source_closure_independently_collected=True,review_source_sha256_before=before,review_source_sha256_after=after,frozen_original_observer_sources=frozen_origin_sources,
        original_sha256=SOURCE_SHA,original_official_js_prefix_unchanged=True,four_original_functions_reread=functions,
        cast_app=dict(env=context['env'],Rc=rc,App=context['App'],memory_bytes=27787264,final_memory_not_used=True,strong_count_not_predicted=True),
        declared_input_ranges=[dict(offset=o,length=n)for o,n in INPUT_RANGES],direct_input_bytes=33,known_bytes=730,independently_predicted_bytes=697,unknown_None_bytes=4438,
        predicted697_sha256=hashlib.sha256(predicted_expected).hexdigest(),decoded_history_from_30_original53845_stores=240,decoded_maps_from_first_seed_pair_and_static_header=128,
        independently_predicted_map_bytes=112,whole_maps_or_history_copied_from_observed=False,live_copy_inputs_supplied=False,
        independent_wat_memory_addresses=[write_trace['app_base'],write_trace['scratch_base']],no_production_model_imported=True,new_original_calls=0,new_original_cases=0,new_mainloop_frames=0,
        reused_original_observation_runs=1,whole_App_legality_proved=False,renderer_or_boot_health_proved=False,original_state_restored=False,
        excluded_prior_context=dict(complete_idle880_returns=result['confirmed_complete880_returns'],runtime_errors=len(runtime['errors']),renderer_panic_preserved=r['prior_run_scope']['renderer_panicked'],
            counted_as_this_review_acceptance=False),
        static_data_proof=dict(table=tableproof,server=serverproof),limitations=[
            'Only697bytespredicted;33capturedinputbytesarenotpredictionvalidation. Unknown4438remainNone.',
            'Priororiginalnaturalconstructorcastonly;noindependentAppallocator/entropy/profile/ownershipproducer.',
            'CapturedAppiscast-time27.8MiBcontext;final413.7MiBmemoryclockstatewasnotcomparedorrestored.',
            'Earlier8idle880andSwiftShaderpanicareexcludedfromprojectionacceptance;nohealthyboot/gameplay/full880reconstructionclaim.'],
        artifacts={p.name:sha(p)for p in out.iterdir()if p.is_file()})
    target=out/'review.json';target.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(dict(directory=str(out),review_sha256=sha(target),predicted_bytes=697,new_original_calls=0)))


if __name__=='__main__':main()
