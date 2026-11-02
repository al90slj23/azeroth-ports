#!/usr/bin/env python3
"""Independent1398740/13563 read-only reference; no author production imports."""
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,math,sqlite3,struct,time
from review_combat139 import bits,fp,f32,local_closure,parse_module,sha,u32
from review_npc_spawn139 import heading_ref
from review_player_motion135 import World

ROOT=Path(__file__).resolve().parents[1]
CASE=ROOT/'evidence/world-position139-oracle-20261102T035151.444640Z'
SOURCE=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
STATIC=ROOT/'evidence/world-position139-static-20261102T033613.062984Z'
COMPARISON_SHA='eb52328da53d1f90ccba3957f649cd3d52314e20287096e23cac2c46794bb931'
HANDOFF_SHA='b055af94f470d828211f361245ba81d0d4ecfc36bd5f2946b72774d0d7bea3f9'
SOURCE_SHA='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
COUNTEREXAMPLE=ROOT/'evidence/world-position139-review-work/counterexample.json'
COUNTEREXAMPLE_SHA='cbc42c1bdc0bf26ca72b390bc3b7273d63e3e1241ec3ff3af5526f4411d591ad'
WORLD_REVIEW=ROOT/'evidence/world139-independent-review-owned-20261102T041305.531201Z/review/review.json'
WORLD_REVIEW_SHA='dcbd2ad0703771e1b023306a91594f33f0d333419b330da0a8797b45c8bfcdff'
HELPERS={'scripts/review_combat139.py':'158d211c3ec36093e26536aaf402606fb558c059ee528134abe12294328932b9',
         'scripts/review_npc_spawn139.py':'aa1c8a9d5ca4fe0363f97cbdad71f13ce00ebccf238fe89b213f354627ef5074',
         'scripts/review_player_motion135.py':'8a339b74435adbc4abcf5aff7f3a25a24d5f8495653e42135f06aa94230de2b2'}
H=float.fromhex
HALFPI=H('0x1.921fb54442d18p0');PI=2*HALFPI;THREEHALFPI=H('0x1.2d97c7f3321d2p2');TAU=4*HALFPI


def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sin_kernel(x):
    squared=x*x;cube=squared*x
    high=(cube*(squared*squared))*(squared*H('0x1.6cd878c3b46a7p-19')+H('-0x1.a00f9e2cae774p-13'))
    low=cube*(squared*H('0x1.11110896efbb2p-7')+H('-0x1.5555554cbac77p-3'))+x
    return f32(high+low)
def cos_kernel(x):
    squared=x*x;fourth=squared*squared
    low=(squared*H('-0x1.ffffffd0c5e81p-2')+1.)+fourth*H('0x1.55553e1053a42p-5')
    return f32(low+(squared*fourth)*(squared*H('0x1.99342e0ee5069p-16')+H('-0x1.6c087e80f1e27p-10')))
def trig(angle):
    raw=bits(angle);magnitude=raw&0x7fffffff;assert magnitude<=0x40c90fdb;x=abs(angle)
    if magnitude<964689920:sine,cosine=x,1.
    elif magnitude<1061752795:sine,cosine=sin_kernel(x),cos_kernel(x)
    elif magnitude<1075235812:sine,cosine=cos_kernel(x-HALFPI),sin_kernel(HALFPI-x)
    elif magnitude<1081824210:sine,cosine=-sin_kernel(x-PI),-cos_kernel(x-PI)
    elif magnitude<1085271520:sine,cosine=-cos_kernel(x-THREEHALFPI),sin_kernel(x-THREEHALFPI)
    else:sine,cosine=sin_kernel(x-TAU),cos_kernel(x-TAU)
    return (-sine if raw>>31 else sine),cosine
def hypot_ref(a,b):
    small,large=sorted([abs(a),abs(b)],key=bits);sm,lg=bits(small),bits(large)
    if sm==0 or lg-sm>=209715200:return f32(large+small)
    factor=1.
    if lg>1568669695:small=f32(small*2.**-90);large=f32(large*2.**-90);factor=2.**90
    elif sm<562036736:small=f32(small*2.**90);large=f32(large*2.**90);factor=2.**-90
    return f32(factor*f32(math.sqrt(f32(small*small+large*large))))
