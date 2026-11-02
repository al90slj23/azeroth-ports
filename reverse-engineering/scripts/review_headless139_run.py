#!/usr/bin/env python3
"""Read-only CLI composition review against immutable historical observations.

Only standard-library code executes. No author CLI/model/verifier, original,
WASM, world builder or mathematical reference is executed by this auditor.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime
import argparse,ast,hashlib,json,os,struct,sys,time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parent
RUN=ROOT/'evidence/raw-natural139-cpu-owned-20261102T163757.908632Z'
ORACLE=ROOT/'evidence/natural-spawn139-oracle-20261102T151856.594632Z'
WORLD=ROOT/'evidence/asset-world139-owned-20261102T031312.028310Z/model/receipt.json'
ASSETS=ROOT/'originals/entry-assets139-20261102T022818.157124Z'
AUTHOR_SOURCE_SHA={
 'reconstruction/run_headless139.py':'a34d048bc8bdcfc360e6db6615929c085b98cd2eec1d734c2186e161564ad5c1',
 'reconstruction/resource_spec/asset_bundle139.py':'fcaa6e4c997e838a27f839d20fde4857af9750d1580fb981c88d2f18e92f2040',
 'scripts/verify_headless139_run.py':'ffdc479265aa353ab877153a5e5927367205d39061843624d5bd6df8bf8b496b'}


def sha(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def load(path):return json.loads(Path(path).read_text())
def save(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def missing(pid,group=False):
    try:(os.killpg if group else os.kill)(pid,0)
    except ProcessLookupError:return True
    return False


def closure(base):
    found={};edges=set();pending=[base/'run_headless139.py'];io={}
    while pending:
        path=pending.pop()
        if path in found:continue
        found[path]=sha(path);package=list(path.relative_to(base).parts[:-1]);tree=ast.parse(path.read_text());calls=[]
        for node in ast.walk(tree):
            modules=[]
            if isinstance(node,ast.Import):modules=[a.name.split('.')for a in node.names]
            elif isinstance(node,ast.ImportFrom):
                prefix=package[:len(package)-node.level+1]if node.level else[]
                if node.module:prefix+=node.module.split('.')
                modules=[prefix]+[prefix+[a.name]for a in node.names if a.name!='*']
            elif isinstance(node,ast.Call):
                f=node.func;label=f.id if isinstance(f,ast.Name)else f.attr if isinstance(f,ast.Attribute)else''
                assert label not in('Popen','run','eval','exec','__import__','import_module','urlopen','socket'),(path,label)
                if label in('open','read_text','read_bytes','write_text','write_bytes'):calls.append(dict(line=node.lineno,call=label))
            for parts in modules:
                if not parts or parts[0]not in('core_spec','resource_spec'):continue
                for n in range(1,len(parts)+1):
                    child=base.joinpath(*parts[:n]);child=child.with_suffix('.py')if child.with_suffix('.py').is_file()else child/'__init__.py'
                    if child.is_file():edges.add((str(path.relative_to(base)),str(child.relative_to(base))));pending.append(child)
        if calls:io[str(path.relative_to(base))]=calls
    return{str(p.relative_to(base)):h for p,h in found.items()},sorted(edges),io


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--handoff',type=Path,required=True);parser.add_argument('--handoff-sha',required=True);parser.add_argument('--verifier',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();began=time.monotonic()
    out=args.output.resolve();assert out.is_relative_to((ROOT/'evidence').resolve())and not out.is_relative_to(RUN.resolve());out.mkdir();script_sha=sha(__file__)
    assert sha(args.handoff)==args.handoff_sha;handoff=load(args.handoff);run=RUN/'model';receipt=load(run/'receipt.json');terminal=load(RUN/'owned-terminal.json');start=load(RUN/'owned-start.json');verifier=load(args.verifier)
    assert len(handoff['author_files'])==6
    for name,h in handoff['author_files'].items():assert sha(ROOT/name)==h
    assert sha(run/'receipt.json')==handoff['runtime_receipt_sha256']=='57832970a4bef0c130c71d2502398c05ffef171e094620ab4f128e982262c8c7'
    assert sha(args.verifier)==handoff['projection_comparison_sha256']=='99b4d85331cb0fe4ec2cc531de14f01945139c49a359b399572efa5d9ef26225'
    for n,h in AUTHOR_SOURCE_SHA.items():assert sha(ROOT/n)==h,n
    current,edges,io=closure(ROOT/'reconstruction');frozen,frozen_edges,frozen_io=closure(run/'source-snapshot')
    assert current==frozen==receipt['source_sha256_before']==receipt['source_sha256_after']and len(current)==93
    assert edges==frozen_edges and len(edges)==392 and io==frozen_io and set(io)=={'run_headless139.py','resource_spec/asset_bundle139.py'}
    assert receipt['kind']=='independent_raw_assets_world_natural_combat139_headless_run'and receipt['version']=='0.139.0'and receipt['actual_build']=='f79c5e2b4'
    assert receipt['original_program_executed']is receipt['original_memory_read']is receipt['pre_parsed_world_read']is False
    assert receipt['original_calls']==receipt['full_main884_frames']==receipt['complete_games']==0
    assert datetime.fromisoformat(receipt['started_at_utc'])<datetime.fromisoformat(receipt['finished_at_utc'])
    assert terminal['exit_code']==0 and terminal['pid_missing']and terminal['pgid_missing']and missing(terminal['pid'])and missing(terminal['pgid'],True)
    assert start['pid']==terminal['pid']and start['pgid']==terminal['pgid']and start['wall_deadline_seconds']==3600 and start['cpu_deadline_seconds']==600
    wrapper=(RUN/'run-owned.py').read_text();assert 'resource.setrlimit(resource.RLIMIT_CPU,(600,610))'in wrapper and 'p.wait(timeout=3600)'in wrapper and 'except BaseException as e:error=repr(e)'in wrapper
    recovered=load(ROOT/'evidence/raw-natural139-formal-owned-20261102T163050.069192Z/recovered-terminal.json')
    assert recovered['child_exit_code']is None and recovered['child_exit_code_not_recorded_by_failed_supervisor']and recovered['pid_missing']and recovered['pgid_missing']
    first=load(ROOT/'evidence/raw-natural139-owned-20261102T162529.468980Z/owned-terminal.json');assert first['exit_code']==0 and first['pid_missing']and first['pgid_missing']
    previous=load(RUN/'previous-wall-deadline.json');assert previous['recovered_terminal']==recovered and previous['normal_outputs_not_reused']and previous['new_child_CPU_budget_seconds']==600 and previous['wall_watchdog_seconds']==3600
    metadata_note=load(ROOT/'evidence/raw-natural139-formal-owned-20261102T163050.069192Z/prior-run-note.json');assert metadata_note['new_original_calls']==0 and metadata_note['prior_run_completed']and 'started_at_utc'in metadata_note['correction']
    assert verifier['passed']and verifier['run_receipt_sha256']==sha(run/'receipt.json')and verifier['verifier_sha256']==AUTHOR_SOURCE_SHA['scripts/verify_headless139_run.py']
    manifest=ASSETS/'resource-map.json';acquisition=ASSETS/'receipt.json'
    assert sha(manifest)==receipt['asset_map_sha256']=='3a794c2e35873852cc8f6661fb93ec9edae9a06626277ff123f1612495927ec2'
    assert sha(acquisition)==receipt['acquisition_receipt_sha256']=='7aec47c1ce5b6d58f2374878e2f6877e95de4784aed7837a21a2075ecf97ea92'
    m=load(manifest);a=load(acquisition);assert a['version']=='0.139.0'and a['stamp']=='f339dd20e0fe'and not a['old_resource_bytes_reused']and a['resource_map_sha256']==sha(manifest)
    asset_rows={}
    for name,row in m.items():
        if not name.startswith('data/')or name.startswith('data/__index'):continue
        parts=name[5:].replace('\\','/').split('/');assert all(p not in('', '.', '..')for p in parts)
        key='\\'.join(parts);path=(REPO/row['file']).resolve()
        assert path.is_relative_to(REPO.resolve())and path.is_relative_to(Path('/Volumes/RuiRui4TB'))and key==key.lower()and key not in asset_rows
        assert path.suffix.lower()not in('.memory','.wasm','.wat','.exe','.bin')and row['http_status']==200 and row['exit_code']==0 and 0<=row['bytes']<=16*1024*1024
        asset_rows[key]=(path,row)
    assert len(asset_rows)==453 and len(m)==454
    requested=receipt['asset_requests'];unique=set(requested);assert len(unique)==receipt['loaded_assets']==451 and len(requested)==461
    total=0;asset_proofs={}
    for name in sorted(unique):
        path,row=asset_rows[name];assert path.stat().st_size==row['bytes']and sha(path)==row['sha256'];total+=row['bytes'];asset_proofs[name]=dict(path=str(path),bytes=row['bytes'],sha256=row['sha256'])
    assert total==receipt['raw_asset_bytes']==67281330 and receipt['raw_assets_unchanged']
    audit=load(run/'read-audit.json');assert not audit['forbidden']and all(v['admitted']for v in audit['opened'])
    allowed_sources={(ROOT/'reconstruction'/n).resolve()for n in current};allowed_assets={v[0]for v in asset_rows.values()};classifications=Counter();seen_assets=set()
    for row in audit['opened']:
        path=Path(row['path']).resolve();assert path.suffix.lower()not in('.memory','.wasm','.wat','.exe')
        if path in allowed_sources:kind='declared_source'
        elif path in allowed_assets:kind='declared_raw_asset';seen_assets.add(path)
        elif path in(manifest.resolve(),acquisition.resolve()):kind='declared_metadata'
        elif path.is_relative_to(run.resolve()):kind='own_output'
        else:raise AssertionError(('unadmitted_project_open',str(path)))
        classifications[kind]+=1
    assert {asset_rows[n][0]for n in unique}<=seen_assets
    cli=(ROOT/'reconstruction/run_headless139.py').read_text();provider=(ROOT/'reconstruction/resource_spec/asset_bundle139.py').read_text()
    assert cli.index('assets = AssetBundle139(')<cli.index('sys.addaudithook(audit)')<cli.index('built = build_world139(')
    assert "p.is_relative_to(REPO)"in cli and 'not OS-wide syscall audit'in cli
    assert "self.manifest_sha256 = digest(self.manifest)"in provider and 'path = (self.root / row[\'file\']).resolve()'in provider
    assert sha(WORLD)=='46a89c27c6be70beb9f957dd05c6fecb8c93c83647fcb40182e255d352ff3a48';world=load(WORLD)
    for name,value in receipt['world_artifacts'].items():
        prior=world['world_artifacts'][name];blob=WORLD.parent/prior['file'];assert value==dict(bytes=prior['bytes'],sha256=prior['sha256'])and blob.stat().st_size==prior['bytes']and sha(blob)==prior['sha256']
    original=load(ORACLE/'comparison.json');prepared=load(ORACLE/'prepared.json')
    assert sha(ORACLE/'comparison.json')=='5cab88ba3b2090e794c41ff23753ecd5aaf1fabb394765ea604cb949e29f3ec9'
    assert sha(ORACLE/'actual.jsonl')==original['artifacts']['actual.jsonl']and sha(ORACLE/'inputs.json')==prepared['frozen']['inputs.json']
    inputs=load(ORACLE/'inputs.json');observed=[json.loads(v)for v in(ORACLE/'actual.jsonl').read_text().splitlines()];assert[int(v['app_seed_u64'])for v in inputs]==[0,50,111]
    byseed={int(i['app_seed_u64']):v for i,v in zip(inputs,observed,strict=True)}
    assert sha(run/'states.jsonl')==receipt['states_sha256'];states=[json.loads(v)for v in(run/'states.jsonl').read_text().splitlines()];counts=Counter();seen=set();last={};sequence=Counter();laststep={}
    def eq(label,want,got):
        counts['assertions']+=1
        assert want==got,(label,want,got)
    def cells(label,rows,hexes,width):
        eq(label+'.capacity',len(rows),len(hexes))
        for i,(row,hx)in enumerate(zip(rows,hexes,strict=True)):
            raw=bytes.fromhex(hx);assert len(row)==len(raw)==width
            for off,(value,byte)in enumerate(zip(row,raw,strict=True)):
                if value is None:counts['unknown_bytes_observed_only']+=1
                else:eq(f'{label}[{i}]+{off}',value,byte);counts['known_bytes_compared']+=1
    for row in states:
        seed,step,stage=row['seed'],row['step'],row['stage'];key=(seed,step,stage);assert key not in seen;seen.add(key);sequence[stage]+=1;s=row['state'];a=byseed[seed]
        if stage=='opening':
            assert step==-1 and seed not in laststep;laststep[seed]=-1;p=a['initial'];combat=a['stages'][0]['before_combat'];heal=a['initial_healing'];gold=earned=0
        else:
            assert stage in('components','choice')and 0<=step<len(a['stages'])
            if stage=='components':assert step==laststep[seed]+1;laststep[seed]=step
            else:assert step==laststep[seed]and a['stages'][step]['selection_index']==0
            o=a['stages'][step]
            if stage=='components'and o['before_choice']is not None:
                v=o['before_choice'];p=v['player'];combat=v['combat'];heal=v['healing'];gold=v['gold1456'];earned=v['earned1100']
            else:p=o['after'];combat=o['combat'];heal=o['healing'];gold=o['gold1456'];earned=o['earned1100']
        tag=str(key);eq(tag+'.growth',s['growth'],p['capture']['projection']);eq(tag+'.xyz',s['player_xyz'],combat['player_xyz'])
        for name,width in(('live',32),('aura',16)):
            eq(tag+'.'+name+'.count',s[name]['count'],p[name]['count']);cells(tag+'.'+name,s[name]['storage'],p[name]['storage'],width)
        b=p['capture']['background'];eq(tag+'.NPC_count',s['physical_NPC_count'],b['units']['count']);cells(tag+'.NPC',s['physical_NPC_storage'],b['units']['storage'],432)
        eq(tag+'.pickup_count',s['pickups_count'],b['pickups']['count']);cells(tag+'.pickups',s['pickups_storage'],b['pickups']['storage'],56)
        for name in('accounted_total_bits','killcost2420_bits','counter2408','movement_sequence2412','kills1084'):eq(tag+'.'+name,s[name],combat[name])
        eq(tag+'.gold',s['gold1456'],gold);eq(tag+'.earned',s['earned1100'],earned)
        for name in('event_counter960','accepted_count1016','reason_totals64'):eq(tag+'.ledger.'+name,s['ledger'][name],heal[name])
        last[seed]=s
    assert sequence==dict(opening=3,components=306,choice=2)and len(seen)==311
    for case in receipt['cases']:
        seed=case['seed'];eq(str(seed)+'.final_state',case['final_state'],last[seed]);eq(str(seed)+'.steps',case['steps'],laststep[seed]+1)
        if seed in(0,50):assert case['steps']==110 and case['boundary']=='requested_step_budget'and len(case['selections'])==1 and case['selections'][0]['chosen_index']==0
        else:assert seed==111 and case['steps']==86 and case['boundary']=='unrestored_real_first_card'and case['selections'][0]['chosen_index']is None and case['selections'][0]['offered'][0]['ability_id']=='demo_shout'
    assert sha(__file__)==script_sha and current=={n:sha(ROOT/'reconstruction'/n)for n in current}
    for name,h in handoff['author_files'].items():assert sha(ROOT/name)==h
    save(out/'asset-proof.json',asset_proofs);save(out/'source-proof.json',dict(sources=current,edges=edges,IO_calls=io))
    result=dict(status='scoped_readonly_headless139_entry_and_historical_projection_review_passed',author_handoff_sha256=args.handoff_sha,author_verifier_sha256=sha(args.verifier),run_receipt_sha256=sha(run/'receipt.json'),states_sha256=sha(run/'states.jsonl'),auditor_sha256=script_sha,source_files=93,import_edges=392,project_IO_modules=2,raw_assets_declared=453,raw_assets_loaded=451,raw_asset_bytes=67281330,asset_requests=461,world_full_artifacts_matched=3,records=dict(sequence),counts=dict(counts),read_audit_classifications=dict(classifications),run_process=terminal,prior_successful_run_process=first,prior_wall_timeout_recovered=recovered,prior_metadata_time_correction=metadata_note,new_CPU_watchdog=previous,asset_proof_sha256=sha(out/'asset-proof.json'),source_proof_sha256=sha(out/'source-proof.json'),author_original_executions=0,author_model_executions=0,author_CLI_or_verifier_executions=0,new_original_acceptance_cases=0,different_mathematical_reference=False,full884_frames=0,native_windows_executions=0,complete_games=0,seconds=time.monotonic()-began,
        limitations=['This is a new independent production entry plus historical-original projection comparison, not a new mathematical reference or neworiginal experiment.','Only declared CLI growth/player/knownNone physical/ledger projections compared; unknown bytes remain observations and packetstream/AIhistory/schedulerhiddenstate are not included.','Python open audit begins after source/metadata freezing and checks project opens; it is not OS-wide filesystem isolation. Static AST audit finds IO only in entry and rawprovider.','Three existing rawworld artifact hashes are matched, not independently rebuilt again by this reviewer.','Only firstThunderchoice policy; seed111actualDemo boundary retained. Full14/884/App/render/audio/save/network/nativeWindows/completegame remain unaccepted.'])
    save(out/'review.json',result);print(json.dumps(dict(output=str(out/'review.json'),sha256=sha(out/'review.json'),counts=dict(counts),records=dict(sequence),seconds=result['seconds'])),flush=True)


if __name__=='__main__':main()
