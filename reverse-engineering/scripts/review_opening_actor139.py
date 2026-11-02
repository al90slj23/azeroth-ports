#!/usr/bin/env python3
"""Different-author current139 actor/kind2 review; no author/target execution."""
from pathlib import Path
from collections import Counter
import hashlib,json,sqlite3,struct,sys
from review_combat139 import parse_module,local_closure,sha,bits,fp,f32
from review_initial139 import reference as constructor_reference
from review_world_position139 import trig,hypot_ref

ROOT=Path(__file__).resolve().parents[1]
CASE=ROOT/'evidence/opening-aux139-flat-oracle-20261102T050802.301653Z'
SOURCE=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
SOURCE_SHA='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
COMP='1031dcfdfa3ba42a8ca6ac9ae14c4c5298a3fc4a78d4cfc13b8c308c398d90d3'
HAND='71ff09cff5bce3c57ba3bcce776b9457099d35a36d4698af0a471180e826f4cd'
HELPERS={'scripts/review_combat139.py':'158d211c3ec36093e26536aaf402606fb558c059ee528134abe12294328932b9',
 'scripts/review_initial139.py':'86d33e69c361eef223ad3ef271b6fb987d170f4d94847c0c068148c56ebe6fbc',
 'scripts/review_world_position139.py':'d842c619169a582ab8eb540cab2829233eb633bbd79d10ab674c50e71c92ab7e',
 'scripts/review_npc_spawn139.py':'aa1c8a9d5ca4fe0363f97cbdad71f13ce00ebccf238fe89b213f354627ef5074',
 'scripts/review_player_motion135.py':'8a339b74435adbc4abcf5aff7f3a25a24d5f8495653e42135f06aa94230de2b2'}
load=lambda p:json.loads(p.read_text())
u=lambda b,o=0:struct.unpack_from('<I',b,o)[0]


def draw(words):
    a,b,c,d=words;rol=lambda x,n:((x<<n)|(x>>(32-n)))&0xffffffff
    return (rol((a+d)&0xffffffff,7)+a)&0xffffffff,(a^b^d,a^b^c,(a^c^(b<<9))&0xffffffff,rol(b^d,11))


def uniform(words,low,high):
    width=f32(high-low)
    for _ in range(1000):
        value,words=draw(words);fraction=f32(fp((value>>9)|0x3f800000)-1.)
        result=f32(low+f32(fraction*width))
        if result<high:return result,words
    raise AssertionError('Independent bounded draw watchdog')


def packed(value):
    raw=value.to_bytes(8,'little')
    return bytes((sum((v!=0)<<i for i,v in enumerate(raw)),))+bytes(v for v in raw if v)


def object_packet(guid,entry,display,scale,xyz,yaw,kind,flags):
    sine,cosine=trig(f32(yaw*.5))
    fields={0:guid&0xffffffff,1:guid>>32,2:33,3:entry,4:scale,8:display,
        9:flags,12:bits(sine),13:bits(cosine),14:1,15:xyz[0],16:xyz[1],
        17:xyz[2],18:bits(yaw),20:35,21:kind}
    mask=sum(1<<key for key in fields)
    return (struct.pack('<IBB',1,0,2)+packed(guid)+bytes((5,80))
        +struct.pack('<4I',*xyz,bits(yaw))+struct.pack('<I',1)
        +bytes((1,))+struct.pack('<I',mask)
        +b''.join(struct.pack('<I',fields[k])for k in sorted(fields))).hex()