def direct_norm(a,b):
    #13563 does NOT call50441. Both products round to f32 before addition.
    return f32(math.sqrt(f32(f32(a*a)+f32(b*b))))
def next_rng(state):
    a,b,c,d=state;rol=lambda x,n:((x<<n)|(x>>(32-n)))&0xffffffff
    out=(rol((a+d)&0xffffffff,7)+a)&0xffffffff
    return out,(a^b^d,a^b^c,(a^c^(b<<9))&0xffffffff,rol(b^d,11))


class Reference:
    def __init__(self,state,world,nav,scalars,tables):
        self.s=state;self.world=world;self.nav=nav;self.scalars=scalars;self.tables=tables;self.words=tuple(state['rng_words']);self.count=Counter()
    def uniform(self,low,high):
        low,high=fp(low),fp(high);width=f32(high-low);assert low<high and math.isfinite(width)
        for _ in range(10001):
            out,self.words=next_rng(self.words);self.count['rng_draws']+=1
            value=f32(low+f32(f32(fp((out>>9)|0x3f800000)-1.)*width))
            if value<high:return value
            self.count['upper_rejections']+=1
        raise AssertionError('Bounded independent RNG watchdog')
    def probe(self,x,y):
        dx,dy=f32(x-fp(self.nav['origin_xy_bits'][0])),f32(y-fp(self.nav['origin_xy_bits'][1]))
        if dx<0 or dy<0:return None,None
        xx,yy=int(dx),int(dy);width=self.nav['width']
        if xx>=width or yy>=width:return None,None
        idx=xx+width*yy;return self.nav['bytes'][idx],idx
    def height(self,x,y):
        result=self.world.height(bits(x),bits(y));return None if result is None else fp(result)
    def xy(self,angle,radius):
        sine,cosine=trig(angle);px,py=map(fp,self.s['player_xyz'][:2])
        return f32(px+f32(cosine*radius)),f32(py+f32(sine*radius))
    def random(self):
        cx,cy=map(fp,self.scalars['center_xy_bits']);limit=fp(self.scalars['radius_bits']);pz=fp(self.s['player_xyz'][2])
        for _ in range(12):
            self.count['random_trials']+=1;angle=f32(self.uniform(0,0x40c90fdb)+0.);radius=self.uniform(self.s['low_radius_bits'],self.s['high_radius_bits'])
            x,y=self.xy(angle,radius);dx,dy=f32(x-cx),f32(y-cy);distance=direct_norm(dx,dy)
            if distance>limit:
                self.count['clamps']+=1
                y=f32(cy+f32(limit*f32(dy/distance)));x=f32(cx+f32(limit*f32(dx/distance)))
            value,_=self.probe(x,y)
            if value:self.count['random_nav_rejections']+=1;continue
            z=self.height(x,y)
            if z is not None and abs(f32(z-pz))<25.:return [bits(x),bits(y),bits(z)]
        self.count['random_final_unclamped']+=1
        angle=f32(self.uniform(0,0x40c90fdb)+0.);radius=self.uniform(self.s['low_radius_bits'],self.s['high_radius_bits']);x,y=self.xy(angle,radius);z=self.height(x,y)
        assert not self.scalars['primary_present']
        if z is None:self.count['world_fallback_z']+=1;z=fp(self.scalars['fallback_height_bits'])
        return [bits(x),bits(y),bits(z)]
    def spawn(self):
        vx,vy=map(fp,self.s['velocity_xy']);moving=f32(f32(vx*vx)+f32(vy*vy))>4.
        heading=heading_ref(vy,vx,self.tables) if moving else 0.;cx,cy=map(fp,self.scalars['center_xy_bits']);limit=fp(self.scalars['radius_bits']);px,py,pz=map(fp,self.s['player_xyz'])
        for _ in range(16):
            self.count['spawn_trials']+=1;biased=False
            if moving:
                out,self.words=next_rng(self.words);self.count['rng_draws']+=1
                biased=f32(float(out>>8)*2.**-24)<fp(self.s['bias_probability_bits'])
            angle=f32(heading+self.uniform(0xbf99999a,0x3f99999a)) if biased else f32(self.uniform(0,0x40c90fdb)+0.)
            radius=self.uniform(self.s['low_radius_bits'],self.s['high_radius_bits'])
            while radius>=12.:
                x,y=self.xy(angle,radius);distance=hypot_ref(f32(x-cx),f32(y-cy));z=None
                if distance<=f32(limit+18.):z=self.height(x,y)
                if z is not None and abs(f32(z-pz))<=(8. if distance>limit else 25.):
                    value,idx=self.probe(x,y);path=self.s['distance_map'];allowed=False
                    if path is None:allowed=value!=1
                    elif not value:
                        if path['field24']<401:allowed=True;self.count['path_lazy_branch']+=1
                        elif idx is not None:
                            assert path['fill_u16'] is not None and idx<path['count'];cost=path['fill_u16'];self.count['path_cost_reads']+=1
                            allowed=cost!=65535 and cost<=f32(f32(hypot_ref(f32(x-px),f32(y-py))*1.5)+12.)
                    if allowed:return [bits(x),bits(y),bits(z)]
                radius=f32(radius-2.);self.count['radius_shrinks']+=1
        self.count['fallback13563']+=1;return self.random()


def load_world(receipt):
    p=Path(receipt['receipt']);assert sha(p)==receipt['receipt_sha256'];source=json.loads(p.read_text());assert source['world_artifacts']==receipt['world_artifacts']
    assert not source['original_memory_read'] and not source['original_program_executed'] and not source['preparsed_world_input_read']
    data={}
    for key,row in source['world_artifacts'].items():
        q=p.parent/row['file'];assert q.stat().st_size==row['bytes'] and sha(q)==row['sha256'];data[key]=q.read_bytes()
    raw=data['terrain'];cursor=0
    def take(fmt):
        nonlocal cursor
        result=struct.unpack_from(fmt,raw,cursor);cursor+=struct.calcsize(fmt);return result
    tile_count,=take('<I');tiles=[]
    for _ in range(tile_count):
        *bounds,count=take('<5I');chunks=[]
        for _ in range(count):
            holes,vertices=take('<HI');assert vertices==145
            chunks.append((tuple(take('<3I') for _ in range(vertices)),holes))
        tiles.append((tuple(chunks),tuple(bounds)))
    assert cursor==len(raw)
    world=World.__new__(World);world.tiles=tiles;world.cache={};world.queries=Counter();world.fallback=source['query_scalars']['fallback_height_bits']
    secondary=source['world_artifacts']['secondary'];world.secondary=(tuple(x[0] for x in struct.iter_unpack('<I',data['secondary'])),*secondary['origin_xy_bits'],secondary['width'])
    nav=dict(source['world_artifacts']['navigation'],bytes=data['navigation'])
    return world,nav,source['query_scalars']