class Reference:
    def __init__(self,case,constructor,center):
        self.c=case;self.center=center;self.words=tuple(constructor['rng_words'])if case['rng_override']is None else tuple(case['rng_override'])
        self.counter=10 if case['counter_override']is None else case['counter_override']
        self.rows=[list(bytes.fromhex(s))for s in case['pickup_backing']]
        self.count=0;self.packets=[];self.packet_cap=0
    def emit(self,entry,display,scale,xyz,kind,flags):
        self.counter=(self.counter+1)&0xffffffff
        guid=0xf110000000000000|((entry&0xffffff)<<24)|(self.counter&0xffffff)
        yaw,self.words=uniform(self.words,0.,fp(0x40c90fdb));yaw=f32(yaw+0.)
        if len(self.packets)==self.packet_cap:self.packet_cap=max(4,2*self.packet_cap)
        self.packets.append([169,object_packet(guid,entry,display,scale,xyz,yaw,kind,flags)])
        return guid
    def state(self):
        return dict(counter=self.counter,rng_words=list(self.words),pickup_capacity=len(self.rows),
            pickup_count=self.count,storage=[list(row)for row in self.rows],
            packet_capacity=self.packet_cap,packets=list(self.packets),phase2587=0)
    def pickup(self,xyz,amount,now):
        x,y=map(fp,xyz[:2]);cx,cy=map(fp,self.center)
        dx,dy=f32(x-cx),f32(y-cy);distance=hypot_ref(dx,dy)
        if distance>118.:
            x=f32(cx+f32(f32(dx/distance)*118.));y=f32(cy+f32(f32(dy/distance)*118.))
        placed=[bits(x),bits(y),self.c['flat_height_bits']]
        guid=self.emit(9005,259,0x3f800000,placed,3,0)
        if self.count==len(self.rows):self.rows.extend([[None]*56 for _ in range(max(4,2*len(self.rows))-len(self.rows))])
        row=self.rows[self.count]
        row[0:4]=bytes(4)
        row[8:56]=struct.pack('<IIQ4I4I',2,amount,guid,0,8,0,9005,*placed,now)
        self.count+=1
    def random_position(self):
        #Actual flat/no-nav fixture: every first trial has radius18..50<120,
        #and equal player/ground Z; no clamp or rejected height trial occurs.
        angle,self.words=uniform(self.words,0.,fp(0x40c90fdb))
        radius,self.words=uniform(self.words,18.,50.)
        sine,cosine=trig(f32(angle+0.));cx,cy=map(fp,self.center)
        return [bits(f32(cx+f32(cosine*radius))),bits(f32(cy+f32(sine*radius))),self.c['flat_height_bits']]