def main():
    started=time.monotonic();assert sha(CASE/'comparison.json')==COMPARISON_SHA and sha(CASE/'task-handoff.json')==HANDOFF_SHA and sha(SOURCE)==SOURCE_SHA
    for name,digest in HELPERS.items():assert sha(ROOT/name)==digest
    receipt=json.loads((CASE/'comparison.json').read_text());prepared=json.loads((CASE/'prepared.json').read_text());handoff=json.loads((CASE/'task-handoff.json').read_text());manifest=json.loads((CASE/'manifest.json').read_text());runtime=json.loads((CASE/'runtime.json').read_text());proof=json.loads((STATIC/'proof.json').read_text())
    for name,digest in handoff['owned_files'].items():assert sha(ROOT/name)==digest
    assert receipt['source_before']==receipt['source_after']==prepared['source_before']
    assert len(handoff['owned_files'])==10 and len(receipt['source_before'])==25
    for name,digest in receipt['source_before'].items():assert sha(ROOT/name)==digest==sha(CASE/'source-snapshot'/name)
    edges=local_closure(receipt['source_before']);assert edges==sorted(receipt['source_import_edges'])
    assert len(edges)==49 and len([p for p in receipt['source_before'] if p.startswith('reconstruction/')])==14
    for name,digest in receipt['artifacts'].items():assert sha(CASE/name)==digest
    for name,digest in prepared['frozen'].items():assert sha(CASE/name)==digest
    assert receipt['expected_before_original'] and not receipt['expectations_from_originalmemory'] and not prepared['original_input_contains_expected']
    assert receipt['model_diagnostics_notdirectoriginalcounters'] and not receipt['old_bad5d940snapshot_loaded']
    assert sha(WORLD_REVIEW)==WORLD_REVIEW_SHA
    world,nav,scalars=load_world(receipt['world_provenance']);assert not scalars['primary_present'] and not scalars['flat_present']
    raw=SOURCE.read_bytes();original=parse_module(raw);modified_raw=(CASE/manifest['module_file']).read_bytes();modified=parse_module(modified_raw)
    for a,b in zip(original['sections'],modified['sections']):
        assert a['kind']==b['kind']
        if a['kind']!=7:assert raw[a['start']:a['end']]==modified_raw[b['start']:b['end']]
    assert len(original['sections'])==len(modified['sections']) and len(original['imports'])==882
    assert modified['exports']==original['exports']+[('research139_position_spawn',0,8740),('research139_position_random',0,13563),('research139_position_stack0',3,0)]
    assert original['types'][original['decl'][8740-882]]==('7f7f7d7d7d','') and original['types'][original['decl'][13563-882]]==('7f7f7d7d','')
    def data(address,size):
        out=bytearray(size)
        for base,offset,count in original['data_segments']:
            if base is None:continue
            lo,hi=max(base,address),min(base+count,address+size)
            if lo<hi:out[lo-address:hi-address]=raw[offset+lo-base:offset+hi-base]
        return out
    tables=[list(struct.unpack('<4f',data(p,16))) for p in [14426512,14426528,14426544,14426560]]
    db=sqlite3.connect(f'file:{PROFILE}/index.sqlite?mode=ro',uri=True);db.row_factory=sqlite3.Row;db.execute('pragma query_only=on');bodies=[]
    with (PROFILE/'official-0.139.0-full.wat').open('rb') as stream:
        for key,record in proof['functions'].items():
            idx=int(key);loc=dict(db.execute('select * from functions where idx=?',(idx,)).fetchone());a,z=original['bodies'][idx];assert (a,z)==(loc['body_start'],loc['body_end']) and hashlib.sha256(raw[a:z]).hexdigest()==record['body_sha256']
            stream.seek(loc['wat_start']);value=stream.read(loc['wat_end']-loc['wat_start']);assert value==(STATIC/f'{idx}.wat').read_bytes()
            bodies.append(dict(index=idx,body_sha256=record['body_sha256'],WAT_sha256=hashlib.sha256(value).hexdigest()))
    random_wat=(STATIC/'13563.wat').read_text();spawn_wat=(STATIC/'8740.wat').read_text()
    assert 'call 50441' not in random_wat and 'call 50441' in spawn_wat
    assert random_wat.count('f32.sqrt')==1 and 'local.tee 18\n          local.get 18\n          f32.mul\n          f32.add\n          f32.sqrt' in random_wat
    assert 'distance = hypot_bits(dx, dy)' in (ROOT/'reconstruction/core_spec/world_position139.py').read_text()
    cases=json.loads((CASE/'inputs.json').read_text());expected=json.loads((CASE/'expected.json').read_text());actual=[json.loads(x) for x in (CASE/'stdout.jsonl').read_text().splitlines()];assert len(cases)==len(expected)==len(actual)==80
    differences=[];details=[];total=Counter();nonrng=rngbytes=0
    ranges=json.loads((CASE/'observed-world-ranges.json').read_text());assert len(ranges['ranges'])==2318 and sum(r['n'] for r in ranges['ranges'])==ranges['bytes']==5950608
    assert len({(r['p'],r['n']) for r in ranges['ranges']})==2318 and all(0<=r['p']<r['p']+r['n']<=111804416 for r in ranges['ranges'])
    for case,want,got in zip(cases,expected,actual):
        assert case['id']==want['id']==got['id'] and case['input']==want['input'] and case['kind']==want['kind']
        reference=Reference(case['input'],world,nav,scalars,tables);position=reference.spawn() if case['kind']=='spawn' else reference.random();answer=dict(position_bits=position,rng_words=list(reference.words));total.update(reference.count)
        if answer!=want['expected'] or answer!=got['projection']:differences.append(dict(id=case['id'],kind=case['kind'],reference=answer,expected=want['expected'],actual=got['projection']))
        before=bytes.fromhex(got['raw_game_before_hex']);after=bytes.fromhex(got['raw_game_after_hex']);assert len(before)==len(after)==2592
        assert list(struct.unpack_from('<4I',before,1720))==case['input']['rng_words'] and list(struct.unpack_from('<3I',before,1416))==case['input']['player_xyz']
        assert list(struct.unpack_from('<4I',after,1720))==answer['rng_words']
        assert u32(before,2348)==20544696 and before[2587]==0
        assert list(struct.unpack_from('<2I',before,1736))==case['input']['velocity_xy']
        for p,(a,b) in enumerate(zip(before,after)):
            if 1720<=p<1736:rngbytes+=1
            else:assert a==b;nonrng+=1
        assert got['world124_before_hex']==got['world124_after_hex'] and got['world_data_digest_before']==got['world_data_digest_after'] and got['world_ranges']==2318
        assert got['world_data_digest_before']==ranges['digest']
        header=bytes.fromhex(got['world124_before_hex']);assert len(header)==124 and u32(header,56)==0xffffffff and header[120]==0
        assert [u32(header,p) for p in [40,44,48,52,100,104,108,112,116]]==[78400,*nav['origin_xy_bits'],280,313600,*nav['origin_xy_bits'],560,scalars['fallback_height_bits']]
        out=bytes.fromhex(got['output16_hex']);assert list(struct.unpack_from('<3I',out))==got['projection']['position_bits'] and out[12:]==bytes([0xa5]*4)
        assert got['before16_hex']=='c3'*16 and got['after16_hex']=='d7'*16 and got['stack_after']==1048576
        path=case['input']['distance_map'];observed=got['path_view']
        if path is None:assert observed is None and u32(before,2368)==0
        else:
            view=bytes.fromhex(observed['before_hex']);assert u32(view,24)==path['field24'] and u32(before,2368)==observed['pointer']
            if path['fill_u16'] is None:assert reference.count['path_cost_reads']==0 and observed['values_pointer'] is None
            else:assert observed['values_count']==path['count'] and observed['values_sha256']==hashlib.sha256(struct.pack('<H',path['fill_u16'])*path['count']).hexdigest()
        details.append(dict(id=case['id'],kind=case['kind'],independent_diagnostics_not_original_counters=dict(reference.count)))
    assert not differences and (nonrng,rngbytes)==(206080,1280)
    assert runtime==receipt['runtime'] and (runtime['full8740_direct_calls'],runtime['full13563_direct_calls'])==(63,17)
    assert runtime['original_export_calls']==80 and runtime['snapshot_restores']==80 and runtime['healthy_v2_input']
    assert runtime['allocator_calls']==102 and runtime['stack_checks']==182 and runtime['denied_imports']==882 and runtime['actual_host_calls']==0
    assert runtime['peak_memory_bytes']==111804416 and runtime['memory_cap_bytes']==268435456 and not runtime['network_used'] and not runtime['user_saves_accessed']
    for name in ['process-terminal.json','validator-terminal.json']:
        terminal=json.loads((CASE/name).read_text());assert terminal['exit_code']==0 and terminal['pid_missing'] and terminal['pgid_missing'] and terminal['seconds']<60
    audit=json.loads((CASE/'expectation-read-audit.json').read_text());assert audit['kind']=='Pythonopen_audit_notOSsyscallaudit' and not audit['forbidden']
    permitted={str(Path(receipt['world_provenance']['receipt']))}|{str(Path(receipt['world_provenance']['receipt']).parent/p['file']) for p in receipt['world_provenance']['world_artifacts'].values()}
    assert all(e['allowed'] and e['path'] in permitted for e in audit['events'])
    assert sha(COUNTEREXAMPLE)==COUNTEREXAMPLE_SHA;counter=json.loads(COUNTEREXAMPLE.read_text())
    candidate=Reference(counter['case_input']['input'],world,nav,scalars,tables);prediction=dict(position_bits=candidate.random(),rng_words=list(candidate.words))
    assert prediction==counter['original_WAT_reference_prediction'] and prediction!=counter['old_hypot_reference_prediction'] and counter['original_executions']==counter['author_production_executions']==0
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('world-position139-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    result=dict(status='not_accepted_source_fidelity_finding_despite80_output_matches',comparison_sha256=COMPARISON_SHA,script_sha256=sha(Path(__file__)),cases=80,differences=differences,reference_counters_not_original_observation=dict(total),details=details,
                nonRNG_Game_bytes=nonrng,RNG_Game_bytes=rngbytes,source_closure=receipt['source_before'],source_edges=edges,static_functions=bodies,helper_sha256=HELPERS,original_executions_by_reviewer=0,author_model_checker_builder_executions_by_reviewer=0,
                finding='13563 f32-square/f32sum/f32sqrt callsite differs from author hypot helper f64square/f64sum/f32demote/f32sqrt;8740 correctly uses50441',
                counterexample_path=str(COUNTEREXAMPLE.relative_to(ROOT)),counterexample_sha256=COUNTEREXAMPLE_SHA,counterexample_reference_prediction=prediction,counterexample_not_original_execution=True,
                world_query_independent_review_dependency=dict(path=str(WORLD_REVIEW.relative_to(ROOT)),sha256=WORLD_REVIEW_SHA),healthy_v2_memory_read_by_reference=False,
                original_world_range_observation=dict(count=2318,bytes=5950608,digest=ranges['digest'],range_file_as_read_sha256=sha(CASE/'observed-world-ranges.json'),original_memory_rehashed_by_reviewer=False),
                snapshot_scope=dict(sha256=receipt['snapshot_sha256'],R=20544696,G=14685248,App=14680072,healthy_v2=True,old_invalid_snapshot=False),
                author_owned_process=receipt['process'],runtime=runtime,seconds=time.monotonic()-started,
                limitations=['80 complete controlled snapshot8740/13563 output/RNG matches are retained but source fidelity is not accepted due concrete13563 clamp arithmetic defect.',
                             'Counterexample is independent current-WAT/raw-world prediction only,not new original observation;author must freeze corrected new sources and perform fresh original test including this input.',
                             'World expectation reads only current139raw canonical terrain/nav/secondary artifacts;World.__init__ is never called and no originalmemory is read by reference. Earlier135math implementation is reused only as independent arithmetic with current139 five-getter static/independent review binding;no old cases/results transferred.',
                             'World2318ranges/5950608B digests and input path no-mutation are frozen-runner observations/assertions;review does not rehash original memory or claim independent WorldRc production.',
                             '182stackchecks are runner assertions/aggregate,not individually serialized.63full8740+17direct13563;internal fallback callcounts/attempts/draws are reference-only diagnostics.',
                             'FullGame2592 conservation verified outside fourRNG words.Output writes12B into16B with4B A5padding and both16B canaries intact;explicitpathMap views are controlled input,not natural owner production.',
                             'Expected Pythonopen audit is not OSsyscall auditing.Healthyv2snapshot accepted as supplied context,not naturalApp/world ownership/full1108/native/fullgame restoration.'])
    save(out/'review.json',result);print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),differences=differences,nonRNG=nonrng,RNG=rngbytes,seconds=time.monotonic()-started)),flush=True)


if __name__=='__main__':main()