def main():
    out=Path(sys.argv[1]).resolve();out.mkdir()
    assert sha(SOURCE)==SOURCE_SHA and sha(CASE/'comparison.json')==COMP and sha(CASE/'task-handoff.json')==HAND
    for n,h in HELPERS.items():assert sha(ROOT/n)==h,(n,sha(ROOT/n))
    receipt,manifest,prepared,runtime=(load(CASE/n)for n in('comparison.json','manifest.json','prepared.json','runtime.json'))
    author=load(CASE/'task-handoff.json')['files']
    for n,h in author.items():assert sha(ROOT/n)==h
    sources=receipt['source_sha256_before'];assert sources==receipt['source_sha256_after']==prepared['sources'] and len(sources)==31
    for n,h in sources.items():assert sha(ROOT/n)==sha(CASE/'source-snapshot'/n)==h
    edges=local_closure(sources);assert len(edges)==67 and edges==sorted(receipt['source_import_edges'])==sorted(prepared['source_import_edges'])
    for n,h in receipt['frozen_artifacts'].items():assert sha(CASE/n)==h==prepared['artifacts'][n]
    for n,h in receipt['artifacts'].items():assert sha(CASE/n)==h
    raw=SOURCE.read_bytes();original=parse_module(raw);changed=(CASE/manifest['module_file']).read_bytes();modified=parse_module(changed)
    assert sha(CASE/manifest['module_file'])==manifest['module_sha256']
    assert len(original['imports'])==882 and len(original['bodies'])==177101 and len(original['sections'])==len(modified['sections'])
    for a,b in zip(original['sections'],modified['sections']):
        assert a['kind']==b['kind']
        if a['kind']!=7:assert raw[a['start']:a['end']]==changed[b['start']:b['end']]
    assert modified['exports']==original['exports']+[tuple(x)for x in manifest['added_exports']]
    gs=next(x for x in original['sections']if x['kind']==6)
    assert raw[gs['payload']:gs['end']].hex()=='017f01418080c0000b'
    assert manifest['added_exports']==[['research139_open_actor1886',0,1886],['research139_open_pickup1446',0,1446],['research139_open_random13563',0,13563],['research139_open_initial1600',0,1600],['research139_open_companion2945',0,2945],['research139_open_begin1108',0,1108],['research139_open_stack0',3,0]]
    assert [(x['module'],x['name'])for x in original['imports']]==[(x['module'],x['name'])for x in manifest['original_imports']]
    def data(address,size):
        result=bytearray(size)
        for at,offset,n in original['data_segments']:
            if at is None:continue
            lo,hi=max(at,address),min(at+n,address+size)
            if lo<hi:result[lo-address:hi-address]=raw[offset+lo-at:offset+hi-at]
        return result
    cls=5877920;race=5874636;mp,count=u(data(race+16,8)),u(data(race+16,8),4)
    classes={1:dict(hp_armor=[u(data(cls+72,8)),u(data(cls+72,8),4)],ability_pointer=5882740)}
    rp=data(race+24,8);racialname=bytes(data(u(rp),u(rp,4)));ability={}
    for i in range(114):
        p=5882740+i*88;ptr,n=struct.unpack('<2I',data(p+12,8));ability[bytes(data(ptr,n))]=p
    races={1:dict(ability_pointer=ability[racialname],modifiers=[(data(mp+8*i,1)[0],u(data(mp+8*i+4,4)))for i in range(count)])}
    zone=data(5871348,152);center=[u(zone,104),u(zone,108)];zones=[dict(xyz=[*center,u(zone,116)])]
    bindings={};texts={};db=sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    with(PROFILE/'official-0.139.0-full.wat').open('rb')as f:
        claims=manifest['functions']|manifest['extra_static_functions']
        for key,row in claims.items():
            idx=int(key);r=db.execute('select *from functions where idx=?',(idx,)).fetchone();a,z=original['bodies'][idx]
            assert(a,z)==(r['body_start'],r['body_end']) and hashlib.sha256(raw[a:z]).hexdigest()==row['body_sha256']
            f.seek(r['wat_start']);value=f.read(r['wat_end']-r['wat_start']);h=hashlib.sha256(value).hexdigest();assert h==row['WAT_sha256']
            (out/f'{idx}.wat').write_bytes(value);bindings[key]=dict(body_sha256=row['body_sha256'],WAT_sha256=h);texts[idx]=value.decode()
    assert 'i32.const 56' in texts[1446]and'i32.const 1886'not in texts[1446]and'call 1886'in texts[1446]
    assert 'call 50441'in texts[1446]and'call 50441'not in texts[13563]
    assert original['types'][original['decl'][1886-882]]==('7f7f7f7f7f','7e')
    assert original['types'][original['decl'][1446-882]]==('7f7f7f7f','')
    cases=load(CASE/'inputs.json');expected=load(CASE/'expected.json');actual=[json.loads(x)for x in(CASE/'actual.jsonl').read_text().splitlines()]
    assert len(cases)==len(expected)==len(actual)==36
    counts=Counter()
    for i,(c,e,a)in enumerate(zip(cases,expected,actual,strict=True)):
        assert c['id']==e['id']==a['id']==i
        inp=dict(class_byte=1,race_byte=1,region_index=0,seed_u64=c['constructor_seed_u64'],object_id_u64='0',flat_height_bits=c['flat_height_bits'])
        ctor,known=constructor_reference(inp,classes,races,zones);claim=e['expected'];assert claim['constructor_cells']==known
        game=bytes.fromhex(a['constructor']['raw_Game2592_hex']);assert len(game)==2592
        for offset,v in enumerate(known):
            if v is None:counts['constructor_None_observed']+=1
            else:assert game[offset]==v;counts['constructor_known']+=1
        assert a['constructor']['rng_words']==ctor['rng_words']==claim['constructor_rng_words']
        selection=bytearray([0xa5]*40);selection[0:4]=bytes(4);selection[8:12]=bytes(4);selection[16:36]=bytes(20);selection[4]=selection[12]=255
        assert a['selected40_hex']==selection.hex()==claim['selected40_hex'] and a['selection_canaries']==['c3'*16,'d7'*16]
        assert a['account_unchanged']and a['profile_unchanged']and a['borrowed_flatquery_unchanged']
        ref=Reference(c,ctor,center);stages=[]
        if c['kind']=='actor':
            g=ref.emit(*c['descriptor'],c['xyz_bits'],c['kind21'],c['flags9']);stages.append(dict(role=1886,returned_guid=str(g),state=ref.state()))
        elif c['kind']=='pickup':
            for op in c['ops']:ref.pickup(op['xyz_bits'],op['amount'],op['now_bits']);stages.append(dict(role=1446,state=ref.state()))
        else:
            for amount in(2,1):
                xyz=ref.random_position();stages.append(dict(role=13563,position_bits=xyz,state=ref.state()));ref.pickup(xyz,amount,c['now_bits']);stages.append(dict(role=1446,state=ref.state()))
        assert stages==claim['stages']
        previous=a['before'];op_index=0
        for want,got in zip(stages,a['stages'],strict=True):
            assert want['role']==got['role'];counts[str(want['role'])]+=1;s=want['state'];g=got['state']
            for k in('returned_guid','position_bits'):
                if k in want:assert want[k]==got[k]
            for k in('counter','rng_words','phase2587'):assert s[k]==g[k]
            assert s['pickup_capacity']==g['pickups']['capacity']and s['pickup_count']==g['pickups']['count']
            assert s['packet_capacity']==g['packets']['capacity']and s['packets']==[[p['opcode'],p['payload_hex']]for p in g['packets']['active']]
            for row,hx in zip(s['storage'],g['pickups']['storage'],strict=True):
                for v,byte in zip(row,bytes.fromhex(hx),strict=True):
                    if v is None:counts['pickup_None_observed']+=1;counts['pickup_nonzero_None']+=byte!=0
                    else:assert v==byte;counts['pickup_known']+=1
            before=bytearray.fromhex(previous['raw_Game2592_hex']);after=bytes.fromhex(g['raw_Game2592_hex'])
            if c['kind']=='pickup':struct.pack_into('<I',before,2352,c['ops'][op_index]['now_bits']);op_index+=1
            for j,w in enumerate(s['rng_words']):struct.pack_into('<I',before,1720+4*j,w)
            for offset,v in((2408,s['counter']),(1868,s['pickup_capacity']),(1876,s['pickup_count']),(1880,s['packet_capacity']),(1888,len(s['packets']))):struct.pack_into('<I',before,offset,v)
            for field,offset in(('pickups',1872),('packets',1884)):
                if g[field]['capacity']!=previous[field]['capacity']:before[offset:offset+4]=after[offset:offset+4];counts['pointer_words_observed']+=1
            assert before==after;counts['relative_Game_bytes']+=2592
            n=previous['packets']['count'];assert previous['packets']['active']==g['packets']['active'][:n]
            assert previous['packets']['metadata_backing_hex'][:32*n]==g['packets']['metadata_backing_hex'][:32*n]
            previous=g
    assert counts['1886']==16 and counts['13563']==26 and counts['1446']==34
    assert counts['pickup_known']==7076 and counts['pickup_None_observed']==4572
    assert counts['constructor_known']==18072 and counts['constructor_None_observed']==75240
    assert counts['pointer_words_observed']==49 and counts['relative_Game_bytes']==196992
    assert runtime['full_calls']=={'2945':36,'1600':36,'1886':16,'13563':26,'1446':34}
    assert runtime['fresh_instances']==36 and runtime['host_calls']==0 and runtime['denied_imports']==882
    assert len(runtime['target_and_setup_returns'])==148 and all(x['returned']and x['before']==x['after']==1048576 for x in runtime['target_and_setup_returns'])
    terminal=load(CASE/'owned-terminal.json');assert terminal['exit_code']==0 and terminal['pid_missing']and terminal['pgid_missing']
    assert not runtime['original_snapshot_loaded'] and not runtime['App_produced'] and runtime['error']is None
    for n,h in author.items():assert sha(ROOT/n)==h
    result=dict(status='pass_current139_bounded_flat_actor_and_kind2_components',comparison_sha256=COMP,handoff_sha256=HAND,
        reviewer_source_sha256=sha(Path(__file__)),helper_sha256=HELPERS,counts=dict(counts),cases=36,
        current_source_sha256=SOURCE_SHA,full_WAT_bindings=bindings,source_files=31,local_edges=67,
        author_files=author,original_owned_process=terminal,reviewer_original_executions=0,
        reviewer_author_model_builder_checker_executions=0,author_files_modified=False,
        limitations=['Explicit borrowed flatquery/velocity0/pathNone only;not a native/nonflatworld/full1108 gameplay acceptance.',
            '2945/1600 are72 setup calls;known502B constructor mask recomputed with current source data,not a full profile/Game or physical ownership prediction.',
            '49 newly allocated pointer words are observations;196796 remaining relative Game byte occurrences checked strictly.',
            'Account/profile/borrowedquery conservation booleans are frozen runner assertions;complete raw before/after profile arrays are not separately serialized.',
            'Pickup padding remainsNone; packet prefix metadata and prior relative Game input are observed-state conservation,not independent allocators.',
            'No134/135 passed-case transfer;reused independent math/constructor helpers are rebound to current139 bodies/data and current actual outputs.'])
    (out/'review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(out=str(out.relative_to(ROOT)),review_sha256=sha(out/'review.json'),counts=dict(counts))))


if __name__=='__main__':main()
